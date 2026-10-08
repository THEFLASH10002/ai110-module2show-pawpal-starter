# PawPal+ (Module 2 Project)

You are building **PawPal+**, a Streamlit app that helps a pet owner plan care tasks for their pet.

## Scenario

A busy pet owner needs help staying consistent with pet care. They want an assistant that can:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

Your job is to design the system first (UML), then implement the logic in Python, then connect it to the Streamlit UI.

## What you will build

Your final app should:

- Let a user enter basic owner + pet info
- Let a user add/edit tasks (duration + priority at minimum)
- Generate a daily schedule/plan based on constraints and priorities
- Display the plan clearly (and ideally explain the reasoning)
- Include tests for the most important scheduling behaviors

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.

## 🖥️ Sample Output

`python main.py` builds a sample household (one owner, two pets, seven tasks, a 100
minute budget and a blocked lunch hour) and walks through every scheduling feature:

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

## 🧪 Testing PawPal+

```bash
# Run the full test suite:
pytest

# Run with coverage:
pytest --cov
```

Sample test output:

```
============================= test session starts =============================
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0 -- C:\Users\kenne\AppData\Local\Programs\Python\Python312\python.exe
cachedir: .pytest_cache
rootdir: ...
plugins: anyio-4.13.0
collecting ... collected 16 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [  6%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [ 12%]
tests/test_pawpal.py::test_owner_collects_tasks_across_all_pets PASSED   [ 18%]
tests/test_pawpal.py::test_high_priority_is_scheduled_before_low PASSED  [ 25%]
tests/test_pawpal.py::test_task_is_skipped_when_budget_runs_out PASSED   [ 31%]
tests/test_pawpal.py::test_completed_tasks_are_left_out_of_the_plan PASSED [ 37%]
tests/test_pawpal.py::test_scheduler_works_around_a_blocked_window PASSED [ 43%]
tests/test_pawpal.py::test_planning_twice_does_not_mutate_the_pets_tasks PASSED [ 50%]
tests/test_pawpal.py::test_sort_by_time_orders_tasks_entered_out_of_order PASSED [ 56%]
tests/test_pawpal.py::test_filter_tasks_narrows_by_pet_and_status PASSED [ 62%]
tests/test_pawpal.py::test_completing_a_daily_task_queues_it_for_tomorrow PASSED [ 68%]
tests/test_pawpal.py::test_completing_a_weekly_task_queues_it_seven_days_out PASSED [ 75%]
tests/test_pawpal.py::test_completing_a_one_off_task_queues_nothing PASSED [ 81%]
tests/test_pawpal.py::test_tomorrows_task_is_not_planned_today PASSED    [ 87%]
tests/test_pawpal.py::test_detect_conflicts_warns_on_overlapping_requested_times PASSED [ 93%]
tests/test_pawpal.py::test_detect_conflicts_is_quiet_when_times_only_touch PASSED [100%]

============================= 16 passed in 0.03s ==============================
```

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

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
