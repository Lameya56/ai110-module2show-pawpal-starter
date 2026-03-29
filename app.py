import streamlit as st

# Step 1 — import backend classes
from pawpal_system import Owner, Pet, Task, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# -----------------------------------------------------------------------
# Step 2 — Session-state initialisation (runs only on the very first load)
# -----------------------------------------------------------------------
if "owner" not in st.session_state:
    st.session_state.owner = None          # Owner object, created by the form below
if "tasks" not in st.session_state:
    st.session_state.tasks = []            # list[Task] accumulated across reruns

# -----------------------------------------------------------------------
# Owner setup
# -----------------------------------------------------------------------
st.subheader("Owner")

with st.form("owner_form"):
    owner_name      = st.text_input("Your name",              value="Jordan")
    avail_minutes   = st.number_input("Available minutes today", min_value=5, max_value=480, value=60)
    preferences     = st.text_input("Preferences (optional)", value="morning routines preferred")
    submitted_owner = st.form_submit_button("Save owner")

if submitted_owner:
    # Replace (or create) the owner stored in session state
    st.session_state.owner = Owner(
        name=owner_name,
        available_minutes=int(avail_minutes),
        preferences=preferences,
    )
    st.success(f"Owner **{owner_name}** saved ({avail_minutes} min available).")

# -----------------------------------------------------------------------
# Add a pet
# -----------------------------------------------------------------------
st.subheader("Add a Pet")

if st.session_state.owner is None:
    st.info("Save an owner above before adding pets.")
else:
    with st.form("pet_form"):
        pet_name      = st.text_input("Pet name",       value="Mochi")
        species       = st.selectbox("Species",         ["dog", "cat", "other"])
        age           = st.number_input("Age (years)",  min_value=0, max_value=30, value=2)
        special_needs = st.text_input("Special needs (optional)", value="")
        submitted_pet = st.form_submit_button("Add pet")

    if submitted_pet:
        new_pet = Pet(name=pet_name, species=species, age=int(age), special_needs=special_needs)
        st.session_state.owner.add_pet(new_pet)   # Step 3 — call Owner.add_pet()
        st.success(f"Pet **{pet_name}** added to {st.session_state.owner.name}'s profile.")

    # Show current pets
    if st.session_state.owner.pets:
        st.write("**Current pets:**")
        for pet in st.session_state.owner.pets:
            st.markdown(f"- {pet.get_summary()}")

# -----------------------------------------------------------------------
# Add tasks
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
            duration = st.number_input("Duration (min)", min_value=1, max_value=240, value=20)
        with col3:
            priority = st.selectbox("Priority", ["low", "medium", "high"], index=2)

        pet_names     = [p.name for p in st.session_state.owner.pets]
        target_pet    = st.selectbox("Assign to pet", pet_names)
        submitted_task = st.form_submit_button("Add task")

    if submitted_task:
        new_task = Task(title=task_title, duration_minutes=int(duration), priority=priority)
        # Step 3 — find the chosen pet and call Pet.add_task()
        for pet in st.session_state.owner.pets:
            if pet.name == target_pet:
                pet.add_task(new_task)
                break
        # Also keep a flat list for the scheduler
        st.session_state.tasks.append(new_task)
        st.success(f"Task **{task_title}** ({duration} min, {priority}) added to {target_pet}.")

    # Show all tasks across all pets
    all_tasks = st.session_state.owner.get_all_tasks()
    if all_tasks:
        st.write("**All tasks:**")
        st.table([t.to_dict() for t in all_tasks])
    else:
        st.info("No tasks yet. Add one above.")

# -----------------------------------------------------------------------
# Generate schedule
# -----------------------------------------------------------------------
st.divider()
st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Please save an owner first.")
    else:
        pending = st.session_state.owner.get_pending_tasks()
        if not pending:
            st.info("No pending tasks to schedule.")
        else:
            scheduler = Scheduler(
                tasks=pending,
                available_minutes=st.session_state.owner.available_minutes,
            )
            plan = scheduler.generate_plan()

            st.success("Schedule generated!")
            st.markdown(f"**{scheduler.explain_plan(plan)}**")
            st.markdown("---")
            st.markdown("### Today's Schedule")
            for i, task in enumerate(plan.tasks, 1):
                st.markdown(
                    f"{i}. {'~~' + task.title + '~~' if task.is_completed else task.title} "
                    f"— {task.duration_minutes} min · *{task.priority}* priority"
                )
            st.caption(f"Total: {plan.total_duration} / {st.session_state.owner.available_minutes} min used")
