import os
from dotenv import load_dotenv
from loguru import logger
from pinecone import Pinecone, ServerlessSpec
from pinecone_text.sparse import BM25Encoder
from langchain_huggingface import HuggingFaceEmbeddings
from app.service.diff import hash_text

load_dotenv(".env")

INDEX_NAME = os.getenv("PINECONE_INDEX", "hybrid-rag-chatbot")
BM25_PATH = os.getenv("BM25_PATH", "bm25_values.json")
EMBED_MODEL = os.getenv("EMBED_MODEL", "all-MiniLM-L6-v2")


def get_pinecone_index():
    api_key = os.getenv("PINECONE_API")
    if not api_key:
        raise ValueError("PINECONE_API env var is required")
    pc = Pinecone(api_key=api_key)
    if INDEX_NAME not in pc.list_indexes().names():
        pc.create_index(
            name=INDEX_NAME,
            dimension=384,
            metric="dotproduct",
            spec=ServerlessSpec(cloud="aws", region="us-east-1"),
        )
        logger.info(f"Index {INDEX_NAME} created successfully")
    return pc.Index(INDEX_NAME)


def get_embedder():
    return HuggingFaceEmbeddings(model_name=EMBED_MODEL)


def get_bm25_encoder():
    encoder = BM25Encoder().default()
    if os.path.exists(BM25_PATH):
        try:
            encoder.load(BM25_PATH)
        except Exception as exc:
            logger.warning(f"Failed to load BM25 values: {exc}")
    return encoder


def save_bm25_encoder(encoder):
    try:
        encoder.dump(BM25_PATH)
    except Exception as exc:
        logger.warning(f"Failed to save BM25 values: {exc}")


def get_existing_hashes(index, url, embedder, top_k=1000):
    try:
        query_vec = embedder.embed_query(url)
        res = index.query(
            vector=query_vec,
            top_k=top_k,
            include_metadata=True,
            filter={"url": {"$eq": url}},
        )
        matches = res.get("matches", []) if isinstance(res, dict) else res.matches
        hashes = {m["metadata"].get("chunk_hash") for m in matches if m.get("metadata")}
        return {h for h in hashes if h}
    except Exception as exc:
        logger.warning(f"Failed to fetch existing hashes: {exc}")
        return set()


def upsert_chunks(index, url, chunks_with_hash, embedder, bm25_encoder):
    if not chunks_with_hash:
        return 0
    texts = [chunk for _, chunk, _ in chunks_with_hash]
    dense_vectors = [embedder.embed_query(text) for text in texts]
    sparse_vectors = bm25_encoder.encode_documents(texts)

    vectors = []
    for (i, text, h), dense_vec, sparse_vec in zip(
        chunks_with_hash, dense_vectors, sparse_vectors
    ):
        vectors.append(
            {
                "id": f"{url}#c{i}",
                "values": dense_vec,
                "sparse_values": sparse_vec,
                "metadata": {
                    "url": url,
                    "chunk_hash": h,
                    "position": i,
                    "context": text,
                },
            }
        )
    index.upsert(vectors=vectors)
    return len(vectors)
