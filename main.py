from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from urllib.parse import urlparse
from loguru import logger
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
from app.service.domain_crawler import crawl_domain
from app.service.sitemap import fetch_all_sitemap_urls


app = FastAPI()

# Add CORS middleware for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IngestRequest(BaseModel):
    url: str


class QueryRequest(BaseModel):
    q: str

@app.post("/ingest")
def ingest(payload: IngestRequest):
    """
    Ingest content from a domain by crawling or using sitemap.
    Processes HTML, chunks content, and indexes to Pinecone with deduplication.
    """
    root_url = payload.url.strip()
    if not urlparse(root_url).scheme:
        root_url = f"https://{root_url}"
    
    logger.info(f"Starting ingestion for domain: {root_url}")

    # Initialize index and encoders
    try:
        index = get_pinecone_index()
        embedder = get_embedder()
        bm25_encoder = get_bm25_encoder()
        logger.success("Successfully initialized Pinecone index and encoders")
    except Exception as exc:
        logger.error(f"Failed to initialize services: {exc}")
        raise HTTPException(status_code=500, detail=f"Initialization error: {str(exc)}")

    total_indexed = 0
    total_skipped = 0
    total_pages = 0
    failed_pages = 0

    # Try to fetch URLs from sitemap first
    logger.info("Attempting to fetch URLs from sitemap...")
    sitemap_urls = fetch_all_sitemap_urls(root_url)

    if sitemap_urls:
        # Path 1: Use sitemap URLs
        logger.success(f"Found {len(sitemap_urls)} URLs in sitemap")
        urls_source = sitemap_urls
        
        for url in urls_source:
            total_pages += 1
            logger.info(f"Processing [{total_pages}/{len(sitemap_urls)}]: {url}")
            
            try:
                html = fetch_html(url)
            except Exception as exc:
                logger.warning(f"Failed to fetch {url}: {exc}")
                failed_pages += 1
                continue

            try:
                data = clean_html(html)
                paragraphs = data.get("paragraphs", [])
                logger.debug(f"Extracted {len(paragraphs)} paragraphs from {url}")
                
                chunks = chunk_text(paragraphs)

                if not chunks:
                    logger.warning(f"No chunks created for {url}")
                    continue

                bm25_encoder.fit(chunks)

                existing_hashes = get_existing_hashes(index, url, embedder)
                to_upsert = diff_chunks(chunks, existing_hashes)
                indexed = upsert_chunks(index, url, to_upsert, embedder, bm25_encoder)

                total_indexed += indexed
                total_skipped += len(chunks) - indexed
            except Exception as exc:
                logger.error(f"Error processing {url}: {exc}")
                failed_pages += 1
                continue
    else:
        # Path 2: Fallback to manual crawling
        logger.info("No sitemap found, falling back to manual crawling (max 50 pages)")
        
        for url, html in crawl_domain(root_url, max_pages=50):
            total_pages += 1
            logger.info(f"Processing crawled page [{total_pages}]: {url}")
            
            try:
                data = clean_html(html)
                paragraphs = data.get("paragraphs", [])
                logger.debug(f"Extracted {len(paragraphs)} paragraphs from {url}")
                
                chunks = chunk_text(paragraphs)

                if not chunks:
                    logger.warning(f"No chunks created for {url}")
                    continue

                bm25_encoder.fit(chunks)

                existing_hashes = get_existing_hashes(index, url, embedder)
                to_upsert = diff_chunks(chunks, existing_hashes)
                indexed = upsert_chunks(index, url, to_upsert, embedder, bm25_encoder)

                total_indexed += indexed
                total_skipped += len(chunks) - indexed
            except Exception as exc:
                logger.error(f"Error processing {url}: {exc}")
                failed_pages += 1
                continue

    save_bm25_encoder(bm25_encoder)
    
    # Final summary
    logger.success(f"Ingestion completed for {root_url}")
    logger.info(f"Summary: {total_pages} pages processed, {failed_pages} failed, "
               f"{total_indexed} chunks indexed, {total_skipped} duplicates skipped")

    return {
        "status": "completed",
        "domain": root_url,
        "pages_processed": total_pages,
        "pages_failed": failed_pages,
        "chunks_indexed": total_indexed,
        "chunks_skipped": total_skipped,
        "deduplication_rate": f"{(total_skipped / (total_indexed + total_skipped) * 100):.1f}%" if (total_indexed + total_skipped) > 0 else "0%"
    }


@app.post("/query")
def ask(payload: QueryRequest):
    return {"answer": query(payload.q)}
