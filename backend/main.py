import logging
import os
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.executor import execute_task as execute_task_steps
from backend.planner import generate_plan
from backend.schemas import TaskCreate, TaskResponse, TaskStep


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("jarvis")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

app = FastAPI(
    title="JARVIS Personal AI Agent",
    description="AI-powered task planning and execution API.",
    version="0.4.0",
)

# Enable CORS for local and web frontend origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Temporary in-memory storage.
TASKS: dict[str, dict] = {}


@app.get("/")
async def root():
    return {
        "app": "JARVIS",
        "message": "Personal AI Agent API is running.",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "app": "JARVIS",
        "version": "0.4.0",
    }


async def run_task(task_id: str):
    """Generate and store a task plan."""

    task = TASKS.get(task_id)

    if task is None:
        logger.error("Task %s was not found.", task_id)
        return

    task["status"] = "running"

    try:
        plan = await generate_plan(task["instruction"])

        task["steps"] = [
            TaskStep(
                step_id=index,
                description=f"{step.title}: {step.description}",
                expected_output=step.expected_output,
            ).model_dump()
            for index, step in enumerate(plan.steps, start=1)
        ]

        task["result"] = plan.summary
        task["status"] = "planned"
        task["error"] = None

        logger.info(
            "Task %s planned with %s steps.",
            task_id,
            len(plan.steps),
        )

    except Exception:
        logger.exception("Planning failed for task %s.", task_id)

        task["status"] = "failed"
        task["error"] = (
            "Planning failed. Check the server logs and "
            "Groq configuration."
        )


@app.post(
    "/api/tasks",
    response_model=TaskResponse,
    status_code=202,
)
async def create_task(
    request: TaskCreate,
    background_tasks: BackgroundTasks,
):
    """Create a task and generate its plan in the background."""

    task_id = str(uuid4())

    task = {
        "task_id": task_id,
        "instruction": request.instruction,
        "status": "queued",
        "steps": [],
        "result": None,
        "error": None,
    }

    TASKS[task_id] = task
    background_tasks.add_task(run_task, task_id)

    return task


@app.get(
    "/api/tasks/{task_id}",
    response_model=TaskResponse,
)
async def get_task(task_id: str):
    """Retrieve task details and progress."""

    task = TASKS.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found.",
        )

    return task


@app.get(
    "/api/tasks",
    response_model=list[TaskResponse],
)
async def list_tasks():
    """Retrieve all tracked tasks."""
    return list(TASKS.values())


@app.post("/api/workflows/briefing")
async def run_briefing_workflow():
    """Execute the meeting briefing workflow with audit logging."""
    try:
        import sys
        import time
        if PROJECT_ROOT not in sys.path:
            sys.path.insert(0, PROJECT_ROOT)
        from tools import create_briefing
        out_name = f"outputs/meeting_briefing_{int(time.time())}.txt"
        result = create_briefing(output_path=out_name)
        return result
    except Exception as exc:
        logger.exception("Briefing workflow error.")
        raise HTTPException(status_code=500, detail=str(exc))


@app.post(
    "/api/tasks/{task_id}/execute",
    response_model=TaskResponse,
    status_code=202,
)
async def start_task_execution(
    task_id: str,
    background_tasks: BackgroundTasks,
):
    """Start executing a previously generated plan."""

    task = TASKS.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found.",
        )

    if task["status"] != "planned":
        raise HTTPException(
            status_code=409,
            detail=(
                "Only tasks with status 'planned' can be executed. "
                f"Current status: {task['status']}."
            ),
        )

    if not task["steps"]:
        raise HTTPException(
            status_code=409,
            detail="This task has no steps to execute.",
        )

    # Reserve the task before scheduling the background job.
    task["status"] = "running"
    task["error"] = None

    background_tasks.add_task(execute_task_steps, task)

    logger.info("Execution requested for task %s.", task_id)

    return task


@app.get("/app", include_in_schema=False)
async def serve_app():
    """Serve the JARVIS Command Center frontend."""
    index_file = os.path.join(PROJECT_ROOT, "index.html")
    if os.path.exists(index_file):
        return FileResponse(index_file)
    raise HTTPException(status_code=404, detail="index.html not found.")


@app.get("/api.js", include_in_schema=False)
async def serve_api_js():
    """Serve the centralized API client service."""
    js_file = os.path.join(PROJECT_ROOT, "api.js")
    if os.path.exists(js_file):
        return FileResponse(js_file, media_type="application/javascript")
    raise HTTPException(status_code=404, detail="api.js not found.")