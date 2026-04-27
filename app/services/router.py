def detect_intent(query: str) -> str:
    q = query.lower()

    faq_keywords = ["how long", "what is", "how do i apply", "training", "nurse", "ambulance"]

    if any(k in q for k in faq_keywords):
        return "faq"

    rag_keywords = ["tell me", "explain", "information", "career", "role"]

    if any(k in q for k in rag_keywords):
        return "rag"

    return "llm"