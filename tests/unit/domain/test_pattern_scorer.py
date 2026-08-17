from domain.logic.pattern_scorer import score

def test_score():
    params = {"Hb": 120, "MCV": 80, "Ferritin": 10}
    rules = {"Hb": 2, "MCV": 1, "Ferritin": 3}
    assert score(params, rules) == 6  # 2+1+3

def test_score_missing_param():
    params = {"Hb": 120}
    rules = {"Hb": 2, "MCV": 1}
    assert score(params, rules) == 2