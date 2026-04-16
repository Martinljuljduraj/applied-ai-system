import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Frequency
from ai_advisor import get_ai_advice

PRIORITY_BADGE = {
    Priority.HIGH:   "🔴 HIGH",
    Priority.MEDIUM: "🟡 MEDIUM",
    Priority.LOW:    "🟢 LOW",
}

PRIORITY_MAP = {"high": Priority.HIGH, "medium": Priority.MEDIUM, "low": Priority.LOW}

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None
if "pet" not in st.session_state:
    st.session_state.pet = None
if "scheduler" not in st.session_state:
    st.session_state.scheduler = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab1, tab2 = st.tabs(["📋 Scheduler", "🤖 AI Advisor"])

# ===========================================================================
# TAB 1 — Scheduler (original app)
# ===========================================================================

with tab1:

    # Step 1 — Owner + Pet setup
    st.subheader("Owner & Pet Info")

    owner_name = st.text_input("Owner name", value="Martin")
    pet_name   = st.text_input("Pet name",   value="Rex")
    species    = st.selectbox("Species", ["dog", "cat", "other"])

    if st.button("Save owner & pet"):
        pet   = Pet(1, pet_name, species, age=0)
        owner = Owner(1, owner_name, "")
        owner.add_pet(pet)
        st.session_state.owner = owner
        st.session_state.pet   = pet
        st.success(f"Saved {owner_name} and {pet_name} the {species}.")

    st.divider()

    # Step 2 — Add tasks
    st.subheader("Tasks")

    col1, col2, col3 = st.columns(3)
    with col1:
        task_title = st.text_input("Task title", value="Morning walk")
    with col2:
        duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
    with col3:
        priority_str = st.selectbox("Priority", ["high", "medium", "low"])

    if st.button("Add task"):
        if st.session_state.pet is None:
            st.warning("Save an owner and pet first.")
        else:
            task_id = len(st.session_state.pet.get_tasks()) + 1
            task    = Task(task_id, task_title, int(duration), PRIORITY_MAP[priority_str])
            st.session_state.pet.add_task(task)
            st.success(f"Added task: {task_title}")

    if st.session_state.pet and st.session_state.pet.get_tasks():
        sort_order = st.radio("Sort tasks by", ["Priority", "Preferred time"], horizontal=True)
        pet = st.session_state.pet
        if sort_order == "Preferred time" and st.session_state.scheduler:
            sorted_tasks = [
                pair[1]
                for pair in st.session_state.scheduler.sort_by_time(
                    [(pet.name, t) for t in pet.get_tasks()]
                )
            ]
        else:
            sorted_tasks = sorted(pet.get_tasks(), key=lambda t: t.priority.value)

        col_a, col_b, col_c = st.columns(3)
        col_a.metric("Total tasks", len(sorted_tasks))
        col_b.metric("High priority", sum(1 for t in sorted_tasks if t.priority == Priority.HIGH))
        col_c.metric("Completed", sum(1 for t in sorted_tasks if t.is_completed))

        st.dataframe(
            [
                {
                    "Task": t.description,
                    "Duration (min)": t.duration_mins,
                    "Priority": PRIORITY_BADGE[t.priority],
                    "Done": "✅" if t.is_completed else "⬜",
                }
                for t in sorted_tasks
            ],
            use_container_width=True,
        )
    else:
        st.info("No tasks yet. Add one above.")

    st.divider()

    # Step 3 — Generate schedule
    st.subheader("Build Schedule")

    if st.button("Generate schedule"):
        if st.session_state.owner is None:
            st.warning("Save an owner and pet first.")
        else:
            scheduler = Scheduler(st.session_state.owner)
            schedule  = scheduler.generate_schedule()
            st.session_state.scheduler = scheduler

            if not schedule:
                st.info("No tasks are due today.")
            else:
                m1, m2, m3 = st.columns(3)
                m1.metric("Tasks scheduled", len(schedule))
                m2.metric("Total due", scheduler._total_due)
                m3.metric("Skipped", scheduler._total_due - len(schedule))

                st.success("Schedule generated!")
                st.dataframe(
                    [block.to_display_row() for block in schedule],
                    use_container_width=True,
                )

                with st.expander("Why this order?"):
                    st.write(scheduler.explain_plan())

                conflicts = scheduler.get_conflicts()
                if conflicts:
                    st.error(
                        f"⚠️ {len(conflicts)} conflict(s) detected — "
                        "two tasks overlap in time."
                    )
                    with st.expander("See conflict details and how to fix them"):
                        for msg in conflicts:
                            st.write(f"- {msg}")
                else:
                    st.success("✅ No conflicts — your pet's schedule is clean.")

    # Step 4 — Filter schedule
    if st.session_state.scheduler and st.session_state.scheduler._schedule:
        st.divider()
        st.subheader("Filter Schedule")

        scheduler     = st.session_state.scheduler
        filter_status = st.selectbox("Show tasks by status", ["All", "Incomplete", "Completed"])
        status_map    = {"All": None, "Incomplete": False, "Completed": True}
        filtered      = scheduler.filter_tasks(completed=status_map[filter_status])

        st.metric("Showing", len(filtered))
        if filtered:
            st.dataframe(
                [block.to_display_row() for block in filtered],
                use_container_width=True,
            )
        else:
            st.info("No tasks match that filter.")


# ===========================================================================
# TAB 2 — AI Advisor
# ===========================================================================

with tab2:
    st.subheader("🤖 PawPal AI Advisor")
    st.write("Ask me anything about your pet's care, or let me suggest tasks for your schedule.")

    if st.session_state.pet is None:
        st.warning("Go to the Scheduler tab and save an owner & pet first.")
    else:
        pet    = st.session_state.pet
        tasks  = [t.description for t in pet.get_tasks()]

        st.info(f"Advising for **{pet.name}** the **{pet.species}** — {len(tasks)} task(s) currently scheduled.")

        # Chat history display
        for message in st.session_state.chat_history:
            with st.chat_message(message["role"]):
                st.write(message["content"])

        # Chat input
        user_input = st.chat_input("Ask about your pet's care...")

        if user_input:
            # Show user message
            with st.chat_message("user"):
                st.write(user_input)
            st.session_state.chat_history.append({"role": "user", "content": user_input})

            # Get AI response
            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = get_ai_advice(
                        user_message=user_input,
                        pet_name=pet.name,
                        species=pet.species,
                        current_tasks=tasks,
                    )
                st.write(response)
            st.session_state.chat_history.append({"role": "assistant", "content": response})

        # Clear chat button
        if st.session_state.chat_history:
            if st.button("Clear chat"):
                st.session_state.chat_history = []
                st.rerun()
