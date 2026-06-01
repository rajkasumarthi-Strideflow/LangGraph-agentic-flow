from uuid import uuid4


def generate_correlation_id() -> str:
    return f"corr_{uuid4().hex[:8]}"
