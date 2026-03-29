from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str  # "low", "medium", "high"
    is_completed: bool = False

    @property
    def priority_value(self) -> int:
        """Maps priority label to a numeric value for sorting (higher = more urgent)."""
        return {"low": 1, "medium": 2, "high": 3}.get(self.priority, 0)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "is_completed": self.is_completed,
        }


@dataclass
class Pet:
    name: str
    species: str  # "dog", "cat", "other"
    age: int
    special_needs: str = ""
    tasks: list[Task] = field(default_factory=list)

    def get_summary(self) -> str:
        """Return a one-line overview of the pet and its task progress."""
        completed = sum(1 for t in self.tasks if t.is_completed)
        return (
            f"{self.name} ({self.species}, age {self.age})"
            + (f" — special needs: {self.special_needs}" if self.special_needs else "")
            + f" | Tasks: {len(self.tasks)} total, {completed} completed"
        )

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self.tasks.append(task)

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.is_completed]


@dataclass
class Owner:
    name: str
    available_minutes: int
    preferences: str = ""
    pets: list[Pet] = field(default_factory=list)

    def set_availability(self, minutes: int) -> None:
        """Update the number of minutes the owner has available today."""
        self.available_minutes = minutes

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        self.pets.append(pet)

    def get_all_tasks(self) -> list[Task]:
        """Returns all tasks across every pet."""
        return [task for pet in self.pets for task in pet.tasks]

    def get_pending_tasks(self) -> list[Task]:
        """Returns only incomplete tasks across every pet."""
        return [task for pet in self.pets for task in pet.get_pending_tasks()]


@dataclass
class DailyPlan:
    tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    reasoning: str = ""

    def add_task(self, task: Task) -> None:
        """Add a task to the plan and accumulate its duration."""
        self.tasks.append(task)
        self.total_duration += task.duration_minutes

    def get_summary(self) -> str:
        """Return a formatted checklist of all planned tasks with durations."""
        if not self.tasks:
            return "No tasks scheduled."
        lines = [f"Daily Plan ({self.total_duration} min total):"]
        for i, task in enumerate(self.tasks, 1):
            status = "[done]" if task.is_completed else "[ ]"
            lines.append(f"  {i}. {status} {task.title} ({task.duration_minutes} min, {task.priority} priority)")
        if self.reasoning:
            lines.append(f"\nReasoning: {self.reasoning}")
        return "\n".join(lines)


class Scheduler:
    def __init__(self, tasks: list[Task], available_minutes: int, pet: Optional[Pet] = None):
        self.tasks = tasks
        self.available_minutes = available_minutes
        self.pet = pet  # optional pet context for priority adjustments

    def generate_plan(self) -> DailyPlan:
        """
        Selects pending tasks that fit within available_minutes,
        sorted by priority (highest first).
        """
        pending = [t for t in self.tasks if not t.is_completed]
        # Sort by priority descending, then by duration ascending as a tiebreaker
        sorted_tasks = sorted(pending, key=lambda t: (-t.priority_value, t.duration_minutes))

        plan = DailyPlan()
        for task in sorted_tasks:
            if plan.total_duration + task.duration_minutes <= self.available_minutes:
                plan.add_task(task)

        plan.reasoning = self._build_reasoning(sorted_tasks, plan)
        return plan

    def explain_plan(self, plan: DailyPlan) -> str:
        if not plan.tasks:
            return (
                f"No tasks could be scheduled within the {self.available_minutes}-minute window. "
                "Consider reducing task durations or increasing availability."
            )
        skipped = [t for t in self.tasks if not t.is_completed and t not in plan.tasks]
        lines = [
            f"Scheduled {len(plan.tasks)} task(s) using {plan.total_duration} of "
            f"{self.available_minutes} available minutes."
        ]
        if self.pet:
            lines.append(f"Optimized for {self.pet.name} ({self.pet.species}).")
        if skipped:
            skipped_titles = ", ".join(t.title for t in skipped)
            lines.append(f"Skipped due to time constraints: {skipped_titles}.")
        lines.append(plan.get_summary())
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _build_reasoning(self, sorted_tasks: list[Task], plan: DailyPlan) -> str:
        if not plan.tasks:
            return "No tasks fit within the available time."
        included = len(plan.tasks)
        skipped = len(sorted_tasks) - included
        msg = f"Selected {included} highest-priority task(s) that fit in {self.available_minutes} min"
        if skipped:
            msg += f"; skipped {skipped} task(s) that exceeded the remaining time"
        msg += "."
        return msg
