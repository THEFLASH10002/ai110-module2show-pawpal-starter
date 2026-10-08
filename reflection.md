# PawPal+ Project Reflection

## 1. System Design

**Core user actions**

Before drawing the UML, I identified the three core actions a pet owner must be able to
perform in PawPal+:

1. **Set up an owner and pet profile.** The user enters their own name and their pet's
   basic info (name, species, breed) along with care preferences, such as how much time
   they have available on a given day and times of day they would rather not schedule
   anything. This is the context every plan is built against, so it has to come first.

2. **Add and edit pet care tasks.** The user builds a list of things their pet needs,
   like a morning walk, feeding, medication, grooming, or enrichment play. For each task
   they give at least a title, how many minutes it takes, and how important it is
   (low / medium / high). They can also go back and change a task or remove one when the
   pet's routine shifts.

3. **Generate and read today's plan.** The user asks PawPal+ for a daily schedule. The
   app fits the tasks into the time the owner actually has, puts the higher-priority care
   first, drops or defers what will not fit, and shows the result as an ordered list of
   times. Alongside the plan it explains its reasoning, so the owner can see why the
   medication landed before the enrichment play and what got left out.

**a. Initial design**

My first UML draft had four classes, split so that each one owns a different kind of
knowledge:

- **`Owner`** holds the person and, more importantly, the constraints they bring to the
  day: their name, how many minutes they actually have, which times are off limits, and
  the list of pets they care for. I kept the constraints here rather than on the
  scheduler because they describe the owner's life, not the algorithm.

- **`Pet`** holds the animal's identity (name, species, breed) and owns its list of care
  tasks. I deliberately hung tasks off the pet instead of the owner, because a walk
  belongs to the dog, not to the person. If a second pet is added later, its tasks stay
  cleanly separate with no rework.

- **`Task`** is one unit of care: a title, how long it takes, how important it is, and
  whether it repeats. It also knows two small things about itself, `priority_rank()` to
  turn "high" into a sortable number and `fits_in()` to answer whether it still fits in
  the time left. Keeping those on the task means the scheduler does not need to reach
  inside it.

- **`Scheduler`** is the only class with real behaviour. It reads the owner's constraints
  and the pet's tasks, chooses which tasks make the cut, orders them, assigns clock times,
  and explains the result. I made it a separate class rather than a method on `Owner`
  because the scheduling strategy is the part most likely to change.

I deliberately left out a separate plan class at this stage, so the scheduler simply kept
`planned` and `skipped` lists of its own. My reasoning was that a fifth class with no
behaviour of its own would be complexity I had not earned yet.

**b. Design changes**

Yes. After writing the skeleton in `pawpal_system.py` I asked an AI assistant to review
it for missing relationships and logic bottlenecks. It raised six issues. I agreed with
all six and made the following changes:

1. **The scheduler now takes the owner, not a single pet.** `Scheduler.__init__` used to
   accept one `Pet`, even though `Owner.pets` was a list. That meant two pets produced two
   independent schedulers, each spending the owner's available minutes a second time and
   each free to put something at 08:00. The scheduler now takes only the `Owner` and
   gathers tasks across every pet, so one budget and one timeline cover the whole day.

2. **I added a `PlannedItem` class after all, reversing my original decision.** This is
   the change I thought hardest about. `Task` had a `scheduled_time` attribute, which
   meant that generating a plan wrote into the pet's permanent task list. Re-running with
   less time available left skipped tasks still carrying a stale timestamp from the
   previous run. Separating the *definition* of a task from one *placement* of it fixes
   that, and `PlannedItem` turned out to have real work to do: it carries the pet, the
   start time, an `end_time()` method and the reason the task landed there. The fifth
   class was earned after all.

3. **Tasks now have a `task_id`.** `edit_task()` and `remove_task()` matched on title, but
   "Feeding" happens twice a day. Matching on title would have edited whichever one came
   first in the list.

4. **`blocked_times: list[str]` became `blocked_windows: list[tuple[str, str]]`.** A
   single string can only mark an instant, and being unavailable is a period with a start
   and an end. The check also changed from `is_time_blocked(start_time)` to
   `overlaps_blocked(start_time, duration_minutes)`, because the old version only looked at
   where a task began, so a 60 minute walk starting at 11:30 would run straight through a
   12:00 block without being noticed.

5. **I split `generate_plan()` into four smaller methods**: `collect_tasks()`,
   `sort_by_priority()`, `select_tasks()` and `assign_times()`. The original did all four
   jobs at once, which meant I could not test "does it order by priority" without also
   exercising time assignment. `generate_plan()` still exists and calls them in order, so
   the UI has one method to call.

6. **`explain_plan()` now takes the plan as an argument.** Before, it read
   `self.planned` and `self.skipped`, so it quietly returned nothing useful unless
   `generate_plan()` had already run. Passing the plan in makes that dependency visible in
   the signature and leaves the scheduler stateless.

7. **`CareTask` became `Task`, and gained completion state.** When I moved from skeleton to
   implementation the spec called for a `Task` that tracks a completion status, so I
   renamed the class and added `is_complete` with `mark_complete()` and
   `mark_incomplete()`. That turned out to matter for more than display: `collect_tasks()`
   now gathers only pending work, so a task ticked off in the morning does not reappear
   when the plan is regenerated in the afternoon. At the same time `is_recurring: bool`
   became `frequency: str`, because a boolean could only ever answer "daily or not" and
   weekly grooming is a real case.

I also updated `diagrams/uml_draft.mmd` to match, so the diagram and the code do not drift
apart before Phase 6.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

The scheduler weighs four constraints, and the order matters because they are applied at
different stages rather than all at once.

1. **A time budget.** `Owner.available_minutes` is how many minutes of care the owner
   actually has. `select_tasks` spends it in priority order and everything past the end of
   the budget is dropped. This is the first constraint applied, because it decides *what*
   happens at all before anything decides *when*.
2. **Priority.** `Task.priority_rank` turns high / medium / low into a sortable number, and
   ties break on the shortest task first. That tie-break is deliberate: given a 45 minute
   grooming session and three 10 minute jobs at the same priority, doing the three short
   ones helps the pet more than one long one.
3. **Requested times.** A task with a `preferred_time` is pinned there, and the clock walks
   forward from task to task so nothing double-books, even across two pets.
4. **Blocked windows and the day's end.** `Owner.blocking_window` checks a task against the
   owner's unavailable periods, and anything that cannot finish before the cutoff is
   deferred rather than allowed to overrun.

I decided the time budget mattered most because it is the constraint the owner cannot
negotiate with. Priority comes next because the scenario is about a busy owner staying
consistent with care that matters, which means medication should survive a squeeze that
enrichment does not. Requested times rank below priority on purpose: a task being at
exactly 09:00 matters less than it happening at all. Blocked windows are last because they
only move a task rather than remove it.

**b. Tradeoffs**

The clearest tradeoff is in how requested times interact with priority. Once a task has a
`preferred_time`, that time wins over importance when the plan is laid out, and every
flexible task is placed after all of the pinned ones.

`Scheduler._order_for_clock` splits the selected tasks into two groups: those with a
requested time, sorted by the clock, and those without, sorted by priority. The requested
group is placed first and the flexible group fills in afterwards. In practice that means a
low priority "evening enrichment" pinned to 18:00 drags a medium priority "litter box"
with no set time out to 18:20, even though the litter box is the more important job and
there was an empty hour at 09:00 it could have filled.

I chose this deliberately rather than by accident. The alternative is a gap-filling
scheduler that slots flexible tasks into the empty space between pinned ones, which is
genuinely better output but needs interval bookkeeping: tracking free windows, trying each
flexible task against each gap, and deciding what to do when a task fits two gaps. That is
a noticeably more complicated algorithm to write, read and test.

For this scenario the simple version is defensible. The things that genuinely must happen
at a fixed time are the ones an owner pins: medication at 09:00, feeding at 08:15. Those
land exactly where they were asked for, which is the behaviour that actually matters for
the pet's health. A flexible task landing at 18:20 instead of 09:00 is untidy, not harmful,
because by definition the owner said they did not care when it happened. The scheduler also
makes the consequence visible rather than hiding it: `explain_plan` prints why each task sits
where it does, so the owner can see a task was placed late and pin it themselves if they
disagree.

A related, smaller tradeoff sits in `detect_conflicts`. It compares the times the owner
*requested*, not the finished plan, and it checks true interval overlap rather than exact
equality, so an 08:15 breakfast lasting 10 minutes is reported as clashing with 08:20
medication. It returns warning strings and never raises. The cost is that it reports a
clash the scheduler then quietly resolves by pushing the later task back, which could read
as a false alarm. I kept it because the warning is the only place the owner learns that
something they pinned to a specific time will not actually happen at that time.

---

## 3. AI Collaboration

**a. How you used AI**

I used an AI coding assistant in agent mode throughout, where it could read and edit
several files at once and run commands itself. Three uses were clearly the most valuable.

The first was **adversarial review of my own design**. After writing the class skeleton I
asked it to look for missing relationships and logic bottlenecks rather than to add
features. It came back with six issues, and all six were real: the scheduler took a single
`Pet` while the owner held a list of them, tasks were identified by title when "Feeding"
happens twice a day, and `generate_plan` was doing four jobs at once so I could not test
ordering without also testing time assignment. Asking "what is wrong with this" produced
far more useful output than asking "what should I build next".

The second was **having it actually run the code instead of describing it**. The agent ran
`python main.py` and the test suite after each change, and used Streamlit's `AppTest`
harness to click through the UI. That is what caught the bugs described below. Code that
looks correct in a chat window is not evidence of anything.

The third was **writing tests from stated edge cases**. I described the situations I cared
about in plain language, such as an owner with no pets or two tasks pinned to the same
minute, and had it draft the tests. Describing the behaviour was the part that needed my
judgement; writing the assertions was not.

The prompts that worked best named a specific file and asked a narrow question about it.
The ones that worked worst were open invitations like "make this better", which produced
plausible code I then had to argue with.

On organising the work across chat sessions: I used an all-in-one workflow rather than
opening a separate session for each phase. Everything from the first UML sketch to this
reflection happened in one continuous session, so the context carried over the whole way
through. By Phase 6 the assistant still knew why I had argued against a separate plan class
in Phase 2 and then reversed that decision in Phase 3, which meant I never had to
re-attach files or re-explain the design to get a useful answer. Keeping one thread is also
what kept the UML, the code, the README and this reflection consistent with each other,
because every one of those was written with the same history behind it rather than from a
fresh description of the project.

**b. Judgment and verification**

The clearest example was sorting tasks by time. The obvious suggestion is:

```python
sorted(tasks, key=lambda t: t.preferred_time)
```

This looks elegant and it works, because `"HH:MM"` strings happen to sort correctly as text
while every value is zero padded. I rejected it. A flexible task has no requested time, so
`preferred_time` is `None`, and the moment one of those enters the list the comparison
raises `TypeError`. I replaced it with a named `_clock_key` method that converts to minutes
and returns `(clock is None, minutes)`, so untimed tasks sort to the end instead of
crashing. It is more lines of code, and I kept it because the `None` handling is visible
rather than being a bug waiting for the first flexible task.

I also reversed one of my own earlier decisions after thinking harder about an AI
observation. I had argued against a separate plan class as unearned complexity, and stored
`scheduled_time` directly on the task. The review pointed out that this meant generating a
plan wrote into the pet's permanent task list. I checked, and it was worse than it sounded:
re-running with a smaller budget left stale timestamps on tasks that had been skipped. I
added `PlannedItem` after all. Being told I was wrong by a tool is only useful if I verify
the claim rather than either dismissing it or accepting it, and in this case writing the
failing scenario out by hand was what settled it.

How I verified things in general: I ran everything. The test suite went from 2 tests to 30,
and three genuine bugs were found by running code rather than by reading it.

- **A recurring task fed itself.** Completing today's walk queued tomorrow's copy, which
  immediately appeared in *today's* plan, because `collect_tasks` ignored `due_date`.
- **A Streamlit widget silently discarded data.** Passing `Pet` objects as selectbox options
  returned a *copy*, so `add_task` mutated an object the owner never saw and every task
  vanished with no error at all. The fix was to select by index and look up the real object.
- **A double click duplicated tomorrow.** `Pet.complete_task` queued a follow-up every time
  it was called, so completing an already-completed task left two copies of tomorrow's walk.

Not one of those three would have been caught by reading the code and agreeing that it
looked right.

---

## 4. Testing and Verification

**a. What you tested**

30 tests in `tests/test_pawpal.py`, split between happy paths and edge cases.

The happy paths cover the behaviours the app is actually for: a task's completion status
changes when it is ticked off, adding a task to a pet grows that pet's list, the owner can
reach tasks across every pet, high priority is scheduled before low, work that does not fit
the budget is skipped with a reason, tasks come back in clock order however they were
entered, filters narrow by pet and status, and completing a daily or weekly task queues the
right next date.

The edge cases are the ones I thought were most likely to break something quietly:

- An owner with no pets, and a pet with no tasks, so the empty state plans cleanly instead
  of raising.
- A zero minute budget, where everything should be skipped and still explained.
- A task requested so late it cannot finish before the cutoff, which should be deferred
  rather than allowed to overrun the day.
- Three tasks pinned to one time, not two, to confirm conflict detection is genuinely
  pairwise.
- Recurrence across month and year boundaries, because `31 December + 1 day` is exactly the
  kind of arithmetic that gets hand-rolled and gets wrong.
- Two tasks that merely touch, one ending as the next begins, which must *not* be reported
  as a conflict.
- Completing the same task twice.
- Generating a plan twice in a row, to prove planning does not mutate the pet's own tasks.

These mattered because most of them are about the system being *quietly* wrong rather than
crashing. A scheduler that raises an exception gets fixed immediately. A scheduler that
drops one task, or queues two copies of tomorrow's walk, gets trusted and then quietly
fails a pet.

**b. Confidence**

**Four out of five.** The scheduling logic itself I trust: every branch that decides what
gets scheduled, what gets dropped and when a task repeats has a test behind it, and the
process of writing those tests found three real bugs rather than confirming what I already
believed.

The missing star is for what the suite does not reach. `app.py` has no committed automated
tests, so the UI was verified with throwaway scripts rather than something that runs every
time. Recurrence is only tested one step forward, never over a simulated week, so I have
not proven that completing a task every day for seven days behaves. And nothing covers a
plan crossing midnight, which is currently unreachable because of the day cutoff rather
than proven safe, since `to_clock` wraps with `% 24` in a way I have not had to think hard
about.

With more time, the next tests I would write are: a committed `tests/test_app.py` using
Streamlit's `AppTest` harness so the UI is covered properly; a multi-day simulation that
completes every task for a week and checks nothing accumulates or disappears; a blocked
window that swallows the entire day; and a task longer than the owner's whole budget, to
confirm it is reported as impossible rather than deferred forever.

---

## 5. Reflection

**a. What went well**

The part I am most satisfied with is that the scheduler explains itself. `explain_plan`
prints why each task sits where it does and why anything dropped was dropped, and every
`PlannedItem` carries the reason it landed where it did rather than that reasoning living
only in my head while I wrote the loop.

That turned out to be worth more than I expected. It was never only a feature for the user.
Because the plan explains itself, wrong behaviour announces itself in the output instead of
hiding in a plausible looking list of times. The recurrence bug, where tomorrow's walk
appeared in today's plan, was visible the moment I read the demo output and saw a task I
had just completed scheduled at 07:30. A bare list of times would have looked perfectly
reasonable.

The second thing that went well was separating `Task` from `PlannedItem`. Keeping the
definition of a task apart from one placement of it removed a whole category of bug, and it
is the change I am most confident was the right call, partly because I had argued against it
first.

**b. What you would improve**

The scheduler places every pinned task before every flexible one, so a low priority task
pinned to 18:00 drags a medium priority flexible task out to 18:20, even when there was an
empty hour at 09:00 it could have filled. The fix is gap filling: track the free windows
between pinned tasks and fit flexible work into them, best fit first. I left it out because
it needs real interval bookkeeping and I would rather ship a simple scheduler I can explain
than a clever one I cannot test. It is the first thing I would build next.

I would also redesign how time is represented. `"HH:MM"` strings are easy to display and
awkward to compute with, which is why `to_minutes` and `to_clock` exist at all and why
`to_clock` wraps at 24 hours in a way that has not been examined properly. Using
`datetime.time`, or minutes since midnight throughout with formatting only at the edges,
would remove that whole class of problem.

Finally I would commit the UI tests. They caught two of the three bugs in this project and
they currently do not exist anywhere in the repository.

**c. Key takeaway**

The AI was dramatically better at finding problems in work that already existed than at
deciding what to build. Asking "what is wrong with this skeleton" produced six real issues.
Asking for code to be written produced things like a one-line sort that crashes on `None`,
or a Streamlit selectbox that silently throws away every task the user adds. Both of those
looked completely reasonable, and neither announced that it was wrong.

What that taught me about being the lead architect is that my job was not writing code, and
it was not reviewing code either, because reading code and agreeing with it is exactly the
failure mode. My job was deciding what counted as correct, and then insisting that something
actually run to prove it. Every bug in this project was found by execution, not by
inspection. The tests, the demo script and the `AppTest` harness were not chores at the end;
they were the only thing standing between confident-looking code and code that works.

The related lesson is that taste still has to come from me. The AI's version of a sort was
shorter and more Pythonic than mine and I kept mine, because handling the empty case visibly
was worth four extra lines. Being the architect meant being willing to choose the less
clever option and be able to say why.
