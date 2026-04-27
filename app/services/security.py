import re

MAX_LENGTH = 500

BLOCK_PATTERNS = [
    r"<script.*?>.*?</script>",
    r"ignore previous instructions",
    r"system override",
    r"rm -rf",
]

def is_malicious(text: str) -> bool:

    if not text:
        return True

    if len(text) > MAX_LENGTH:
        return True

    text_lower = text.lower()

    for pattern in BLOCK_PATTERNS:

        if re.search(pattern, text_lower):
            return True

    return False