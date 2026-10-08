from typing import List, Dict, Any, Optional
from app.models.document import DocumentChunk


def get_curated_active_recall_items() -> List[Dict[str, Any]]:
    return [
        {
            "topic_title": "Deadlocks & Banker's Algorithm",
            "concept_summary": "Deadlocks occur when processes enter mutual blocking waiting for each other's resources.",
            "retrieval_prompt": "Without looking at notes: Name all four Coffman deadlock conditions from memory, and explain the single most common architectural technique used to prevent Circular Wait.",
            "retrieval_answer": (
                "1. Mutual Exclusion\n"
                "2. Hold and Wait\n"
                "3. No Preemption\n"
                "4. Circular Wait\n\n"
                "To prevent Circular Wait: Enforce a global total ordering on all resources (F: R -> N) "
                "and require processes to request resources in strictly increasing numerical order."
            ),
            "difficulty": "intermediate",
            "concept_tag": "deadlocks",
        },
        {
            "topic_title": "Process Synchronization",
            "concept_summary": "Mechanisms ensuring that concurrent processes execute critical sections safely without race conditions.",
            "retrieval_prompt": "Active Recall Challenge: State the three indispensable requirements for solving the Critical Section problem, and explain what happens if 'Progress' is violated.",
            "retrieval_answer": (
                "1. Mutual Exclusion: At most one process in the critical section.\n"
                "2. Progress: If no process is in the critical section, only processes ready to enter can participate in deciding who enters next (processes halted in non-critical section cannot block others).\n"
                "3. Bounded Waiting: A limit on how many times others can enter before a waiting process gets to enter.\n\n"
                "If Progress is violated, a deadlock or indefinite freeze occurs where no process can proceed."
            ),
            "difficulty": "intermediate",
            "concept_tag": "critical_section",
        },
        {
            "topic_title": "CPU Scheduling Algorithms",
            "concept_summary": "OS schedulers determine which ready process is allocated the CPU.",
            "retrieval_prompt": "Active Recall Challenge: What is the 'Convoy Effect' in FCFS scheduling, and how does the choice of time quantum in Round Robin affect system performance?",
            "retrieval_answer": (
                "Convoy Effect: When short, I/O-bound processes are forced to wait behind a single long CPU-burst process, leading to low resource utilization.\n\n"
                "Round Robin Time Quantum:\n"
                "- If quantum is too small: Excessive context switching overhead destroys throughput.\n"
                "- If quantum is too large: Round Robin degenerates into FCFS with poor interactive response times."
            ),
            "difficulty": "intermediate",
            "concept_tag": "cpu_scheduling",
        },
        {
            "topic_title": "Memory Management & Paging",
            "concept_summary": "Virtual addressing, page tables, TLB, and address translation.",
            "retrieval_prompt": "Active Recall Challenge: Differentiate internal vs external fragmentation, and explain why paging completely eliminates external fragmentation.",
            "retrieval_answer": (
                "Internal Fragmentation: Unused space inside an allocated frame (e.g. process needs 5KB, gets two 4KB pages = 3KB wasted internally).\n"
                "External Fragmentation: Total free memory is sufficient to satisfy a request, but storage is non-contiguous and fragmented into small chunks.\n\n"
                "Why Paging eliminates external fragmentation: Any free physical frame can be allocated to any process regardless of physical location."
            ),
            "difficulty": "intermediate",
            "concept_tag": "paging",
        },
        {
            "topic_title": "ACID Transactions & 2PL",
            "concept_summary": "Database transaction guarantees and Two-Phase Locking concurrency.",
            "retrieval_prompt": "Active Recall Challenge: What does Two-Phase Locking (2PL) guarantee, and what is the difference between Growing Phase and Shrinking Phase?",
            "retrieval_answer": (
                "2PL Guarantee: Guarantees conflict serializability of concurrent transactions.\n\n"
                "Growing Phase: Transaction may acquire locks, but cannot release any lock.\n"
                "Shrinking Phase: Transaction may release locks, but cannot acquire any new lock."
            ),
            "difficulty": "intermediate",
            "concept_tag": "two_phase_locking",
        },
        {
            "topic_title": "Linear & Logistic Regression",
            "concept_summary": "Foundational supervised learning models for continuous regression and binary classification.",
            "retrieval_prompt": "Active Recall Challenge: Explain why L1 (Lasso) regularization produces sparse weights with exact zeros, while L2 (Ridge) only shrinks weights toward zero.",
            "retrieval_answer": (
                "L1 Penalty (|w|): Has a diamond-shaped constraint contour with sharp corners on coordinate axes. Level curves of the loss function hit these corners first, driving irrelevant feature coefficients exactly to zero.\n\n"
                "L2 Penalty (w^2): Has a smooth spherical/circular contour without corners, pulling weights asymptotically toward zero without setting them strictly to zero."
            ),
            "difficulty": "intermediate",
            "concept_tag": "regularization",
        },
    ]


def synthesize_active_recall_from_chunks(
    topic: str,
    chunks: List[DocumentChunk],
) -> List[Dict[str, Any]]:
    items = []
    for i, c in enumerate(chunks[:3]):
        sec = c.section_title or f"Section {i+1}"
        items.append({
            "topic_title": topic,
            "concept_summary": f"Key concepts from {sec}: '{c.content[:120]}...'",
            "retrieval_prompt": f"Active Recall Challenge on {sec}: Without looking, state the primary conclusion or principle introduced in this section regarding {topic}.",
            "retrieval_answer": f"Core principle established in {sec}:\n{c.content[:250]}...",
            "difficulty": "intermediate",
            "concept_tag": f"doc_{c.document_id}",
        })
    return items
