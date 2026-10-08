"""Streamlit front end for PawPal+. All logic lives in pawpal_system.py."""

import streamlit as st

from pawpal_system import Owner, Pet, Scheduler, Task

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")


def get_owner() -> Owner:
    """Return the Owner held in session state, creating it only on the first run.

    Streamlit re-runs this script top to bottom on every interaction, so an Owner
    built at module level would be rebuilt empty each time. Keeping it in
    st.session_state means the same object survives every re-run, and because the
    UI mutates that object in place, no copying back and forth is needed.
    """
    if "owner" not in st.session_state:
        st.session_state.owner = Owner("Jordan", available_minutes=120)
    return st.session_state.owner


owner = get_owner()

st.title("🐾 PawPal+")
st.caption("Plan the day's pet care around the time you actually have.")

# --- Owner and constraints -------------------------------------------------
with st.sidebar:
    st.header("Owner")
    owner.name = st.text_input("Owner name", value=owner.name)
    owner.set_availability(
        st.slider("Minutes of care time today", 15, 480, owner.available_minutes, step=15)
    )

    st.subheader("Blocked times")
    st.caption("Periods you are unavailable. The scheduler plans around them.")
    block_start, block_end = st.columns(2)
    with block_start:
        new_start = st.time_input("From", value=None, key="block_from")
    with block_end:
        new_end = st.time_input("To", value=None, key="block_to")

    if st.button("Block this window", use_container_width=True):
        if new_start is None or new_end is None:
            st.warning("Pick both a start and an end time.")
        else:
            try:
                owner.block_window(new_start.strftime("%H:%M"), new_end.strftime("%H:%M"))
                st.rerun()
            except ValueError as exc:
                st.error(str(exc))

    for index, (start, end) in enumerate(list(owner.blocked_windows)):
        row, remove = st.columns([3, 1])
        row.write(f"{start} – {end}")
        if remove.button("✕", key=f"unblock_{index}"):
            owner.blocked_windows.pop(index)
            st.rerun()

# --- Pets ------------------------------------------------------------------
st.subheader("Pets")

with st.form("add_pet", clear_on_submit=True):
    name_col, species_col, breed_col = st.columns(3)
    pet_name = name_col.text_input("Name")
    pet_species = species_col.selectbox("Species", ["dog", "cat", "other"])
    pet_breed = breed_col.text_input("Breed (optional)")
    if st.form_submit_button("Add pet"):
        if not pet_name.strip():
            st.warning("Give the pet a name first.")
        else:
            owner.add_pet(Pet(pet_name.strip(), pet_species, pet_breed.strip()))
            st.rerun()

if not owner.pets:
    st.info("No pets yet. Add one above to get started.")
    st.stop()

st.write(", ".join(f"**{p.name}** ({p.species})" for p in owner.pets))

# --- Tasks -----------------------------------------------------------------
st.subheader("Care tasks")

with st.form("add_task", clear_on_submit=True):
    # Select by index, not by Pet object: Streamlit round-trips widget values through
    # session state, so passing the objects themselves hands back a copy and any
    # method called on it would mutate something the owner never sees.
    pet_index = st.selectbox(
        "Which pet?",
        range(len(owner.pets)),
        format_func=lambda i: f"{owner.pets[i].name} ({owner.pets[i].species})",
    )
    pet_choice = owner.pets[pet_index]
    title = st.text_input("Task title", placeholder="Morning walk")

    duration_col, priority_col, frequency_col = st.columns(3)
    duration = duration_col.number_input("Minutes", min_value=1, max_value=240, value=20)
    priority = priority_col.selectbox("Priority", ["high", "medium", "low"], index=1)
    frequency = frequency_col.selectbox("Frequency", ["daily", "weekly", "once"])

    wants_time = st.checkbox("This has to happen at a particular time")
    preferred = st.time_input("Preferred time", value=None, disabled=not wants_time)

    if st.form_submit_button("Add task"):
        if not title.strip():
            st.warning("Give the task a title first.")
        else:
            pet_choice.add_task(
                Task(
                    title.strip(),
                    int(duration),
                    priority,
                    frequency,
                    preferred_time=preferred.strftime("%H:%M")
                    if wants_time and preferred
                    else None,
                )
            )
            st.rerun()

for pet in owner.pets:
    with st.expander(f"{pet.name} — {len(pet.pending_tasks())} pending", expanded=True):
        if not pet.tasks:
            st.caption("No tasks yet.")
        for task in list(pet.tasks):
            done_col, label_col, remove_col = st.columns([1, 6, 1])

            done = done_col.checkbox(
                "Done", value=task.is_complete, key=f"done_{task.task_id}",
                label_visibility="collapsed",
            )
            if done != task.is_complete:
                task.mark_complete() if done else task.mark_incomplete()
                st.rerun()

            detail = f"{task.duration_minutes} min · {task.priority} · {task.frequency}"
            if task.preferred_time:
                detail += f" · at {task.preferred_time}"
            label_col.write(f"{'~~' + task.title + '~~' if done else task.title}  \n`{detail}`")

            if remove_col.button("✕", key=f"remove_{task.task_id}"):
                pet.remove_task(task.task_id)
                st.rerun()

st.divider()

# --- Plan ------------------------------------------------------------------
st.subheader("Today's plan")

start_col, end_col = st.columns(2)
day_starts = start_col.time_input("Start the day at", value=None, key="day_start")
day_ends = end_col.time_input("Wrap up by", value=None, key="day_end")

if st.button("Generate schedule", type="primary", use_container_width=True):
    scheduler = Scheduler(
        owner, day_ends=day_ends.strftime("%H:%M") if day_ends else "21:00"
    )
    planned, skipped = scheduler.generate_plan(
        start_time=day_starts.strftime("%H:%M") if day_starts else "08:00"
    )
    st.session_state.plan = (planned, skipped, scheduler)

if "plan" in st.session_state:
    planned, skipped, scheduler = st.session_state.plan

    if planned:
        st.table(
            [
                {
                    "When": f"{item.start_time}–{item.end_time()}",
                    "Pet": item.pet.name,
                    "Task": item.task.title,
                    "Priority": item.task.priority,
                }
                for item in planned
            ]
        )
    else:
        st.info("Nothing fits in the time available. Try raising your minutes in the sidebar.")

    if skipped:
        st.warning("Not scheduled today:")
        for item in skipped:
            st.write(f"- **{item.pet.name}: {item.task.title}** — {item.reason}")

    with st.expander("Why this plan?"):
        st.text(scheduler.explain_plan(planned, skipped))
