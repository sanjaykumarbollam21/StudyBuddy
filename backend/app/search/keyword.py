import re
import math
from typing import List, Dict, Any

class KeywordSearchEngine:
    """
    Lexical keyword search engine.
    Boosts exact technical terms, acronyms (e.g. TCP, SQL, OS, ACID),
    and exact phrase matches alongside term frequency scoring.
    """

    def _tokenize(self, text: str) -> List[str]:
        cleaned = re.sub(r"[^\w\s]", " ", text.lower())
        return [t for t in cleaned.split() if len(t) > 1]

    def _extract_acronyms(self, text: str) -> List[str]:
        # Identify uppercase words of length 2-6 (e.g. TCP, HTTP, SQL, ACID, CPU)
        return re.findall(r"\b[A-Z]{2,6}\b", text)

    def score_chunk(self, query: str, chunk_content: str) -> float:
        query_tokens = self._tokenize(query)
        if not query_tokens:
            return 0.0

        content_lower = chunk_content.lower()
        chunk_tokens = self._tokenize(chunk_content)
        if not chunk_tokens:
            return 0.0

        score = 0.0

        # 1. Exact phrase match bonus
        if query.lower() in content_lower:
            score += 0.4

        # 2. Token overlap & term frequency
        matches = 0
        for token in query_tokens:
            count = content_lower.count(token)
            if count > 0:
                matches += 1
                score += min(0.3, 0.05 * math.log1p(count))

        # Percentage of query tokens matched
        token_coverage = matches / len(query_tokens)
        score += 0.3 * token_coverage

        # 3. Technical acronym / capitalized term boost
        acronyms = self._extract_acronyms(query)
        for acr in acronyms:
            if re.search(r"\b" + re.escape(acr) + r"\b", chunk_content, re.IGNORECASE):
                score += 0.2

        return min(1.0, round(score, 4))

    def search(
        self,
        query: str,
        candidates: List[Dict[str, Any]],
        top_k: int = 8,
    ) -> List[Dict[str, Any]]:
        scored = []
        for cand in candidates:
            score = self.score_chunk(query, cand["content"])
            if score > 0.05:
                item = dict(cand)
                item["similarity"] = score
                item["score_type"] = "keyword"
                scored.append(item)

        scored.sort(key=lambda x: x["similarity"], reverse=True)
        return scored[:top_k]
