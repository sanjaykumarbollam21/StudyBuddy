from typing import List, Dict, Any, Optional
from app.teaching.state import ConceptStep

BUILTIN_CURRICULA: Dict[str, List[Dict[str, Any]]] = {
    "deadlock": [
        {
            "step_index": 0,
            "title": "Deadlock Definition & Circular Waiting",
            "explanation": (
                "A deadlock is a situation where a set of processes are permanently blocked "
                "because each process is holding a resource and waiting for another resource acquired by some other process."
            ),
            "analogy": (
                "Think of two people each holding one key while waiting for the other's key to unlock their door."
            ),
            "check_question": "Why can't either process continue?",
            "expected_core_concept": (
                "each process is waiting for a resource held by another, creating a circular wait where neither can proceed"
            ),
            "key_terms": ["circular wait", "holding", "blocked", "resources"],
            "common_misconceptions": {
                "cpu is too slow": "Deadlock is a concurrency conflict over resource ownership, not a CPU speed or performance limitation.",
                "cpu speed": "Deadlock happens regardless of CPU clock speed; it is a logical lock over resource allocation.",
                "out of memory": "Deadlock is not an out-of-memory error; it occurs even with ample memory if resources are locked mutually.",
            },
            "simpler_analogy": (
                "Imagine two people: Person A has Key 1 and needs Key 2, while Person B has Key 2 and needs Key 1."
            ),
            "socratic_hint": "Focus on what each process currently holds versus what each is waiting for.",
        },
        {
            "step_index": 1,
            "title": "The Four Coffman Conditions",
            "explanation": (
                "For a deadlock to arise, four conditions must hold simultaneously:\n"
                "1. Mutual Exclusion: At least one resource must be non-shareable.\n"
                "2. Hold and Wait: A process holds at least one resource while waiting for others.\n"
                "3. No Preemption: Resources cannot be forcibly confiscated from a process.\n"
                "4. Circular Wait: A closed chain of processes exists where each waits for the next."
            ),
            "analogy": (
                "Like a four-legged stool: all four legs must be present for a deadlock to exist. "
                "If you break even ONE leg, deadlock is impossible."
            ),
            "check_question": (
                "If an operating system is allowed to forcibly take away a resource from a process, "
                "which of the four conditions is eliminated?"
            ),
            "expected_core_concept": "No Preemption is eliminated because the resource can be preempted",
            "key_terms": ["no preemption", "preemption", "preempt"],
            "common_misconceptions": {
                "mutual exclusion": "Mutual exclusion means resources cannot be shared; taking away resources is preemption.",
            },
            "simpler_analogy": "If a teacher can take a shared pencil away from a student, that is preemption.",
            "socratic_hint": "Preemption means interrupting and taking back a resource.",
        },
        {
            "step_index": 2,
            "title": "Resource Allocation Graphs (RAG)",
            "explanation": (
                "A Resource Allocation Graph is a directed graph where processes and resources are vertices. "
                "A directed edge from process to resource means a request; an edge from resource to process means assignment. "
                "If resources have single instances, a cycle in the graph guarantees deadlock."
            ),
            "analogy": (
                "Think of a circular traffic gridlock at a 4-way intersection where every car is blocked by the car in front of it."
            ),
            "check_question": "In a system with single-instance resources, what topological feature of the graph proves a deadlock exists?",
            "expected_core_concept": "A cycle or circular loop in the directed graph",
            "key_terms": ["cycle", "circular loop", "directed cycle"],
            "common_misconceptions": {
                "too many nodes": "The number of nodes does not matter; only the presence of a directed cycle determines deadlock.",
            },
            "simpler_analogy": "If you follow the arrows from process to resource and end up back where you started, that's a cycle.",
            "socratic_hint": "Look for a closed loop where arrows lead in a circle.",
        },
        {
            "step_index": 3,
            "title": "Deadlock Avoidance & Banker's Algorithm",
            "explanation": (
                "Dijkstra's Banker's Algorithm dynamically tests for safety by simulating the allocation "
                "of predetermined maximum possible amounts of all resources before deciding whether allocation should continue. "
                "An allocation is only granted if the resulting state is safe (there exists a sequence where all processes can finish)."
            ),
            "analogy": (
                "Like a conservative banker who only approves loans if guaranteed that every customer will eventually be able to pay back in full."
            ),
            "check_question": "What is the defining condition of a 'safe state' in Banker's Algorithm?",
            "expected_core_concept": "There exists a safe sequence of processes that can all run to completion with available resources",
            "key_terms": ["safe sequence", "all processes finish", "completion"],
            "common_misconceptions": {
                "no processes are running": "In a safe state, processes can and do run concurrently.",
            },
            "simpler_analogy": "Safe means there is a clear order where everyone finishes without getting stuck.",
            "socratic_hint": "Think about finding an orderly sequence where every process gets what it needs.",
        },
    ],
    "concurrency": [
        {
            "step_index": 0,
            "title": "Mutual Exclusion & Critical Sections",
            "explanation": (
                "When multiple threads execute concurrently, the critical section is the code segment "
                "accessing shared variables. Mutual exclusion ensures that only one thread executes in its critical section at any given time."
            ),
            "analogy": "Like a single-occupancy fitting room in a clothing store: only one customer can enter at a time.",
            "check_question": "What catastrophic problem happens if two threads update a shared bank balance simultaneously without mutual exclusion?",
            "expected_core_concept": "Race condition leading to corrupted or incorrect balance",
            "key_terms": ["race condition", "data corruption", "inconsistent state"],
            "common_misconceptions": {},
            "simpler_analogy": "If two people write on the exact same line of a chalkboard at the same second, the text is ruined.",
            "socratic_hint": "Think about both threads reading the old value before either writes the new value.",
        }
    ],
}

def get_curriculum_for_topic(
    topic: str,
    rag_chunks: Optional[List[Dict[str, Any]]] = None,
) -> List[ConceptStep]:
    """
    Returns structured pedagogical concept steps for a given topic.
    If matching RAG chunks exist, grounds the steps with authentic citations.
    """
    topic_lower = topic.lower().strip()

    # 1. If authentic RAG / document chunks exist, construct curriculum steps strictly from them
    if rag_chunks and len(rag_chunks) > 0:
        steps: List[ConceptStep] = []
        for idx, chunk in enumerate(rag_chunks[:4]):
            content = chunk.get("content", "").strip()
            doc_name = chunk.get("document_name", "Uploaded Material")
            sec_title = chunk.get("section_title") or f"Section {idx + 1}"

            sentences = [s.strip() for s in content.split(".") if len(s.strip()) > 15]
            core_summary = sentences[0] if sentences else content[:150]

            step = ConceptStep(
                step_index=idx,
                title=f"{sec_title} — {doc_name}",
                explanation=content,
                analogy=f"This section establishes the formal principles and context detailed in {doc_name}.",
                check_question=f"Based on this section of {doc_name}, what is the central concept or requirement explained here?",
                expected_core_concept=core_summary,
                key_terms=[w.lower() for w in sec_title.split() if len(w) > 3],
                common_misconceptions={},
                simpler_analogy=f"Core takeaway: {core_summary}",
                socratic_hint=f"Focus on the main principles detailed in {sec_title}.",
                source_citation={
                    "document_id": chunk.get("document_id"),
                    "document_name": doc_name,
                    "page_number": chunk.get("page_number", 1),
                    "section_title": sec_title,
                    "snippet": content[:250],
                },
            )
            steps.append(step)
        return steps

    # 2. Check built-in curricula for explicit topics
    selected_data = None
    for key, steps in BUILTIN_CURRICULA.items():
        if key in topic_lower:
            selected_data = steps
            break

    # 3. If no exact builtin matched, create an adaptive 3-step lesson
    if not selected_data:
        selected_data = [
            {
                "step_index": 0,
                "title": f"Core Foundations of {topic.title()}",
                "explanation": f"{topic.title()} is a central concept designed to coordinate system behavior and solve fundamental challenges.",
                "analogy": f"Imagine an organized framework where every component has a distinct role and clear rules of engagement.",
                "check_question": f"In your own words, what is the primary goal that {topic} achieves?",
                "expected_core_concept": f"coordinates operations and ensures correctness for {topic}",
                "key_terms": [topic_lower],
                "common_misconceptions": {},
                "simpler_analogy": "Think of it like traffic lights keeping an intersection moving safely.",
                "socratic_hint": "Focus on the main problem this technique was invented to solve.",
            },
            {
                "step_index": 1,
                "title": f"Key Mechanisms of {topic.title()}",
                "explanation": f"To function reliably, {topic} relies on specific rules, state invariants, and step-by-step mechanisms.",
                "analogy": "Like gears in a watch: each part triggers the next in a precise, deterministic sequence.",
                "check_question": f"What happens if one of the core rules of {topic} is violated?",
                "expected_core_concept": "The system enters an inconsistent or failing state",
                "key_terms": ["inconsistent", "error", "failure"],
                "common_misconceptions": {},
                "simpler_analogy": "If one gear slips, the watch stops keeping accurate time.",
                "socratic_hint": "Consider the consequence of missing one necessary step.",
            },
        ]

    steps: List[ConceptStep] = []
    for item in selected_data:
        step = ConceptStep(**item)
        steps.append(step)

    return steps
