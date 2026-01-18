<p align="center">
  <a href="https://github.com/ZainMansoori/Web-Crawler-RAG-Chatbot">
    <img src="https://img.shields.io/github/stars/ZainMansoori/Web-Crawler-RAG-Chatbot?style=social" alt="GitHub Stars">
  </a>
  <a href="https://github.com/ZainMansoori/Web-Crawler-RAG-Chatbot/fork">
    <img src="https://img.shields.io/github/forks/ZainMansoori/Web-Crawler-RAG-Chatbot?style=social" alt="GitHub Forks">
  </a>
  <a href="https://github.com/ZainMansoori/Web-Crawler-RAG-Chatbot/commits/main">
    <img src="https://img.shields.io/github/commit-activity/m/ZainMansoori/Web-Crawler-RAG-Chatbot" alt="GitHub Commits">
  </a>
</p>

# Hybrid RAG Chatbot (Web Crawler + Hybrid Search)

This project ingests a website (domain) by crawling it (or reading its sitemap), extracts readable content, chunks it, and indexes it into **Pinecone** using **hybrid retrieval**:

- **Dense vectors** (semantic search via embeddings)
- **Sparse vectors** (keyword search via BM25)

Then you can ask questions against the indexed content via an API.

---

## Features

- **Domain ingestion**: Provide `example.com` and the system crawls internal pages only.
- **Sitemap-first strategy**: Tries common sitemap locations and `robots.txt` discovery before crawling.
- **Internal-link only crawling**: Follows same-domain `<a href="...">` links and skips outbound links.
- **AI HTML cleaning**: Uses Gemini to extract main readable content (title + paragraphs).
- **Chunking + deduplication**: Content is chunked and hashed (SHA-256) to avoid re-indexing duplicates.
- **Hybrid indexing**: Upserts both dense + sparse vectors into Pinecone.
- **API + minimal UI**: FastAPI backend + a minimal React UI (Vite) under `app/design/`.

---

## Project Structure

```
.
├── main.py                     # FastAPI app (POST /ingest, POST /query)
├── requirements.txt            # Python deps
└── app/
    ├── design/                 # Minimal React (Vite) frontend
    ├── query/                  # Retriever logic
    └── service/                # Crawling, sitemap, cleaning, chunking, hashing, pinecone
```

---

## API Endpoints

### POST `/ingest`

Ingests a domain by sitemap or crawling.

**Request**

```json
{ "url": "webflicky.com" }
```

**Response (example)**

```json
{
  "status": "completed",
  "domain": "https://webflicky.com",
  "pages_processed": 25,
  "pages_failed": 2,
  "chunks_indexed": 180,
  "chunks_skipped": 45,
  "deduplication_rate": "20.0%"
}
```

### POST `/query`

Ask a question against the indexed content.

**Request**

```json
{ "q": "What is this site about?" }
```

**Response**

```json
{ "answer": "..." }
```

---

## How Crawling Works

### Sitemap discovery

Implemented in `app/service/sitemap.py`.

It tries:
- `robots.txt` → `Sitemap:` entries
- Common sitemap paths:
  - `/sitemap.xml`
  - `/sitemap_index.xml`
  - `/sitemap`
  - `/sitemap.php`
  - `/sitemap.txt`
  - `/sitemap1.xml`

It also supports sitemap indexes that reference multiple sitemap files.

### Domain crawling (fallback)

Implemented in `app/service/domain_crawler.py` using BFS:
- Maintains a `visited` set
- Uses `extract_internal_links()` to enqueue same-domain links only
- Stops at `max_pages` limit

Internal link extraction is in `app/service/link_extractor.py` and filters by netloc (domain).

---

## Cleaning, Chunking, and Deduplication

### Cleaning (Gemini)

`app/service/cleaner.py` sends HTML to Gemini and expects **JSON only**:
- `title`
- `paragraphs` (ordered list of strings)

### Chunking

`app/service/chunking.py` combines paragraphs into ~800-character chunks.
If a single paragraph is larger than the limit, it is split at **word boundaries**.

It logs chunk stats (count, min/max/avg length) and warns if chunks become unusually large.

### Hashing + dedupe

`app/service/diff.py`:
- Hashes each chunk with **SHA-256**
- Compares hashes vs existing hashes stored in Pinecone metadata
- Only upserts chunks whose hashes do **not** already exist

This avoids duplicate indexing when you ingest the same domain again.

---

## Pinecone Hybrid Indexing

`app/service/index_config.py`:
- Dense embeddings via `langchain_huggingface.HuggingFaceEmbeddings`
- Sparse vectors via `pinecone_text.sparse.BM25Encoder`
- Upserts into Pinecone with metadata:
  - `url`
  - `chunk_hash`
  - `position`
  - `context`
  - `chunk_length`

---

## Environment Variables

Create a `.env` in the repo root.

### Required (backend)

```
PINECONE_API=...
PINECONE_INDEX=...
EMBED_MODEL=all-MiniLM-L6-v2

GEMINI_API_KEY=...
GEMINI_MODEL=...
```

### Optional / recommended

```
BM25_PATH=bm25_values.json
VITE_URL=http://localhost:5173
```

Notes:
- `VITE_URL` is used for backend CORS allowlist (see `main.py`).
- `bm25_values.json` is persisted locally; consider ignoring it in git.

---

## Run Locally (Backend)

1) Create and activate a virtual environment.

2) Install dependencies:

```bash
pip install -r requirements.txt
```

3) Start the API:

```bash
uvicorn main:app --reload
```

Backend runs at:
- `http://localhost:8000`
- Docs: `http://localhost:8000/docs`

---

## Run Locally (Frontend)

Frontend lives in `app/design/`.

```bash
cd app/design
npm install
npm run dev
```

Frontend runs at:
- `http://localhost:5173`

---


### Common deployment pitfalls

- **Frontend calling `/ingest` in production**: If UI and API are on different domains, you must use a full backend URL in the frontend. If you deploy both on the same domain (recommended here), `/ingest` works.
- **CORS errors**: Set `VITE_URL` to your deployed frontend origin, or allow multiple origins.

---

## Logging

The backend uses `loguru` heavily for:
- sitemap discovery
- crawl progress
- chunking stats
- dedupe stats
- upsert progress

Watch the server logs while running ingestion for visibility.

---

## Security Notes

- Never commit `.env`
- API keys (Pinecone, Gemini) must be stored as environment variables

## 🧑‍💻 Author
Zain Mansoori – Python Developer | Automation Specialist

🔗 GitHub: https://github.com/ZainMansoori

LinkedIn:  https://www.linkedin.com/in/zain-mansoori-python-developer/
