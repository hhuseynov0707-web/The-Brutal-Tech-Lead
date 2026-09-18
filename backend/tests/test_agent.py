import pytest

from app.agent import AgentError, parse_evaluation


def test_parses_plain_json():
    ev = parse_evaluation('{"response": "Wrong.", "tech_score": 20, "stress_score": 80}')
    assert ev.response == "Wrong." and ev.tech_score == 20 and ev.stress_score == 80


def test_parses_fenced_json_with_prose():
    raw = 'Here you go:\n```json\n{"response": "Meh", "tech_score": "55", "stress_score": 10}\n```'
    ev = parse_evaluation(raw)
    assert ev.tech_score == 55


def test_extracts_json_embedded_in_text():
    ev = parse_evaluation('Sure! {"response": "Ok", "tech_score": 60, "stress_score": 30} bye')
    assert ev.response == "Ok"


def test_clamps_out_of_range_scores():
    ev = parse_evaluation('{"response": "x", "tech_score": 150, "stress_score": -5}')
    assert (ev.tech_score, ev.stress_score) == (100, 0)


@pytest.mark.parametrize("raw", ["not json", '{"tech_score": 10}', '{"response": ""}'])
def test_rejects_invalid_replies(raw):
    with pytest.raises(AgentError):
        parse_evaluation(raw)
