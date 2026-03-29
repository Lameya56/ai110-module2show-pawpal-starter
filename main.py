from pawpal_system import Owner, Pet, Task, Scheduler

# --- Create pets ---
buddy = Pet(name="Buddy", species="dog", age=3, special_needs="hip dysplasia")
luna = Pet(name="Luna", species="cat", age=5)

# --- Add tasks to Buddy ---
buddy.add_task(Task(title="Morning walk",        duration_minutes=30, priority="high"))
buddy.add_task(Task(title="Physical therapy",    duration_minutes=20, priority="high"))
buddy.add_task(Task(title="Brush teeth",         duration_minutes=5,  priority="medium"))

# --- Add tasks to Luna ---
luna.add_task(Task(title="Playtime with wand toy", duration_minutes=15, priority="medium"))
luna.add_task(Task(title="Administer ear drops",   duration_minutes=5,  priority="high"))
luna.add_task(Task(title="Clean litter box",       duration_minutes=10, priority="low"))

# --- Create owner and register pets ---
owner = Owner(name="Alex", available_minutes=90, preferences="morning routines preferred")
owner.add_pet(buddy)
owner.add_pet(luna)

# --- Build today's schedule via Scheduler ---
all_pending = owner.get_pending_tasks()
scheduler = Scheduler(tasks=all_pending, available_minutes=owner.available_minutes)
plan = scheduler.generate_plan()

# --- Print Today's Schedule ---
print("=" * 50)
print("          PawPal — Today's Schedule")
print("=" * 50)
print(f"Owner : {owner.name}  |  Available: {owner.available_minutes} min\n")

for pet in owner.pets:
    print(pet.get_summary())
print()

print(scheduler.explain_plan(plan))
print("=" * 50)
