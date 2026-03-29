from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional


@dataclass
class Task:
    title: str
    duration_minutes: int
    priority: str           # "low", "medium", "high"
    is_completed: bool = False
    recur_days: int = 0         # 0 = one-time; >0 = repeat every N days
    pet_name: str = ""          # which pet this task belongs to (set by Pet.add_task)
    scheduled_time: str = ""    # optional wall-clock start time in "HH:MM" format
    due_date: date = field(default_factory=date.today)

    @property
    def priority_value(self) -> int:
        """Maps priority label to a numeric value for sorting (higher = more urgent)."""
        return {"low": 1, "medium": 2, "high": 3}.get(self.priority, 0)

    def mark_complete(self) -> None:
        """Mark this task as completed."""
        self.is_completed = True

    def next_occurrence(self) -> "Task":
        """Return a new Task representing the next recurrence of this task."""
        if self.recur_days <= 0:
            raise ValueError("Task does not recur.")
        return Task(
            title=self.title,
            duration_minutes=self.duration_minutes,
            priority=self.priority,
            recur_days=self.recur_days,
            pet_name=self.pet_name,
            scheduled_time=self.scheduled_time,
            is_completed=False,
            due_date=self.due_date + timedelta(days=self.recur_days),
        )

    def to_dict(self) -> dict:
        """Return a dictionary representation of this task."""
        return {
            "title": self.title,
            "duration_minutes": self.duration_minutes,
            "priority": self.priority,
            "is_completed": self.is_completed,
            "recur_days": self.recur_days,
            "pet_name": self.pet_name,
            "due_date": self.due_date.isoformat(),
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
        """Append a task to this pet's task list and tag it with the pet's name."""
        task.pet_name = self.name
        self.tasks.append(task)

    def get_pending_tasks(self) -> list[Task]:
        """Return all tasks that have not yet been completed."""
        return [t for t in self.tasks if not t.is_completed]

    def get_tasks_by_status(self, completed: bool) -> list[Task]:
        """Filter tasks by completion status."""
        return [t for t in self.tasks if t.is_completed == completed]


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

    def get_tasks_for_pet(self, pet_name: str) -> list[Task]:
        """Return all tasks belonging to a specific pet by name."""
        for pet in self.pets:
            if pet.name == pet_name:
                return pet.tasks
        return []

    def get_recurring_tasks(self) -> list[Task]:
        """Return all tasks that are set to recur."""
        return [t for t in self.get_all_tasks() if t.recur_days > 0]


@dataclass
class DailyPlan:
    tasks: list[Task] = field(default_factory=list)
    total_duration: int = 0
    reasoning: str = ""
    conflicts: list[str] = field(default_factory=list)  # human-readable conflict messages

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
            recur = f" (recurs every {task.recur_days}d)" if task.recur_days > 0 else ""
            pet   = f" [{task.pet_name}]" if task.pet_name else ""
            lines.append(
                f"  {i}. {status}{pet} {task.title}"
                f" ({task.duration_minutes} min, {task.priority} priority{recur})"
            )
        if self.conflicts:
            lines.append("\nConflicts detected:")
            for c in self.conflicts:
                lines.append(f"  [!] {c}")
        if self.reasoning:
            lines.append(f"\nReasoning: {self.reasoning}")
        return "\n".join(lines)


class Scheduler:
    def __init__(self, tasks: list[Task], available_minutes: int, pet: Optional[Pet] = None):
        """Initialise the scheduler with a task pool, a time budget, and an optional pet context."""
        self.tasks = tasks
        self.available_minutes = available_minutes
        self.pet = pet

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def generate_plan(self) -> DailyPlan:
        """Select pending tasks sorted by priority; detect conflicts; expand recurring tasks."""
        pending = self._expand_recurring([t for t in self.tasks if not t.is_completed])
        sorted_tasks = self._sort_by_priority(pending)

        plan = DailyPlan()
        for task in sorted_tasks:
            if plan.total_duration + task.duration_minutes <= self.available_minutes:
                plan.add_task(task)

        plan.conflicts = self._detect_conflicts(plan.tasks)
        plan.reasoning = self._build_reasoning(sorted_tasks, plan)
        return plan

    def filter_by_pet(self, pet_name: str) -> list[Task]:
        """Return only tasks that belong to the named pet."""
        return [t for t in self.tasks if t.pet_name == pet_name]

    def filter_by_status(self, completed: bool) -> list[Task]:
        """Return tasks filtered by completion status."""
        return [t for t in self.tasks if t.is_completed == completed]

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by scheduled_time (HH:MM); tasks with no time set sort to the end."""
        return sorted(tasks, key=lambda t: t.scheduled_time if t.scheduled_time else "99:99")

    def sort_by_duration(self, tasks: list[Task], ascending: bool = True) -> list[Task]:
        """Sort a list of tasks by duration."""
        return sorted(tasks, key=lambda t: t.duration_minutes, reverse=not ascending)

    def explain_plan(self, plan: DailyPlan) -> str:
        """Return a human-readable explanation of the generated plan."""
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

    def mark_task_complete(self, task: Task, pet: "Pet") -> Optional["Task"]:
        """Mark a task done; if it recurs, auto-spawn the next occurrence on the pet and return it."""
        task.mark_complete()
        if task.recur_days > 0:
            new_task = task.next_occurrence()
            pet.add_task(new_task)
            self.tasks.append(new_task)
            return new_task
        return None

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Sort tasks by priority desc, then duration asc as a tiebreaker."""
        return sorted(tasks, key=lambda t: (-t.priority_value, t.duration_minutes))

    def _expand_recurring(self, tasks: list[Task]) -> list[Task]:
        """
        For every recurring task that is completed, generate a fresh copy so it
        re-appears in today's plan (simulating the next occurrence).
        """
        result = []
        for task in tasks:
            result.append(task)
        # Add reset copies of completed recurring tasks so they re-enter the pool
        for task in self.tasks:
            if task.recur_days > 0 and task.is_completed:
                fresh = Task(
                    title=task.title,
                    duration_minutes=task.duration_minutes,
                    priority=task.priority,
                    recur_days=task.recur_days,
                    pet_name=task.pet_name,
                )
                result.append(fresh)
        return result

    def _detect_conflicts(self, planned: list[Task]) -> list[str]:
        """
        Flag simple conflicts:
        - Duplicate task titles for the same pet in the full pending pool.
        - Any single task that exceeds the total available time.
        """
        conflicts: list[str] = []
        seen: set[str] = set()

        # Check the full pending pool for duplicates, not just what fit in the plan
        pending = [t for t in self.tasks if not t.is_completed]
        for task in pending:
            key = f"{task.pet_name}:{task.title.lower()}"
            if key in seen:
                conflicts.append(
                    f'"{task.title}" is scheduled more than once for '
                    f'{task.pet_name or "unknown pet"} today.'
                )
            else:
                seen.add(key)

        # Check planned tasks for ones that alone exceed availability
        for task in planned:
            if task.duration_minutes > self.available_minutes:
                conflicts.append(
                    f'"{task.title}" ({task.duration_minutes} min) exceeds the full '
                    f"{self.available_minutes}-minute availability window."
                )

        # Check for time-slot collisions across all pending tasks
        conflicts.extend(self._detect_time_conflicts(pending))

        return conflicts

    def _detect_time_conflicts(self, tasks: list[Task]) -> list[str]:
        """
        Lightweight time-slot collision check.
        Groups tasks by scheduled_time; if two or more share the same non-empty
        slot, emit a warning message instead of raising an exception.
        """
        from collections import defaultdict
        slot_map: dict[str, list[Task]] = defaultdict(list)
        for task in tasks:
            if task.scheduled_time:
                slot_map[task.scheduled_time].append(task)

        warnings: list[str] = []
        for time_slot, colliding in slot_map.items():
            if len(colliding) > 1:
                names = ", ".join(
                    f'"{t.title}" ({t.pet_name or "no pet"})' for t in colliding
                )
                warnings.append(
                    f"[TIME CONFLICT] {time_slot} has {len(colliding)} overlapping tasks: {names}."
                )
        return warnings

    def check_time_conflicts(self) -> list[str]:
        """Public helper: return time-slot conflict warnings for all pending tasks."""
        pending = [t for t in self.tasks if not t.is_completed]
        return self._detect_time_conflicts(pending)

    def _build_reasoning(self, sorted_tasks: list[Task], plan: DailyPlan) -> str:
        """Summarise why tasks were included or skipped."""
        if not plan.tasks:
            return "No tasks fit within the available time."
        included = len(plan.tasks)
        skipped  = len(sorted_tasks) - included
        msg = f"Selected {included} highest-priority task(s) that fit in {self.available_minutes} min"
        if skipped:
            msg += f"; skipped {skipped} task(s) that exceeded the remaining time"
        msg += "."
        return msg
