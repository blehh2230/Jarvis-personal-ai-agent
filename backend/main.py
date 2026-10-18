import logging
import os
from uuid import uuid4

from typing import Optional
from fastapi import BackgroundTasks, FastAPI, HTTPException, Request
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
async def root(request: Request):
    accept = request.headers.get("accept", "")
    if "text/html" in accept:
        index_file = os.path.join(PROJECT_ROOT, "index.html")
        if os.path.exists(index_file):
            return FileResponse(index_file)

    return {
        "app": "JARVIS",
        "message": "Personal AI Agent API is running.",
        "ui": "/app",
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

        summary_text = ""
        msg = ""
        if isinstance(result.get("output"), dict):
            summary_text = result["output"].get("summary", "")
            msg = result["output"].get("message", "")
        elif isinstance(result.get("output"), str):
            summary_text = result["output"]

        return {
            "success": result.get("success", True),
            "summary": summary_text,
            "output": result.get("output"),
            "file": out_name,
            "message": msg,
            "audit_entry": f"Audit logged to outputs/audit.log at {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "error": result.get("error"),
        }
    except Exception as exc:
        logger.exception("Briefing workflow error.")
        raise HTTPException(status_code=500, detail=str(exc))


from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(..., min_length=1)
    max_sentences: int = Field(3, ge=1, le=20)


class SaveBriefingRequest(BaseModel):
    content: str = Field(..., min_length=1)
    filepath: Optional[str] = None


class AuditLogRequest(BaseModel):
    message: str = Field(..., min_length=1)


@app.get("/api/tools")
async def list_tools_inventory():
    """List all available tools and their operational status."""
    return {
        "tools": [
            {
                "id": "read_notes",
                "name": "read_notes",
                "status": "ONLINE",
                "desc": "Ingests user notes and operational text files from disk workspace.",
                "type": "file_reader"
            },
            {
                "id": "summarize_text",
                "name": "summarize_text",
                "status": "ONLINE",
                "desc": "Produces concise executive summaries.",
                "type": "nlp_summarizer"
            },
            {
                "id": "save_briefing",
                "name": "save_briefing",
                "status": "ONLINE",
                "desc": "Writes structured briefings to outputs directory with file protection.",
                "type": "file_writer"
            },
            {
                "id": "audit_logger",
                "name": "audit_log_event",
                "status": "ONLINE",
                "desc": "Event logging with timestamps into outputs/audit.log.",
                "type": "audit_system"
            },
            {
                "id": "tavily_web_search",
                "name": "tavily_web_search",
                "status": "ONLINE" if os.getenv("TAVILY_API_KEY") else "STANDBY",
                "desc": "Searches the live web for verified facts and citations.",
                "type": "web_search"
            },
            {
                "id": "python_shell_executor",
                "name": "python_shell_executor",
                "status": "ONLINE",
                "desc": "Isolated Python verification and execution environment.",
                "type": "code_executor"
            }
        ]
    }


@app.post("/api/tools/read-notes")
async def tool_read_notes(filename: Optional[str] = None):
    """Execute read_notes tool."""
    import sys
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from tools import read_notes
    fn = filename or "sample_data/meeting_notes.txt"
    return read_notes(fn)


@app.post("/api/tools/summarize")
async def tool_summarize(req: SummarizeRequest):
    """Execute summarize_text tool."""
    import sys
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from tools import summarize_text
    return summarize_text(req.text, req.max_sentences)


@app.post("/api/tools/save-briefing")
async def tool_save_briefing(req: SaveBriefingRequest):
    """Execute save_briefing tool."""
    import sys
    import time
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from tools import save_briefing
    fp = req.filepath or f"outputs/meeting_briefing_{int(time.time())}.txt"
    res = save_briefing(req.content, fp)
    res["filepath"] = fp
    return res


@app.get("/api/tools/audit-log")
async def tool_get_audit_log(limit: int = 20):
    """Retrieve recent lines from audit log."""
    log_path = os.path.join(PROJECT_ROOT, "outputs", "audit.log")
    if not os.path.exists(log_path):
        return {"events": [], "count": 0}
    with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
        lines = [line.strip() for line in f.readlines() if line.strip()]
    return {"events": lines[-limit:], "total": len(lines)}


@app.post("/api/tools/audit-log")
async def tool_post_audit_log(req: AuditLogRequest):
    """Record an audit event."""
    import sys
    if PROJECT_ROOT not in sys.path:
        sys.path.insert(0, PROJECT_ROOT)
    from audit import log_event
    log_event(req.message)
    return {"success": True, "logged": req.message}


@app.post("/api/testing/run")
async def run_automated_tests():
    """Run pytest suite programmatically and return execution results."""
    import subprocess
    import sys
    import time

    start_time = time.time()
    python_bin = sys.executable

    try:
        proc = subprocess.run(
            [python_bin, "-m", "pytest", "tests", "-v", "--tb=short"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=30,
        )
        duration = round(time.time() - start_time, 2)
        output = proc.stdout + ("\n" + proc.stderr if proc.stderr else "")
        passed = proc.returncode == 0

        return {
            "success": passed,
            "returncode": proc.returncode,
            "duration_seconds": duration,
            "output": output,
            "status": "ALL TESTS PASSED" if passed else "TESTS FAILED",
        }
    except Exception as exc:
        return {
            "success": False,
            "error": str(exc),
            "status": "ERROR RUNNING TESTS",
        }


from backend.memory import (
    add_memory as add_memory_record,
    delete_memory as delete_memory_record,
    get_real_memory_insights,
    load_memories as load_memory_records,
)
from pydantic import BaseModel, Field


class MemoryCreateRequest(BaseModel):
    text: str = Field(..., min_length=2, max_length=2000)
    cat: str = Field("GENERAL", max_length=50)
    tag: str = Field("OPERATOR", max_length=50)


@app.get("/api/memory/insights")
async def get_memory_insights_endpoint():
    """Retrieve real memory telemetry, audit counts, and system RAM usage."""
    return get_real_memory_insights(active_tasks_count=len(TASKS))


@app.get("/api/memory/items")
async def get_memory_items_endpoint():
    """Retrieve all persistent memory items."""
    return load_memory_records()


@app.post("/api/memory/items", status_code=201)
async def create_memory_item_endpoint(request: MemoryCreateRequest):
    """Store and persist a new memory vector record."""
    new_mem = add_memory_record(
        text=request.text,
        cat=request.cat,
        tag=request.tag,
    )
    return new_mem


@app.delete("/api/memory/items/{memory_id}")
async def delete_memory_item_endpoint(memory_id: str):
    """Delete a memory record by ID."""
    success = delete_memory_record(memory_id)
    if not success:
        raise HTTPException(status_code=404, detail="Memory item not found.")
    return {"status": "deleted", "id": memory_id}



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