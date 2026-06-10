"""Expand audience/industry slang for SLM and requirement storage."""

TERM_GLOSSARY: dict[str, str] = {
    "gen z": "Generation Z (born ~1997–2012), digital-native audience",
    "genz": "Generation Z (born ~1997–2012), digital-native audience",
    "gen-z": "Generation Z (born ~1997–2012), digital-native audience",
    "gen y": "Millennials / Generation Y (born ~1981–1996)",
    "geny": "Millennials / Generation Y (born ~1981–1996)",
    "millennials": "Millennials / Generation Y (born ~1981–1996)",
    "gen x": "Generation X (born ~1965–1980)",
    "genx": "Generation X (born ~1965–1980)",
    "boomers": "Baby Boomers (born ~1946–1964)",
    "b2b": "Business-to-business customers",
    "b2c": "Business-to-consumer / end users",
    "smb": "Small and medium-sized businesses",
    "sme": "Small and medium enterprises",
    "mvp": "Minimum viable product — core features for first launch",
    "saas": "Software as a Service subscription product",
}


def expand_terms(text: str) -> str:
    """Append glossary expansions when known terms appear in user text."""
    if not text:
        return text
    lower = text.lower()
    expansions: list[str] = []
    for term, meaning in TERM_GLOSSARY.items():
        if term in lower and meaning not in expansions:
            expansions.append(f"{term!r} → {meaning}")
    if not expansions:
        return text
    return f"{text}\n[Term context: {'; '.join(expansions)}]"
