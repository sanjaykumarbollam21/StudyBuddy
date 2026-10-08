# Study Buddy — AI Teacher Engine Architecture (Phase 4A)

## 1. Overview & Vision

Study Buddy is designed not as a passive RAG search bot or essay generator, but as a **patient, attentive personal teacher who sits beside the student**.

Unlike standard chat interfaces that dump large walls of text, the **Teaching Engine** executes an active multi-turn pedagogical state loop:

```text
Student: "Teach me deadlocks"
           │
           ▼
1. Assess Prior Knowledge ("What do you already know?")
           │
           ▼
2. Teach ONE Concept (Concise explanation + Physical analogy + Cited notes)
           │
           ▼
3. Check for Understanding ("🎯 Why can't either process continue?")
           │
           ▼
4. Evaluate Comprehension
           │
   ┌───────┴───────┐
   ▼               ▼
[CORRECT]     [STRUGGLING / MISCONCEPTION]
• Reinforce why it's right   • Diagnose specific error
• Mastery ↑                  • Re-explain with simpler analogy
• Advance to Next Concept    • Guided Socratic question
                             • Re-test
```

---

## 2. Pedagogical State Machine (`TeachingSession`)

| State | Role | Example Action / Prompt |
| :--- | :--- | :--- |
| `ASSESS_PRIOR_KNOWLEDGE` | Evaluates student baseline | *"Before we start, what do you already know about {topic}?"* |
| `TEACH_CONCEPT` | Delivers one sub-concept | Concise explanation (≤ 3 paragraphs) + concrete analogy |
| `CHECK_UNDERSTANDING` | Targeted formative question | *"🎯 Why can't either process continue?"* |
| `EVALUATING` | Diagnoses student response | Classifies as `CORRECT`, `PARTIALLY_CORRECT`, `MISCONCEPTION`, or `STRUGGLING` |
| `RETEACHING` | Adaptive remediation | Re-explains addressing the error + simpler analogy + simpler check question |
| `ADVANCING` | Positive reinforcement | Praises insight, increases mastery, moves to next sub-concept |
| `COMPLETED` | Topic mastery reached | Congratulates student, awards 100% mastery, suggests quiz |

---

## 3. First-Class LLM Provider Abstraction

The teaching engine is **provider-independent** and supports both 100% offline local operation and optional cloud reasoning without bypassing grounding rules:

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, prompt: str, system_prompt: str) -> str: ...

    @abstractmethod
    async def evaluate_student_answer(
        self, concept_title: str, question: str, expected_concept: str,
        student_answer: str, common_misconceptions: dict, context_text: str
    ) -> dict: ...

    @abstractmethod
    async def generate_remediation(
        self, concept_title: str, student_answer: str, misconception: str,
        original_analogy: str, context_text: str
    ) -> dict: ...
```

### Implementations:
1. **`LocalLLMProvider`** (Offline Mode):
   - Uses local pretrained semantic embeddings (`BAAI/bge-small-en-v1.5`) to match student answers against target concepts and known misconceptions.
   - Zero external HTTP requests; verified with socket connections blocked.
2. **`CloudLLMProvider`** (`GeminiLLMProvider`, `OpenAILLMProvider`):
   - Structured JSON completion with strict Socratic system instructions.
   - Never bypasses RAG grounding rules.
3. **`MockLLMProvider`**:
   - Deterministic test harness simulating pedagogical evaluation.

---

## 4. Answer Evaluation Engine & Diagnostic Remediation

### Evaluation Verdicts:
1. **`CORRECT`**: Student identifies the core mechanism. (+25% mastery).
2. **`PARTIALLY_CORRECT`**: Identifies part of the mechanism. (+10% mastery).
3. **`MISCONCEPTION`**: Identifies a specific conceptual misunderstanding (e.g., *"CPU too slow"* vs *"circular resource wait"*). (Triggers remediation).
4. **`STRUGGLING`**: Student says *"I don't know"*, *"hint"*, or *"explain simpler"*. (Triggers simplified analogy and guided hint).

### Adaptive Remediation:
When a student has a misconception:
1. Re-explains why the intuition was reasonable but technically flawed.
2. Introduces a simpler everyday physical analogy (e.g., *Two people each holding one key while needing the other*).
3. Presents a bite-sized check question testing the simpler case.

---

## 5. API Endpoints

- `POST /api/v1/teaching/start`: Initiates a structured teaching session.
- `POST /api/v1/teaching/{session_id}/interact`: Submits student answer or requests hint/simplification.
- `GET /api/v1/teaching/{session_id}`: Retrieves full session state and dialogue turn history.
