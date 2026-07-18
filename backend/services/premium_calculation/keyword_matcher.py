"""Rule-based keyword matching for premium field labels."""

from typing import List, Tuple


def _normalize(text: str) -> str:
    return " ".join(str(text or "").lower().split())


def keyword_match_score(cell_text: str, keywords: List[str]) -> Tuple[float, str]:
    """
    Return (score 0..1, matched_keyword).

    Scoring:
    - exact keyword equality: 1.0
    - cell contains full keyword phrase: 0.90
    - keyword contains cell (short labels like TSI): 0.80
    - token overlap / partial: up to 0.70
    """
    text = _normalize(cell_text)
    if not text:
        return 0.0, ""

    best_score = 0.0
    best_keyword = ""

    for keyword in keywords:
        key = _normalize(keyword)
        if not key:
            continue

        score = 0.0

        if text == key:
            score = 1.0
        elif key in text:
            # Prefer tighter containment (keyword length vs cell length)
            ratio = len(key) / max(len(text), 1)
            score = 0.75 + 0.15 * min(ratio, 1.0)
        elif text in key and len(text) >= 3:
            score = 0.80
        else:
            text_tokens = set(text.replace("/", " ").replace("-", " ").split())
            key_tokens = set(key.replace("/", " ").replace("-", " ").split())
            if text_tokens and key_tokens:
                overlap = len(text_tokens & key_tokens) / len(key_tokens)
                if overlap >= 0.5:
                    score = 0.45 + 0.25 * overlap

        if score > best_score:
            best_score = score
            best_keyword = keyword

    return best_score, best_keyword
