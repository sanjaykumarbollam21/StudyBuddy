from typing import Dict, Any, List
from app.exam.profiles.base import ExamProfileDefinition, ExamStageConfig


def get_upsc_profile() -> ExamProfileDefinition:
    """
    UPSC Civil Services Examination Profile.
    Complete syllabus graph, negative marking (-0.66 GS, -0.83 CSAT),
    Prelims, Mains descriptive answer writing rubrics, and DAF interview prep.
    """
    stages = [
        ExamStageConfig(
            stage_id="prelims",
            title="Civil Services (Preliminary) Examination",
            description="Objective screening examination with 2 compulsory papers (GS-1 & CSAT-2).",
            paper_names=["General Studies Paper I", "CSAT Paper II"],
            has_negative_marking=True,
            negative_marking_ratio=0.33,
            is_descriptive=False,
        ),
        ExamStageConfig(
            stage_id="mains",
            title="Civil Services (Main) Examination",
            description="Written descriptive examination of 9 papers testing deep conceptual, analytical and multidimensional understanding.",
            paper_names=[
                "Essay",
                "General Studies Paper I",
                "General Studies Paper II",
                "General Studies Paper III",
                "General Studies Paper IV (Ethics)",
                "Optional Paper I",
                "Optional Paper II",
            ],
            has_negative_marking=False,
            negative_marking_ratio=0.0,
            is_descriptive=True,
        ),
        ExamStageConfig(
            stage_id="interview",
            title="Personality Test / Interview",
            description="Comprehensive personality and situational assessment based on Detailed Application Form (DAF).",
            paper_names=["Personality Test Board"],
            has_negative_marking=False,
            negative_marking_ratio=0.0,
            is_descriptive=True,
        ),
    ]

    syllabus_tree: List[Dict[str, Any]] = [
        {
            "node_code": "UPSC-GS1-POLITY",
            "title": "Indian Polity & Governance",
            "paper_name": "General Studies Paper I & II",
            "stage": "both",
            "exam_weight": 1.6,
            "importance": "high",
            "pyq_frequency": 18,
            "children": [
                {
                    "node_code": "POL-CONST",
                    "title": "Constitution & Preamble",
                    "exam_weight": 1.5,
                    "importance": "high",
                    "pyq_frequency": 6,
                    "children": [
                        {"node_code": "POL-FR", "title": "Fundamental Rights (Articles 12-35)", "exam_weight": 1.8, "importance": "high", "pyq_frequency": 5},
                        {"node_code": "POL-DPSP", "title": "Directive Principles of State Policy (Articles 36-51)", "exam_weight": 1.4, "importance": "high", "pyq_frequency": 3},
                        {"node_code": "POL-FD", "title": "Fundamental Duties (Article 51A)", "exam_weight": 1.2, "importance": "medium", "pyq_frequency": 2},
                        {"node_code": "POL-AMEND", "title": "Constitutional Amendments & Basic Structure", "exam_weight": 1.6, "importance": "high", "pyq_frequency": 4},
                    ],
                },
                {
                    "node_code": "POL-PARLIAMENT",
                    "title": "Parliament & Union Executive",
                    "exam_weight": 1.6,
                    "importance": "high",
                    "pyq_frequency": 5,
                    "children": [
                        {"node_code": "POL-BILLS", "title": "Legislative Procedure & Money Bills", "exam_weight": 1.5, "importance": "high", "pyq_frequency": 3},
                        {"node_code": "POL-PRESIDENT", "title": "President, Governor & Ordinance Powers", "exam_weight": 1.4, "importance": "high", "pyq_frequency": 2},
                    ],
                },
                {
                    "node_code": "POL-JUDICIARY",
                    "title": "Judiciary & Judicial Review",
                    "exam_weight": 1.5,
                    "importance": "high",
                    "pyq_frequency": 4,
                    "children": [
                        {"node_code": "POL-SC-POWERS", "title": "Supreme Court Original, Appellate & Writ Jurisdiction", "exam_weight": 1.5, "importance": "high", "pyq_frequency": 3},
                    ],
                },
            ],
        },
        {
            "node_code": "UPSC-GS1-HISTORY",
            "title": "History of India & Indian National Movement",
            "paper_name": "General Studies Paper I",
            "stage": "both",
            "exam_weight": 1.5,
            "importance": "high",
            "pyq_frequency": 16,
            "children": [
                {
                    "node_code": "HIST-MODERN",
                    "title": "Modern Indian History & Freedom Struggle",
                    "exam_weight": 1.7,
                    "importance": "high",
                    "pyq_frequency": 10,
                    "children": [
                        {"node_code": "HIST-GANDHI", "title": "Gandhian Movements (NCM, CDM, Quit India)", "exam_weight": 1.7, "importance": "high", "pyq_frequency": 5},
                        {"node_code": "HIST-1857", "title": "Revolt of 1857 & Early Resistance", "exam_weight": 1.3, "importance": "medium", "pyq_frequency": 2},
                    ],
                },
                {
                    "node_code": "HIST-ANCIENT",
                    "title": "Ancient & Medieval India",
                    "exam_weight": 1.2,
                    "importance": "medium",
                    "pyq_frequency": 6,
                },
            ],
        },
        {
            "node_code": "UPSC-GS1-ECONOMY",
            "title": "Economic & Social Development",
            "paper_name": "General Studies Paper I & III",
            "stage": "both",
            "exam_weight": 1.6,
            "importance": "high",
            "pyq_frequency": 17,
            "children": [
                {
                    "node_code": "ECON-MACRO",
                    "title": "Macroeconomics & Monetary Policy",
                    "exam_weight": 1.6,
                    "importance": "high",
                    "pyq_frequency": 7,
                    "children": [
                        {"node_code": "ECON-RBI", "title": "RBI Monetary Policy & Inflation Control", "exam_weight": 1.7, "importance": "high", "pyq_frequency": 4},
                        {"node_code": "ECON-FISCAL", "title": "Fiscal Policy, Budget & FRBM Act", "exam_weight": 1.5, "importance": "high", "pyq_frequency": 3},
                    ],
                },
            ],
        },
        {
            "node_code": "UPSC-GS1-ENV",
            "title": "Environment, Ecology, Biodiversity & Climate Change",
            "paper_name": "General Studies Paper I & III",
            "stage": "both",
            "exam_weight": 1.7,
            "importance": "high",
            "pyq_frequency": 20,
            "children": [
                {
                    "node_code": "ENV-PROT",
                    "title": "Protected Areas & Wildlife Conservation",
                    "exam_weight": 1.8,
                    "importance": "high",
                    "pyq_frequency": 11,
                    "children": [
                        {"node_code": "ENV-NP", "title": "National Parks & Tiger Reserves", "exam_weight": 1.8, "importance": "high", "pyq_frequency": 7},
                        {"node_code": "ENV-CONV", "title": "International Conventions (UNFCCC, CBD, Ramsar)", "exam_weight": 1.7, "importance": "high", "pyq_frequency": 4},
                    ],
                },
            ],
        },
        {
            "node_code": "UPSC-CSAT",
            "title": "CSAT Paper II (Qualifying 33% / 66 marks)",
            "paper_name": "CSAT Paper II",
            "stage": "prelims",
            "exam_weight": 1.3,
            "importance": "high",
            "pyq_frequency": 80,
            "children": [
                {"node_code": "CSAT-RC", "title": "Reading Comprehension", "exam_weight": 1.5, "importance": "high", "pyq_frequency": 27},
                {"node_code": "CSAT-LR", "title": "Logical Reasoning & Analytical Ability", "exam_weight": 1.4, "importance": "high", "pyq_frequency": 24},
                {"node_code": "CSAT-NUM", "title": "Basic Numeracy & Data Interpretation", "exam_weight": 1.5, "importance": "high", "pyq_frequency": 29},
            ],
        },
    ]

    return ExamProfileDefinition(
        id="upsc_cse",
        name="UPSC Civil Services Examination",
        category="civil_services",
        country="India",
        conducting_body="Union Public Service Commission (UPSC)",
        stages=stages,
        subjects=[
            "Indian Polity & Governance",
            "Modern History & Freedom Struggle",
            "Ancient & Medieval History",
            "Indian & World Geography",
            "Economic & Social Development",
            "Environment & Ecology",
            "Science & Technology",
            "Current Affairs (National & International)",
            "CSAT Comprehension & Reasoning",
            "CSAT Quantitative Aptitude",
        ],
        syllabus_tree=syllabus_tree,
        question_types=[
            "single_correct",
            "assertion_reason",
            "statement_based",
            "match_following",
            "chronology",
            "elimination_based",
            "mains_descriptive_10m",
            "mains_descriptive_15m",
            "csat_comprehension",
            "csat_quant",
        ],
        duration_minutes=120,
        default_daily_hours=7.0,
        has_csat=True,
        has_answer_writing=True,
        has_negative_marking=True,
        negative_marking_ratio=0.33,
        marking_scheme={
            "prelims_gs_correct": 2.0,
            "prelims_gs_negative": 0.66,
            "prelims_csat_correct": 2.5,
            "prelims_csat_negative": 0.83,
            "csat_qualifying_percentage": 33.33,
            "mains_10_marker_word_limit": 150,
            "mains_15_marker_word_limit": 250,
        },
        language_options=["English", "Hindi"],
    )
