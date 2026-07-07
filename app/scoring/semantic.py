"""
Optional semantic similarity helper — a fallback signal for near-miss terms
the LLM's own JSON extraction didn't already unify into a shared capability
(e.g. resume says "Docker", JD says "containerization").

This is NOT infrastructure. It's a handful of cosine_similarity(embed(a), embed(b))
calls on short strings, used only as a tiebreaker in scoring/engine.py after the
LLM-based literal/capability matching has already run.

IMPORTANT: sentence-transformers (and its torch dependency) is heavy and slow to
import. It is deliberately NOT imported at module load time — only inside
get_embedder(), the first time it's actually needed. This means the app boots
and every other scoring category works fine even if this package was never
installed, as requirements.txt marks it optional.
"""
import logging
from functools import lru_cache

logger = logging.getLogger(__name__)

_DEFAULT_MODEL_NAME = "all-MiniLM-L6-v2"  # small, fast, good enough for short skill/tool terms


class SemanticScoringUnavailable(Exception):
    """Raised when sentence-transformers isn't installed. Callers should catch
    this and simply skip the semantic fallback — it's optional, never required."""


@lru_cache
def _get_embedder(model_name: str = _DEFAULT_MODEL_NAME):
    """
    Lazily import and cache a SentenceTransformer model. Cached so repeated
    calls within a process don't reload the model from disk each time.
    """
    try:
        from sentence_transformers import SentenceTransformer
    except ImportError as e:
        raise SemanticScoringUnavailable(
            "sentence-transformers is not installed. "
            "Install with: pip install sentence-transformers torch"
        ) from e

    logger.info(f"Loading sentence-transformers model '{model_name}' for semantic scoring.")
    return SentenceTransformer(model_name)


def is_available() -> bool:
    """Cheap check callers can use to skip semantic scoring entirely without
    triggering the (slow) import/model-load path."""
    try:
        import sentence_transformers  # noqa: F401
        return True
    except ImportError:
        return False


def cosine_similarity(term_a: str, term_b: str) -> float:
    """
    Return cosine similarity in [-1.0, 1.0] (in practice ~[0, 1] for short
    natural-language terms) between two short strings.

    Raises SemanticScoringUnavailable if the optional dependency isn't installed —
    callers in scoring/engine.py should catch this and treat it as "no semantic
    fallback available", never as a hard failure.
    """
    import numpy as np

    embedder = _get_embedder()
    vectors = embedder.encode([term_a, term_b], normalize_embeddings=True)
    # Vectors are already L2-normalized, so cosine similarity is just the dot product.
    return float(np.dot(vectors[0], vectors[1]))


def find_best_semantic_match(
    query_term: str,
    candidate_terms: list[str],
    threshold: float = 0.55,
) -> tuple[str, float] | None:
    """
    Given a JD term with no literal or LLM-capability match, check it against
    a resume's candidate terms (technical_skills/tools/inferred_capabilities)
    using embedding similarity. Returns (best_matching_term, score) if the best
    match clears `threshold`, else None.

    This is intentionally a small, single-purpose function — scoring/engine.py
    calls this only for the specific unmatched terms left over after literal
    and LLM-capability matching, not as a bulk operation over every term pair.
    """
    if not candidate_terms:
        return None

    embedder = _get_embedder()
    all_terms = [query_term] + candidate_terms
    vectors = embedder.encode(all_terms, normalize_embeddings=True)

    query_vec = vectors[0]
    best_term = None
    best_score = -1.0

    for term, vec in zip(candidate_terms, vectors[1:]):
        score = float(query_vec @ vec)
        if score > best_score:
            best_score = score
            best_term = term

    if best_term is not None and best_score >= threshold:
        return best_term, best_score
    return None