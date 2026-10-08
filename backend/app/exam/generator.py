import uuid
import random
from typing import List, Dict, Any, Optional
from app.practice.types import QuestionType, DifficultyLevel, GeneratedQuestion
from app.practice.generator import QuestionGenerator


DEFAULT_BLUEPRINTS: Dict[str, Dict[str, float]] = {
    "Operating Systems": {
        "Processes": 0.15,
        "CPU Scheduling": 0.15,
        "Synchronization": 0.15,
        "Deadlocks": 0.15,
        "Memory Management": 0.20,
        "File Systems": 0.10,
        "I/O Systems": 0.10,
    },
    "Database Systems": {
        "Transactions & ACID": 0.25,
        "Relational Algebra & SQL": 0.20,
        "B-Trees & Indexing": 0.20,
        "Normalization": 0.15,
        "Concurrency Control & 2PL": 0.20,
    },
    "Machine Learning": {
        "Linear & Logistic Regression": 0.25,
        "Neural Networks & Backprop": 0.25,
        "Optimization & Loss Functions": 0.20,
        "Model Evaluation & Metrics": 0.15,
        "Regularization": 0.15,
    },
    "Data Structures & Algorithms": {
        "Trees & BSTs": 0.25,
        "Graphs & Shortest Path": 0.25,
        "Sorting & Binary Search": 0.20,
        "Dynamic Programming": 0.15,
        "Arrays & Linked Lists": 0.15,
    },
}


class ExamGenerator:
    """
    Synthesizes balanced, blueprint-adhering mock examinations with diverse question
    formats, explicit mark weighting, and distractor misconception tracking.
    """

    def __init__(self, question_generator: Optional[QuestionGenerator] = None):
        self.question_generator = question_generator or QuestionGenerator()

    def get_default_blueprint(self, subject: str) -> Dict[str, float]:
        for k, bp in DEFAULT_BLUEPRINTS.items():
            if k.lower() in subject.lower() or subject.lower() in k.lower():
                return bp
        return DEFAULT_BLUEPRINTS["Operating Systems"]

    def generate_exam_questions(
        self,
        subject: str,
        blueprint: Optional[Dict[str, float]] = None,
        total_questions: int = 10,
        total_marks: float = 100.0,
        difficulty_mix: Optional[Dict[str, float]] = None,
        negative_marking_ratio: float = 0.25,
    ) -> List[Dict[str, Any]]:
        bp = blueprint or self.get_default_blueprint(subject)
        mix = difficulty_mix or {"beginner": 0.3, "intermediate": 0.5, "advanced": 0.2}

        # Calculate question counts per topic based on blueprint percentages
        allocated_counts: Dict[str, int] = {}
        remaining_slots = total_questions
        topics = list(bp.keys())

        for topic, weight in bp.items():
            count = max(1, round(total_questions * weight))
            allocated_counts[topic] = min(count, remaining_slots)
            remaining_slots -= allocated_counts[topic]
            if remaining_slots <= 0:
                break

        # Distribute any leftover slots
        while remaining_slots > 0:
            for topic in topics:
                if remaining_slots <= 0:
                    break
                allocated_counts[topic] = allocated_counts.get(topic, 0) + 1
                remaining_slots -= 1

        all_questions: List[Dict[str, Any]] = []
        mark_per_question = round(total_marks / total_questions, 1)

        for topic, count in allocated_counts.items():
            if count <= 0:
                continue
            topic_qs = self._generate_topic_exam_questions(subject, topic, count, mix)
            for q in topic_qs:
                q["marks"] = mark_per_question
                q["negative_marks"] = round(mark_per_question * negative_marking_ratio, 2)
                all_questions.append(q)

        # Truncate or ensure exact count
        all_questions = all_questions[:total_questions]
        for idx, q in enumerate(all_questions):
            q["order_index"] = idx + 1

        return all_questions

    def _generate_topic_exam_questions(
        self,
        subject: str,
        topic: str,
        count: int,
        difficulty_mix: Dict[str, float],
    ) -> List[Dict[str, Any]]:
        questions: List[Dict[str, Any]] = []

        # 1. Check specialized exam bank for subject & topic
        specialized = self._get_specialized_exam_bank(subject, topic)
        if specialized:
            questions.extend(specialized[:count])

        # 2. Use base practice question generator if more are needed
        if len(questions) < count:
            needed = count - len(questions)
            practice_qs = self.question_generator.generate_questions(topic=topic, count=needed)
            for pq in practice_qs:
                questions.append({
                    "id": pq.id,
                    "topic": topic,
                    "question_type": pq.question_type.value,
                    "prompt": pq.prompt,
                    "options": pq.options,
                    "correct_answer": pq.correct_answer,
                    "explanation": pq.explanation,
                    "distractor_explanations": pq.distractor_explanations,
                    "difficulty": pq.difficulty.value,
                    "concept_tag": pq.concept_tag or topic.lower().replace(" ", "_"),
                    "learning_objective": pq.learning_objective or f"Master concepts in {topic}",
                })

        # 3. Fallback synthesis if bank did not provide enough
        if len(questions) < count:
            needed = count - len(questions)
            for i in range(needed):
                q_id = f"q-exam-{uuid.uuid4().hex[:6]}"
                questions.append({
                    "id": q_id,
                    "topic": topic,
                    "question_type": "scenario" if i % 2 == 1 else "mcq",
                    "prompt": f"Analyze a critical system scenario in {topic}: What trade-off is prioritized when optimizing throughput versus response latency?",
                    "options": [
                        "Favoring compute-bound batches over interactive slices",
                        "Preempting all background tasks immediately",
                        "Eliminating context switching overhead by pinning threads",
                        "Allocating unlimited virtual buffer pages",
                    ],
                    "correct_answer": "Favoring compute-bound batches over interactive slices",
                    "explanation": f"In {topic}, maximizing throughput prioritizes longer execution quanta to amortize context switching, sacrificing short-term interactive response time.",
                    "distractor_explanations": {
                        "Preempting all background tasks immediately": "This favors interactive latency, reducing overall compute throughput.",
                        "Eliminating context switching overhead by pinning threads": "Pinning threads without load balancing causes CPU starvation.",
                        "Allocating unlimited virtual buffer pages": "Memory allocations cannot eliminate CPU scheduling trade-offs.",
                    },
                    "difficulty": "intermediate",
                    "concept_tag": f"{topic.lower().replace(' ', '_')}_tradeoffs",
                    "learning_objective": f"Evaluate throughput versus latency architectural trade-offs in {topic}.",
                })

        return questions[:count]

    def _get_specialized_exam_bank(self, subject: str, topic: str) -> List[Dict[str, Any]]:
        t = topic.lower()
        if "deadlock" in t:
            return [
                {
                    "id": f"exam-dl-1-{uuid.uuid4().hex[:6]}",
                    "topic": topic,
                    "question_type": "scenario",
                    "prompt": (
                        "A database engine has 3 concurrent transactions requesting locks on tables A, B, and C. "
                        "Transaction 1 holds A and requests B. Transaction 2 holds B and requests C. "
                        "Transaction 3 holds C and requests A. "
                        "Identify the architectural mechanism required to handle this situation, and distinguish whether this represents prevention, avoidance, or detection."
                    ),
                    "options": [
                        "Deadlock Detection via Wait-For-Graph (WFG) cycle analysis and victim rollback",
                        "Deadlock Prevention via Banker's algorithm safe-state matrix lookahead",
                        "Deadlock Avoidance via static global resource ordering enumeration",
                        "Deadlock Prevention by disabling preemption on table locks",
                    ],
                    "correct_answer": "Deadlock Detection via Wait-For-Graph (WFG) cycle analysis and victim rollback",
                    "explanation": (
                        "Because transactions have already acquired resources and formed a circular dependency "
                        "(T1 -> T2 -> T3 -> T1), the system must use Deadlock Detection (WFG cycle check) and abort/rollback "
                        "a selected victim transaction. Avoidance (Banker's) requires prior declaration of maximum claims; "
                        "Prevention statically denies Coffman conditions."
                    ),
                    "distractor_explanations": {
                        "Deadlock Prevention via Banker's algorithm safe-state matrix lookahead": (
                            "Banker's algorithm is Deadlock AVOIDANCE, not prevention. Prevention statically restricts requests."
                        ),
                        "Deadlock Avoidance via static global resource ordering enumeration": (
                            "Resource ordering is Deadlock PREVENTION (eliminates circular wait), not avoidance."
                        ),
                        "Deadlock Prevention by disabling preemption on table locks": (
                            "Disabling preemption INCREASES the probability of deadlocks; permitting preemption breaks hold-and-wait."
                        ),
                    },
                    "difficulty": "advanced",
                    "concept_tag": "prevention_vs_avoidance",
                    "learning_objective": "Distinguish between deadlock prevention, avoidance, and runtime detection recovery.",
                },
                {
                    "id": f"exam-dl-2-{uuid.uuid4().hex[:6]}",
                    "topic": topic,
                    "question_type": "mcq",
                    "prompt": (
                        "Which statement precisely characterizes the distinction between Deadlock Prevention and Deadlock Avoidance?"
                    ),
                    "options": [
                        "Prevention eliminates one of the four Coffman conditions statically; Avoidance dynamically evaluates request safety using maximum claim matrices.",
                        "Prevention uses runtime cycle detection; Avoidance aborts transactions with timeouts.",
                        "Prevention and Avoidance are synonyms in modern OS kernels.",
                        "Prevention dynamically simulates state transitions; Avoidance requires hardware lock-free primitives.",
                    ],
                    "correct_answer": "Prevention eliminates one of the four Coffman conditions statically; Avoidance dynamically evaluates request safety using maximum claim matrices.",
                    "explanation": (
                        "Deadlock Prevention structurally invalidates Coffman conditions (e.g. strict resource ordering). "
                        "Deadlock Avoidance (e.g. Banker's Algorithm) permits arbitrary requests but only grants them if the resulting state is verified to be safe."
                    ),
                    "distractor_explanations": {
                        "Prevention uses runtime cycle detection; Avoidance aborts transactions with timeouts.": (
                            "Runtime cycle detection is Deadlock Detection, not Prevention."
                        ),
                        "Prevention and Avoidance are synonyms in modern OS kernels.": (
                            "They are fundamentally distinct strategies with vastly different overheads and constraints."
                        ),
                        "Prevention dynamically simulates state transitions; Avoidance requires hardware lock-free primitives.": (
                            "State simulation is the definition of Avoidance, not Prevention."
                        ),
                    },
                    "difficulty": "intermediate",
                    "concept_tag": "prevention_vs_avoidance",
                    "learning_objective": "Differentiate static prevention constraints from dynamic avoidance safety checks.",
                },
            ]

        if "schedul" in t or "cpu" in t:
            return [
                {
                    "id": f"exam-cpu-1-{uuid.uuid4().hex[:6]}",
                    "topic": topic,
                    "question_type": "mcq",
                    "prompt": (
                        "Consider 3 processes arriving at time 0 with burst times: P1=24ms, P2=3ms, P3=3ms. "
                        "What is the average waiting time under Shortest Job First (SJF) non-preemptive scheduling?"
                    ),
                    "options": [
                        "3.0 ms",
                        "6.0 ms",
                        "17.0 ms",
                        "27.0 ms",
                    ],
                    "correct_answer": "3.0 ms",
                    "explanation": (
                        "Execution order under SJF: P2 (0 to 3ms), P3 (3 to 6ms), P1 (6 to 30ms). "
                        "Waiting times: P2=0ms, P3=3ms, P1=6ms. "
                        "Average waiting time = (0 + 3 + 6) / 3 = 9 / 3 = 3.0 ms. (Under FCFS it would be 17ms)."
                    ),
                    "distractor_explanations": {
                        "6.0 ms": "6ms is the waiting time of process P1 alone, not the average of all three.",
                        "17.0 ms": "17ms is the waiting time under FCFS order (P1 first), which suffers from the convoy effect.",
                        "27.0 ms": "27ms is the turnaround time for P2/P3 under suboptimal order.",
                    },
                    "difficulty": "intermediate",
                    "concept_tag": "sjf_convoy_effect",
                    "learning_objective": "Calculate average waiting times and evaluate SJF optimization over FCFS convoy effect.",
                },
            ]

        if "sync" in t or "mutex" in t:
            return [
                {
                    "id": f"exam-sync-1-{uuid.uuid4().hex[:6]}",
                    "topic": topic,
                    "question_type": "scenario",
                    "prompt": (
                        "A student implements a counting semaphore initialized to value 1 to guard a shared print queue. "
                        "Thread A calls sem_wait(), thread B concurrently calls sem_wait(), and then Thread C calls sem_post(). "
                        "What is the internal semaphore value immediately after Thread C executes sem_post()?"
                    ),
                    "options": [
                        "0 (Thread B is unblocked and permitted into the critical section while semaphore count remains 0)",
                        "1 (The semaphore is completely free and unheld)",
                        "-1 (The semaphore queue remains congested)",
                        "2 (Semaphore counter increments beyond capacity)",
                    ],
                    "correct_answer": "0 (Thread B is unblocked and permitted into the critical section while semaphore count remains 0)",
                    "explanation": (
                        "Initially S=1. Thread A decrements S to 0 and enters. Thread B decrements S to -1 (or blocks in waiting queue). "
                        "When Thread C signals sem_post(), one waiting thread (Thread B) is awakened, leaving the count at 0."
                    ),
                    "distractor_explanations": {
                        "1 (The semaphore is completely free and unheld)": "Thread B is still waiting to consume the awakened permit.",
                        "-1 (The semaphore queue remains congested)": "The post operation increments the permit count from -1 to 0.",
                        "2 (Semaphore counter increments beyond capacity)": "A counting semaphore initialized to 1 behaves as a binary mutex here.",
                    },
                    "difficulty": "advanced",
                    "concept_tag": "counting_semaphore_mechanics",
                    "learning_objective": "Trace counting semaphore state transitions and blocked thread unblocking queues.",
                },
            ]

        if "memory" in t or "page" in t:
            return [
                {
                    "id": f"exam-mem-1-{uuid.uuid4().hex[:6]}",
                    "topic": topic,
                    "question_type": "mcq",
                    "prompt": (
                        "A 32-bit virtual address architecture uses a two-level paging scheme with 4 KB page size (offset = 12 bits). "
                        "Each Page Table Entry (PTE) takes 4 bytes. If the outer page directory and inner page tables are each exactly one page (4 KB), "
                        "how many bits are used for the outer page index and inner page index respectively?"
                    ),
                    "options": [
                        "10 bits outer, 10 bits inner",
                        "12 bits outer, 8 bits inner",
                        "14 bits outer, 6 bits inner",
                        "8 bits outer, 12 bits inner",
                    ],
                    "correct_answer": "10 bits outer, 10 bits inner",
                    "explanation": (
                        "4 KB page = 2^12 bytes -> 12 bits offset. "
                        "Virtual address is 32 bits, so 32 - 12 = 20 bits for page table indexing. "
                        "A 4 KB page holding 4-byte entries contains 4096 / 4 = 1024 = 2^10 entries -> 10 bits per table. "
                        "Hence 10 bits outer and 10 bits inner."
                    ),
                    "distractor_explanations": {
                        "12 bits outer, 8 bits inner": "A 4 KB page cannot hold 2^12 four-byte entries without overflowing.",
                        "14 bits outer, 6 bits inner": "Unequal division would make the inner table significantly smaller than a full page.",
                        "8 bits outer, 12 bits inner": "2^12 entries * 4 bytes = 16 KB, which exceeds the 4 KB page size constraint.",
                    },
                    "difficulty": "advanced",
                    "concept_tag": "two_level_paging_math",
                    "learning_objective": "Calculate hierarchical page table bit partitions from page size and entry dimensions.",
                },
            ]

        return []
