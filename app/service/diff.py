import hashlib
from loguru import logger

def hash_text(text: str) -> str:
    """Generate SHA-256 hash of text for deduplication."""
    return hashlib.sha256(text.encode()).hexdigest()


def diff_chunks(new_chunks, existing_hashes):
    """
    Compare new chunks against existing hashes to find new content.
    
    Args:
        new_chunks: List of chunk texts
        existing_hashes: Set of existing chunk hashes from database
    
    Returns:
        List of tuples (index, chunk_text, hash) for new content only
    """
    to_upsert = []
    duplicate_count = 0
    
    for idx, chunk in enumerate(new_chunks):
        h = hash_text(chunk)
        if h not in existing_hashes:
            to_upsert.append((idx, chunk, h))
        else:
            duplicate_count += 1
            logger.debug(f"Skipping duplicate chunk {idx} (hash: {h[:16]}...)")
    
    # Log deduplication statistics
    total_chunks = len(new_chunks)
    new_chunks_count = len(to_upsert)
    
    if total_chunks > 0:
        duplicate_pct = (duplicate_count / total_chunks) * 100
        logger.info(f"Deduplication: {new_chunks_count} new, {duplicate_count} duplicates "
                   f"({duplicate_pct:.1f}% duplicated)")
    
    return to_upsert