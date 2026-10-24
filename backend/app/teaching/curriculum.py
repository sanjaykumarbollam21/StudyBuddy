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
            "key_ideas": [
                "processes hold resources while waiting for other resources",
                "circular waiting dependency where neither can proceed",
                "processes are permanently blocked without external resolution",
            ],
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
            "key_ideas": [
                "No preemption condition is eliminated",
                "preemption allows taking away held resources forcibly",
            ],
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
            "key_ideas": [
                "a cycle or circular loop in the directed graph",
                "guarantees deadlock for single-instance resources",
            ],
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
            "key_ideas": [
                "existence of a safe execution sequence",
                "all processes can finish with available resources without deadlocking",
            ],
            "key_terms": ["safe sequence", "all processes finish", "completion"],
            "common_misconceptions": {
                "no processes are running": "In a safe state, processes can and do run concurrently.",
            },
            "simpler_analogy": "Safe means there is a clear order where everyone finishes without getting stuck.",
            "socratic_hint": "Think about finding an orderly sequence where every process gets what it needs.",
        },
    ],
    "rational agent": [
        {
            "step_index": 0,
            "title": "Core Definition of Rational Agents",
            "explanation": (
                "In artificial intelligence, a rational agent is an autonomous entity that perceives its environment "
                "through sensors and selects actions that maximize its expected performance measure, "
                "given its percept sequence and built-in knowledge."
            ),
            "analogy": (
                "Think of a thermostat or self-driving car: it senses environment data and chooses the best action "
                "to achieve its specific objective, even when future outcomes are uncertain."
            ),
            "check_question": "In your own words, what is a rational agent in AI?",
            "expected_core_concept": (
                "An agent that acts to maximize expected performance based on its percept sequence and knowledge."
            ),
            "key_ideas": [
                "perceives environment through percepts or sensors",
                "acts to achieve best expected outcome or maximize performance",
                "decisions are guided by goals, percept history, and knowledge",
            ],
            "key_terms": ["percept sequence", "performance measure", "expected outcome", "actions"],
            "common_misconceptions": {
                "fast cpu": "Rationality is about making optimal decisions, not having a fast CPU or hardware clock speed.",
                "cpu speed": "A slow computer can be completely rational if its choices maximize expected outcome; hardware speed does not define rationality.",
                "omniscience": "Rationality maximizes expected performance given what is known; it does not mean omniscient knowledge of the future.",
                "inaction": "A rational agent takes actions to achieve goals; shutting down or doing nothing fails the performance measure.",
            },
            "simpler_analogy": "Think of a smart thermostat: it senses temperature and chooses whether to turn heat on or off to reach its goal.",
            "socratic_hint": "Focus on how the agent perceives its environment and chooses actions to maximize success.",
        },
        {
            "step_index": 1,
            "title": "Key Mechanisms of Rational Agents",
            "explanation": (
                "A rational agent operates via an agent function mapping percept histories to actions, "
                "implemented by an agent architecture and program under a specific PEAS specification (Performance, Environment, Actuators, Sensors)."
            ),
            "analogy": "Like an automated chess player: sensors read the board, the algorithm evaluates choices, and actuators move pieces.",
            "check_question": "What happens if an agent acts purely randomly without using its percept history?",
            "expected_core_concept": "It fails to maximize expected performance and cannot be considered rational.",
            "key_ideas": [
                "fails to maximize expected performance",
                "cannot adapt actions to the perceived environment",
            ],
            "key_terms": ["performance", "agent function", "random", "irrational"],
            "common_misconceptions": {
                "still rational": "Random action without regard to percepts or goals is irrational in AI.",
            },
            "simpler_analogy": "A driver closing their eyes and turning the steering wheel randomly will crash instead of reaching the destination.",
            "socratic_hint": "Think about whether random actions can consistently achieve a goal.",
        },
    ],
    "cap theorem": [
        {
            "step_index": 0,
            "title": "CAP Theorem Fundamentals",
            "explanation": (
                "The CAP theorem states that any distributed data store can simultaneously provide "
                "at most two of three guarantees: Consistency (all nodes return the latest data), "
                "Availability (every non-failing node returns a response), and Partition tolerance (the system works despite network partitions)."
            ),
            "analogy": (
                "Like a two-way switch during a storm: when the communication line between two servers is cut, "
                "you must choose whether to pause writes (Consistency) or serve potentially stale data (Availability)."
            ),
            "check_question": "What does the CAP theorem state regarding distributed data systems?",
            "expected_core_concept": (
                "When network partitions occur, a distributed data store can simultaneously guarantee at most two of Consistency, Availability, and Partition tolerance."
            ),
            "key_ideas": [
                "guarantees at most two out of Consistency, Availability, and Partition tolerance",
                "trade-off is forced when network partitions occur",
                "applies to distributed databases and data stores",
            ],
            "key_terms": ["consistency", "availability", "partition tolerance", "trade-off"],
            "common_misconceptions": {
                "centralized processing": "CAP stands for Consistency, Availability, and Partition tolerance in distributed databases, not Centralized Application Processing.",
                "no partitions": "CAP theorem assumes network partitions will happen; it does not prevent or eliminate them.",
                "can have all three": "You cannot guarantee both 100% consistency and 100% availability when a network partition happens.",
            },
            "simpler_analogy": (
                "Two ice cream shops connected by phone: if the phone line is cut, you either close until connected (Consistency) or keep selling with outdated counts (Availability)."
            ),
            "socratic_hint": "Think about what trade-off a distributed system must make when communication between nodes fails.",
        },
        {
            "step_index": 1,
            "title": "Key Mechanisms of CAP Theorem",
            "explanation": (
                "In real distributed networks, network partitions (P) are unavoidable physical realities. "
                "Therefore, distributed architectures are in practice choices between CP (Consistency + Partition Tolerance) "
                "and AP (Availability + Partition Tolerance)."
            ),
            "analogy": "Like designing an emergency protocol: you choose whether to halt operations safely or continue running with degraded sync.",
            "check_question": "Why is 'CA' (Consistency and Availability without Partition Tolerance) rarely achievable in distributed networks?",
            "expected_core_concept": "Network failures and partitions are inevitable across physical distributed networks.",
            "key_ideas": [
                "network partitions are inevitable across physical networks",
                "systems must be partition tolerant to function distributedly",
            ],
            "key_terms": ["network failure", "unavoidable", "partition tolerance"],
            "common_misconceptions": {
                "networks never fail": "Cables get cut and packets drop routinely in distributed infrastructure.",
            },
            "simpler_analogy": "You cannot promise a reliable bridge without assuming rivers will flood.",
            "socratic_hint": "Consider whether real-world network cables and routers ever fail.",
        },
    ],
    "fundamental rights": [
        {
            "step_index": 0,
            "title": "Core Purpose of Fundamental Rights",
            "explanation": (
                "Part III of the Constitution of India (Articles 12-35) enshrines Fundamental Rights. "
                "They are justiciable constitutional guarantees that protect basic civil liberties and human dignity "
                "against arbitrary state action, ensuring equality before law and democratic freedoms."
            ),
            "analogy": (
                "Like an unbreakable constitutional shield that prevents the government from acting arbitrarily "
                "against individual citizens."
            ),
            "check_question": "What is the primary constitutional goal of Fundamental Rights?",
            "expected_core_concept": (
                "To guarantee basic civil liberties and human dignity while protecting individuals against arbitrary state action."
            ),
            "key_ideas": [
                "guarantees basic civil liberties, freedoms, or human dignity",
                "protects individuals against arbitrary state action or overreach",
                "enforces constitutional rights and rule of law",
            ],
            "key_terms": ["civil liberties", "arbitrary state action", "human dignity", "part iii"],
            "common_misconceptions": {
                "absolute rights": "Fundamental Rights are not absolute; they are subject to reasonable restrictions in the public interest.",
                "only article 21": "Article 21 is crucial, but Fundamental Rights encompass a broader charter (Articles 12-35) including equality and freedoms.",
            },
            "simpler_analogy": "A rulebook in a game that gives every player untouchable safety rules that no referee can arbitrarily cancel.",
            "socratic_hint": "Think about why citizens need constitutional protections against the power of the state.",
        },
        {
            "step_index": 1,
            "title": "Right to Life & Personal Liberty (Article 21)",
            "explanation": (
                "Article 21 guarantees that no person shall be deprived of life or personal liberty "
                "except according to procedure established by law, expanded in the Maneka Gandhi case to require that "
                "procedure be just, fair, and reasonable."
            ),
            "analogy": "Like requiring that a referee not only follow written rules, but that the rules themselves be fundamentally fair.",
            "check_question": "What standard did the Maneka Gandhi case introduce for procedures depriving liberty?",
            "expected_core_concept": "Procedure must be just, fair, and reasonable, not arbitrary or harsh.",
            "key_ideas": [
                "procedure must be just, fair, and reasonable",
                "substantive due process preventing arbitrary law",
            ],
            "key_terms": ["just fair reasonable", "maneka gandhi", "procedure established by law"],
            "common_misconceptions": {
                "any law is fine": "Mere enactment of a harsh written law is insufficient; it must be just and fair.",
            },
            "simpler_analogy": "The rule must not only be written in ink; it must be genuinely fair.",
            "socratic_hint": "Focus on the three adjectives the Supreme Court required for legal procedure.",
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
            "key_ideas": [
                "race condition occurs",
                "data corruption or incorrect shared state",
            ],
            "key_terms": ["race condition", "data corruption", "inconsistent state"],
            "common_misconceptions": {
                "hardware speed": "Faster processors do not prevent race conditions; synchronization primitives are required.",
            },
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
    Includes explicit key_ideas and non-empty common_misconceptions for all topics.
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
                key_ideas=[
                    f"Core principles detailed in {sec_title}",
                    f"Operational requirements and constraints in {doc_name}",
                ],
                key_terms=[w.lower() for w in sec_title.split() if len(w) > 3],
                common_misconceptions={
                    "hardware speed": "The concept is defined by architectural and logical rules, not hardware clock speed.",
                    "superficial match": "A superficial keyword match is insufficient without understanding the underlying mechanism.",
                },
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
        if key in topic_lower or topic_lower in key:
            selected_data = steps
            break

    # 3. If no exact builtin matched, create an adaptive structured lesson with key_ideas and non-empty misconceptions
    if not selected_data:
        selected_data = [
            {
                "step_index": 0,
                "title": f"Core Foundations of {topic.title()}",
                "explanation": f"{topic.title()} is a central concept designed to coordinate system behavior and solve fundamental challenges.",
                "analogy": f"Imagine an organized framework where every component has a distinct role and clear rules of engagement.",
                "check_question": f"In your own words, what is the primary goal that {topic} achieves?",
                "expected_core_concept": f"coordinates operations and ensures correctness for {topic}",
                "key_ideas": [
                    f"core definition and primary purpose of {topic}",
                    f"fundamental problem that {topic} is designed to solve",
                    f"key operational invariants governing {topic}",
                ],
                "key_terms": [topic_lower],
                "common_misconceptions": {
                    "cpu speed": f"{topic} is a conceptual or algorithmic principle, not a CPU hardware execution speed issue.",
                    "hardware speed": f"{topic} behavior is governed by logical rules, not processor clock frequency.",
                    "inaction": f"{topic} actively coordinates outcomes rather than passively shutting down.",
                },
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
                "key_ideas": [
                    "system enters an inconsistent or failing state",
                    "invariants are violated leading to breakdown",
                ],
                "key_terms": ["inconsistent", "error", "failure"],
                "common_misconceptions": {
                    "self healing": "Without proper error handling, rule violations cause cascading failures.",
                },
                "simpler_analogy": "If one gear slips, the watch stops keeping accurate time.",
                "socratic_hint": "Consider the consequence of missing one necessary step.",
            },
        ]

    steps: List[ConceptStep] = []
    for item in selected_data:
        step = ConceptStep(**item)
        steps.append(step)

    return steps
