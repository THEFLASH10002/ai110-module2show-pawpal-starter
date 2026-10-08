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

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

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

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
- What kinds of prompts or questions were most helpful?

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
- How did you evaluate or verify what the AI suggested?

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
- Why were these tests important?

**b. Confidence**

- How confident are you that your scheduler works correctly?
- What edge cases would you test next if you had more time?

---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
