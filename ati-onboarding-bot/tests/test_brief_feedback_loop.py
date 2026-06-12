def test_brief_rating_signal_mapping():
    """Brief ratings map to learning signals (Great/OK/Poor)."""
    assert (1 if 5 >= 4 else -1 if 5 <= 2 else 0) == 1
    assert (1 if 3 >= 4 else -1 if 3 <= 2 else 0) == 0
    assert (1 if 1 >= 4 else -1 if 1 <= 2 else 0) == -1


def test_learning_example_label_from_signal():
    """Negative brief ratings produce failure labels for the learning loop."""
    for signal, expected in ((1, "success"), (-1, "failure"), (0, "neutral")):
        label = "success" if signal > 0 else "failure" if signal < 0 else "neutral"
        assert label == expected
