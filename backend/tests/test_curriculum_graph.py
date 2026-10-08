import pytest
from app.curriculum.graph import (
    KnowledgeGraph,
    ConceptNode,
    get_os_knowledge_graph,
    get_dbms_knowledge_graph,
    get_ml_knowledge_graph,
    get_python_dsa_knowledge_graph,
    get_curated_knowledge_graph,
)
from app.curriculum.extractor import DocumentConceptExtractor
from app.curriculum.service import CurriculumService
from app.models.document import DocumentChunk
from app.models.user import User


def test_knowledge_graph_dag_and_topological_sort():
    kg = KnowledgeGraph("Test DAG")

    node_a = ConceptNode(id="A", title="Basics", description="Intro", subject="CS")
    node_b = ConceptNode(id="B", title="Intermediate", description="Building", subject="CS")
    node_c = ConceptNode(id="C", title="Advanced", description="Mastery", subject="CS")

    kg.add_node(node_a)
    kg.add_node(node_b)
    kg.add_node(node_c)

    # A -> B (A is prerequisite for B)
    # B -> C (B is prerequisite for C)
    assert kg.add_prerequisite("A", "B") is True
    assert kg.add_prerequisite("B", "C") is True
    assert not kg.has_cycle()

    order = kg.topological_sort()
    order_ids = [n.id for n in order]
    assert order_ids.index("A") < order_ids.index("B") < order_ids.index("C")

    # Cycle rejection: Adding C -> A would create a cycle (A -> B -> C -> A)
    assert kg.add_prerequisite("C", "A") is False
    assert not kg.has_cycle()


def test_os_knowledge_graph_pedagogical_ordering():
    """
    Verifies the user's specific requirement:
    - 'You should learn processes before CPU scheduling.'
    - 'You should understand synchronization before deadlocks.'
    """
    os_kg = get_os_knowledge_graph()

    assert not os_kg.has_cycle()
    sorted_nodes = os_kg.topological_sort()
    titles = [n.title for n in sorted_nodes]

    # Verify Processes precedes CPU Scheduling
    proc_idx = titles.index("Processes & Lifecycle")
    sched_idx = titles.index("CPU Scheduling Algorithms")
    assert proc_idx < sched_idx, "Processes must precede CPU Scheduling"

    # Verify Synchronization precedes Deadlocks
    sync_idx = titles.index("Process Synchronization & Concurrency")
    deadlock_idx = titles.index("Deadlocks & Banker's Algorithm")
    assert sync_idx < deadlock_idx, "Synchronization must precede Deadlocks"

    # Verify Memory Management precedes Virtual Memory
    mem_idx = titles.index("Memory Management & Paging")
    vmem_idx = titles.index("Virtual Memory & Page Replacement")
    assert mem_idx < vmem_idx, "Paging/Memory Management must precede Virtual Memory"

    # Verify frontier unlock logic
    # With zero mastered topics, frontier should be OS Fundamentals
    frontier = os_kg.get_frontier_unlocked(mastered_identifiers=set())
    frontier_titles = [f.title for f in frontier]
    assert "OS Fundamentals & Architecture" in frontier_titles
    assert "Deadlocks & Banker's Algorithm" not in frontier_titles

    # If OS Fundamentals, Processes, Threads, and Synchronization are mastered:
    mastered = {
        "os-fund",
        "os-proc",
        "os-threads",
        "os-sync",
    }
    new_frontier = os_kg.get_frontier_unlocked(mastered_identifiers=mastered)
    new_frontier_titles = [f.title for f in new_frontier]
    assert "Deadlocks & Banker's Algorithm" in new_frontier_titles
    assert "CPU Scheduling Algorithms" in new_frontier_titles


def test_all_curated_graphs_are_valid_dags():
    graphs = [
        get_os_knowledge_graph(),
        get_dbms_knowledge_graph(),
        get_ml_knowledge_graph(),
        get_python_dsa_knowledge_graph(),
    ]
    for g in graphs:
        assert not g.has_cycle(), f"{g.name} contains a cycle!"
        sorted_nodes = g.topological_sort()
        assert len(sorted_nodes) == len(g.nodes), f"{g.name} topological sort dropped nodes!"


def test_document_concept_extractor():
    chunks = [
        DocumentChunk(
            id="c1",
            document_id="doc-1",
            user_id="user-1",
            chunk_index=0,
            page_number=1,
            section_title="Chapter 1: Network Layer Basics",
            content="The network layer is responsible for host-to-host communication. **IP Addressing** and packets.",
        ),
        DocumentChunk(
            id="c2",
            document_id="doc-1",
            user_id="user-1",
            chunk_index=1,
            page_number=2,
            section_title="Chapter 2: Routing Algorithms",
            content="Prerequisite: Chapter 1: Network Layer Basics. We discuss Dijkstra and Bellman-Ford algorithms.",
        ),
    ]

    extractor = DocumentConceptExtractor()
    kg = extractor.extract_from_chunks(chunks, document_title="Computer Networks")

    assert not kg.has_cycle()
    assert len(kg.nodes) == 2
    order = kg.topological_sort()
    assert order[0].title == "Chapter 1: Network Layer Basics"
    assert order[1].title == "Chapter 2: Routing Algorithms"


@pytest.mark.asyncio
async def test_curriculum_service_and_recommendations(db_session):
    # Setup test user
    user = User(
        id="test-curriculum-user-1",
        email="curriculum_student@example.com",
        full_name="Curriculum Tester",
        hashed_password="fakehashpassword123",
    )
    db_session.add(user)
    await db_session.commit()

    service = CurriculumService(db_session)

    # 1. Generate roadmap for Operating Systems
    roadmap = await service.generate_roadmap(
        user_id=user.id,
        subject="Operating Systems",
        goal="Ace Operating Systems Exam",
    )
    assert roadmap["subject"] == "Operating Systems"
    assert roadmap["total_steps"] >= 5
    topics = roadmap["topics"]
    assert topics[0]["custom_title"] == "OS Fundamentals & Architecture"
    assert topics[0]["status"] == "in_progress"  # First node starts in_progress
    assert topics[1]["status"] == "locked"  # Dependent nodes start locked

    # 2. Test "What should I learn next?"
    next_rec = await service.get_next_recommendation(user_id=user.id, roadmap_id=roadmap["id"])
    assert next_rec["topic_title"] == "OS Fundamentals & Architecture"
    assert "foundational starting point" in next_rec["why_recommended"].lower()

    # 3. Test "Why am I learning this?"
    why_explanation = await service.explain_why_learning(
        user_id=user.id,
        topic_title="Deadlocks & Banker's Algorithm",
        goal="Ace Operating Systems Exam",
    )
    assert "Process Synchronization & Concurrency" in why_explanation["prerequisites"]
    assert "Why Learn Deadlocks & Banker's Algorithm?" in why_explanation["full_explanation"]

    # 4. Simulate mastering the first 2 topics (OS Fundamentals & Processes)
    await service.update_progress_from_mastery(
        user_id=user.id,
        topic_title="OS Fundamentals & Architecture",
        mastery_score=95.0,
    )
    await service.update_progress_from_mastery(
        user_id=user.id,
        topic_title="Processes & Lifecycle",
        mastery_score=90.0,
    )

    # Re-fetch roadmap to verify dynamic prerequisite unlocking
    updated_roadmap = await service.get_roadmap(user_id=user.id, roadmap_id=roadmap["id"])
    updated_topics = updated_roadmap["topics"]

    # Processes was mastered -> Threads, CPU Scheduling should now be unlocked or in_progress
    sched_item = next(t for t in updated_topics if t["custom_title"] == "CPU Scheduling Algorithms")
    assert sched_item["status"] in ["unlocked", "in_progress"]


@pytest.mark.asyncio
async def test_curriculum_api_endpoints(client, db_session):
    # Register/login user
    reg_res = await client.post(
        "/api/v1/auth/signup",
        json={"email": "graph_api_user@example.com", "password": "Password123!", "full_name": "Graph Student"},
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}


    # 1. Generate roadmap
    gen_res = await client.post(
        "/api/v1/curriculum/roadmap/generate",
        json={"subject": "Database Management Systems", "goal": "Become a backend DBA"},
        headers=headers,
    )
    assert gen_res.status_code == 200
    data = gen_res.json()
    assert data["total_steps"] == 6
    roadmap_id = data["id"]

    # 2. Fetch roadmap
    fetch_res = await client.get(f"/api/v1/curriculum/roadmap/{roadmap_id}", headers=headers)
    assert fetch_res.status_code == 200
    assert len(fetch_res.json()["topics"]) == 6

    # 3. Get What Should I Learn Next
    next_res = await client.get("/api/v1/curriculum/next", headers=headers)
    assert next_res.status_code == 200
    assert "Relational Model & SQL Fundamentals" in next_res.json()["topic_title"]

    # 4. Get Why Am I Learning This
    why_res = await client.get(
        "/api/v1/curriculum/why?topic=Schema Normalization & Functional Dependencies",
        headers=headers,
    )
    assert why_res.status_code == 200
    assert "Relational Model & SQL Fundamentals" in why_res.json()["prerequisites"]

    # 5. List tracks
    tracks_res = await client.get("/api/v1/curriculum/tracks")
    assert tracks_res.status_code == 200
    assert len(tracks_res.json()) >= 4
