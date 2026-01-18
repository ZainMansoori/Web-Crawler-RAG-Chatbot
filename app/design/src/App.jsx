import { useState } from 'react'

function App() {
  // Ingest state
  const [domainUrl, setDomainUrl] = useState('')
  const [isIngesting, setIsIngesting] = useState(false)
  const [ingestResult, setIngestResult] = useState(null)
  const [ingestError, setIngestError] = useState(null)

  // Query state
  const [question, setQuestion] = useState('')
  const [isQuerying, setIsQuerying] = useState(false)
  const [answer, setAnswer] = useState(null)
  const [queryError, setQueryError] = useState(null)

  const handleIngest = async (e) => {
    e.preventDefault()
    
    if (!domainUrl.trim()) {
      setIngestError('Please enter a domain URL')
      return
    }

    setIsIngesting(true)
    setIngestError(null)
    setIngestResult(null)

    try {
      const response = await fetch('/ingest', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ url: domainUrl }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setIngestResult(data)
    } catch (error) {
      setIngestError(error.message || 'Failed to ingest domain')
    } finally {
      setIsIngesting(false)
    }
  }

  const handleQuery = async (e) => {
    e.preventDefault()
    
    if (!question.trim()) {
      setQueryError('Please enter a question')
      return
    }

    setIsQuerying(true)
    setQueryError(null)
    setAnswer(null)

    try {
      const response = await fetch('/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ q: question }),
      })

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data = await response.json()
      setAnswer(data.answer)
    } catch (error) {
      setQueryError(error.message || 'Failed to get answer')
    } finally {
      setIsQuerying(false)
    }
  }

  return (
    <div className="container">
      <header className="header">
        <h1>Hybrid RAG Chatbot</h1>
        <p>Ingest domain content and ask questions</p>
      </header>

      <div className="content">
        {/* Ingest Section */}
        <section className="card">
          <h2>Ingest Domain</h2>
          <p className="description">
            Enter a domain URL to crawl and index its content
          </p>
          
          <form onSubmit={handleIngest} className="form">
            <div className="input-group">
              <input
                type="text"
                value={domainUrl}
                onChange={(e) => setDomainUrl(e.target.value)}
                placeholder="example.com or https://example.com"
                disabled={isIngesting}
                className="input"
              />
              <button 
                type="submit" 
                disabled={isIngesting}
                className="button"
              >
                {isIngesting ? 'Processing...' : 'Ingest'}
              </button>
            </div>
          </form>

          {isIngesting && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Crawling and indexing domain... This may take a few minutes.</p>
            </div>
          )}

          {ingestError && (
            <div className="error">
              <strong>Error:</strong> {ingestError}
            </div>
          )}

          {ingestResult && (
            <div className="result">
              <h3>Ingestion Complete</h3>
              <div className="stats">
                <div className="stat-item">
                  <span className="stat-label">Domain:</span>
                  <span className="stat-value">{ingestResult.domain}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Pages Processed:</span>
                  <span className="stat-value">{ingestResult.pages_processed}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Pages Failed:</span>
                  <span className="stat-value">{ingestResult.pages_failed}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Chunks Indexed:</span>
                  <span className="stat-value">{ingestResult.chunks_indexed}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Chunks Skipped:</span>
                  <span className="stat-value">{ingestResult.chunks_skipped}</span>
                </div>
                <div className="stat-item">
                  <span className="stat-label">Deduplication Rate:</span>
                  <span className="stat-value">{ingestResult.deduplication_rate}</span>
                </div>
              </div>
            </div>
          )}
        </section>

        {/* Query Section */}
        <section className="card">
          <h2>Ask Questions</h2>
          <p className="description">
            Ask questions about the indexed content
          </p>
          
          <form onSubmit={handleQuery} className="form">
            <div className="input-group">
              <input
                type="text"
                value={question}
                onChange={(e) => setQuestion(e.target.value)}
                placeholder="What would you like to know?"
                disabled={isQuerying}
                className="input"
              />
              <button 
                type="submit" 
                disabled={isQuerying}
                className="button"
              >
                {isQuerying ? 'Asking...' : 'Ask'}
              </button>
            </div>
          </form>

          {isQuerying && (
            <div className="loading">
              <div className="spinner"></div>
              <p>Getting answer...</p>
            </div>
          )}

          {queryError && (
            <div className="error">
              <strong>Error:</strong> {queryError}
            </div>
          )}

          {answer && (
            <div className="answer">
              <h3>Answer</h3>
              <p>{answer}</p>
            </div>
          )}
        </section>
      </div>
    </div>
  )
}

export default App
