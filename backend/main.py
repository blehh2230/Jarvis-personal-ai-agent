
import asyncio
from uuid import uuid4

from fastapi import BackgroundTasks, FastAPI, HTTPException

from backend.schemas import TaskCreate, TaskResponse, TaskStep

app = FastAPI(
    title="JARVIS Personal AI Agent",
    description="AI-powered task planning and execution API.",
    version="0.2.0",
)

# Temporary in-memory storage for the hackathon prototype.
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
        "version": "0.2.0",
    }


async def run_task(task_id: str):
    """Demonstrate task lifecycle until the real AI executor is integrated."""
    task = TASKS[task_id]
    task["status"] = "running"

    for step in task["steps"]:
        step["status"] = "running"
        await asyncio.sleep(0.5)

        step["status"] = "completed"
        step["result"] = (
            "Demo step completed. No external action was performed."
        )

    task["status"] = "completed"
    task["result"] = (
        "Demo workflow completed. Real AI planning and approved tool "
        "execution will be integrated next."
    )


@app.post("/api/tasks", response_model=TaskResponse, status_code=202)
async def create_task(
    request: TaskCreate,
    background_tasks: BackgroundTasks,
):
    task_id = str(uuid4())

    task = {
        "task_id": task_id,
        "instruction": request.instruction,
        "status": "queued",
        "steps": [
            TaskStep(
                step_id=1,
                description="Validate the task instruction",
            ).model_dump(),
            TaskStep(
                step_id=2,
                description="Prepare the task workflow",
            ).model_dump(),
            TaskStep(
                step_id=3,
                description="Prepare the execution result",
            ).model_dump(),
        ],
        "result": None,
        "error": None,
    }

    TASKS[task_id] = task
    background_tasks.add_task(run_task, task_id)

    return task


@app.get("/api/tasks/{task_id}", response_model=TaskResponse)
async def get_task(task_id: str):
    task = TASKS.get(task_id)

    if task is None:
        raise HTTPException(
            status_code=404,
            detail="Task not found.",
        )

    return task
