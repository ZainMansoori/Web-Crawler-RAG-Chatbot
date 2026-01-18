from pinecone_text.hybrid import hybrid_convex_scale
from app.service.index_config import get_bm25_encoder, get_embedder, get_pinecone_index


def query(q: str):
    embedder = get_embedder()
    bm25_encoder = get_bm25_encoder()
    index = get_pinecone_index()

    sparse_vec = bm25_encoder.encode_queries(q)
    dense_vec = embedder.embed_query(q)
    dense_vec, sparse_vec = hybrid_convex_scale(dense_vec, sparse_vec, 0.5)
    sparse_vec["values"] = [float(v) for v in sparse_vec["values"]]

    result = index.query(
        vector=dense_vec,
        sparse_vector=sparse_vec,
        top_k=4,
        include_metadata=True,
    )
    matches = result.get("matches", []) if isinstance(result, dict) else result.matches
    answers = []
    for res in matches:
        metadata = res.get("metadata") or {}
        text = (
            metadata.get("context")
            or metadata.get("text")
            or metadata.get("chunk")
            or ""
        )
        if text:
            answers.append(text)
    return answers
