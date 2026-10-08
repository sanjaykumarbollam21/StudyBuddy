import uuid
import re
from typing import List, Dict, Any, Optional
from app.practice.types import QuestionType, DifficultyLevel, GeneratedQuestion
from app.models.document import DocumentChunk
from app.tutor.providers import LLMProvider


class QuestionGenerator:
    """
    Generates high-quality practice and exam questions across all 7 question types,
    complete with plausible distractors, misconception rationales, and difficulty adaptation.
    """

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self.llm_provider = llm_provider

    def generate_questions(
        self,
        topic: str,
        count: int = 5,
        difficulty: Optional[DifficultyLevel] = None,
        rag_chunks: Optional[List[DocumentChunk]] = None,
    ) -> List[GeneratedQuestion]:
        """
        Produces `count` structured questions for the given topic or document.
        """
        questions: List[GeneratedQuestion] = []

        # 1. Check curated question bank for topic
        curated = self._get_curated_questions_for_topic(topic)
        if curated:
            # Filter by difficulty if requested
            if difficulty:
                filtered = [q for q in curated if q.difficulty == difficulty]
                if filtered:
                    curated = filtered
            questions.extend(curated[:count])

        # 2. If RAG chunks provided and more questions needed, synthesize from document
        if len(questions) < count and rag_chunks:
            rag_generated = self._generate_from_rag_chunks(topic, rag_chunks, count - len(questions))
            questions.extend(rag_generated)

        # 3. Fallback synthesis if still fewer than count
        if len(questions) < count:
            remaining = count - len(questions)
            synth = self._synthesize_generic_questions(topic, remaining, difficulty or DifficultyLevel.INTERMEDIATE)
            questions.extend(synth)

        # Assign order indices
        for i, q in enumerate(questions):
            q.order_index = i + 1

        return questions[:count]

    def _get_curated_questions_for_topic(self, topic: str) -> List[GeneratedQuestion]:
        t = topic.lower()
        if any(k in t for k in ["deadlock", "banker"]):
            return self._deadlock_questions()
        if any(k in t for k in ["process", "sync", "mutex", "semaphore"]):
            return self._process_sync_questions()
        if any(k in t for k in ["schedul", "cpu", "fcfs", "round robin"]):
            return self._cpu_scheduling_questions()
        if any(k in t for k in ["memory", "page", "virtual memory", "tlb"]):
            return self._memory_management_questions()
        if any(k in t for k in ["acid", "transaction", "concurrency", "2pl"]):
            return self._db_transaction_questions()
        if any(k in t for k in ["b-tree", "index", "sql"]):
            return self._db_indexing_questions()
        if any(k in t for k in ["linear regression", "logistic", "gradient descent"]):
            return self._ml_regression_questions()
        if any(k in t for k in ["neural", "backpropagation", "deep learning"]):
            return self._ml_neural_questions()
        if any(k in t for k in ["linked list", "tree", "bst", "stack", "queue"]):
            return self._dsa_questions()
        return []

    # -------------------------------------------------------------------------
    # Curated Question Banks with Distractor Misconceptions
    # -------------------------------------------------------------------------

    def _deadlock_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-deadlock-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt="Which of the following is NOT one of the four necessary Coffman conditions for a deadlock to occur?",
                options=[
                    "Mutual Exclusion",
                    "Hold and Wait",
                    "Preemption Allowed",
                    "Circular Wait",
                ],
                correct_answer="Preemption Allowed",
                explanation="The four Coffman conditions are Mutual Exclusion, Hold and Wait, No Preemption, and Circular Wait. If preemption is allowed, the OS can forcibly preempt allocated resources, preventing deadlock.",
                distractor_explanations={
                    "Mutual Exclusion": "Mutual Exclusion is an essential Coffman condition: resources cannot be shared simultaneously.",
                    "Hold and Wait": "Hold and Wait is an essential Coffman condition: a process must hold at least one resource while waiting for another.",
                    "Circular Wait": "Circular Wait is an essential Coffman condition: a closed chain of processes exists where each waits for a resource held by the next.",
                },
                difficulty=DifficultyLevel.BEGINNER,
                learning_objective="Identify the four necessary Coffman deadlock conditions.",
                concept_tag="coffman_conditions",
            ),
            GeneratedQuestion(
                id=f"q-deadlock-2-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MULTIPLE_SELECT,
                prompt="Which of the following strategies successfully eliminate the 'Circular Wait' condition in deadlock prevention? (Select all that apply)",
                options=[
                    "Impose a strict global numerical ordering on all resource types.",
                    "Require processes to request resources only in strictly increasing order of enumeration.",
                    "Allow processes to hold an arbitrary number of resources without restrictions.",
                    "Allocate all required resources simultaneously before process execution begins.",
                ],
                correct_answer="Impose a strict global numerical ordering on all resource types., Require processes to request resources only in strictly increasing order of enumeration.",
                explanation="Imposing a global numbering F: R -> N and requiring that processes request resources strictly in increasing order mathematically prevents any circular dependency graph.",
                distractor_explanations={
                    "Allow processes to hold an arbitrary number of resources without restrictions.": "This exacerbates Hold and Wait and increases the probability of deadlocks.",
                    "Allocate all required resources simultaneously before process execution begins.": "This prevents 'Hold and Wait', not 'Circular Wait'.",
                },
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective="Apply resource ordering to eliminate circular wait.",
                concept_tag="circular_wait",
            ),
            GeneratedQuestion(
                id=f"q-deadlock-3-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.TRUE_FALSE,
                prompt="True or False: If a system state is safe in the Banker's algorithm, a deadlock is guaranteed not to occur.",
                options=["True", "False"],
                correct_answer="True",
                explanation="By definition, a safe state means there exists at least one safe execution sequence of processes such that all processes can finish without deadlocking.",
                distractor_explanations={
                    "False": "A safe state guarantees that at least one allocation sequence exists that avoids deadlock. An unsafe state is not necessarily deadlocked, but a safe state is strictly deadlock-free.",
                },
                difficulty=DifficultyLevel.BEGINNER,
                learning_objective="Understand safe state properties in Banker's algorithm.",
                concept_tag="banker_safety",
            ),
            GeneratedQuestion(
                id=f"q-deadlock-4-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.FILL_BLANK,
                prompt="In Banker's Algorithm, the matrix equation for remaining resource requirements is Need[i, j] = _______[i, j] - Allocation[i, j].",
                options=[],
                correct_answer="Max",
                explanation="Need = Max - Allocation. The Need matrix indicates the remaining resources process i may request to complete execution.",
                distractor_explanations={},
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective="Recall Banker's algorithm data structures.",
                concept_tag="banker_matrix",
            ),
            GeneratedQuestion(
                id=f"q-deadlock-5-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.SCENARIO,
                prompt="Scenario: Process P1 holds Resource R1 and requests R2. Process P2 holds R2 and requests R1. Both processes are non-preemptive. Diagnose the system state and propose the minimal architectural intervention to break the condition.",
                options=[],
                correct_answer="Deadlock due to circular wait between P1 and P2. To resolve: forcibly preempt R1 or R2, or enforce a global resource acquisition order so both request R1 before R2.",
                explanation="P1 and P2 form a cycle in the Resource Allocation Graph (P1 -> R2 -> P2 -> R1 -> P1). Since non-preemption and mutual exclusion hold, they are in a deadlock. Resolution requires preemption or resource ordering.",
                distractor_explanations={},
                difficulty=DifficultyLevel.ADVANCED,
                learning_objective="Diagnose deadlocks in resource allocation graphs and prescribe remediation.",
                concept_tag="deadlock_diagnosis",
            ),
        ]

    def _process_sync_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-sync-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt="Which critical section requirement states that a process halted in its non-critical section must not prevent other processes from entering the critical section?",
                options=["Mutual Exclusion", "Progress", "Bounded Waiting", "Atomicity"],
                correct_answer="Progress",
                explanation="Progress ensures that if no process is in its critical section, only processes that are not in their remainder section can participate in deciding who enters next.",
                distractor_explanations={
                    "Mutual Exclusion": "Mutual Exclusion requires that only one process can be in the critical section at a time.",
                    "Bounded Waiting": "Bounded Waiting limits the number of times other processes can enter while a process is waiting.",
                    "Atomicity": "Atomicity refers to an operation executing as an indivisible unit.",
                },
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective="Distinguish between Mutual Exclusion, Progress, and Bounded Waiting.",
                concept_tag="critical_section",
            ),
            GeneratedQuestion(
                id=f"q-sync-2-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.SHORT_ANSWER,
                prompt="What atomic hardware instruction tests and modifies a memory word in a single indivisible clock cycle to implement mutex locks?",
                options=[],
                correct_answer="Test-and-Set (or Compare-and-Swap)",
                explanation="Test-and-Set (or Compare-and-Swap / CAS) atomically reads and updates a flag, allowing spinlocks and mutexes to be built without race conditions.",
                distractor_explanations={},
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective="Explain hardware synchronization primitives.",
                concept_tag="atomic_instructions",
            ),
            GeneratedQuestion(
                id=f"q-sync-3-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.CODING,
                prompt="Implement a Python class 'SimpleCountingSemaphore' initialized with an integer 'value', containing thread-safe 'wait()' (or acquire) and 'signal()' (or release) methods using threading.Condition.",
                options=[],
                correct_answer="""class SimpleCountingSemaphore:
    def __init__(self, value: int):
        self.value = value
        self.cond = threading.Condition()

    def wait(self):
        with self.cond:
            while self.value <= 0:
                self.cond.wait()
            self.value -= 1

    def signal(self):
        with self.cond:
            self.value += 1
            self.cond.notify()""",
                explanation="A counting semaphore decrements on wait (blocking while value <= 0) and increments on signal, notifying a waiting thread.",
                distractor_explanations={},
                difficulty=DifficultyLevel.ADVANCED,
                learning_objective="Implement counting semaphore concurrency logic in Python.",
                concept_tag="semaphore_implementation",
            ),
        ]

    def _cpu_scheduling_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-sched-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt="In First-Come, First-Served (FCFS) scheduling, what is the term for when short processes get stuck waiting behind a single very long CPU-bound process?",
                options=["Starvation", "Convoy Effect", "Belady's Anomaly", "Priority Inversion"],
                correct_answer="Convoy Effect",
                explanation="The Convoy Effect occurs in FCFS when small I/O-bound processes pile up behind a large CPU-burst process, dramatically reducing CPU and device utilization.",
                distractor_explanations={
                    "Starvation": "Starvation is indefinite postponement, common in Priority and SJF schedulers, not FCFS.",
                    "Belady's Anomaly": "Belady's Anomaly occurs in FIFO page replacement, not CPU scheduling.",
                    "Priority Inversion": "Priority Inversion occurs when a lower-priority task holds a lock needed by a higher-priority task.",
                },
                difficulty=DifficultyLevel.BEGINNER,
                learning_objective="Identify the Convoy Effect in FCFS scheduling.",
                concept_tag="convoy_effect",
            ),
            GeneratedQuestion(
                id=f"q-sched-2-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt="If the time quantum in Round Robin scheduling is set to an extremely large value (t -> infinity), how does Round Robin behave?",
                options=[
                    "It becomes equivalent to FCFS.",
                    "It becomes equivalent to Shortest Job First (SJF).",
                    "It causes infinite context switching overhead.",
                    "It causes process starvation.",
                ],
                correct_answer="It becomes equivalent to FCFS.",
                explanation="When the time slice is larger than any process burst, no process is preempted before completion, degenerating Round Robin directly into FCFS.",
                distractor_explanations={
                    "It becomes equivalent to Shortest Job First (SJF).": "Round Robin maintains a FIFO ready queue, not shortest remaining time.",
                    "It causes infinite context switching overhead.": "Extremely small quantum causes high context switching, not large quantum.",
                    "It causes process starvation.": "FCFS does not cause starvation; all processes eventually run.",
                },
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective="Analyze the effect of time quantum size in Round Robin.",
                concept_tag="round_robin_quantum",
            ),
        ]

    def _memory_management_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-mem-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt="What type of fragmentation is caused by fixed-size paging, where allocated memory frames are slightly larger than process needs?",
                options=["External Fragmentation", "Internal Fragmentation", "Virtual Fragmentation", "Segmental Fragmentation"],
                correct_answer="Internal Fragmentation",
                explanation="Paging eliminates external fragmentation entirely because any free physical frame can be assigned. However, the last page allocated to a process is rarely completely full, causing internal fragmentation.",
                distractor_explanations={
                    "External Fragmentation": "External fragmentation happens in segmentation or contiguous allocation when total free memory is sufficient but not contiguous.",
                    "Virtual Fragmentation": "Virtual Fragmentation is not a recognized OS memory term.",
                },
                difficulty=DifficultyLevel.BEGINNER,
                learning_objective="Differentiate internal and external fragmentation.",
                concept_tag="internal_fragmentation",
            ),
            GeneratedQuestion(
                id=f"q-mem-2-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.SCENARIO,
                prompt="Scenario: A system with 3 physical page frames executes the page reference string: [1, 2, 3, 4, 1, 2]. Using the FIFO page replacement algorithm, calculate the total number of page faults.",
                options=[],
                correct_answer="6 page faults",
                explanation="Frames initially empty. 1 (fault, [1]), 2 (fault, [1,2]), 3 (fault, [1,2,3]), 4 replaces 1 (fault, [4,2,3]), 1 replaces 2 (fault, [4,1,3]), 2 replaces 3 (fault, [4,1,2]). Total = 6 faults.",
                distractor_explanations={},
                difficulty=DifficultyLevel.ADVANCED,
                learning_objective="Simulate FIFO page replacement and compute page faults.",
                concept_tag="fifo_page_replacement",
            ),
        ]

    def _db_transaction_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-db-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt="Which ACID property is strictly guaranteed by Two-Phase Locking (2PL)?",
                options=["Atomicity", "Consistency", "Isolation (Serializability)", "Durability"],
                correct_answer="Isolation (Serializability)",
                explanation="Two-Phase Locking ensures conflict serializability, which enforces the Isolation property among concurrent transactions.",
                distractor_explanations={
                    "Atomicity": "Atomicity is guaranteed by Write-Ahead Logging (WAL) and undo logs.",
                    "Durability": "Durability is guaranteed by redo logs and persistent storage commits.",
                    "Consistency": "Consistency is maintained by integrity constraints and correct transaction logic.",
                },
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective="Relate 2PL protocol to ACID isolation.",
                concept_tag="two_phase_locking",
            ),
        ]

    def _db_indexing_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-db-idx-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.TRUE_FALSE,
                prompt="True or False: In a B+ Tree, data pointers or actual records are stored exclusively in the leaf nodes, while internal nodes store only search keys and routing pointers.",
                options=["True", "False"],
                correct_answer="True",
                explanation="Unlike standard B-Trees, B+ Trees store all records and data pointers strictly in leaf nodes. This maximizes the fan-out of internal nodes and provides efficient range scanning via leaf node linked lists.",
                distractor_explanations={
                    "False": "Standard B-Trees store data in internal nodes; B+ Trees store data strictly at leaf nodes.",
                },
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective="Understand B+ Tree structure and fan-out advantages.",
                concept_tag="b_plus_tree",
            ),
        ]

    def _ml_regression_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-ml-reg-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt="What is the primary architectural difference between L1 (Lasso) and L2 (Ridge) regularization?",
                options=[
                    "L1 produces sparse models with exact zero feature weights, while L2 shrinks weights asymptotically toward zero.",
                    "L2 is used for classification while L1 is only used for regression.",
                    "L1 adds squared weights while L2 adds absolute weights.",
                    "L1 increases model variance while L2 reduces bias.",
                ],
                correct_answer="L1 produces sparse models with exact zero feature weights, while L2 shrinks weights asymptotically toward zero.",
                explanation="L1 regularization adds the sum of absolute weights (|w|). Its diamond-shaped constraint geometry causes coordinate intersections at zero, driving irrelevant feature weights exactly to 0 for feature selection.",
                distractor_explanations={
                    "L2 is used for classification while L1 is only used for regression.": "Both L1 and L2 can be used for both regression and classification.",
                    "L1 adds squared weights while L2 adds absolute weights.": "The reverse is true: L1 adds absolute weights and L2 adds squared weights.",
                },
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective="Contrast L1 and L2 regularization mechanisms and sparsity.",
                concept_tag="l1_l2_regularization",
            ),
        ]

    def _ml_neural_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-ml-nn-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.FILL_BLANK,
                prompt="The backpropagation algorithm in neural networks calculates gradients using the mathematical _______ rule of calculus across the computational graph.",
                options=[],
                correct_answer="Chain",
                explanation="Backpropagation applies the multivariate Chain Rule of calculus from output loss back to weights.",
                distractor_explanations={},
                difficulty=DifficultyLevel.BEGINNER,
                learning_objective="Understand chain rule mechanics in backpropagation.",
                concept_tag="backpropagation_chain_rule",
            ),
        ]

    def _dsa_questions(self) -> List[GeneratedQuestion]:
        return [
            GeneratedQuestion(
                id=f"q-dsa-1-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt="What is the worst-case time complexity of searching for an element in an unbalanced Binary Search Tree (BST)?",
                options=["O(1)", "O(log n)", "O(n)", "O(n log n)"],
                correct_answer="O(n)",
                explanation="When a BST becomes completely degenerate (e.g., elements inserted in sorted order), it resembles a linked list, degrading search time from O(log n) to O(n).",
                distractor_explanations={
                    "O(log n)": "O(log n) is the average or balanced tree search time (e.g. AVL or Red-Black Tree), not the unbalanced worst case.",
                    "O(1)": "O(1) is the average lookup for a Hash Map.",
                },
                difficulty=DifficultyLevel.BEGINNER,
                learning_objective="Analyze time complexity bounds of unbalanced binary search trees.",
                concept_tag="bst_worst_case",
            ),
        ]

    def _generate_from_rag_chunks(
        self,
        topic: str,
        chunks: List[DocumentChunk],
        needed: int,
    ) -> List[GeneratedQuestion]:
        """
        Synthesizes grounded questions from uploaded document text.
        """
        questions = []
        for i, chunk in enumerate(chunks[:needed]):
            sec = chunk.section_title or f"Section {i+1}"
            first_sentence = chunk.content.split(".")[0].strip()
            prompt = f"Based on {sec}: Which of the following statements is directly supported by the text regarding {topic}?"

            q = GeneratedQuestion(
                id=f"rag-q-{uuid.uuid4().hex[:6]}",
                question_type=QuestionType.MCQ,
                prompt=prompt,
                options=[
                    first_sentence if len(first_sentence) > 10 else f"Core principle of {sec}",
                    f"{sec} is not relevant to real-world applications.",
                    f"{topic} can operate without any memory or computational resources.",
                    f"All operations in {topic} execute in zero time.",
                ],
                correct_answer=first_sentence if len(first_sentence) > 10 else f"Core principle of {sec}",
                explanation=f"Directly stated in {sec}: '{chunk.content[:150]}...'",
                distractor_explanations={
                    f"{sec} is not relevant to real-world applications.": "Contradicts the source material which presents this as essential knowledge.",
                    f"{topic} can operate without any memory or computational resources.": "Physical systems require computational resources.",
                },
                difficulty=DifficultyLevel.INTERMEDIATE,
                learning_objective=f"Analyze document assertions in {sec}.",
                concept_tag=f"doc_{chunk.document_id}",
            )
            questions.append(q)
        return questions

    def _synthesize_generic_questions(
        self,
        topic: str,
        needed: int,
        difficulty: DifficultyLevel,
    ) -> List[GeneratedQuestion]:
        synthesized = []
        for i in range(needed):
            q_id = f"synth-q-{i+1}-{uuid.uuid4().hex[:6]}"
            if i % 2 == 0:
                synthesized.append(
                    GeneratedQuestion(
                        id=q_id,
                        question_type=QuestionType.MCQ,
                        prompt=f"Which of the following best describes the core architectural purpose of {topic}?",
                        options=[
                            f"To manage resources, enforce safety invariants, and provide abstractions for {topic}.",
                            f"To permanently disable all concurrent execution.",
                            f"To eliminate the need for computer hardware entirely.",
                            f"To make system operations completely non-deterministic.",
                        ],
                        correct_answer=f"To manage resources, enforce safety invariants, and provide abstractions for {topic}.",
                        explanation=f"{topic} serves to provide structured abstractions and enforce system safety constraints.",
                        distractor_explanations={
                            f"To permanently disable all concurrent execution.": f"Disabling concurrency destroys throughput; {topic} coordinates concurrency safely.",
                            f"To eliminate the need for computer hardware entirely.": f"Software models hardware, it does not replace it.",
                        },
                        difficulty=difficulty,
                        learning_objective=f"Understand fundamental architectural role of {topic}.",
                        concept_tag="fundamentals",
                    )
                )
            else:
                synthesized.append(
                    GeneratedQuestion(
                        id=q_id,
                        question_type=QuestionType.TRUE_FALSE,
                        prompt=f"True or False: In {topic}, understanding foundational mechanisms and prerequisites is necessary before implementing advanced optimizations.",
                        options=["True", "False"],
                        correct_answer="True",
                        explanation=f"Foundational understanding is essential in {topic} because advanced features build directly upon lower-level primitives.",
                        distractor_explanations={
                            "False": "Attempting advanced optimizations without foundational understanding leads to subtle bugs and misconceptions.",
                        },
                        difficulty=difficulty,
                        learning_objective=f"Recognize foundational dependencies in {topic}.",
                        concept_tag="prerequisites",
                    )
                )
        return synthesized
