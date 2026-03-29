# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

The three core actions a user should be able to perform in PawPal+:

1. **Add a pet** — The user enters their pet's basic information (name, species, age, and any special needs). This sets up the context the scheduler uses when evaluating task priorities. For example, an older dog may have more frequent medication tasks, and the system should know that before generating a plan.

2. **Add or edit a care task** — The user creates a task (such as a walk, feeding, or grooming session) and sets its duration and priority level. They can also edit an existing task if the pet's routine changes. This action is the primary way the user builds the list of things that need to happen each day.

3. **Generate and view today's plan** — The user triggers the scheduler, which takes the current task list and any time or priority constraints and produces a daily schedule. The plan is displayed with an explanation of why tasks were ordered the way they were, so the owner understands the reasoning and can trust the output.

- Briefly describe your initial UML design.
- What classes did you include, and what responsibilities did you assign to each?

**b. Design changes**

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
