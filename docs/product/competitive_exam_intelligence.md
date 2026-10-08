# Competitive Examination Intelligence & Personal AI Strategist

## 1. Overview & Pedagogical Mission

Study Buddy's **Competitive Examination Intelligence Engine** upgrades the platform from a conversational tutor into a long-term exam strategist, study planner, evaluator, and revision coach. It is specifically designed to serve aspirants preparing for structured, high-stakes competitive examinations including:

* **UPSC Civil Services Examination (CSE)** (Prelims GS 1, CSAT Paper 2, Mains GS I-IV, Essay, Optional, DAF Personality Test)
* **SSC CGL / CHSL** (Staff Selection Commission Tier 1 & Tier 2)
* **Banking Examinations** (IBPS PO, SBI PO, RBI Grade B)
* **GATE** (Graduate Aptitude Test in Engineering - CS & Engineering disciplines)
* **JEE (Main & Advanced)** (Engineering entrance physics, chemistry, mathematics)
* **NEET (UG)** (Medical entrance biology, physics, chemistry)
* **State Public Service Commissions (State PSCs)** (UPPSC, BPSC, MPSC, TNPSC, KPSC, etc.)
* **UGC NET / JRF** (University Grants Commission Teaching & Research Aptitude)
* **Custom / University Examinations** (Flexible institution-configured curricula)

---

## 2. Pluggable Exam Profile Architecture

To prevent hard-coding examination-specific assumptions across the core learning systems, all examination properties are defined in pluggable specifications adhering to `ExamProfileDefinition`:

```
backend/app/exam/profiles/
├── base.py                 # Abstract specification (ExamProfileDefinition, ExamStageConfig)
├── upsc.py                 # Comprehensive UPSC CSE syllabus tree & rules
├── registry.py             # Central pluggable registry (UPSC, SSC, Banking, GATE, JEE, NEET, etc.)
```

### Profile Attributes:
1. **Stages**: Hierarchical multi-stage definitions (e.g. Prelims, Mains, Interview).
2. **Negative Marking Ratios**: Precise per-question negative marking penalties (e.g. -0.33x for UPSC GS, -0.83x for CSAT, -0.25x for SSC/Banking).
3. **Paper Classifications**: Objective vs descriptive exam requirements.
4. **Syllabus Hierarchy**: Subject → Module → Topic → Subtopic DAG nodes with historical PYQ weights and prerequisite dependencies.

---

## 3. Dynamic Multidimensional Priority Scoring

Unlike naive study planners that only sort topics alphabetically or by calendar days, Study Buddy's `StudyPlannerEngine` computes a dynamic priority score for every topic using the formula:

$$\text{Priority Score} = 0.25 \times G + 0.20 \times W_{\text{exam}} + 0.20 \times F_{\text{pyq}} + 0.15 \times U_{\text{rev}} + 0.10 \times P_{\text{prox}} + 0.05 \times R_{\text{weak}} + 0.05 \times I_{\text{prereq}}$$

* **Mastery Gap ($G$)**: $1.0 - (\text{Mastery Percentage} / 100.0)$.
* **Exam Weight ($W_{\text{exam}}$)**: Relative syllabus weighting in official examination blueprint.
* **PYQ Frequency ($F_{\text{pyq}}$)**: Normalized occurrence count over the past 10 examination cycles.
* **Revision Urgency ($U_{\text{rev}}$)**: Ebbinghaus forgetting curve decay and overdue status in SM-2 spaced repetition queue.
* **Exam Proximity ($P_{\text{prox}}$)**: Urgency multiplier scaling as examination date approaches.
* **Weakness Recurrence ($R_{\text{weak}}$)**: Repetition of careless or misconception errors during mock tests.
* **Prerequisite Importance ($I_{\text{prereq}}$)**: Foundational dependency score blocking downstream syllabus nodes.

---

## 4. Cognitive Mistake Diagnostics

When a student marks an objective question incorrectly, Study Buddy does not simply mark it wrong. The `PYQService` and `PrelimsEngine` classify the mistake into an actionable **Cognitive Error Category**:

| Error Category | Diagnostic Trigger | Pedagogical Remediation |
| :--- | :--- | :--- |
| **KNOWLEDGE_ERROR** | Unfamiliar factual/legal rule | Schedule targeted Socratic reteaching session. |
| **READING_ERROR** | Overlooked "not", "except", or qualifiers | Flag question stem highlighting in UI drills. |
| **CARELESS_ERROR** | Rushed response ($<15$ seconds) | Enforce 10-second deliberate pause before confirming answer. |
| **GUESSING_ERROR** | Low-confidence speculative attempt | Train risk-reward threshold under negative penalties. |
| **TIME_PRESSURE** | Answered in final seconds of session clock | Speed drill pacing with timed micro-sessions. |
| **MISCONCEPTION** | High confidence in wrong legal concept | Contrastive concept breakdown highlighting nuances. |

---

## 5. Current Affairs & Static Concept Linking

Dynamic news events (e.g., Supreme Court rulings, RBI Monetary Policy decisions, COP climate treaties) are explicitly linked to static textbook knowledge in `CurrentAffairsService`:

* **Event**: Supreme Court bench judgment on digital device searches.
* **Linked Static Concepts**: Article 20(3) (Self-Incrimination), Article 21 (Right to Privacy - Puttaswamy case), Proportionality Doctrine.
* **Prospective Prelims Question**: Identifying testimonial vs physical evidence under Article 20(3).
* **Prospective Mains Framework**: Balancing cyber-crime investigative efficacy with citizen digital privacy.

---

## 6. Mains Answer Writing Pedagogical Evaluation (8 Rubrics)

Descriptive answers are evaluated across 8 structured dimensions in `MainsAnswerWritingService`:

1. **Content Accuracy (25%)**: Constitutional articles, statutory provisions, and factual grounding.
2. **Structural Flow (15%)**: Clear Introduction $\to$ Subheaded Body $\to$ Way Forward Conclusion.
3. **Syllabus Relevance (15%)**: Direct adherence to question directives (*critically analyze*, *examine*, *evaluate*).
4. **Critical Analysis (15%)**: Counter-arguments, systemic bottlenecks, and balance.
5. **Examples & Data (10%)**: Case laws, committee reports, economic survey figures.
6. **Balanced Viewpoint (10%)**: Constructive synthesis avoiding ideological bias.
7. **Forward-Looking Conclusion (5%)**: Visionary solutions linked to constitutional values and SDGs.
8. **Presentation & Subheadings (5%)**: Legibility, bulleted points, and clear demarcation.

---

## 7. Multi-Dimensional Readiness Dashboard

The `ReadinessDashboardService` synthesizes a comprehensive preparation report:
* **Overall Preparation Percentage**: Weighted aggregate across syllabus completion and topic mastery.
* **Readiness Radar**:
  * *Concept Readiness*
  * *Prelims Readiness*
  * *Mains Readiness*
  * *Revision Health*
  * *Mock Readiness*
* **Topic Heatmap**: Categorizes syllabus into *Strong ($\ge 80\%$)*, *Good ($50-79\%$)*, *Weak ($<50\%$)*, and *Critical (High Weight + Weak)*.
* **Target Countdown**: Days remaining until primary examination date.

---

## 8. Responsible AI Guardrails & Disclaimers

> [!IMPORTANT]
> **Independent Educational Aid**: Study Buddy is an independent educational tool designed to help students master syllabus concepts and practice exam strategies. It is not affiliated with, authorized by, or endorsed by the Union Public Service Commission (UPSC), Staff Selection Commission (SSC), National Testing Agency (NTA), or any state/central government examination authority. All evaluation scores, model outlines, and trend predictions are formative educational estimates to support student learning.
