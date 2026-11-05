"""Backward-compatible entry point: the code now lives in the `pawpal` package."""

from pawpal.legacy import DailyPlan, Scheduler, SkippedTask
from pawpal.models import Owner, Pet, Task

__all__ = ["DailyPlan", "Owner", "Pet", "Scheduler", "SkippedTask", "Task"]
