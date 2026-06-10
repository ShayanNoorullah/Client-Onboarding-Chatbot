from app.agent.term_glossary import expand_terms


def test_expand_genz():
    result = expand_terms("Our audience is genz")
    assert "Generation Z" in result
    assert "genz" in result.lower()


def test_expand_no_match():
    assert expand_terms("Corporate website") == "Corporate website"
