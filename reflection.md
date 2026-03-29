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
Yes
- If yes, describe at least one change and why you made it.
The first change made by using AI feedback is adding self._schedule: list[ScheduledBlock] = [] to Scheduler.__init__ because without stored state, methods like check_conflicts() and explain_plan() would have had nothing to inspect — every method would need the schedule passed in as a parameter, making the class awkward and stateless. Keeping the schedule on the instance means generate_schedule() can populate it once, and every other method can reference it naturally. 
The second change implemented _fits_in_window() because Python's built-in time type does not support arithmetic — adding a timedelta directly to a time object raises a TypeError at runtime. The fix converts both the task's start time and the owner's availability end to full datetime objects using datetime.combine(date.today(), ...), performs the addition safely, then compares the two datetime values. Without this, any attempt to check whether a task fits inside the owner's day would have crashed the moment it ran.

---

## 2. Scheduling Logic and Tradeoffs

**a. Constraints and priorities**

- What constraints does your scheduler consider (for example: time, priority, preferences)?
The constraints our scheduler considers is, for one, the tasks that are ranked in priority from HIGH, MEDIUM, LOW and scheduled in that order. A preference I've made is that tasks can choose to specify a preferred_time. Made sure that every task must fit between available_start and available_end.
- How did you decide which constraints mattered most?
The constraint that matters most is the priority. Prioritizing which tasks need to be completed is the whole point of a scheduler in the first place. Availability is also just as important because if a schedule runs outside the hours in which the Owner isn't home then that wouldn't make sense in the first place.

**b. Tradeoffs**

- Describe one tradeoff your scheduler makes.
Each task starts exactly when the previous one ends, ignoring preferred_time as a hard start time.
- Why is that tradeoff reasonable for this scenario?
For a pet care app, getting all high-priority tasks done matters more than hitting an exact preferred time.
---

## 3. AI Collaboration

**a. How you used AI**

- How did you use AI tools during this project (for example: design brainstorming, debugging, refactoring)?
I used AI (particularly Claude Code inside VS Code) for brainstorming the UML diagram. I also used AI for debugging when, for example, there was no data for the tasks that can now be run and printed in main.py.
- What kinds of prompts or questions were most helpful?
The prompt I made in which gave me the code for mermaid.live and visualizing the UML diagram helped immensely in seeing the structure of the classes and also how certain code needs to be written.

**b. Judgment and verification**

- Describe one moment where you did not accept an AI suggestion as-is.
AI attempted to condense a docstring on line 147 in pawpal_system.py into a one-liner.
- How did you evaluate or verify what the AI suggested?
I rejected it as I felt since it is a comment left there for future reference in this project, having comments in one line will be annoying (at least for me personally) for debugging purposes in the code that follows it. It may be such a small detail in the grand scheme of this project yet I prefer to keep everything readily available and as easy to understand.

---

## 4. Testing and Verification

**a. What you tested**

- What behaviors did you test?
I tested the test_daily_next_occurrance_not_due_today function to verify that completed "Daily" task's next copy is not due today. Also, I tests test_daily_next_due_date_is_tomorrow which helps us verify that if a task happens "Daily," its new due date should be today + 1 day.
- Why were these tests important?
These tests are important as due dates on a scheduler are important and we don't want to confuse whether or not a task is supposed to occur.

**b. Confidence**

- How confident are you that your scheduler works correctly?
I am very confident that my scheduler works. The functionality has been updated dramatically and I've done several tests on my own just to be sure.
- What edge cases would you test next if you had more time?
An edge case I would test if I had more time would be scheduling multiple pets. Tasks from two or more different pets being collected, sorted and interleaved is something I could not find the time to test.
---

## 5. Reflection

**a. What went well**

- What part of this project are you most satisfied with?
I am most satisfied with all of our required tests passing when using pytest as it is a good feeling as a programmer when you get all the green text telling you "17/17 PASSED".

**b. What you would improve**

- If you had another iteration, what would you improve or redesign?
Making preferred_time a had constraint option. It doesn't reject a time slot for being too early and I wish there was just a bit more time to improve on that.

**c. Key takeaway**

- What is one important thing you learned about designing systems or working with AI on this project?
One important thing I've learned working with AI on this project is that I believed that I could simply lean on AI to do everything for me. I thought that this would be a simple pet scheduler app. However, I used AI quite a lot on this app and quickly realized that there's a good amount of debugging to do along with truly understanding what the Chatbox is spitting out. It is very good at generating code, yet way better at helping you describe what is going on. It is best practice to use those descriptions and improve on it yourself afterwards. Ultimately, you still have to be the decision maker regardless of the code coming out correctly. 
