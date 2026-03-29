# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions a user should be able to perform in PawPal+:

1. **Add a pet** — The user enters their pet's basic information (name, species, age, and any special needs). This sets up the context the scheduler uses when evaluating task priorities. For example, an older dog may have more frequent medication tasks, and the system should know that before generating a plan.

2. **Add or edit a care task** — The user creates a task (such as a walk, feeding, or grooming session) and sets its duration and priority level. They can also edit an existing task if the pet's routine changes. This action is the primary way the user builds the list of things that need to happen each day.

3. **Generate and view today's plan** — The user triggers the scheduler, which takes the current task list and any time or priority constraints and produces a daily schedule. The plan is displayed with an explanation of why tasks were ordered the way they were, so the owner understands the reasoning and can trust the output.

The initial UML design includes five classes: `Pet`, `Task`, `Owner`, `DailyPlan`, and `Scheduler`.

- **Pet** — a data container for the animal's basic profile: name, species, age, and any special needs. Its only method, `get_summary()`, returns a readable description. It holds no logic.

- **Task** — a data container for a single care activity. It stores a title, duration in minutes, a priority label (low/medium/high), and a completion flag. It has a `mark_complete()` method to flip the flag and a `to_dict()` method for display.

- **Owner** — ties together the person using the app, their time budget for the day, and the list of tasks they've created. It also holds a reference to their one Pet. `set_availability()` lets the UI update the time budget.

- **DailyPlan** — the output object produced by the Scheduler. It holds the ordered list of selected tasks, the total duration of those tasks, and a plain-text reasoning string. `add_task()` appends to the list; `get_summary()` formats the plan for display.

- **Scheduler** — the only class with real logic. It receives a task list, a time budget, and optionally a Pet reference, then produces a `DailyPlan` via `generate_plan()` and a human-readable explanation via `explain_plan()`.

**b. Design changes**

After reviewing the skeleton, two issues were identified and fixed:

1. **Added `pet` parameter to `Scheduler`** — The original design passed only `tasks` and `available_minutes` to the Scheduler, meaning pet-specific context (age, special needs) was completely inaccessible during scheduling. For example, a senior pet's medication task should arguably be treated as high priority regardless of what the owner labeled it. Adding `pet` as an optional parameter gives the Scheduler the information it needs to make those adjustments later.

2. **Added `priority_value` property to `Task`** — Priority was stored as the string `"low"`, `"medium"`, or `"high"`. Sorting tasks by priority in `generate_plan()` would have required comparing strings directly, which is fragile. The `priority_value` property maps those labels to integers (1, 2, 3), so sorting becomes a simple numeric comparison: `sorted(tasks, key=lambda t: t.priority_value, reverse=True)`.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

**Tradeoff: Exact time-slot matching instead of overlap detection based on duration**

The current conflict detector flags two tasks as a conflict only when their `scheduled_time` strings are exactly equal (e.g., both set to `"07:00"`). It does not check whether one task's *duration* causes it to run into another task's start time. For example, a 30-minute walk starting at `07:00` would not be flagged as conflicting with a 5-minute feeding starting at `07:15`, even though the walk is still in progress at that moment.

This is a deliberate simplicity tradeoff. Implementing true interval-overlap detection would require converting `"HH:MM"` strings into `datetime` objects, computing each task's end time as `start + timedelta(minutes=duration)`, and then checking every pair of tasks for `start_a < end_b and start_b < end_a`. That is roughly O(n²) in comparisons and adds meaningful parsing and error-handling complexity (e.g., what if `scheduled_time` is missing or malformed?).

For a daily pet-care planner where tasks are short, loosely scheduled, and entered by a single owner, exact-match detection catches the most common and obvious mistake — accidentally assigning two things to the same time slot — without introducing fragile time-arithmetic logic. A pet owner noticing a `[TIME CONFLICT]` warning on `07:00` can immediately understand and fix it. A more precise overlap warning like *"Morning walk ends at 07:30, which overlaps with Brush teeth starting at 07:15"* would be more accurate but also more complex to implement correctly and interpret quickly. The simpler strategy is the right fit for this scope.

---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
