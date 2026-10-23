from datetime import datetime, date, time

import streamlit as st
from pawpal_system import Task, Pet, Owner, Scheduler

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")
st.title("🐾 PawPal+")

if "owner" not in st.session_state:
    st.session_state.owner = Owner(name="Jordan", available_minutes=120)

owner = st.session_state.owner

st.markdown(
    """
Welcome to PawPal+. Create one or more pets, assign tasks to a pet, and then generate a daily schedule.
"""
)

with st.container():
    owner_name = st.text_input("Owner name", value=owner.name)
    available_minutes = st.number_input(
        "Available minutes",
        min_value=0,
        max_value=240,
        value=owner.available_minutes,
    )

    owner.name = owner_name
    owner.available_minutes = int(available_minutes)

    if st.button("Update owner profile"):
        st.success("Owner profile updated.")

st.divider()

st.subheader("Pets")
if owner.pets:
    for pet in owner.pets:
        st.write(f"- {pet.name} ({pet.species})")
else:
    st.info("No pets added yet.")

with st.form("add_pet_form"):
    pet_name_input = st.text_input("New pet name", value="")
    pet_species_input = st.selectbox("Species", ["dog", "cat", "other"], index=0)
    if st.form_submit_button("Add pet"):
        if pet_name_input.strip():
            pet = Pet(name=pet_name_input.strip(), species=pet_species_input)
            owner.add_pet(pet)
            st.success(f"Added pet '{pet.name}'.")
        else:
            st.warning("Please enter a pet name.")

st.divider()

st.subheader("Add a task")
priority_map = {"low": 1, "medium": 2, "high": 3}

if not owner.pets:
    st.info("Add a pet before creating tasks.")
else:
    with st.form("add_task_form", clear_on_submit=True):
        pet_names = [pet.name for pet in owner.pets]
        selected_pet_name = st.selectbox("Pet", pet_names, index=0)

        col1, col2, col3, col4 = st.columns([2.3, 1.2, 1.1, 1.1])
        with col1:
            task_title = st.text_input("Task title", value="Morning walk")
        with col2:
            duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
        with col3:
            priority_label = st.selectbox("Priority", ["low", "medium", "high"], index=2)
        with col4:
            required = st.checkbox("Required")

        col5, col6, col7 = st.columns([1.3, 1.2, 1.2])
        with col5:
            task_date = st.date_input("Date", value=date.today())
        with col6:
            task_time = st.time_input("Time", value=time(8, 0))
        with col7:
            recurrence = st.selectbox("Repeat", ["once", "daily", "weekly"], index=0)

        submitted = st.form_submit_button("Add task")
        if submitted:
            selected_pet = next(pet for pet in owner.pets if pet.name == selected_pet_name)
            task_datetime = datetime.combine(task_date, task_time)
            existing_same_time = [
                task for task in owner.get_all_tasks() if not task.completed and task.time == task_datetime
            ]
            if existing_same_time:
                st.warning(
                    "Warning: another task is already scheduled for "
                    f"{task_datetime.strftime('%Y-%m-%d %H:%M')}: "
                    + ", ".join(f"{task.title} ({task.pet_name})" for task in existing_same_time)
                    + "."
                )
            task = Task(
                title=task_title,
                duration_minutes=int(duration),
                priority=priority_map[priority_label],
                pet_name=selected_pet.name,
                is_required=required,
                time=task_datetime,
                recurrence=recurrence,
            )
            selected_pet.add_task(task)
            st.success(
                f"Added '{task.title}' to {selected_pet.name} at {task.time.strftime('%Y-%m-%d %H:%M')} ({recurrence})."
            )

st.divider()

st.subheader("Current tasks")
active_tasks = [task for task in owner.get_all_tasks() if not task.completed]
if active_tasks:
    for task in active_tasks:
        key = f"done_{id(task)}"
        col_pet, col_title, col_time, col_repeat, col_priority, col_done = st.columns([1.4, 2.2, 1.3, 1.1, 0.9, 1.0])
        with col_pet:
            st.write(task.pet_name)
        with col_title:
            label = "*" if task.is_required else ""
            st.write(f"{label}{task.title}")
        with col_time:
            st.write(task.time.strftime("%Y-%m-%d %H:%M"))
        with col_repeat:
            st.write(task.recurrence)
        with col_priority:
            st.write(f"P{task.priority}")
        with col_done:
            checked = st.checkbox("Done", key=key)
            if checked:
                owning_pet = next(pet for pet in owner.pets if pet.name == task.pet_name)
                owning_pet.complete_task(task)
                st.success(f"Marked '{task.title}' complete for {task.pet_name} and scheduled the next {task.recurrence} task.")
                st.rerun()
else:
    st.info("No active tasks yet. Add one above.")

st.divider()

st.subheader("Build schedule")
with st.form("build_schedule_form"):
    generate_schedule = st.form_submit_button("Generate schedule")
    if generate_schedule:
        scheduler = Scheduler(owner)
        plan = scheduler.generate_plan()
        warnings = getattr(plan, "warnings", [])
        if warnings:
            st.warning("\n".join(warnings))
        st.code(scheduler.explain(plan), language="text")

        if plan.scheduled:
            st.markdown("### Scheduled tasks")
            for i, task in enumerate(plan.scheduled, 1):
                st.write(f"{i}. {task.title} ({task.pet_name}) — {task.duration_minutes} min")

        if plan.skipped:
            st.markdown("### Skipped tasks")
            for item in plan.skipped:
                st.write(f"- {item.task.title} ({item.task.pet_name}): {item.reason}")
