import streamlit as st
from datetime import date
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# -----------------------------------------------------------------------
# Session-state initialisation
# -----------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None

# -----------------------------------------------------------------------
# Owner setup
# -----------------------------------------------------------------------
st.subheader("Owner")

with st.form("owner_form"):
    owner_name    = st.text_input("Your name", value="Jordan")
    avail_minutes = st.number_input("Available minutes today",
                                    min_value=5, max_value=480, value=60)
    preferences   = st.text_input("Preferences (optional)",
                                  value="morning routines preferred")
    submitted_owner = st.form_submit_button("Save owner")

if submitted_owner:
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=int(avail_minutes),
        preferences=preferences,
    )
    st.success(f"Owner **{owner_name}** saved — {avail_minutes} min available today.")

# -----------------------------------------------------------------------
# Add a pet
# -----------------------------------------------------------------------
st.subheader("Add a Pet")

if st.session_state.owner is None:
    st.info("Save an owner above before adding pets.")
else:
    with st.form("pet_form"):
        pet_name      = st.text_input("Pet name", value="Mochi")
        species       = st.selectbox("Species", ["dog", "cat", "other"])
        age           = st.number_input("Age (years)", min_value=0, max_value=30, value=2)
        special_needs = st.text_input("Special needs (optional)", value="")
        submitted_pet = st.form_submit_button("Add pet")

    if submitted_pet:
        new_pet = Pet(name=pet_name, species=species,
                      age=int(age), special_needs=special_needs)
        st.session_state.owner.add_pet(new_pet)
        st.success(f"**{pet_name}** added to {st.session_state.owner.name}'s profile.")

    if st.session_state.owner.pets:
        st.write("**Current pets:**")
        for pet in st.session_state.owner.pets:
            st.markdown(f"- {pet.get_summary()}")

# -----------------------------------------------------------------------
# Add a task
# -----------------------------------------------------------------------
st.subheader("Add a Task")

if st.session_state.owner is None or not st.session_state.owner.pets:
    st.info("Add at least one pet before adding tasks.")
else:
    with st.form("task_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (min)",
                                       min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        col4, col5, col6 = st.columns(3)
        with col4:
            scheduled_time = st.text_input("Time (HH:MM, optional)", value="")
        with col5:
            recur_days = st.number_input("Repeat every N days (0 = one-time)",
                                         min_value=0, max_value=365, value=0)
        with col6:
            pet_names  = [p.name for p in st.session_state.owner.pets]
            target_pet = st.selectbox("Assign to pet", pet_names)

        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        new_task = Task(
            title=task_title,
            duration_minutes=int(duration),
            priority=priority,
            scheduled_time=scheduled_time.strip(),
            recur_days=int(recur_days),
            due_date=date.today(),
        )
        for pet in st.session_state.owner.pets:
            if pet.name == target_pet:
                pet.add_task(new_task)
                break
        recur_label = f", repeats every {recur_days}d" if recur_days else ""
        st.success(
            f"**{task_title}** ({duration} min, {priority}{recur_label}) "
            f"added to {target_pet}."
        )

    # --- Live task table sorted by time ---
    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        scheduler_preview = Scheduler(tasks=all_tasks,
                                      available_minutes=st.session_state.owner.available_minutes)

        # Conflict check shown immediately after adding a task
        conflicts = scheduler_preview.check_time_conflicts()
        if conflicts:
            st.warning("**Time-slot conflicts detected in your task list:**")
            for c in conflicts:
                st.warning(f"⏰ {c}")

        # Sorted task table
        sorted_tasks = scheduler_preview.sort_by_time(all_tasks)
        st.write("**All tasks (sorted by scheduled time):**")
        rows = []
        for t in sorted_tasks:
            rows.append({
                "Time":     t.scheduled_time or "—",
                "Pet":      t.pet_name,
                "Task":     t.title,
                "Duration": f"{t.duration_minutes} min",
                "Priority": t.priority,
                "Recurs":   f"every {t.recur_days}d" if t.recur_days else "one-time",
                "Status":   "Done" if t.is_completed else "Pending",
            })
        st.table(rows)
    else:
        st.info("No tasks yet. Add one above.")

# -----------------------------------------------------------------------
# Filter view
# -----------------------------------------------------------------------
owner = st.session_state.owner
if owner and owner.pets and owner.get_all_tasks():
    with st.expander("Filter tasks by pet or status"):
        col_a, col_b = st.columns(2)
        with col_a:
            filter_pet = st.selectbox(
                "Show tasks for pet",
                ["All pets"] + [p.name for p in owner.pets],
                key="filter_pet",
            )
        with col_b:
            filter_status = st.selectbox(
                "Show by status",
                ["All", "Pending", "Done"],
                key="filter_status",
            )

        all_tasks = owner.get_all_tasks()
        sched = Scheduler(tasks=all_tasks,
                          available_minutes=owner.available_minutes)

        filtered = all_tasks
        if filter_pet != "All pets":
            filtered = [t for t in filtered if t.pet_name == filter_pet]
        if filter_status == "Pending":
            filtered = [t for t in filtered if not t.is_completed]
        elif filter_status == "Done":
            filtered = [t for t in filtered if t.is_completed]

        filtered_sorted = sched.sort_by_time(filtered)

        if filtered_sorted:
            st.write(f"**{len(filtered_sorted)} task(s) found:**")
            filter_rows = []
            for t in filtered_sorted:
                filter_rows.append({
                    "Time":     t.scheduled_time or "—",
                    "Pet":      t.pet_name,
                    "Task":     t.title,
                    "Duration": f"{t.duration_minutes} min",
                    "Priority": t.priority,
                    "Status":   "Done" if t.is_completed else "Pending",
                })
            st.table(filter_rows)
        else:
            st.info("No tasks match the selected filters.")

# -----------------------------------------------------------------------
# Generate schedule
# -----------------------------------------------------------------------
st.divider()
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner first.")
    else:
        owner = st.session_state.owner
        pending = owner.get_pending_tasks()
        if not pending:
            st.info("No pending tasks to schedule.")
        else:
            scheduler = Scheduler(
                tasks=pending,
                available_minutes=owner.available_minutes,
            )

            # --- Conflict warnings shown BEFORE the plan ---
            conflicts = scheduler.check_time_conflicts()
            if conflicts:
                st.warning(
                    "**Heads up — time-slot conflicts were found. "
                    "The schedule below was still generated, but you may want "
                    "to adjust these tasks:**"
                )
                for c in conflicts:
                    st.warning(f"⏰ {c}")

            plan = scheduler.generate_plan()

            # --- Plan conflicts (duplicate titles, over-budget tasks) ---
            if plan.conflicts:
                for c in plan.conflicts:
                    if "TIME CONFLICT" not in c:   # already shown above
                        st.warning(f"⚠️ {c}")

            st.success(
                f"Schedule generated — "
                f"{plan.total_duration} of {owner.available_minutes} min planned."
            )

            # --- Today's schedule sorted by time ---
            st.markdown("### Today's Schedule")
            time_sorted = scheduler.sort_by_time(plan.tasks)

            schedule_rows = []
            for task in time_sorted:
                schedule_rows.append({
                    "Time":     task.scheduled_time or "—",
                    "Pet":      task.pet_name,
                    "Task":     task.title,
                    "Duration": f"{task.duration_minutes} min",
                    "Priority": task.priority,
                    "Recurs":   f"every {task.recur_days}d" if task.recur_days else "one-time",
                })
            st.table(schedule_rows)

            # --- Capacity bar ---
            used  = plan.total_duration
            total = owner.available_minutes
            pct   = min(used / total, 1.0)
            st.progress(pct, text=f"{used} / {total} min used")

            # --- Skipped tasks ---
            skipped = [t for t in pending if t not in plan.tasks]
            if skipped:
                with st.expander(f"{len(skipped)} task(s) skipped — not enough time"):
                    for t in skipped:
                        st.markdown(
                            f"- **{t.title}** ({t.duration_minutes} min, "
                            f"{t.priority} priority)"
                        )
