from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from urllib.parse import urlparse
from app.service.crawler import fetch_html
from app.service.cleaner import clean_html
from app.service.chunking import chunk_text
from app.service.diff import diff_chunks
from app.service.index_config import (
    get_bm25_encoder,
    get_embedder,
    get_existing_hashes,
    get_pinecone_index,
    save_bm25_encoder,
    upsert_chunks,
)
from app.query.retriever import query

app = FastAPI()


class IngestRequest(BaseModel):
    url: str


class QueryRequest(BaseModel):
    q: str

@app.post("/ingest")
def ingest(payload: IngestRequest):
    url = payload.url.strip()
    if not urlparse(url).scheme:
        url = f"https://{url}"
    html = fetch_html(url)
    data = clean_html(html)
    paragraphs = data.get("paragraphs", [])
    if not isinstance(paragraphs, list):
        raise HTTPException(status_code=400, detail="Invalid paragraphs format")
    chunks = chunk_text(paragraphs)
    if not chunks:
        return {"status": "no_content", "indexed": 0}

    index = get_pinecone_index()
    embedder = get_embedder()
    bm25_encoder = get_bm25_encoder()
    bm25_encoder.fit(chunks)
    save_bm25_encoder(bm25_encoder)

    existing_hashes = get_existing_hashes(index, url, embedder)
    to_upsert = diff_chunks(chunks, existing_hashes)
    indexed = upsert_chunks(index, url, to_upsert, embedder, bm25_encoder)
    return {"status": "indexed", "indexed": indexed, "skipped": len(chunks) - indexed}

@app.post("/query")
def ask(payload: QueryRequest):
    return {"answer": query(payload.q)}
