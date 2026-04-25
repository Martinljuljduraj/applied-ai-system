# Model Card — PawPal+ AI Advisor

## Model details

**Model used:** Claude claude-haiku-4-5 by Anthropic  
**Integration type:** API call via the `anthropic` Python SDK  
**Role in system:** Context-aware pet care advisor that reads live pet and schedule data to generate personalized task recommendations and answer pet care questions

---

## Intended use

PawPal+ AI Advisor is designed to help individual pet owners manage their pet's daily care by suggesting tasks, answering care questions, and identifying gaps in the current schedule. It is intended for personal, non-commercial use.

**Intended users:** Pet owners who want AI-assisted guidance on managing their pet's care routine.

**Out-of-scope use:** The advisor is not intended to diagnose medical conditions, replace veterinary advice, or make safety-critical decisions about animal welfare.

---

## Limitations and biases

**Knowledge limitations:** Claude's pet care knowledge reflects its training data and may not align with the latest veterinary research or breed-specific guidelines. Advice should be treated as a starting point, not a professional recommendation.

**Species bias:** The model has significantly more knowledge about common pets such as dogs and cats than exotic or uncommon species. Advice for unusual animals may be generic or less accurate.

**No memory across sessions:** The system passes only the current session's pet name, species, and task list to Claude. It does not retain information between conversations, so it cannot track a pet's health history or notice changes over time.

**No medical diagnosis:** The AI advisor is not equipped to diagnose health conditions. Any health-related output should be verified with a licensed veterinarian before acting on it.

**Prompt sensitivity:** Response quality and specificity can vary based on how a question is phrased. Vague questions tend to produce more generic advice. Providing breed, age, and specific context consistently improves output quality.

---

## Could this AI be misused?

**Over-reliance on AI advice:** A user could follow AI task suggestions without consulting a vet, potentially missing a health issue that requires professional attention. The system mitigates this by framing all suggestions as recommendations, not medical instructions, and by not making any diagnostic claims.

**Incorrect species input:** A user could enter an incorrect or unusual species and receive irrelevant or misleading care advice. A future version could add species validation or a confidence warning when the species is uncommon.

**Data privacy:** Chat interactions are logged locally to `logs/pawpal_ai_log.jsonl`. These logs contain pet names and user messages. The logs directory is excluded from version control via `.gitignore`, but users running the app locally should be aware that this data is stored on their machine.

**Prompt injection:** If a user types adversarial instructions into the chat input attempting to override the system prompt, Claude may partially follow them. A future version could add input sanitization or stricter system prompt constraints.

---

## What surprised me while testing reliability

The AI was consistently good at formatting task suggestions in the requested structure (Task | Duration | Priority) even when questions were phrased casually or conversationally. This was better than expected.

What surprised me negatively was that the model occasionally gave overly long responses to simple yes/no questions about pet care. Adding a `max_tokens` cap and a prompt instruction to keep responses concise helped, but responses can still be verbose for simple queries.

The error handling performed exactly as designed. When the API key was invalid and when the account had insufficient credits, the app displayed a safe fallback message rather than crashing, and both failures were logged correctly with their error messages.

---

## AI collaboration notes

**Where AI was helpful:** Claude was particularly useful in structuring the system prompt for the AI advisor. Specifically the instruction to format suggestions as `Task | Duration | Priority`. This format made it straightforward to parse and display responses consistently in the UI. Claude also suggested the JSONL logging format early in development, which turned out to be the right choice for structured interaction records.

**Where AI was flawed:** When asked how to handle the case where a user opens the AI Advisor tab before saving a pet, the AI suggested wrapping the entire tab in a `try/except` block. This would have silently swallowed unrelated errors and made debugging much harder. A targeted `if st.session_state.pet is None` guard was used instead as it is more precise and easier to reason about.

---

## Testing results

| Test area | Result |
|---|---|
| Scheduler priority ordering | 4/4 passed |
| Recurrence logic | 4/4 passed |
| Conflict detection | 4/4 passed |
| Task and pet fundamentals | 5/5 passed |
| AI advisor error handling | Returns safe fallback on API failure |
| AI advisor logging | Logs all interactions to JSONL with context |
| **Total** | **17/17 scheduler tests passed** |

---

## Reflection

**What this project taught me about AI and problem-solving:**

The most important thing this project reinforced is that AI is most useful when given precise, structured context. A generic chatbot and a useful AI advisor use the same underlying model. The difference is entirely in how much relevant state you pass into each call. By including the pet's name, species, and current task list in every request, the AI's responses became dramatically more relevant and actionable.

The project also clarified when not to use AI. The scheduler is deterministic and rule-based because scheduling needs to be predictable, testable, and explainable. Replacing it with an AI model would introduce unpredictability with no benefit. Knowing where to draw that line, using the AI for open-ended reasoning, and rules for deterministic logic is one of the most practical skills in applied AI development.

Working with Claude as a coding assistant throughout this project also highlighted the importance of staying in the decision-making role. AI generates code quickly, but understanding what it generates, questioning its suggestions, and adapting them to the specific needs of your system is what separates a working prototype from a well-designed one. Every suggestion from the AI was evaluated before being accepted, and several were rejected or modified which in each case led to cleaner and more maintainable code.
