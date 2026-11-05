"""GeminiLLM'in akış, engelleme ve hata çevirisi mantığı — sahte istemciyle (ağ yok)."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from google.genai import errors

from psycalm.llm import BLOCKED_FALLBACK, ChatTurn, GeminiLLM, LLMError, _parse_json_list, _to_contents


def _chunk(text="", finish=None, block=None):
    cand = SimpleNamespace(finish_reason=SimpleNamespace(name=finish) if finish else None)
    return SimpleNamespace(
        text=text,
        candidates=[cand],
        prompt_feedback=SimpleNamespace(block_reason=block) if block else None,
    )


class FakeModels:
    def __init__(self, behaviour):
        self.behaviour = behaviour
        self.calls = 0

    def generate_content_stream(self, **kwargs):
        self.calls += 1
        result = self.behaviour(self.calls)
        if isinstance(result, Exception):
            raise result
        return iter(result)


def _llm(behaviour, monkeypatch):
    monkeypatch.setattr("time.sleep", lambda s: None)
    llm = GeminiLLM.__new__(GeminiLLM)
    llm._model = "test-model"
    llm._client = SimpleNamespace(models=FakeModels(behaviour))
    return llm


def _run(llm):
    return "".join(llm.stream_reply(system_prompt="s", history=[ChatTurn("user", "merhaba")], temperature=0.5))


def test_normal_stream(monkeypatch):
    llm = _llm(lambda n: [_chunk("Mer"), _chunk("haba"), _chunk("", finish="STOP")], monkeypatch)
    assert _run(llm) == "Merhaba"


def test_blocked_prompt_returns_safe_fallback(monkeypatch):
    llm = _llm(lambda n: [_chunk(block="SAFETY")], monkeypatch)
    assert _run(llm) == BLOCKED_FALLBACK
    assert "112" in BLOCKED_FALLBACK


def test_safety_finish_without_text_returns_fallback(monkeypatch):
    llm = _llm(lambda n: [_chunk("", finish="SAFETY")], monkeypatch)
    assert _run(llm) == BLOCKED_FALLBACK


def test_partial_text_then_safety_keeps_text(monkeypatch):
    llm = _llm(lambda n: [_chunk("Kısmi cevap"), _chunk("", finish="SAFETY")], monkeypatch)
    assert _run(llm) == "Kısmi cevap"


def _api_error(code):
    return errors.APIError(code, {"error": {"code": code, "message": "x", "status": "X"}})


@pytest.mark.parametrize(
    "code, fragment, retryable",
    [(401, "API anahtarı", False), (404, "modeli bulunamadı", False), (429, "kota", True), (503, "geçici", True)],
)
def test_errors_are_translated(monkeypatch, code, fragment, retryable):
    llm = _llm(lambda n: _api_error(code), monkeypatch)
    with pytest.raises(LLMError) as exc:
        _run(llm)
    assert fragment in exc.value.user_message
    assert exc.value.retryable == retryable
    # Geçici hatalarda bir kez yeniden denenir, kalıcı hatalarda denenmez
    assert llm._client.models.calls == (2 if retryable else 1)


def test_transient_error_then_success(monkeypatch):
    llm = _llm(lambda n: _api_error(503) if n == 1 else [_chunk("tamam")], monkeypatch)
    assert _run(llm) == "tamam"


def test_history_trimming_starts_with_user():
    hist = [ChatTurn("assistant", "selam")] + [ChatTurn("user", "a"), ChatTurn("assistant", "b")]
    contents = _to_contents(hist)
    assert contents[0]["role"] == "user"
    assert [c["role"] for c in contents] == ["user", "model"]


def test_memory_json_parsing_is_defensive():
    assert _parse_json_list('["a", "b"]') == ["a", "b"]
    assert _parse_json_list('```json\n["a"]\n```') == ["a"]
    assert _parse_json_list("bozuk") == []
    assert _parse_json_list('{"a": 1}') == []
    assert len(_parse_json_list(str([f"not {i}" for i in range(10)]).replace("'", '"'))) == 5
