from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

SEP = "=" * 55

# --- Create pets ---
buddy = Pet(name="Buddy", species="dog", age=3)
luna  = Pet(name="Luna",  species="cat", age=5)

# --- Normal tasks (no conflicts) ---
buddy.add_task(Task(title="Morning walk",        duration_minutes=30, priority="high",
                    scheduled_time="07:00", recur_days=1, due_date=date.today()))
buddy.add_task(Task(title="Physical therapy",    duration_minutes=20, priority="high",
                    scheduled_time="10:30"))
luna.add_task(Task(title="Administer ear drops", duration_minutes=5,  priority="high",
                   scheduled_time="09:00", recur_days=1, due_date=date.today()))

# --- Intentional time-slot collisions ---
# Buddy already has 07:00; add another task for Buddy at the same time
buddy.add_task(Task(title="Brush teeth",         duration_minutes=5,  priority="medium",
                    scheduled_time="07:00"))          # same-pet conflict at 07:00

# Different pet (Luna) also at 07:00 — cross-pet conflict
luna.add_task(Task(title="Morning feeding",      duration_minutes=5,  priority="high",
                   scheduled_time="07:00"))            # cross-pet conflict at 07:00

# --- Create owner and scheduler ---
owner = Owner(name="Alex", available_minutes=120)
owner.add_pet(buddy)
owner.add_pet(luna)

pending   = owner.get_pending_tasks()
scheduler = Scheduler(tasks=pending, available_minutes=owner.available_minutes)

# -----------------------------------------------------------------------
# Show all scheduled tasks before running the plan
# -----------------------------------------------------------------------
print(SEP)
print("  Full task list (insertion order)")
print(SEP)
for t in scheduler.sort_by_time(pending):
    print(f"  {t.scheduled_time or '--:--'}  [{t.pet_name:<5}]  {t.title}")

# -----------------------------------------------------------------------
# Standalone conflict check (returns warnings, never crashes)
# -----------------------------------------------------------------------
print(f"\n{SEP}")
print("  Time-slot conflict check")
print(SEP)
warnings = scheduler.check_time_conflicts()
if warnings:
    for w in warnings:
        print(f"  [!] {w}")
else:
    print("  No time conflicts found.")

# -----------------------------------------------------------------------
# Generate plan — conflicts also surface inside DailyPlan.get_summary()
# -----------------------------------------------------------------------
plan = scheduler.generate_plan()
print(f"\n{SEP}")
print("  Generated plan (conflicts embedded in summary)")
print(SEP)
print(plan.get_summary())
print(SEP)
