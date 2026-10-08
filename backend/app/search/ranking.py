from typing import List, Dict, Any

class SearchResultRanker:
    """
    Ranks, merges, deduplicates, and diversifies candidates from semantic
    and keyword retrieval pipelines.
    """

    def merge_hybrid(
        self,
        semantic_results: List[Dict[str, Any]],
        keyword_results: List[Dict[str, Any]],
        alpha: float = 0.7,
        top_k: int = 8,
    ) -> List[Dict[str, Any]]:
        """
        Combines semantic and keyword lists with score interpolation:
        score = alpha * semantic_score + (1 - alpha) * keyword_score
        """
        combined: Dict[str, Dict[str, Any]] = {}

        # 1. Add semantic results
        for item in semantic_results:
            cid = item["chunk_id"]
            entry = dict(item)
            entry["similarity"] = round(float(alpha * item["similarity"]), 4)
            entry["score_type"] = "hybrid"
            combined[cid] = entry

        # 2. Blend keyword results
        for item in keyword_results:
            cid = item["chunk_id"]
            kw_contrib = (1.0 - alpha) * item["similarity"]
            if cid in combined:
                combined[cid]["similarity"] = round(float(combined[cid]["similarity"] + kw_contrib), 4)
            else:
                entry = dict(item)
                entry["similarity"] = round(float(kw_contrib), 4)
                entry["score_type"] = "hybrid"
                combined[cid] = entry

        results = list(combined.values())
        results.sort(key=lambda x: x["similarity"], reverse=True)
        return self.diversify_and_deduplicate(results, top_k=top_k)

    def diversify_and_deduplicate(
        self,
        results: List[Dict[str, Any]],
        top_k: int = 8,
        max_per_section: int = 2,
    ) -> List[Dict[str, Any]]:
        """
        Removes exact duplicates and prevents one section/page from dominating
        all top slots, ensuring context diversity across documents and topics.
        """
        seen_ids = set()
        section_counts: Dict[str, int] = {}
        filtered: List[Dict[str, Any]] = []

        for item in results:
            cid = item["chunk_id"]
            if cid in seen_ids:
                continue

            sec_key = f"{item['document_id']}_{item.get('section_title') or 'default'}"
            current_sec_count = section_counts.get(sec_key, 0)

            # Allow if under max_per_section or if we still have low candidate count
            if current_sec_count < max_per_section or len(filtered) + (len(results) - len(filtered)) <= top_k:
                seen_ids.add(cid)
                section_counts[sec_key] = current_sec_count + 1
                filtered.append(item)

            if len(filtered) >= top_k:
                break

        # If strict section capping left us with fewer than top_k, backfill with remaining
        if len(filtered) < top_k:
            for item in results:
                if item["chunk_id"] not in seen_ids:
                    seen_ids.add(item["chunk_id"])
                    filtered.append(item)
                    if len(filtered) >= top_k:
                        break

        return filtered
