from typing import List, Dict, Any, Optional
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession


class CurrentAffairsService:
    """
    Phase G & H: Current Affairs Intelligence & Static Knowledge Linking Engine.
    Connects dynamic current events (Supreme Court rulings, RBI MPC decisions, COP conferences)
    to static constitutional articles, standard textbook concepts, and prelims/mains dimensions.
    """

    DEFAULT_CURRENT_AFFAIRS = [
        {
            "id": "ca-2026-pol-01",
            "date": "2026-10-05T00:00:00Z",
            "title": "Supreme Court Bench Clarifies Scope of Article 20(3) Against Self-Incrimination in Digital Device Searches",
            "category": "polity",
            "summary": "The Supreme Court examined constitutional limits on investigative agencies compelling individuals to disclose biometric credentials or passwords during criminal probes without judicial warrants.",
            "background": "Historically governed by the Selvi v. State of Karnataka (2010) precedent regarding involuntary narco-analysis and polygraph tests under Article 20(3).",
            "static_concepts": [
                {"concept": "Article 20(3)", "description": "Protection against self-incrimination"},
                {"concept": "Article 21", "description": "Right to Privacy and informational autonomy (Puttaswamy case)"},
                {"concept": "Doctrine of Proportionality", "description": "Three-fold test for state interference in individual liberty"},
            ],
            "prelims_pointers": [
                "Article 20(3) applies only to criminal proceedings, not civil inquiries.",
                "Immunity extends to personal testimony, but physical evidence (blood, handwriting) is admissible.",
                "Article 20 cannot be suspended even during a National Emergency (Article 359).",
            ],
            "mains_pointers": [
                "Balance between state interests in cyber-investigation and citizen's fundamental right to digital privacy.",
                "Need for standardized digital search protocols aligning police powers with human rights jurisprudence.",
                "Comparative constitutional perspectives (US Fourth & Fifth Amendments vs Indian Constitution).",
            ],
            "source": "The Hindu / Supreme Court Observer",
            "is_cached": True,
        },
        {
            "id": "ca-2026-econ-02",
            "date": "2026-10-04T00:00:00Z",
            "title": "RBI Monetary Policy Committee Maintains Stance on Flexible Inflation Targeting (FIT)",
            "category": "economy",
            "summary": "The MPC kept policy repo rate unchanged, emphasizing sticky food inflation and climate-induced supply volatility while projecting real GDP growth.",
            "background": "The Monetary Policy Committee was established under the RBI Act 1934 (amended in 2016) following recommendations of the Urjit Patel Committee.",
            "static_concepts": [
                {"concept": "Monetary Policy Committee (MPC)", "description": "6-member body with statutory inflation mandate of 4% +/- 2%"},
                {"concept": "Headline vs Core Inflation", "description": "CPI all-inclusive vs CPI excluding food and fuel components"},
                {"concept": "Repo Rate & Liquidity Adjustment Facility", "description": "Key policy rate at which RBI lends short-term funds to banks against government securities"},
            ],
            "prelims_pointers": [
                "MPC has 6 members: 3 from RBI and 3 external members appointed by Central Government.",
                "Governor of RBI acts as ex-officio Chairperson with casting vote in case of a tie.",
                "Target is mandated under Section 45ZA of RBI Act 1934.",
            ],
            "mains_pointers": [
                "Effectiveness of interest rate tools in mitigating supply-side cost-push inflation in developing economies.",
                "Coordination challenges between fiscal stimulus and monetary contraction.",
            ],
            "source": "Reserve Bank of India Press Release / Indian Express",
            "is_cached": True,
        },
        {
            "id": "ca-2026-env-03",
            "date": "2026-10-02T00:00:00Z",
            "title": "New Ramsar Sites Designated in India's Peninsular River Basins",
            "category": "environment",
            "summary": "Three additional wetland complexes have been added to the Ramsar List of Wetlands of International Importance, enhancing conservation frameworks for migratory waterbirds along the Central Asian Flyway.",
            "background": "The Ramsar Convention on Wetlands is an intergovernmental treaty adopted in Ramsar, Iran (1971). India became a contracting party in 1982.",
            "static_concepts": [
                {"concept": "Ramsar Convention (1971)", "description": "Wise use and ecological conservation of wetlands"},
                {"concept": "Montreux Record", "description": "Register of Ramsar wetland sites where ecological changes have occurred, are occurring, or are likely to occur"},
                {"concept": "Wetland Rules 2017", "description": "National decentralised conservation framework for state wetland authorities"},
            ],
            "prelims_pointers": [
                "India currently has over 80 designated Ramsar sites.",
                "Chilika Lake (Odisha) and Keoladeo National Park (Rajasthan) were the first Indian sites designated in 1981.",
                "Montreux Record in India currently includes Loktak Lake (Manipur) and Keoladeo National Park.",
            ],
            "mains_pointers": [
                "Ecological services provided by wetlands: flood buffer, carbon sequestration, and groundwater recharge.",
                "Encroachment, sewage inflow, and real estate pressure undermining urban wetland preservation.",
            ],
            "source": "PIB / Ministry of Environment, Forest and Climate Change",
            "is_cached": True,
        },
    ]

    def __init__(self, db: Optional[AsyncSession] = None):
        self.db = db

    async def get_current_affairs(
        self,
        category: Optional[str] = None,
        limit: int = 15,
    ) -> List[Dict[str, Any]]:
        """
        Retrieves curated current affairs feed with full static concept attributes.
        Supports filtering by competitive exam syllabus domain.
        """
        items = list(self.DEFAULT_CURRENT_AFFAIRS)
        if category:
            items = [item for item in items if item["category"].lower() == category.lower()]
        return items[:limit]

    async def get_feed(self, exam_id: str = "upsc_cse", category: Optional[str] = None, limit: int = 15) -> List[Dict[str, Any]]:
        """Alias for get_current_affairs."""
        return await self.get_current_affairs(category=category, limit=limit)

    def link_event_to_static_syllabus(self, affair_item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Phase H: Connects a dynamic news event to static syllabus curriculum,
        generating prospective Prelims MCQs and Mains analytical answer frameworks.
        """
        static_links = affair_item.get("static_concepts", [])
        title = affair_item.get("title", "")
        category = affair_item.get("category", "general")

        # Synthesize prospective examination angles
        prospective_prelims = [
            f"Statement-based question checking statutory vs constitutional status of {static_links[0]['concept'] if static_links else 'the core concept'}.",
            f"Match the following: Institutions and their statutory mandates highlighted in this development.",
        ]

        prospective_mains = [
            f"Critically analyze the implications of '{title[:60]}...' on constitutional governance and citizen rights. (150 words / 10 marks)",
            f"Discuss the institutional mechanisms required to address the structural issues emerging from this scenario. (250 words / 15 marks)",
        ]

        return {
            "affair_id": affair_item.get("id"),
            "event_title": title,
            "category": category,
            "connected_static_concepts": static_links,
            "prospective_prelims_questions": prospective_prelims,
            "prospective_mains_questions": prospective_mains,
            "pedagogical_advice": "Read the static chapter in your textbook corresponding to these concepts before attempting PYQs on this theme.",
        }
