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

Running `python main.py` builds a sample household (one owner, two pets, six tasks,
a 100 minute budget and a blocked lunch hour) and prints the plan:

```
================================================================
                  TODAY'S SCHEDULE for Jordan
================================================================
  07:30-08:00   Biscuit   Morning walk           [high]
  08:15-08:25   Biscuit   Breakfast              [high]
  09:00-09:05   Mochi     Thyroid medication     [high]
  18:00-18:20   Biscuit   Evening enrichment     [low]
  18:20-18:30   Mochi     Litter box             [medium]
----------------------------------------------------------------
  NOT SCHEDULED TODAY
  --            Biscuit   Full grooming          [low]
                why: needs 45 min but only 25 min of the budget was left
================================================================

WHY THIS PLAN
Jordan has 100 minutes today across 2 pets.
Tasks were ranked by priority, then by how short they are, so quick wins are not crowded out by one long low-priority job.
The plan works around these blocked times: 12:00-13:00.
  07:30 Biscuit: Morning walk -> high priority, picked 3 of 6 into the 100 min budget; placed at the requested time
  08:15 Biscuit: Breakfast -> high priority, picked 2 of 6 into the 100 min budget; placed at the requested time
  09:00 Mochi: Thyroid medication -> high priority, picked 1 of 6 into the 100 min budget; placed at the requested time
  18:00 Biscuit: Evening enrichment -> low priority, picked 5 of 6 into the 100 min budget; placed at the requested time
  18:20 Mochi: Litter box -> medium priority, picked 4 of 6 into the 100 min budget
  dropped Biscuit: Full grooming -> needs 45 min but only 25 min of the budget was left
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
platform win32 -- Python 3.12.0, pytest-9.1.1, pluggy-1.6.0
rootdir: .../ai110-module2show-pawpal-starter
collected 8 items

tests/test_pawpal.py::test_mark_complete_changes_status PASSED           [ 12%]
tests/test_pawpal.py::test_adding_task_increases_pet_task_count PASSED   [ 25%]
tests/test_pawpal.py::test_owner_collects_tasks_across_all_pets PASSED   [ 37%]
tests/test_pawpal.py::test_high_priority_is_scheduled_before_low PASSED  [ 50%]
tests/test_pawpal.py::test_task_is_skipped_when_budget_runs_out PASSED   [ 62%]
tests/test_pawpal.py::test_completed_tasks_are_left_out_of_the_plan PASSED [ 75%]
tests/test_pawpal.py::test_scheduler_works_around_a_blocked_window PASSED [ 87%]
tests/test_pawpal.py::test_planning_twice_does_not_mutate_the_pets_tasks PASSED [100%]

============================== 8 passed in 0.02s ==============================
```

## 📐 Smarter Scheduling

| Feature | Method(s) | Notes |
|---------|-----------|-------|
| Task sorting | `Scheduler.sort_by_priority`, `Task.priority_rank` | High before low, then shortest first so quick wins are not crowded out by one long job |
| Filtering | `Scheduler.select_tasks`, `Task.fits_in` | Spends the owner's minute budget in priority order; anything that no longer fits is skipped with a reason |
| Conflict handling | `Scheduler.assign_times`, `Owner.blocking_window` | Tasks run back to back from a single cursor, so two pets never collide; blocked windows are checked against the whole task duration, not just its start |
| Recurring tasks | `Task.frequency`, `Task.mark_complete` | `frequency` records daily / weekly / once; completed tasks drop out of the next plan until `mark_incomplete` resets them |

## 📸 Demo Walkthrough

Describe your app in numbered steps so a reader can follow along without watching a video:

1. <!-- Describe this step -->
2. <!-- Describe this step -->
3. <!-- Describe this step -->
4. <!-- Describe this step -->
5. <!-- Add more steps as needed -->

**Screenshot or video** *(optional)*: <!-- Insert a screenshot or link to a demo video here -->
