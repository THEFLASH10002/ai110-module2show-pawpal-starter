# PawPal+ Project Reflection

## 1. System Design

**a. Core user actions**

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

**b. Initial design**

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**c. Design changes**

- Did your design change during implementation?
- If yes, describe at least one change and why you made it.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
- How did you decide which constraints mattered most?

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
- Why is that tradeoff reasonable for this scenario?

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
