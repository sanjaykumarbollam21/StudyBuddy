from typing import Dict, List, Optional
from app.exam.profiles.base import ExamProfileDefinition, ExamStageConfig
from app.exam.profiles.upsc import get_upsc_profile


def get_ssc_profile() -> ExamProfileDefinition:
    return ExamProfileDefinition(
        id="ssc_cgl",
        name="Staff Selection Commission Combined Graduate Level (SSC CGL)",
        category="staff_selection",
        conducting_body="Staff Selection Commission",
        stages=[
            ExamStageConfig(
                stage_id="tier_1",
                title="Tier 1 Computer Based Examination",
                description="Objective screening test covering Quant, Reasoning, English, and General Awareness.",
                paper_names=["Tier 1 Composite"],
                has_negative_marking=True,
                negative_marking_ratio=0.25,
            ),
            ExamStageConfig(
                stage_id="tier_2",
                title="Tier 2 Computer Based Examination",
                description="Advanced assessment of Mathematical Abilities, Reasoning, English Language, and General Awareness.",
                paper_names=["Paper 1 Sectional"],
                has_negative_marking=True,
                negative_marking_ratio=0.33,
            ),
        ],
        subjects=["Quantitative Aptitude", "General Intelligence & Reasoning", "English Comprehension", "General Awareness"],
        has_negative_marking=True,
        negative_marking_ratio=0.25,
        default_daily_hours=5.0,
    )


def get_banking_profile() -> ExamProfileDefinition:
    return ExamProfileDefinition(
        id="banking_po",
        name="Banking Probationary Officer (IBPS / SBI PO)",
        category="banking",
        conducting_body="IBPS / SBI",
        stages=[
            ExamStageConfig(
                stage_id="prelims",
                title="Preliminary Examination",
                description="Speed and accuracy test: English, Quantitative Aptitude, Reasoning Ability.",
                paper_names=["Prelims Composite"],
                has_negative_marking=True,
                negative_marking_ratio=0.25,
            ),
            ExamStageConfig(
                stage_id="mains",
                title="Main Examination & Descriptive Test",
                description="Reasoning & Computer, Data Analysis, General/Economy/Banking Awareness, English, Letter/Essay.",
                paper_names=["Mains Objective", "Descriptive English"],
                has_negative_marking=True,
                negative_marking_ratio=0.25,
                is_descriptive=True,
            ),
        ],
        subjects=["Reasoning Ability", "Quantitative Aptitude / Data Interpretation", "English Language", "Banking & Financial Awareness"],
        has_answer_writing=True,
        default_daily_hours=5.0,
    )


def get_gate_profile() -> ExamProfileDefinition:
    return ExamProfileDefinition(
        id="gate",
        name="Graduate Aptitude Test in Engineering (GATE)",
        category="engineering",
        conducting_body="IITs / IISc",
        stages=[
            ExamStageConfig(
                stage_id="cbt",
                title="GATE Computer Based Test",
                description="General Aptitude and Engineering Discipline core papers.",
                paper_names=["General Aptitude", "Technical Discipline"],
                has_negative_marking=True,
                negative_marking_ratio=0.33,
            )
        ],
        subjects=["Engineering Mathematics", "General Aptitude", "Core Discipline Topics"],
        default_daily_hours=5.5,
    )


def get_jee_profile() -> ExamProfileDefinition:
    return ExamProfileDefinition(
        id="jee_main",
        name="Joint Entrance Examination (JEE Main & Advanced)",
        category="engineering",
        conducting_body="NTA / IITs",
        stages=[
            ExamStageConfig(
                stage_id="jee_main",
                title="JEE Main CBT",
                description="Physics, Chemistry, and Mathematics objective and numerical assessment.",
                paper_names=["Paper 1 B.E./B.Tech"],
                has_negative_marking=True,
                negative_marking_ratio=0.25,
            )
        ],
        subjects=["Physics", "Chemistry", "Mathematics"],
        default_daily_hours=7.0,
    )


def get_neet_profile() -> ExamProfileDefinition:
    return ExamProfileDefinition(
        id="neet_ug",
        name="National Eligibility cum Entrance Test (NEET UG)",
        category="medical",
        conducting_body="National Testing Agency (NTA)",
        stages=[
            ExamStageConfig(
                stage_id="exam",
                title="NEET UG Single Stage",
                description="Physics, Chemistry, Botany, Zoology pen-and-paper examination.",
                paper_names=["NEET UG Composite"],
                has_negative_marking=True,
                negative_marking_ratio=0.25,
            )
        ],
        subjects=["Physics", "Chemistry", "Botany", "Zoology"],
        default_daily_hours=7.0,
    )


def get_state_psc_profile() -> ExamProfileDefinition:
    return ExamProfileDefinition(
        id="state_psc",
        name="State Public Service Commission Examination (State PSC)",
        category="civil_services",
        conducting_body="State Public Service Commissions (UPPSC, BPSC, MPSC, TNPSC, etc.)",
        stages=[
            ExamStageConfig(stage_id="prelims", title="State PSC Preliminary", description="General Studies and State Special Paper.", paper_names=["GS Paper 1", "CSAT/State Paper 2"]),
            ExamStageConfig(stage_id="mains", title="State PSC Mains", description="Descriptive papers covering General Studies and State Heritage/Economy.", paper_names=["GS Papers 1-4", "General Hindi/Language"], is_descriptive=True),
        ],
        subjects=["General Studies", "State History & Geography", "State Economy & Current Affairs"],
        has_answer_writing=True,
        default_daily_hours=6.0,
    )


def get_ugc_net_profile() -> ExamProfileDefinition:
    return ExamProfileDefinition(
        id="ugc_net",
        name="UGC National Eligibility Test (UGC NET / JRF)",
        category="teaching",
        conducting_body="National Testing Agency",
        stages=[
            ExamStageConfig(stage_id="exam", title="UGC NET Composite CBT", description="Paper 1 Teaching/Research Aptitude + Paper 2 Subject specialization.", paper_names=["Paper 1 General", "Paper 2 Subject"], has_negative_marking=False)
        ],
        subjects=["Teaching Aptitude", "Research Methodology", "Higher Education System", "Core Subject Specialization"],
        has_negative_marking=False,
        negative_marking_ratio=0.0,
        default_daily_hours=4.0,
    )


def get_custom_profile() -> ExamProfileDefinition:
    return ExamProfileDefinition(
        id="custom_exam",
        name="Custom / College / University Examination",
        category="academic",
        conducting_body="Custom Institution",
        stages=[
            ExamStageConfig(stage_id="final", title="Final Examination", description="User-configured syllabus and examination structure.", paper_names=["Course Exam"], has_negative_marking=False)
        ],
        subjects=["Custom Subject 1", "Custom Subject 2"],
        has_negative_marking=False,
        default_daily_hours=4.0,
    )


class ExamProfileRegistry:
    """
    Central repository of competitive exam profiles.
    Allows easy extensibility without hardcoding exam rules.
    """
    def __init__(self):
        self._profiles: Dict[str, ExamProfileDefinition] = {}
        self._init_default_profiles()

    def _init_default_profiles(self):
        self.register(get_upsc_profile())
        self.register(get_ssc_profile())
        self.register(get_banking_profile())
        self.register(get_gate_profile())
        self.register(get_jee_profile())
        self.register(get_neet_profile())
        self.register(get_state_psc_profile())
        self.register(get_ugc_net_profile())
        self.register(get_custom_profile())

    def register(self, profile: ExamProfileDefinition):
        self._profiles[profile.id] = profile

    def get_profile(self, profile_id: str) -> Optional[ExamProfileDefinition]:
        return self._profiles.get(profile_id)

    def list_all(self) -> List[ExamProfileDefinition]:
        return list(self._profiles.values())

    @classmethod
    def list_all_profiles(cls) -> List[Dict[str, Any]]:
        return [
            {
                "id": p.id,
                "name": p.name,
                "category": p.category,
                "conducting_body": p.conducting_body,
                "stages": [s.stage_id for s in p.stages],
                "subjects": p.subjects,
                "has_negative_marking": p.has_negative_marking,
                "default_daily_hours": p.default_daily_hours,
            }
            for p in _registry_instance.list_all()
        ]

    @classmethod
    def get(cls, profile_id: str) -> Optional[ExamProfileDefinition]:
        return _registry_instance.get_profile(profile_id)


# Global singleton registry
_registry_instance = ExamProfileRegistry()


def get_exam_registry() -> ExamProfileRegistry:
    return _registry_instance
