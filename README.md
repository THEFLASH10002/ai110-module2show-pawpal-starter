# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## ✨ Features

**Pets and tasks**
- Track any number of pets under one owner, each with their own care tasks
- Every task carries a title, a duration in minutes, a priority, a frequency and an optional fixed time
- Edit, remove or tick off a task; stable task ids mean two tasks called "Feeding" never get confused

**Constraints the planner respects**
- A daily time budget: how many minutes of care the owner actually has
- Blocked windows: periods the owner is unavailable, checked against a task's whole duration rather than just its start time
- A day cutoff: anything that cannot finish before the end of the day is deferred instead of overrunning

**Scheduling algorithms**
- **Sorting by time** — tasks are laid out in clock order, using the scheduled time where one exists and the owner's requested time otherwise, with flexible tasks placed last
- **Sorting by priority** — high before low, then shortest first, so one long low-priority job cannot crowd out several quick important ones
- **Filtering** — narrow tasks by pet, completion status, priority or due date, in any combination
- **Conflict warnings** — overlapping requested times are reported as warnings, across pets as well as within one, with the resolution explained rather than silently applied
- **Daily and weekly recurrence** — completing a repeating task automatically queues its next occurrence, one day or one week ahead, and tomorrow's copy stays out of today's plan
- **Explained plans** — every plan comes with the reasoning: why each task sits where it does, and why anything dropped was dropped

**Two front ends**
- A Streamlit app (`app.py`) for day-to-day use
- A terminal demo (`main.py`) that exercises every feature end to end

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## 🏗️ Architecture

All logic lives in `pawpal_system.py`; `app.py` and `main.py` are front ends over it and
contain no scheduling rules of their own. The full class diagram is in
[`diagrams/uml_final.mmd`](diagrams/uml_final.mmd).

| Class | Responsibility |
|---|---|
| **`Task`** | One care activity. Holds its description (`title`), how long it takes, priority, frequency, an optional fixed `preferred_time`, the `due_date` it next falls due, and its completion status. Knows how to mark itself complete, rank its own priority, say whether it fits in a given gap, and build its next occurrence. |
| **`Pet`** | A pet's identity plus the collection of tasks it needs. Adds, finds, edits, removes and lists tasks, and `complete_task` ticks one off *and* queues its follow-up. |
| **`Owner`** | The person, their pets, and the constraints they bring: a daily minute budget and any blocked windows. Exposes the whole household's tasks through `all_tasks`, `pending_tasks` and `filter_tasks`, so nothing else has to reach into `Pet.tasks` directly. |
| **`PlannedItem`** | One task placed at one time for one pet, plus the reason it landed there. Scheduling state lives here rather than on `Task`, so generating a plan never writes into a pet's permanent task list. |
| **`Scheduler`** | The brain. Reads the household through the `Owner`, then collects, sorts, filters, selects within the budget, assigns clock times around blocked windows, flags conflicts, and explains the result. Works across every pet at once, on one shared time budget and one shared clock. |

**How they fit together:** an `Owner` has many `Pet`s, a `Pet` has many `Task`s, and the
`Scheduler` reads the whole tree through the `Owner` and emits `PlannedItem`s. The arrows
only run one way, so there are no circular dependencies.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Running the terminal demo

```bash
python main.py
```

Builds a sample household and walks through every scheduling feature in order: sorting by
time, filtering, conflict detection, recurrence, and the final explained plan. No arguments
needed. See [Sample Output](#-sample-output) for what it prints.

### Running the Streamlit app

```bash
streamlit run app.py
```

Opens PawPal+ in your browser at `http://localhost:8501`. Add pets and tasks, set your
time budget and blocked hours in the sidebar, then press **Generate schedule**.

### Running the tests

```bash
python -m pytest
```

30 tests. See [Testing PawPal+](#-testing-pawpal) for what they cover.

## 🖥️ Sample Output

The plan `python main.py` produces for a sample household: one owner with 100 minutes,
two pets, seven tasks and a blocked lunch hour.

```
====================================================================
                    TODAY'S SCHEDULE for Jordan
====================================================================
  08:15-08:20   Mochi     Thyroid medication     [high]
  08:20-08:30   Biscuit   Breakfast              [high]
  18:00-18:20   Biscuit   Evening enrichment     [low]
  18:20-18:30   Mochi     Litter box             [medium]
  18:30-19:15   Biscuit   Full grooming          [low]

====================================================================
                           WHY THIS PLAN
====================================================================
Jordan has 100 minutes today across 2 pets.
Tasks were ranked by priority, then by how short they are, so quick wins are not crowded out by one long low-priority job.
The plan works around these blocked times: 12:00-13:00.
  08:15 Mochi: Thyroid medication -> high priority, picked 1 of 5 into the 100 min budget; placed at the requested time
  08:20 Biscuit: Breakfast -> high priority, picked 2 of 5 into the 100 min budget
  18:00 Biscuit: Evening enrichment -> low priority, picked 4 of 5 into the 100 min budget; placed at the requested time
  18:20 Mochi: Litter box -> medium priority, picked 3 of 5 into the 100 min budget
  18:30 Biscuit: Full grooming -> low priority, picked 5 of 5 into the 100 min budget
```

The full run, which also shows sorting, filtering, conflict detection and recurrence, is
in [Demo Walkthrough](#-demo-walkthrough).

## 🧪 Testing PawPal+

Run the suite from the project root:

```bash
python -m pytest
```

```bash
# with coverage
python -m pytest --cov
```

### What the tests cover

30 tests in `tests/test_pawpal.py`, split between happy paths and edge cases.

| Area | Behaviour verified |
|---|---|
| Task state | A new task starts pending; `mark_complete` flips it; adding a task grows the pet's list |
| Data access | `Owner.all_tasks` reaches across every pet; `filter_tasks` narrows by pet, status and priority, and ignores case on the name |
| Sorting | Tasks entered back to front come out in clock order, untimed ones last, and the order is stable when nothing has a time |
| Priority | High priority is scheduled before low, and the shortest task breaks a tie |
| Time budget | Work that no longer fits is skipped with a readable reason; a zero minute budget skips everything |
| Recurrence | Completing a daily task queues tomorrow's and a weekly task next week's; a one-off queues nothing; rollover across month and year boundaries is correct |
| Conflicts | Overlapping requested times produce a warning per clashing pair; touching tasks do not |
| Blocked time | A task that would run into an unavailable window is pushed past it |
| Day boundary | A task that cannot finish before the cutoff is deferred, not overrun |
| Re-run safety | Generating a plan twice does not mutate the pet's own task objects |
| Empty states | An owner with no pets, and a pet with no tasks, plan cleanly instead of raising |
| Bad input | Zero durations, unknown priorities and backwards blocked windows raise; unknown task ids return False or None |

### Sample test output

```
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\kenne\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: ...
plugins: anyio-4.13.0
collecting ... collected 30 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  3%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [  6%]
tests/test_pawpal.py::test_owner_collects_tasks_across_all_pets PASSED   [ 10%]
tests/test_pawpal.py::test_high_priority_is_scheduled_before_low PASSED  [ 13%]
tests/test_pawpal.py::test_task_is_skipped_when_budget_runs_out PASSED   [ 16%]
tests/test_pawpal.py::test_completed_tasks_are_left_out_of_the_plan PASSED [ 20%]
tests/test_pawpal.py::test_scheduler_works_around_a_blocked_window PASSED [ 23%]
tests/test_pawpal.py::test_planning_twice_does_not_mutate_the_pets_tasks PASSED [ 26%]
tests/test_pawpal.py::test_sort_by_time_orders_tasks_entered_out_of_order PASSED [ 30%]
tests/test_pawpal.py::test_filter_tasks_narrows_by_pet_and_status PASSED [ 33%]
tests/test_pawpal.py::test_completing_a_daily_task_queues_it_for_tomorrow PASSED [ 36%]
tests/test_pawpal.py::test_completing_a_weekly_task_queues_it_seven_days_out PASSED [ 40%]
tests/test_pawpal.py::test_completing_a_one_off_task_queues_nothing PASSED [ 43%]
tests/test_pawpal.py::test_tomorrows_task_is_not_planned_today PASSED    [ 46%]
tests/test_pawpal.py::test_detect_conflicts_warns_on_overlapping_requested_times PASSED [ 50%]
tests/test_pawpal.py::test_detect_conflicts_is_quiet_when_times_only_touch PASSED [ 53%]
tests/test_pawpal.py::test_completing_the_same_task_twice_queues_only_one_follow_up PASSED [ 56%]
tests/test_pawpal.py::test_owner_with_no_pets_produces_an_empty_plan PASSED [ 60%]
tests/test_pawpal.py::test_pet_with_no_tasks_produces_an_empty_plan PASSED [ 63%]
tests/test_pawpal.py::test_everything_is_skipped_when_there_is_no_time_at_all PASSED [ 66%]
tests/test_pawpal.py::test_task_requested_too_late_in_the_day_is_deferred PASSED [ 70%]
tests/test_pawpal.py::test_three_tasks_at_the_same_time_report_every_clashing_pair PASSED [ 73%]
tests/test_pawpal.py::test_daily_recurrence_rolls_over_the_year_boundary PASSED [ 76%]
tests/test_pawpal.py::test_weekly_recurrence_rolls_over_a_month_boundary PASSED [ 80%]
tests/test_pawpal.py::test_filter_by_pet_name_ignores_case PASSED        [ 83%]
tests/test_pawpal.py::test_sort_by_time_is_stable_when_nothing_has_a_requested_time PASSED [ 86%]
tests/test_pawpal.py::test_invalid_task_values_are_rejected_at_construction PASSED [ 90%]
tests/test_pawpal.py::test_invalid_blocked_window_is_rejected PASSED     [ 93%]
tests/test_pawpal.py::test_editing_or_removing_an_unknown_task_returns_false PASSED [ 96%]
tests/test_pawpal.py::test_scheduler_sorts_and_plans_across_two_pets PASSED [100%]

============================= 30 passed in 0.04s ==============================
```

### Confidence level

**★★★★☆ (4 / 5)**

The scheduling logic itself I trust. Every branch that decides what gets scheduled, what
gets dropped and when a task repeats is covered by a test, and writing those tests found
three real bugs: a freshly queued task appearing in the same day's plan, a double
completion queueing two copies of tomorrow's task, and a Streamlit form field that
silently discarded the time the user typed.

The missing star is for what the suite does not reach. `app.py` has no automated tests, so
the UI is verified by hand. Recurrence is only tested one step forward, never over a week
of simulated days. And nothing covers a plan that runs past midnight, because the day
cutoff currently makes that unreachable rather than because it is known to be safe.

## 📐 Smarter Scheduling

Four scheduling features, and the methods that implement each one.

### Sorting

| Behaviour | Method(s) |
|---|---|
| By clock time, scheduled time first and requested time as the fallback, untimed tasks last | `Scheduler.sort_by_time`, `Scheduler._clock_key` |
| By importance, high before low, then shortest first so quick wins are not crowded out | `Scheduler.sort_by_priority`, `Task.priority_rank` |

`_clock_key` converts `"HH:MM"` to minutes rather than sorting the strings directly.
Text sorting only works while every value is zero padded and non-null, and a task with
no requested time is `None`; the key returns `(clock is None, minutes)` so untimed tasks
sort to the end instead of raising.

### Filtering

| Behaviour | Method(s) |
|---|---|
| By pet name, completion status, priority or due date, in any combination | `Owner.filter_tasks` |
| Outstanding work only, per pet or across the household | `Pet.pending_tasks`, `Owner.pending_tasks` |
| Only what is actually due by the planning date | `Scheduler.collect_tasks` |

Every filter argument left as `None` is simply not applied, so `filter_tasks()` returns
everything and `filter_tasks(pet_name="Mochi", completed=False)` returns just what Mochi
still needs.

### Conflict detection

| Behaviour | Method(s) |
|---|---|
| Warns when two requested times overlap, across pets as well as within one | `Scheduler.detect_conflicts`, `Task.window` |
| Keeps real overlaps out of the finished plan by advancing one shared clock cursor | `Scheduler.assign_times` |
| Steps over the owner's unavailable periods, checked against the whole task duration | `Owner.blocking_window`, `Owner.overlaps_blocked` |

`detect_conflicts` returns a list of warning strings and never raises, so two tasks
pinned to 08:15 produce a message the owner can act on rather than a crash. It compares
what was *requested*, because `assign_times` has already pushed the clash apart by the
time a plan exists. Touching tasks (one ending exactly as the next begins) are not
treated as a conflict.

### Recurring tasks

| Behaviour | Method(s) |
|---|---|
| Completing a task queues its next occurrence | `Pet.complete_task` |
| Works out the next due date with `timedelta`, daily `+1` day and weekly `+7` | `Task.next_due_date`, `FREQUENCY_DAYS` |
| Builds the follow-up as a fresh pending copy | `Task.next_occurrence` |
| Keeps tomorrow's copy out of today's plan | `Scheduler.collect_tasks` |

`Task.mark_complete` only flips the status; `Pet.complete_task` is the method that also
queues the follow-up, because creating one needs the list to add it to. A task with
frequency `once` returns `None` and does not come back.

## 📸 Demo Walkthrough

### What the UI offers

| Area | What the user can do |
|---|---|
| Sidebar | Set their name, drag a slider for how many minutes of care time they have today, and add or remove blocked windows such as a lunch hour |
| Pets | Add a pet with a name, species and optional breed |
| Care tasks | Add a task to a chosen pet with a duration, priority, frequency and optional fixed time; tick tasks off, remove them, or filter the list by Outstanding / Done / All |
| Conflict banner | See a warning whenever two pinned tasks want overlapping slots, with the resolution spelled out |
| Today's plan | Pick a start time and a cutoff, generate the schedule, and read it as a table alongside summary metrics, the dropped tasks with reasons, and an expandable explanation |

### An example workflow

1. **Add a pet.** Type `Biscuit`, pick `dog`, submit. The form calls `owner.add_pet(Pet(...))`
   and the page redraws with Biscuit present.
2. **Add tasks.** Add `Morning walk`, 30 minutes, high priority, daily, pinned to 07:30.
   Then `Breakfast`, 10 minutes, high, daily, pinned to 08:15. Leave `Litter box` with no
   time so the planner can place it freely. Each submit calls `pet.add_task(Task(...))`.
3. **Set the constraints.** In the sidebar, drag the budget to 100 minutes and block
   12:00–13:00 for work.
4. **Watch a conflict appear.** Add `Thyroid medication` for a second pet, also pinned to
   08:15. A banner appears immediately: *"1 time clash between tasks you pinned to a set
   time. PawPal+ will keep the earlier one where you asked and push the later one back."*
5. **Generate the schedule.** The plan appears as a table in clock order, with metrics
   above it showing how many tasks were scheduled, how much care time they take, how much
   budget is left and how many were dropped.
6. **Tick off the morning walk.** Because it is a daily task, PawPal+ queues a fresh copy
   for tomorrow and tells you so. Regenerate the plan and tomorrow's copy does not appear,
   because the scheduler only collects what is due today.

### Scheduler behaviours this shows

- **Sorting by time** — the plan table is ordered by `Scheduler.sort_by_time`, so it reads
  top to bottom the way the day runs, no matter what order tasks were entered in.
- **Priority within a budget** — with only 100 minutes, `select_tasks` spends the budget
  high priority first and the 45 minute grooming job is dropped with the reason shown.
- **Conflict warnings** — `detect_conflicts` compares requested intervals, not exact
  string equality, so an 08:15 breakfast lasting 10 minutes clashes with 08:20 medication.
- **Blocked windows** — `assign_times` steps the clock over 12:00–13:00 instead of
  scheduling through it.
- **Recurrence** — `Pet.complete_task` queues the next occurrence via `timedelta`, and
  `collect_tasks` keeps it out of today.
- **Explainability** — the "Why this plan?" expander prints `Scheduler.explain_plan`.

### Sample CLI output

Running `python main.py` walks through every one of those behaviours in the terminal:

```
====================================================================
                     ALL TASKS, SORTED BY TIME
====================================================================
  07:30      Biscuit   Morning walk           [high]
  08:15      Biscuit   Breakfast              [high]
  08:15      Mochi     Thyroid medication     [high]
  18:00      Biscuit   Evening enrichment     [low]
  flexible   Biscuit   Full grooming          [low]
  flexible   Mochi     Litter box             [medium]
  flexible   Mochi     Nail trim              [low]

====================================================================
                             FILTERING
====================================================================
  Mochi only:
    - Litter box
    - Thyroid medication
    - Nail trim
  Still outstanding (any pet):
    - Biscuit: Evening enrichment
    - Biscuit: Morning walk
    - Biscuit: Full grooming
    - Biscuit: Breakfast
    - Mochi: Litter box
    - Mochi: Thyroid medication
    - Mochi: Nail trim
  High priority only:
    - Biscuit: Morning walk
    - Biscuit: Breakfast
    - Mochi: Thyroid medication

====================================================================
                           CONFLICT CHECK
====================================================================
  WARNING: Biscuit's Breakfast (08:15-08:25) overlaps Mochi's Thyroid medication (08:15-08:20); the later one will be pushed back.

====================================================================
                          RECURRING TASKS
====================================================================
  Completing Biscuit's 'Morning walk' (due 2026-10-07, daily)
  -> next instance queued for 2026-10-08
  Completing Mochi's 'Nail trim' (once)
  -> None queued, because it does not repeat
  Outstanding for Biscuit now:
    - Evening enrichment (due 2026-10-07)
    - Full grooming (due 2026-10-07)
    - Breakfast (due 2026-10-07)
    - Morning walk (due 2026-10-08)

====================================================================
                    TODAY'S SCHEDULE for Jordan
====================================================================
  08:15-08:20   Mochi     Thyroid medication     [high]
  08:20-08:30   Biscuit   Breakfast              [high]
  18:00-18:20   Biscuit   Evening enrichment     [low]
  18:20-18:30   Mochi     Litter box             [medium]
  18:30-19:15   Biscuit   Full grooming          [low]

====================================================================
                           WHY THIS PLAN
====================================================================
Jordan has 100 minutes today across 2 pets.
Tasks were ranked by priority, then by how short they are, so quick wins are not crowded out by one long low-priority job.
The plan works around these blocked times: 12:00-13:00.
  08:15 Mochi: Thyroid medication -> high priority, picked 1 of 5 into the 100 min budget; placed at the requested time
  08:20 Biscuit: Breakfast -> high priority, picked 2 of 5 into the 100 min budget
  18:00 Biscuit: Evening enrichment -> low priority, picked 4 of 5 into the 100 min budget; placed at the requested time
  18:20 Mochi: Litter box -> medium priority, picked 3 of 5 into the 100 min budget
  18:30 Biscuit: Full grooming -> low priority, picked 5 of 5 into the 100 min budget
```
