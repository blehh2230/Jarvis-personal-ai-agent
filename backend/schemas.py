from typing import Literal

from pydantic import BaseModel, Field


TaskStatus = Literal[
    "queued",
    "running",
    "planned",
    "completed",
    "blocked",
    "failed",
]

StepStatus = Literal[
    "queued",
    "running",
    "completed",
    "blocked",
    "failed",
]


class TaskCreate(BaseModel):
    """Request schema for creating a task."""

    instruction: str = Field(
        ...,
        min_length=5,
        max_length=2000,
        description="The instruction JARVIS should process.",
    )


class TaskStep(BaseModel):
    """An individual step in a task plan."""

    step_id: int = Field(..., ge=1)
    description: str = Field(..., min_length=1)
    status: StepStatus = "queued"
    expected_output: str | None = None
    result: str | None = None


class TaskResponse(BaseModel):
    """Task details and execution progress."""

    task_id: str
    instruction: str
    status: TaskStatus
    steps: list[TaskStep] = Field(default_factory=list)
    result: str | None = None
    error: str | None = None