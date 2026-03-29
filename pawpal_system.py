from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    age: int
    special_needs: str = ""

    def get_summary(self) -> str:
        pass


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    is_completed: bool = False

    def mark_complete(self) -> None:
        pass

    def to_dict(self) -> dict:
        pass


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: str = ""
    pet: Optional[Pet] = None
    tasks: list[Task] = field(default_factory=list)

    def set_availability(self, minutes: int) -> None:
        pass


@dataclass
class DailyPlan:
    tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    reasoning: str = ""

    def add_task(self, task: Task) -> None:
        pass

    def get_summary(self) -> str:
        pass


class Scheduler:
    def __init__(self, tasks: list[Task], available_minutes: int):
        self.tasks = tasks
        self.available_minutes = available_minutes

    def generate_plan(self) -> DailyPlan:
        pass

    def explain_plan(self, plan: DailyPlan) -> str:
        pass
