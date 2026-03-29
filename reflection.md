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

The scheduler considers three constraints:

1. **Time budget** (`available_minutes`) — the hard ceiling. No combination of tasks in a plan can exceed this value. This was treated as the most important constraint because it is non-negotiable: the owner either has time or they don't, and a plan that overruns is worse than no plan at all.

2. **Priority** (`high / medium / low`) — the primary sorting key. Tasks are ranked numerically (3 / 2 / 1) and sorted descending before the greedy selection loop runs. This ensures that if something must be dropped, it is always the lowest-priority item.

3. **Duration as a tiebreaker** — when two tasks share the same priority level, the shorter one is scheduled first. This is a secondary heuristic: fitting a 5-minute task before a 25-minute one of equal importance leaves more flexibility for what comes after.

Owner `preferences` is stored as a free-text string but is not yet parsed into scheduling logic — it is available as context for a future AI-assisted priority adjustment based on pet age or special needs.

**b. Tradeoffs**

**Tradeoff: Exact time-slot matching instead of overlap detection based on duration**

The current conflict detector flags two tasks as a conflict only when their `scheduled_time` strings are exactly equal (e.g., both set to `"07:00"`). It does not check whether one task's *duration* causes it to run into another task's start time. For example, a 30-minute walk starting at `07:00` would not be flagged as conflicting with a 5-minute feeding starting at `07:15`, even though the walk is still in progress at that moment.

This is a deliberate simplicity tradeoff. Implementing true interval-overlap detection would require converting `"HH:MM"` strings into `datetime` objects, computing each task's end time as `start + timedelta(minutes=duration)`, and then checking every pair of tasks for `start_a < end_b and start_b < end_a`. That is roughly O(n²) in comparisons and adds meaningful parsing and error-handling complexity (e.g., what if `scheduled_time` is missing or malformed?).

For a daily pet-care planner where tasks are short, loosely scheduled, and entered by a single owner, exact-match detection catches the most common and obvious mistake — accidentally assigning two things to the same time slot — without introducing fragile time-arithmetic logic. A pet owner noticing a `[TIME CONFLICT]` warning on `07:00` can immediately understand and fix it. A more precise overlap warning like *"Morning walk ends at 07:30, which overlaps with Brush teeth starting at 07:15"* would be more accurate but also more complex to implement correctly and interpret quickly. The simpler strategy is the right fit for this scope.

---

## 3. AI Collaboration

**a. How you used AI**

AI was used across every phase of the project, but in different roles at different times:

- **Design phase** — Agent Mode was used to generate the initial class stubs and think through relationships (e.g., whether `Owner` should hold one `Pet` or many). The most useful prompt type here was asking "what would break if I designed it this way instead?" to surface tradeoffs before writing any code.

- **Implementation phase** — Inline Chat was used for targeted method generation: asking for a lambda sort key for `"HH:MM"` strings, for the `timedelta` pattern to advance a due date, and for the `defaultdict` grouping pattern used in conflict detection. These are small, self-contained patterns where AI is fast and reliable.

- **Testing phase** — Chat with `#codebase` was used to ask "what edge cases should I test for a scheduler with recurring tasks and time conflicts?" The response surfaced several cases (empty task list, task longer than the full budget, cross-pet time collisions) that would not have been immediately obvious from just rereading the code.

- **Debugging** — When tests failed, Inline Chat on the failing assertion was used to distinguish between a test logic error and a system logic error. In every case the explanation was accurate and pointed to the right fix immediately.

The most effective prompt pattern overall was being specific about scope: instead of "write tests for my scheduler," asking "write a test that verifies a recurring task spawns a new instance on the correct due date when marked complete." Narrow, concrete prompts produced usable code; broad prompts produced boilerplate that needed heavy editing.

**b. Judgment and verification**

The clearest example of rejecting an AI suggestion was during conflict detection. The initial AI-generated `_detect_conflicts` method only checked tasks that made it into the final `DailyPlan` — meaning a duplicate task that got cut by the time budget would never trigger a warning. The code was syntactically correct and passed a naive reading, but testing it with a deliberate duplicate that exceeded the available time showed it silently produced no warning.

The fix was to change the check to scan the full *pending pool* rather than just the scheduled tasks. This required understanding *why* the original suggestion was wrong, not just that it was. The verification step was writing a test first (`test_time_conflict_detected_for_same_slot`) and watching it fail against the AI-generated version, then confirming it passed after the fix. Running the test before accepting the logic — rather than trusting the code because it looked plausible — was the key habit that caught the issue.

---

## 4. Testing and Verification

**a. What you tested**

The 18-test suite covers five areas:

- **Task basics** — `mark_complete` flips the flag; `add_task` grows the list; the pet name is stamped automatically. These were tested first because every other behavior depends on them.
- **Sorting** — Tasks added in reverse order come out chronologically; tasks without a time sort last; `sort_by_duration` produces ascending order. Sorting is silent — it never raises an error — so the only way to verify it is to assert on the output order.
- **Recurrence** — `next_occurrence` advances `due_date` by exactly `recur_days` days (daily and weekly); calling it on a one-time task raises `ValueError`; `mark_task_complete` registers the new task on both the pet and the scheduler pool; one-time completion returns `None`. These were the highest-risk behaviors because they involve state mutation across two objects simultaneously.
- **Conflict detection** — Same-pet and cross-pet time collisions are both flagged; different times produce no warning. This tested both the true-positive and true-negative paths to ensure the detector was neither too noisy nor silent.
- **Edge cases** — Empty task list, task longer than the full budget, completed tasks excluded from pending views, filter correctness.

**b. Confidence**

★★★★☆ (4 / 5)

All 18 tests pass. Confidence is high for the core scheduling loop, recurrence math, and conflict detection. The main untested gap is duration-based overlap — the system does not flag a 30-minute task at 07:00 conflicting with a second task at 07:15. Testing that would require interval arithmetic and additional test cases covering partial overlaps, back-to-back tasks, and tasks with no scheduled time. Given more time, those would be the next tests to write.

---

## 5. Reflection

**a. What went well**

The part of the project I'm most satisfied with is the recurring task system. The design — a `recur_days` field on `Task`, a `next_occurrence()` method that returns a fresh copy with an advanced `due_date`, and a single `mark_task_complete()` entry point on `Scheduler` that wires them together — ended up being clean and easy to test in isolation. Each piece does exactly one thing: `Task` knows how to describe its next occurrence, `Scheduler` knows when to trigger it. The separation made the behavior predictable and the tests straightforward to write.

Using separate AI chat sessions for design, implementation, testing, and debugging also worked better than expected. Starting a new context window for each phase prevented earlier decisions from contaminating later questions, and it forced a brief mental reset before each transition — which often surfaced things that needed to be reconsidered.

**b. What you would improve**

Two things stand out for a next iteration:

1. **Duration-based overlap detection** — replace the exact-match time collision check with true interval arithmetic (`start + timedelta(minutes=duration)`) so the scheduler catches cases like a 30-minute walk at 07:00 overlapping with a task at 07:20.

2. **Owner preferences as structured data** — `preferences` is currently a free-text string with no effect on scheduling. It should be a structured set of rules (e.g., `prefer_morning: True`, `max_consecutive_minutes: 30`) that the Scheduler can actually apply when generating a plan.

**c. Key takeaway**

The most important thing I learned is that working with AI requires you to be more precise about your own intent, not less. When a prompt is vague, the AI produces something plausible — and plausible is dangerous because it looks right until you test it. The conflict detection bug was a perfect example: the AI's suggestion was clean, readable, and wrong in a subtle way that only showed up under a specific condition.

Being the "lead architect" in an AI collaboration means holding the design vision clearly enough that you can evaluate every suggestion against it. AI is extremely good at filling in implementation details within a structure you define. It is not good at knowing which structure is right for your specific problem — that judgment has to come from you. The projects where AI helps most are the ones where the human has already done the hard thinking about what the system should do and why.
