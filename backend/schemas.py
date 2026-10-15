
from typing import Literal

from pydantic import BaseModel, Field


TaskStatus = Literal["queued", "running", "completed", "failed"]
StepStatus = Literal["queued", "running", "completed", "failed"]


class TaskCreate(BaseModel):
    instruction: str = Field(
        min_length=3,
        max_length=2000,
        description="The task JARVIS should process.",
    )


class TaskStep(BaseModel):
    step_id: int
    description: str
    status: StepStatus = "queued"
    result: str | None = None


class TaskResponse(BaseModel):
    task_id: str
    instruction: str
    status: TaskStatus
    steps: list[TaskStep]
    result: str | None = None
    error: str | None = None
