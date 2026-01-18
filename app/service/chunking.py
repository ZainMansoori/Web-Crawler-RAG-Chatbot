from loguru import logger

def chunk_text(paragraphs, max_chars=800):
    """
    Split paragraphs into chunks of approximately max_chars size.
    Handles oversized paragraphs by splitting them at word boundaries.
    
    Args:
        paragraphs: List of paragraph strings
        max_chars: Maximum characters per chunk (default: 800)
    
    Returns:
        List of text chunks with validation
    """
    chunks, current, oversized_count = [], "", 0

    for p in paragraphs:
        if not p:
            continue
        
        # Handle oversized paragraphs
        if len(p) > max_chars:
            oversized_count += 1
            logger.debug(f"Handling oversized paragraph: {len(p)} chars")
            
            # Save current chunk if exists
            if current:
                chunks.append(current.strip())
                current = ""
            
            # Split large paragraph into smaller chunks at word boundaries
            words = p.split()
            for word in words:
                if len(current) + len(word) + 1 > max_chars:
                    if current:  # Avoid empty chunks
                        chunks.append(current.strip())
                    current = word
                else:
                    current = f"{current} {word}".strip()
        elif len(current) + len(p) + 1 < max_chars:
            current = f"{current} {p}".strip()
        else:
            if current:
                chunks.append(current.strip())
            current = p
    
    if current:
        chunks.append(current.strip())
    
    # Validation and logging
    if chunks:
        chunk_sizes = [len(c) for c in chunks]
        avg_size = sum(chunk_sizes) / len(chunk_sizes)
        max_size = max(chunk_sizes)
        min_size = min(chunk_sizes)
        
        logger.info(f"Created {len(chunks)} chunks | Avg: {avg_size:.0f} chars | "
                   f"Min: {min_size} | Max: {max_size} | Oversized paragraphs: {oversized_count}")
        
        # Warn if any chunk is too large
        for idx, size in enumerate(chunk_sizes):
            if size > max_chars * 1.5:
                logger.warning(f"Chunk {idx} is unusually large: {size} chars (limit: {max_chars})")
    
    return chunks
