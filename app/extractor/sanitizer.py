import hashlib


def build_content_hash(normalized_url: str, plain_text: str) -> str:
    digest = hashlib.sha256()
    digest.update(normalized_url.encode("utf-8"))
    digest.update(b"\n")
    digest.update(plain_text.encode("utf-8"))
    return digest.hexdigest()
