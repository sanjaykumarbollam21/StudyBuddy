# Spaced Repetition & Intelligent Revision Engine Architecture

## 1. Architectural Role in the Learning Loop

Phase 6 implements the long-term retention and intelligent review scheduler of Study Buddy:

```text
                 MASTERY (5)
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
      Strong                  Weak
          │                   │
          ↓                   ↓
   Longer interval       Shorter interval
          │                   │
          └─────────┬─────────┘
                    ↓
             Review Scheduler (6: SM-2)
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
      Recall      Practice    Re-teach
        │           │           │
        └───────────┼───────────┘
                    ↓
              New Evidence
                    ↓
          Hardened Mastery Update
                    ↓
             Next Review Date
```

---

## 2. SuperMemo SM-2 Algorithm & Hardened Mastery

### 2.1 SM-2 Scheduling
- **Quality Scale ($q \in [0, 5]$)**:
  - 5: Perfect recall with zero hesitation
  - 4: Good recall after hesitation
  - 3: Serious difficulty, but correct
  - 2: Failed recall; remembered upon reveal
  - 1: Failed recall; recognized
  - 0: Complete blackout
- **Ease Factor Update**:
  $$EF' = \max\left(1.3, EF + \left(0.1 - (5 - q) \times (0.08 + (5 - q) \times 0.02)\right)\right)$$
- **Interval Progression ($I$)**:
  - $q < 3$: Reset $n = 0$, $I = 1$ day.
  - $q \ge 3$:
    - $n = 0 \implies I = 1$ day, $n = 1$.
    - $n = 1 \implies I = 6$ days, $n = 2$.
    - $n \ge 2 \implies I = \text{round}(I_{\text{prev}} \times EF')$, $n = n + 1$.

### 2.2 Hardened Multi-Factor Mastery
Mastery moves beyond simple moving averages and incorporates:
- **Historical Trajectory**: Rewards upward learning streaks ($40 \to 60 \to 80 \to 100$) over regression ($80 \to 80 \to 60 \to 40$).
- **Ebbinghaus Forgetting Curve**: Memory decay factor ($R = e^{-0.03 \cdot t_{\text{overdue}}}$) penalizes concepts neglected beyond their scheduled date.
- **Misconception Recurrence Penalty**: Reduces mastery score if recurrent misconceptions are logged in `StudentMastery.weak_areas`.
- **Independent Recall Consistency Boost**: Rewards consecutive independent active recalls.

---

## 3. Active Recall Paradigm

Study Buddy never simply displays passive study notes.
1. The student is presented with an **Active Retrieval Probe** (e.g. *"Explain the 4 Coffman conditions from memory and what each means"*).
2. The student retrieves the concept mentally (optionally writing it down).
3. The student reveals the canonical key concepts and self-evaluates on the 0-5 scale.
4. If recall lapses ($q < 3$), Study Buddy automatically logs the misconception and offers a one-tap action to **Re-teach with the Socratic AI Teacher (Phase 4A)**.

---

## 4. "Today's Learning" Dashboard Hub

The main Home dashboard acts as an intelligent learning manager:
- 📚 **Continue Learning**: Active curriculum roadmap milestone (Phase 4B).
- 🧠 **Due for Review**: Real-time counter of concepts due for SM-2 active recall today.
- ⚠️ **Weak Area Alert**: Highlights the student's lowest-mastery concept (e.g. "Circular Wait — 42%").
- 🎯 **Recommended Practice**: Context-aware daily retrieval recommendation.
- 🔥 **Exam Priority**: High-yield exam topic weighting.
