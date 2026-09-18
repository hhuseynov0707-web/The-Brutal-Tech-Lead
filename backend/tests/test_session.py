import asyncio

from app.schemas import Evaluation, MessageType, Verdict
from app.session import InterviewSession


def make_session(scores, max_turns=8, fail_first=False):
    scores = list(scores)
    state = {"failed": not fail_first}

    async def evaluator(messages):
        if not state["failed"]:
            state["failed"] = True
            raise RuntimeError("boom")
        return Evaluation(response="next", tech_score=scores.pop(0), stress_score=50)

    return InterviewSession(
        role="AI Engineer",
        first_question="Q1?",
        system_message={"role": "system", "content": "sys"},
        evaluator=evaluator,
        max_turns=max_turns,
    )


def run(coro):
    return asyncio.run(coro)


def test_ends_after_max_turns_and_hires_strong_candidate():
    session = make_session([80, 90], max_turns=2)
    run(session.answer("a"))
    replies = run(session.answer("b"))
    assert [r.type for r in replies] == [MessageType.EVALUATION, MessageType.END]
    assert replies[-1].verdict == Verdict.HIRED
    assert session.finished
    assert run(session.answer("c")) == []


def test_three_weak_answers_in_a_row_ends_early():
    session = make_session([10, 20, 5])
    run(session.answer("a"))
    run(session.answer("b"))
    replies = run(session.answer("c"))
    assert replies[-1].type == MessageType.END
    assert replies[-1].verdict == Verdict.REJECTED
    assert session.turn == 3


def test_failed_evaluation_does_not_corrupt_history():
    session = make_session([70], fail_first=True)
    try:
        run(session.answer("a"))
    except RuntimeError:
        pass
    assert session.turn == 0
    assert len(session._history) == 1
    run(session.answer("a"))
    assert session.turn == 1


def test_language_instruction_is_added_to_answer():
    seen = []

    async def evaluator(messages):
        seen.append(messages[-1]["content"])
        return Evaluation(response="ok", tech_score=70, stress_score=20)

    session = InterviewSession(
        role="AI Engineer",
        first_question="Q1?",
        system_message={"role": "system", "content": "sys"},
        evaluator=evaluator,
    )
    run(session.answer("cavab", "az-AZ"))
    run(session.answer("answer"))
    assert "Azərbaycan dilində" in seen[0]
    assert seen[1] == "Namizədin cavabı: answer"
