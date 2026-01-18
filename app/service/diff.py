import hashlib

def hash_text(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


def diff_chunks(new_chunks, existing_hashes):
    to_upsert = []
    for idx, chunk in enumerate(new_chunks):
        h = hash_text(chunk)
        if h not in existing_hashes:
            to_upsert.append((idx, chunk, h))
    return to_upsert