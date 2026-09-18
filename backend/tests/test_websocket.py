import json


def test_health(client):
    body = client.get("/health").json()
    assert body["status"] == "ok" and body["agent_ready"] is True


def test_interview_flow(client, fake_agent):
    with client.websocket_connect("/ws/interview?role=Python%20Engineer") as ws:
        opening = ws.receive_json()
        assert opening["type"] == "question"
        assert opening["ai_reply"]

        ws.send_text(json.dumps({"type": "answer", "text": "The GIL serialises bytecode."}))
        reply = ws.receive_json()
        assert reply["type"] == "evaluation"
        assert reply["turn"] == 1
        assert reply["tech_accuracy_score"] == 70

        # Plain text is accepted too, and history is passed to the agent.
        ws.send_text("Second answer")
        ws.receive_json()
        last_call = fake_agent.calls[-1]
        assert last_call[0]["role"] == "system"
        assert last_call[-1]["content"].endswith("Second answer")


def test_blank_answer_is_rejected(client):
    with client.websocket_connect("/ws/interview") as ws:
        ws.receive_json()
        ws.send_text(json.dumps({"type": "answer", "text": ""}))
        assert ws.receive_json()["type"] == "error"


def test_missing_agent_reports_error(client):
    client.app.state.agent = None
    with client.websocket_connect("/ws/interview") as ws:
        assert ws.receive_json()["type"] == "error"


def test_opening_question_falls_back_to_bank(client, fake_agent):
    from app.agent import AgentError

    async def broken(profile, lang):
        raise AgentError("down")

    fake_agent.opening_question = broken
    with client.websocket_connect("/ws/interview?role=Python%20Engineer") as ws:
        opening = ws.receive_json()
        assert opening["type"] == "question" and "?" in opening["ai_reply"]
