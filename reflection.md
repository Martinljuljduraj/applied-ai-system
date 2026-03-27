# PawPal+ Project Reflection

## 1. System Design

**a. Initial design**

- Briefly describe your initial UML design.
The initial UML design centered on five classes: Owner, Pet, Task, Scheduler, and ScheduledBlock, plus two enums (Priority, Frequency).

- What classes did you include, and what responsibilities did you assign to each?
The classes I made are the Owner, Pet, Task, Scheduler, and ScheduledBlock. The owner
can own, add, or remove pets. Pet can be given tasks or tasks removed from Pet. Scheduler takes an owner, collects all tasks across all pets, sorts them by priority, checks for time conflicts, and generates the daily plan within the owner's available hours. The ScheduledBlock has the pet name, task, start and end times along with reason. Task has a description as to what is required, the amount of time it will take to do a particular task in minutes, priority, time it will take place, how frequently the task may be done (if done more than once), and will be mark when completed.

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
