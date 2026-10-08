# Practice, Assessment & Mastery Engine Architecture

## 1. Architectural Role in the Learning Loop

Phase 5 introduces the application and evidence-based assessment layer of Study Buddy:

```text
                    STUDY BUDDY
                         │
                   Curriculum (4B)
                         ↓
                      TEACH (4A)
                         ↓
                     PRACTICE (5)
                         ↓
                 ┌───────┴───────┐
                 ↓               ↓
              Correct         Incorrect
                 ↓               ↓
           Harder question    Diagnose Misconception
                 ↓               ↓
           Deeper mastery     Remediate with Teacher
                 │               │
                 └───────┬───────┘
                         ↓
                      MASTERY
                         ↓
                Review later (6)
                         ↓
                 Spaced Repetition
```

---

## 2. Seven Question Types & Evaluation Engine

The engine supports seven pedagogical assessment formats:
1. **MCQ (Single-Choice)**: Direct concept retrieval with distractor analysis.
2. **Multiple-Select**: Multi-constraint verification with precision/recall partial credit.
3. **True / False**: Invariant checking with misconception refutations.
4. **Short Answer**: Keyword and synonym evaluation.
5. **Fill-in-the-Blank**: Precise terminology and definition recall.
6. **Scenario / Application**: Problem-diagnosis and system intervention simulation.
7. **Coding**: Implementation checking (syntactic invariants, thread-safety, locks, condition variables).

### 2.1 Distractor Generation & Misconception Diagnosis
Rather than generic multiple-choice options, every incorrect option is explicitly paired with a known misconception rationale:
```json
{
  "Mutual Exclusion": "Misconception: Mistaking Mutual Exclusion as a preventative measure instead of a deadlock prerequisite.",
  "Hold and Wait": "Hold and Wait is an essential Coffman condition: a process must hold at least one resource while waiting for another."
}
```
When a student selects an incorrect option, the system diagnoses the exact conceptual confusion and proposes immediate remediation.

---

## 3. Evidence-Based Mastery Tracking

Mastery is updated based on empirical performance, not completion checkboxes:

$$M_{\text{new}} = (\alpha \cdot M_{\text{old}}) + ((1 - \alpha) \cdot \text{Score}_{\text{scaled}})$$

Where:
- $\alpha = 0.7$ (damping factor preserving historical performance).
- $\text{Score}_{\text{scaled}} = \text{Score} \times 100$.
- `consecutive_correct` is tracked to measure consistency.
- Any score $< 0.70$ or distractor diagnosis logs a structured entry in `StudentMastery.weak_areas`.
- When $M_{\text{new}} \ge 80\%$, the topic triggers downstream unlocks in the Phase 4B Knowledge Graph / Curriculum Roadmap.

---

## 4. Integration with Prior Phases

- **Phase 4A Teacher Engine**: When a misconception is diagnosed in practice, a direct action button (*"Re-teach with AI Teacher"*) launches the Socratic `InteractiveTeacherScreen`.
- **Phase 4B Curriculum Engine**: Practice mastery updates directly feed into topic unlocking in the DAG roadmap.
- **Phase 3 RAG Engine**: Document chunks from uploaded PDFs generate grounded practice questions.
