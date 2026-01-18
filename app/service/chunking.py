def chunk_text(paragraphs, max_chars=800):
    chunks, current = [], ""
    for p in paragraphs:
        if not p:
            continue
        if len(current) + len(p) < max_chars:
            current = f"{current} {p}".strip()
        else:
            chunks.append(current.strip())
            current = p
    if current:
        chunks.append(current.strip())
    return chunks
