"""
Knowledge Graph Engine for Study Buddy.
Implements a Directed Acyclic Graph (DAG) for concepts, topics, and prerequisites,
with cycle detection, topological sorting, and foundational pre-built curricula.
"""

from typing import Dict, List, Set, Optional, Any
from dataclasses import dataclass, field
import uuid


@dataclass
class ConceptNode:
    id: str
    title: str
    description: str
    subject: str
    difficulty: str = "medium"  # beginner, intermediate, advanced
    estimated_mins: int = 30
    parent_concept: Optional[str] = None  # Topic -> Concept -> Sub-concept hierarchy
    sub_concepts: List[str] = field(default_factory=list)
    prerequisites: List[str] = field(default_factory=list)  # Titles or IDs of prerequisite nodes
    learning_objectives: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "subject": self.subject,
            "difficulty": self.difficulty,
            "estimated_mins": self.estimated_mins,
            "parent_concept": self.parent_concept,
            "sub_concepts": self.sub_concepts,
            "prerequisites": self.prerequisites,
            "learning_objectives": self.learning_objectives,
        }


class KnowledgeGraph:
    """
    Directed Acyclic Graph (DAG) representing concept prerequisite networks.
    A directed edge u -> v means concept u is a prerequisite for concept v (u must be learned before v).
    """

    def __init__(self, name: str = "Curriculum Graph"):
        self.name = name
        # Node storage: id/title -> ConceptNode
        self.nodes: Dict[str, ConceptNode] = {}
        # Title to ID mapping for flexible lookup
        self.title_to_id: Dict[str, str] = {}
        # Adjacency list: prereq_id -> list of dependent target_ids (forward edges)
        self.adj: Dict[str, List[str]] = {}
        # Reverse adjacency list: target_id -> list of prereq_ids (incoming edges)
        self.in_edges: Dict[str, List[str]] = {}

    def add_node(self, node: ConceptNode) -> None:
        self.nodes[node.id] = node
        self.title_to_id[node.title.lower().strip()] = node.id
        if node.id not in self.adj:
            self.adj[node.id] = []
        if node.id not in self.in_edges:
            self.in_edges[node.id] = []

    def get_node(self, identifier: str) -> Optional[ConceptNode]:
        if identifier in self.nodes:
            return self.nodes[identifier]
        norm = identifier.lower().strip()
        if norm in self.title_to_id:
            return self.nodes[self.title_to_id[norm]]
        # Partial match fallback
        for title_key, node_id in self.title_to_id.items():
            if norm in title_key or title_key in norm:
                return self.nodes[node_id]
        return None

    def add_prerequisite(self, prereq_identifier: str, target_identifier: str) -> bool:
        """
        Declares that prereq_identifier is a prerequisite for target_identifier.
        Returns False if adding the edge would introduce a cycle.
        """
        prereq = self.get_node(prereq_identifier)
        target = self.get_node(target_identifier)
        if not prereq or not target or prereq.id == target.id:
            return False

        # Check if edge already exists
        if target.id in self.adj[prereq.id]:
            return True

        # Temporarily add edge to test for cycle
        self.adj[prereq.id].append(target.id)
        self.in_edges[target.id].append(prereq.id)

        if self.has_cycle():
            # Rollback edge if it introduces cycle
            self.adj[prereq.id].remove(target.id)
            self.in_edges[target.id].remove(prereq.id)
            return False

        if prereq.title not in target.prerequisites and prereq.id not in target.prerequisites:
            target.prerequisites.append(prereq.title)

        return True

    def has_cycle(self) -> bool:
        """
        DFS 3-color cycle detection.
        0 = unvisited (white), 1 = visiting (gray), 2 = visited (black).
        """
        color: Dict[str, int] = {node_id: 0 for node_id in self.nodes}

        def dfs(u: str) -> bool:
            color[u] = 1
            for v in self.adj.get(u, []):
                if color.get(v, 0) == 1:
                    return True  # Back edge found -> cycle
                if color.get(v, 0) == 0 and dfs(v):
                    return True
            color[u] = 2
            return False

        for node_id in self.nodes:
            if color[node_id] == 0:
                if dfs(node_id):
                    return True
        return False

    def topological_sort(self) -> List[ConceptNode]:
        """
        Returns nodes in valid pedagogical order using Kahn's algorithm.
        Prerequisites always appear before dependent concepts.
        """
        in_degree: Dict[str, int] = {node_id: len(self.in_edges.get(node_id, [])) for node_id in self.nodes}
        queue = [node_id for node_id, deg in in_degree.items() if deg == 0]
        # Sort queue deterministically
        queue.sort(key=lambda nid: (self.nodes[nid].difficulty == "advanced", self.nodes[nid].title))

        order: List[ConceptNode] = []
        while queue:
            curr_id = queue.pop(0)
            order.append(self.nodes[curr_id])

            for dependent_id in self.adj.get(curr_id, []):
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
            queue.sort(key=lambda nid: (self.nodes[nid].difficulty == "advanced", self.nodes[nid].title))

        # If graph had disconnected cycles or remaining nodes, append them safely
        if len(order) < len(self.nodes):
            remaining = [self.nodes[nid] for nid in self.nodes if self.nodes[nid] not in order]
            order.extend(remaining)

        return order

    def get_prerequisites(self, identifier: str, recursive: bool = False) -> List[ConceptNode]:
        """
        Returns all immediate or recursive prerequisite nodes for the given concept.
        """
        target = self.get_node(identifier)
        if not target:
            return []

        if not recursive:
            return [self.nodes[pid] for pid in self.in_edges.get(target.id, []) if pid in self.nodes]

        visited: Set[str] = set()
        result: List[ConceptNode] = []

        def dfs(curr_id: str):
            for pid in self.in_edges.get(curr_id, []):
                if pid not in visited:
                    visited.add(pid)
                    if pid in self.nodes:
                        result.append(self.nodes[pid])
                        dfs(pid)

        dfs(target.id)
        return result

    def get_dependents(self, identifier: str, recursive: bool = False) -> List[ConceptNode]:
        """
        Returns concepts that depend on this concept (concepts unlocked by mastering this).
        """
        target = self.get_node(identifier)
        if not target:
            return []

        if not recursive:
            return [self.nodes[did] for did in self.adj.get(target.id, []) if did in self.nodes]

        visited: Set[str] = set()
        result: List[ConceptNode] = []

        def dfs(curr_id: str):
            for did in self.adj.get(curr_id, []):
                if did not in visited:
                    visited.add(did)
                    if did in self.nodes:
                        result.append(self.nodes[did])
                        dfs(did)

        dfs(target.id)
        return result

    def get_frontier_unlocked(self, mastered_identifiers: Set[str]) -> List[ConceptNode]:
        """
        Returns all concepts whose prerequisites have ALL been mastered, but are not yet mastered.
        """
        mastered_ids: Set[str] = set()
        for m in mastered_identifiers:
            node = self.get_node(m)
            if node:
                mastered_ids.add(node.id)

        unlocked: List[ConceptNode] = []
        for node in self.topological_sort():
            if node.id in mastered_ids:
                continue
            prereqs = self.in_edges.get(node.id, [])
            if all(p in mastered_ids for p in prereqs):
                unlocked.append(node)
        return unlocked


# -----------------------------------------------------------------------------
# Curated Foundational Knowledge Graphs (100% Offline Capable)
# -----------------------------------------------------------------------------

def get_os_knowledge_graph() -> KnowledgeGraph:
    """
    Curated hierarchical knowledge graph for Operating Systems.
    Decomposes into Topic -> Concept -> Sub-concepts with prerequisite dependencies.
    """
    kg = KnowledgeGraph(name="Operating Systems Curriculum")

    nodes = [
        ConceptNode(
            id="os-fund",
            title="OS Fundamentals & Architecture",
            description="Role of the operating system, kernel vs user mode, system calls, and hardware abstraction.",
            subject="Operating Systems",
            difficulty="beginner",
            estimated_mins=30,
            sub_concepts=["Kernel Mode & User Mode", "Dual-mode Operation", "System Call Interface", "Interrupts & Traps"],
            learning_objectives=[
                "Understand the distinction between user mode and kernel mode privilege rings.",
                "Explain how traps and interrupts transition execution to the OS kernel.",
                "Identify common system calls (e.g. fork, exec, read, write).",
            ],
        ),
        ConceptNode(
            id="os-proc",
            title="Processes & Lifecycle",
            description="Process structure, Process Control Block (PCB), process states, and context switching.",
            subject="Operating Systems",
            difficulty="beginner",
            estimated_mins=45,
            parent_concept="OS Fundamentals & Architecture",
            sub_concepts=["Process States (New, Ready, Running, Waiting, Terminated)", "Process Control Block (PCB)", "Context Switching Overhead"],
            prerequisites=["OS Fundamentals & Architecture"],
            learning_objectives=[
                "Diagram the five standard process lifecycle states.",
                "Detail the data stored inside a Process Control Block (PCB).",
                "Describe the cost and CPU register mechanics of context switching.",
            ],
        ),
        ConceptNode(
            id="os-threads",
            title="Threads & Multithreading",
            description="Thread execution units, user-level vs kernel-level threads, and multithreading models.",
            subject="Operating Systems",
            difficulty="intermediate",
            estimated_mins=40,
            parent_concept="Processes & Lifecycle",
            sub_concepts=["User vs Kernel Threads", "Shared Heap vs Private Stack", "Multithreading Models (1:1, M:N)"],
            prerequisites=["Processes & Lifecycle"],
            learning_objectives=[
                "Differentiate thread memory isolation from process address space isolation.",
                "Explain the performance advantages of lightweight thread switching over process switching.",
            ],
        ),
        ConceptNode(
            id="os-sched",
            title="CPU Scheduling Algorithms",
            description="Preemptive vs non-preemptive scheduling, FCFS, SJF, Round Robin, and Priority Scheduling.",
            subject="Operating Systems",
            difficulty="intermediate",
            estimated_mins=50,
            parent_concept="Processes & Lifecycle",
            sub_concepts=["FCFS & Convoy Effect", "Shortest Job First (SJF)", "Round Robin & Time Quantum", "Priority Scheduling & Starvation"],
            prerequisites=["Processes & Lifecycle"],
            learning_objectives=[
                "Calculate average waiting time and turnaround time for FCFS, SJF, and Round Robin.",
                "Explain how time quantum choice in Round Robin impacts context switch overhead and latency.",
                "Understand starvation and aging in priority schedulers.",
            ],
        ),
        ConceptNode(
            id="os-sync",
            title="Process Synchronization & Concurrency",
            description="Race conditions, critical section problem, Peterson's algorithm, mutex locks, and semaphores.",
            subject="Operating Systems",
            difficulty="intermediate",
            estimated_mins=60,
            sub_concepts=["Race Conditions", "Critical Section Problem", "Mutex Locks", "Counting & Binary Semaphores"],
            prerequisites=["Processes & Lifecycle", "Threads & Multithreading"],
            learning_objectives=[
                "Define the three critical section requirements: Mutual Exclusion, Progress, and Bounded Waiting.",
                "Implement mutual exclusion using atomic test-and-set and mutexes.",
                "Compare binary semaphores with counting semaphores.",
            ],
        ),
        ConceptNode(
            id="os-deadlock",
            title="Deadlocks & Banker's Algorithm",
            description="The four Coffman deadlock conditions, resource allocation graphs, deadlock avoidance, and Banker's algorithm.",
            subject="Operating Systems",
            difficulty="advanced",
            estimated_mins=60,
            parent_concept="Process Synchronization & Concurrency",
            sub_concepts=["Mutual Exclusion", "Hold and Wait", "No Preemption", "Circular Wait", "Banker's Algorithm"],
            prerequisites=["Process Synchronization & Concurrency"],
            learning_objectives=[
                "Identify the four necessary Coffman conditions for deadlock.",
                "Detect cycles in Resource Allocation Graphs (RAG).",
                "Execute the Banker's safety and resource-request algorithm step-by-step.",
            ],
        ),
        ConceptNode(
            id="os-mem",
            title="Memory Management & Paging",
            description="Address binding, logical vs physical addresses, internal and external fragmentation, and paging.",
            subject="Operating Systems",
            difficulty="intermediate",
            estimated_mins=50,
            sub_concepts=["Logical vs Physical Address Spaces", "Contiguous Allocation & Fragmentation", "Paging & Page Tables", "Translation Lookaside Buffer (TLB)"],
            prerequisites=["OS Fundamentals & Architecture"],
            learning_objectives=[
                "Explain the MMU translation from logical page numbers to physical frame numbers.",
                "Contrast internal fragmentation in paging with external fragmentation in segmentation.",
                "Calculate Effective Memory Access Time with a TLB hit ratio.",
            ],
        ),
        ConceptNode(
            id="os-vmem",
            title="Virtual Memory & Page Replacement",
            description="Demand paging, page faults, Belady's anomaly, and page replacement algorithms (FIFO, LRU, Optimal).",
            subject="Operating Systems",
            difficulty="advanced",
            estimated_mins=55,
            parent_concept="Memory Management & Paging",
            sub_concepts=["Demand Paging & Page Fault Handling", "FIFO Replacement & Belady's Anomaly", "Least Recently Used (LRU)", "Thrashing & Working Set Model"],
            prerequisites=["Memory Management & Paging"],
            learning_objectives=[
                "Trace the step-by-step sequence of handling a hardware page fault trap.",
                "Simulate FIFO, Optimal, and LRU page replacement for a given reference string.",
                "Diagnose thrashing and outline the Working Set Model solution.",
            ],
        ),
        ConceptNode(
            id="os-files",
            title="File Systems & Storage Management",
            description="File system interface, inodes, directory structures, allocation methods (contiguous, linked, indexed).",
            subject="Operating Systems",
            difficulty="intermediate",
            estimated_mins=45,
            sub_concepts=["Inodes & File Metadata", "Indexed & Extent-based Allocation", "Hard Links vs Symbolic Links"],
            prerequisites=["OS Fundamentals & Architecture"],
            learning_objectives=[
                "Explain how UNIX inodes point to direct, indirect, and double-indirect blocks.",
                "Compare contiguous, linked, and indexed block allocation strategies.",
            ],
        ),
    ]

    for n in nodes:
        kg.add_node(n)

    # Add prerequisite edges
    kg.add_prerequisite("os-fund", "os-proc")
    kg.add_prerequisite("os-proc", "os-threads")
    kg.add_prerequisite("os-proc", "os-sched")
    kg.add_prerequisite("os-proc", "os-sync")
    kg.add_prerequisite("os-threads", "os-sync")
    kg.add_prerequisite("os-sync", "os-deadlock")
    kg.add_prerequisite("os-fund", "os-mem")
    kg.add_prerequisite("os-mem", "os-vmem")
    kg.add_prerequisite("os-fund", "os-files")

    return kg


def get_dbms_knowledge_graph() -> KnowledgeGraph:
    """
    Curated hierarchical knowledge graph for Database Management Systems.
    """
    kg = KnowledgeGraph(name="DBMS Curriculum")

    nodes = [
        ConceptNode(
            id="db-fund",
            title="Relational Model & SQL Fundamentals",
            description="Relational data model, primary/foreign keys, relational algebra, and SQL DDL/DML.",
            subject="Database Management Systems",
            difficulty="beginner",
            estimated_mins=35,
            sub_concepts=["Tables, Rows, and Attributes", "Primary & Foreign Keys", "Relational Algebra Operations", "Basic SELECT, JOIN, GROUP BY"],
            learning_objectives=[
                "Model entities and relationships using relational constraints.",
                "Write complex SQL queries utilizing INNER, LEFT, and FULL joins.",
            ],
        ),
        ConceptNode(
            id="db-norm",
            title="Schema Normalization & Functional Dependencies",
            description="Functional dependencies, Armstrong's axioms, 1NF, 2NF, 3NF, and Boyce-Codd Normal Form (BCNF).",
            subject="Database Management Systems",
            difficulty="intermediate",
            estimated_mins=50,
            sub_concepts=["Functional Dependencies", "1NF (Atomic Attributes)", "2NF (No Partial Key Dependency)", "3NF (No Transitive Dependency)", "BCNF"],
            prerequisites=["Relational Model & SQL Fundamentals"],
            learning_objectives=[
                "Find candidate keys using functional dependency closures.",
                "Decompose unnormalized relations into 3NF and BCNF without loss of information.",
            ],
        ),
        ConceptNode(
            id="db-index",
            title="Indexing, B-Trees & Storage",
            description="Clustered vs unclustered indexes, dense vs sparse indexes, B-Trees and B+ Trees query operations.",
            subject="Database Management Systems",
            difficulty="intermediate",
            estimated_mins=55,
            sub_concepts=["Primary vs Secondary Indexes", "B+ Tree Search and Insertion", "Hash Indexes", "I/O Cost Models"],
            prerequisites=["Relational Model & SQL Fundamentals"],
            learning_objectives=[
                "Explain why B+ Trees are preferred over binary trees for disk storage.",
                "Trace range scan execution on leaf node linked lists in B+ Trees.",
            ],
        ),
        ConceptNode(
            id="db-acid",
            title="Transactions & ACID Properties",
            description="Transaction concepts, Atomicity, Consistency, Isolation levels (Read Uncommitted to Serializable), and Durability.",
            subject="Database Management Systems",
            difficulty="intermediate",
            estimated_mins=45,
            sub_concepts=["Atomicity & Write-Ahead Logging", "Consistency Constraints", "Isolation Levels & Anomalies", "Durability Guarantee"],
            prerequisites=["Relational Model & SQL Fundamentals"],
            learning_objectives=[
                "Define Dirty Read, Non-repeatable Read, and Phantom Read anomalies.",
                "Map ANSI SQL isolation levels to the phenomena they prevent.",
            ],
        ),
        ConceptNode(
            id="db-concur",
            title="Concurrency Control & Two-Phase Locking",
            description="Conflict serializability, precedence graphs, Two-Phase Locking (2PL), Strict 2PL, and deadlock resolution.",
            subject="Database Management Systems",
            difficulty="advanced",
            estimated_mins=60,
            sub_concepts=["Conflict vs View Serializability", "Precedence (Serialization) Graph", "Shared & Exclusive Locks", "Two-Phase Locking (2PL)", "Deadlock Detection via Wait-For Graphs"],
            prerequisites=["Transactions & ACID Properties"],
            learning_objectives=[
                "Test schedule conflict serializability using cycle detection on precedence graphs.",
                "Prove why 2PL guarantees serializability and why Strict 2PL prevents cascading aborts.",
            ],
        ),
        ConceptNode(
            id="db-recovery",
            title="Crash Recovery & Write-Ahead Logging (ARIES)",
            description="Buffer management (Steal/No-Force), Write-Ahead Logging protocol, checkpointing, and ARIES recovery algorithm.",
            subject="Database Management Systems",
            difficulty="advanced",
            estimated_mins=55,
            sub_concepts=["WAL Protocol", "Checkpoints (Fuzzy Checkpoint)", "Analysis Pass", "Redo Pass", "Undo Pass"],
            prerequisites=["Transactions & ACID Properties"],
            learning_objectives=[
                "Trace the three passes of the ARIES crash recovery algorithm.",
                "Explain why logging Compensation Log Records (CLRs) prevents crash loops during recovery.",
            ],
        ),
    ]

    for n in nodes:
        kg.add_node(n)

    kg.add_prerequisite("db-fund", "db-norm")
    kg.add_prerequisite("db-fund", "db-index")
    kg.add_prerequisite("db-fund", "db-acid")
    kg.add_prerequisite("db-acid", "db-concur")
    kg.add_prerequisite("db-acid", "db-recovery")

    return kg


def get_ml_knowledge_graph() -> KnowledgeGraph:
    """
    Curated hierarchical knowledge graph for Machine Learning.
    """
    kg = KnowledgeGraph(name="Machine Learning Curriculum")

    nodes = [
        ConceptNode(
            id="ml-math",
            title="Math Foundations: Linear Algebra & Calculus",
            description="Vectors, matrices, dot products, eigenvalues, partial derivatives, and gradient vectors.",
            subject="Machine Learning",
            difficulty="beginner",
            estimated_mins=40,
            sub_concepts=["Vector Spaces & Matrix Multiplication", "Gradients & Jacobians", "Probability Distributions & Expectation"],
            learning_objectives=[
                "Compute matrix transformations and gradient vectors for multivariable loss functions.",
            ],
        ),
        ConceptNode(
            id="ml-reg",
            title="Linear & Logistic Regression",
            description="Supervised learning formulation, ordinary least squares, sigmoid activation, binary cross-entropy, and gradient descent.",
            subject="Machine Learning",
            difficulty="beginner",
            estimated_mins=50,
            sub_concepts=["Cost Function MSE", "Batch vs Stochastic Gradient Descent", "Sigmoid Activation", "Binary Cross-Entropy Loss"],
            prerequisites=["Math Foundations: Linear Algebra & Calculus"],
            learning_objectives=[
                "Derive the analytical normal equation and gradient descent update rule for linear regression.",
                "Interpret logistic regression outputs as calibrated probabilities.",
            ],
        ),
        ConceptNode(
            id="ml-overfit",
            title="Bias-Variance Tradeoff & Regularization",
            description="Model capacity, underfitting vs overfitting, L1 Lasso, L2 Ridge, and K-fold cross validation.",
            subject="Machine Learning",
            difficulty="intermediate",
            estimated_mins=45,
            sub_concepts=["Bias vs Variance Decomposition", "L1 Regularization (Lasso & Sparsity)", "L2 Regularization (Ridge / Weight Decay)", "Cross-Validation Techniques"],
            prerequisites=["Linear & Logistic Regression"],
            learning_objectives=[
                "Explain why L1 regularization produces sparse feature weights while L2 shrinks weights smoothly.",
                "Diagnose high bias vs high variance from training and validation learning curves.",
            ],
        ),
        ConceptNode(
            id="ml-trees",
            title="Decision Trees & Ensemble Methods",
            description="Information gain, Gini impurity, CART trees, Random Forests, and Gradient Boosted Decision Trees.",
            subject="Machine Learning",
            difficulty="intermediate",
            estimated_mins=55,
            sub_concepts=["Entropy & Information Gain", "Gini Impurity", "Bagging & Random Forests", "Boosting & Gradient Boosting"],
            prerequisites=["Bias-Variance Tradeoff & Regularization"],
            learning_objectives=[
                "Calculate entropy and information gain splits.",
                "Compare bagging variance reduction with boosting bias reduction.",
            ],
        ),
        ConceptNode(
            id="ml-nn",
            title="Neural Networks & Backpropagation",
            description="Multilayer perceptrons, activation functions (ReLU, GELU), computational graphs, chain rule, and backpropagation.",
            subject="Machine Learning",
            difficulty="advanced",
            estimated_mins=65,
            sub_concepts=["Multilayer Perceptron Architecture", "Activation Functions (ReLU, Sigmoid, Softmax)", "Chain Rule on Computational Graphs", "Backpropagation Algorithm"],
            prerequisites=["Math Foundations: Linear Algebra & Calculus", "Linear & Logistic Regression"],
            learning_objectives=[
                "Trace forward and backward passes through a 2-layer neural network.",
                "Explain the vanishing and exploding gradient problem and how modern activations mitigate it.",
            ],
        ),
    ]

    for n in nodes:
        kg.add_node(n)

    kg.add_prerequisite("ml-math", "ml-reg")
    kg.add_prerequisite("ml-reg", "ml-overfit")
    kg.add_prerequisite("ml-overfit", "ml-trees")
    kg.add_prerequisite("ml-math", "ml-nn")
    kg.add_prerequisite("ml-reg", "ml-nn")

    return kg


def get_python_dsa_knowledge_graph() -> KnowledgeGraph:
    """
    Curated knowledge graph for Python Data Structures & Algorithms.
    """
    kg = KnowledgeGraph(name="Python DSA Curriculum")

    nodes = [
        ConceptNode(
            id="dsa-py-fund",
            title="Python Data Types & Time Complexity (Big-O)",
            description="Python primitive types, lists, dictionaries, time and space complexity, asymptotic Big-O notation.",
            subject="Python & Data Structures",
            difficulty="beginner",
            estimated_mins=35,
            sub_concepts=["Big-O, Big-Theta, Big-Omega", "Python List amortized O(1) appending", "Hash Map O(1) average lookup"],
            learning_objectives=["Analyze code snippets for time and space complexity."],
        ),
        ConceptNode(
            id="dsa-linked-list",
            title="Linked Lists & Pointer Manipulation",
            description="Singly linked lists, doubly linked lists, sentinel nodes, and two-pointer fast/slow runner technique.",
            subject="Python & Data Structures",
            difficulty="intermediate",
            estimated_mins=45,
            sub_concepts=["Singly Linked List node insertion/deletion", "Fast & Slow Pointer (Floyd's Cycle Detection)", "Reversing a Linked List in-place"],
            prerequisites=["Python Data Types & Time Complexity (Big-O)"],
            learning_objectives=["Implement in-place linked list reversal and cycle detection."],
        ),
        ConceptNode(
            id="dsa-stack-queue",
            title="Stacks, Queues & Monotonic Stacks",
            description="LIFO and FIFO data structures, collections.deque in Python, matching parentheses, and next greater element.",
            subject="Python & Data Structures",
            difficulty="intermediate",
            estimated_mins=45,
            sub_concepts=["Stack operations LIFO", "Queue operations FIFO with collections.deque", "Monotonic Stack Pattern"],
            prerequisites=["Python Data Types & Time Complexity (Big-O)"],
            learning_objectives=["Solve sliding window maximum and next-greater element problems."],
        ),
        ConceptNode(
            id="dsa-trees",
            title="Binary Trees & Binary Search Trees (BST)",
            description="Tree representation, pre-order, in-order, post-order DFS traversals, level-order BFS, and BST properties.",
            subject="Python & Data Structures",
            difficulty="intermediate",
            estimated_mins=60,
            sub_concepts=["DFS Traversals (Inorder, Preorder, Postorder)", "BFS Level-Order with Deque", "BST Search, Insert, and Validate"],
            prerequisites=["Linked Lists & Pointer Manipulation", "Stacks, Queues & Monotonic Stacks"],
            learning_objectives=["Implement recursive and iterative tree traversals and validate BST invariants."],
        ),
        ConceptNode(
            id="dsa-graphs",
            title="Graph Algorithms (BFS, DFS & Topological Sort)",
            description="Adjacency list representations, cycle detection in directed graphs, BFS shortest path, and Kahn's topological sort.",
            subject="Python & Data Structures",
            difficulty="advanced",
            estimated_mins=65,
            sub_concepts=["Adjacency List vs Matrix", "Breadth-First Search (Shortest Path)", "Depth-First Search & Cycle Detection", "Topological Sort (Kahn's Algorithm)"],
            prerequisites=["Binary Trees & Binary Search Trees (BST)"],
            learning_objectives=["Implement BFS shortest path and topological sorting on directed acyclic graphs."],
        ),
    ]

    for n in nodes:
        kg.add_node(n)

    kg.add_prerequisite("dsa-py-fund", "dsa-linked-list")
    kg.add_prerequisite("dsa-py-fund", "dsa-stack-queue")
    kg.add_prerequisite("dsa-linked-list", "dsa-trees")
    kg.add_prerequisite("dsa-stack-queue", "dsa-trees")
    kg.add_prerequisite("dsa-trees", "dsa-graphs")

    return kg


def get_curated_knowledge_graph(subject_or_query: str) -> Optional[KnowledgeGraph]:
    """
    Matches a user query or subject against pre-built offline curricula.
    """
    q = subject_or_query.lower()
    if any(k in q for k in ["os", "operating system", "process", "concurrency", "deadlock", "memory management"]):
        return get_os_knowledge_graph()
    if any(k in q for k in ["dbms", "database", "sql", "normalization", "transaction", "acid", "relational"]):
        return get_dbms_knowledge_graph()
    if any(k in q for k in ["ml", "machine learning", "regression", "neural network", "deep learning", "classifier"]):
        return get_ml_knowledge_graph()
    if any(k in q for k in ["dsa", "data structure", "algorithm", "python", "linked list", "tree", "graph"]):
        return get_python_dsa_knowledge_graph()
    return None
