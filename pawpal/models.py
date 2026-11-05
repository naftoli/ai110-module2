"""Plain data models shared by every other module. No scheduling or I/O logic lives here."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Union


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: int  # 1 (low) to 3 (high)
    pet_name: str
    is_required: bool = False
    completed: bool = False
    time: Union[str, datetime] = "00:00"
    recurrence: str = "once"
    due_date: Optional[datetime] = None
    fixed_time: bool = False

    def __post_init__(self) -> None:
        """Normalize recurrence and ensure each task has a real datetime value."""
        if self.recurrence not in {"once", "daily", "weekly"}:
            self.recurrence = "once"
        if isinstance(self.time, str):
            for fmt in ("%Y-%m-%d %H:%M", "%H:%M"):
                try:
                    self.time = datetime.strptime(self.time, fmt)
                    break
                except ValueError:
                    continue
            else:
                self.time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if self.due_date is None:
            self.due_date = self.time
        elif isinstance(self.due_date, str):
            for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    self.due_date = datetime.strptime(self.due_date, fmt)
                    break
                except ValueError:
                    continue

    def mark_complete(self) -> None:
        """Mark the task as completed."""
        self.completed = True

    def next_instance(self) -> Optional["Task"]:
        """Create the next recurring instance for the task using a real datetime offset."""
        if self.recurrence not in {"daily", "weekly"}:
            return None
        delta_days = 1 if self.recurrence == "daily" else 7
        next_time = self.time + timedelta(days=delta_days)
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            pet_name=self.pet_name,
            is_required=self.is_required,
            completed=False,
            time=next_time,
            recurrence=self.recurrence,
            due_date=next_time,
            fixed_time=self.fixed_time,
        )


@dataclass
class Pet:
    name: str
    species: str
    tasks: List[Task] = field(default_factory=list)

    def add_task(self, task: Task) -> None:
        """Add a task to this pet and assign it to the pet."""
        task.pet_name = self.name
        if task.due_date is None:
            task.due_date = task.time
        self.tasks.append(task)

    def complete_task(self, task: Task) -> Optional[Task]:
        """Mark a task complete and recreate it for the next recurring cycle if needed."""
        if task not in self.tasks:
            return None
        task.mark_complete()
        next_task = task.next_instance()
        if next_task is not None:
            self.tasks.append(next_task)
            return next_task
        return None

    def remove_task(self, task: Task) -> None:
        """Remove a task from this pet if it exists."""
        if task in self.tasks:
            self.tasks.remove(task)


@dataclass(frozen=True)
class AvailabilityWindow:
    starts_at: datetime
    ends_at: datetime


@dataclass
class OwnerPreferences:
    break_minutes: int = 0  # minimum gap required between two scheduled tasks


@dataclass
class Owner:
    name: str
    available_minutes: int
    pets: List[Pet] = field(default_factory=list)
    availability: List[AvailabilityWindow] = field(default_factory=list)
    preferences: OwnerPreferences = field(default_factory=OwnerPreferences)

    def add_pet(self, pet: Pet) -> None:
        """Add a pet to the owner's list of pets."""
        self.pets.append(pet)

    def get_all_tasks(self) -> List[Task]:
        """Return all tasks owned by this owner's pets."""
        return [task for pet in self.pets for task in pet.tasks]
