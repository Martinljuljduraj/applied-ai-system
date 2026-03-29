import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler, Priority, Frequency

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

# ---------------------------------------------------------------------------
# Session state initialisation
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None

if "pet" not in st.session_state:
    st.session_state.pet = None

# ---------------------------------------------------------------------------
# Step 1 — Owner + Pet setup
# ---------------------------------------------------------------------------

st.subheader("Owner & Pet Info")

owner_name = st.text_input("Owner name", value="Martin")
pet_name    = st.text_input("Pet name",   value="Rex")
species     = st.selectbox("Species", ["dog", "cat", "other"])

if st.button("Save owner & pet"):
    pet   = Pet(1, pet_name, species, age=0)
    owner = Owner(1, owner_name, "")
    owner.add_pet(pet)
    st.session_state.owner = owner
    st.session_state.pet   = pet
    st.success(f"Saved {owner_name} and {pet_name} the {species}.")

st.divider()

# ---------------------------------------------------------------------------
# Step 2 — Add tasks
# ---------------------------------------------------------------------------

st.subheader("Tasks")

PRIORITY_MAP = {"high": Priority.HIGH, "medium": Priority.MEDIUM, "low": Priority.LOW}

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
    st.write("Current tasks:")
    st.table([t.to_display_row() if hasattr(t, "to_display_row") else
              {"Task": t.description, "Duration": t.duration_mins, "Priority": t.priority.name}
              for t in st.session_state.pet.get_tasks()])
else:
    st.info("No tasks yet. Add one above.")

st.divider()

# ---------------------------------------------------------------------------
# Step 3 — Generate schedule
# ---------------------------------------------------------------------------

st.subheader("Build Schedule")

if st.button("Generate schedule"):
    if st.session_state.owner is None:
        st.warning("Save an owner and pet first.")
    else:
        scheduler = Scheduler(st.session_state.owner)
        schedule  = scheduler.generate_schedule()

        if not schedule:
            st.info("No tasks are due today.")
        else:
            st.success("Schedule generated!")
            st.table([block.to_display_row() for block in schedule])
            st.markdown("**Plan explanation:**")
            st.write(scheduler.explain_plan())
