"""Streamlit AppTest ile uçtan uca akış testleri (gerçek API çağrısı yok, MockLLM)."""

from __future__ import annotations

from pathlib import Path

import pytest

pytest.importorskip("streamlit")
from streamlit.testing.v1 import AppTest  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture()
def app(tmp_path, monkeypatch):
    monkeypatch.setenv("PSYCALM_MOCK", "1")
    monkeypatch.setenv("PSYCALM_DB", str(tmp_path / "app.db"))
    monkeypatch.chdir(ROOT)
    # cache_resource önbelleğini temizle: her test kendi veritabanını kullansın
    import streamlit as st

    st.cache_resource.clear()
    at = AppTest.from_file(str(ROOT / "app.py"), default_timeout=20)
    yield at
    st.cache_resource.clear()


def _storage():
    from views import ui

    return ui.storage()


def _ready_user(store, *, risk="hayir", memory=True):
    from psycalm import consent

    u = store.register("deniz", "guclu-sifre", "18-24")
    store.record_consent(u.id, "disclaimer", consent.DISCLAIMER.version, True)
    store.record_consent(u.id, "processing", consent.PROCESSING.version, True)
    store.record_consent(u.id, "memory", consent.MEMORY.version, memory)
    store.save_profile(u.id, {"topics": ["uyku"], "risk": risk})
    store.update_user(u.id, onboarding_done=1, tutorial_done=1, nickname="Deniz")
    return u


def test_logged_out_sees_login_and_no_exception(app):
    app.run()
    assert not app.exception
    assert app.title[0].value == "Psycalm"


def test_gates_follow_state(app):
    app.run()
    store = _storage()
    u = store.register("deniz", "guclu-sifre", "18-24")
    app.session_state["uid"] = u.id
    app.run()
    assert app.title[0].value == "Başlamadan önce"  # izinler önce gelir
    # Zorunlu kutular işaretlenmeden buton pasif
    confirm = next(b for b in app.button if b.label == "Onayla ve devam et")
    assert confirm.disabled
    from psycalm import consent

    store.record_consent(u.id, "disclaimer", consent.DISCLAIMER.version, True)
    store.record_consent(u.id, "processing", consent.PROCESSING.version, True)
    app.run()
    assert app.title[0].value == "Tanışalım"
    store.update_user(u.id, onboarding_done=1)
    app.run()
    assert app.title[0].value == "Hoş geldin"
    store.update_user(u.id, tutorial_done=1)
    app.run()
    assert not app.exception
    assert any("seni dinliyorum" in m.value for m in app.markdown)


def test_chat_message_reply_and_sources(app):
    app.run()
    u = _ready_user(_storage())
    app.session_state["uid"] = u.id
    app.run()
    app.chat_input[0].set_value("Bir süredir uyuyamıyorum").run()
    assert not app.exception
    msgs = _storage().get_messages(u.id, app.session_state["conv_id"])
    assert [m["role"] for m in msgs] == ["user", "assistant"]
    rendered = " ".join(m.value for m in app.markdown)
    assert "📚 Kaynaklar" in rendered and "[kaynak:" not in rendered


def test_crisis_message_is_flagged_and_card_shown(app):
    app.run()
    u = _ready_user(_storage())
    app.session_state["uid"] = u.id
    app.run()
    app.chat_input[0].set_value("Artık yaşamak istemiyorum").run()
    msgs = _storage().get_messages(u.id, app.session_state["conv_id"])
    assert msgs[0]["risk_level"] == "high"
    text = " ".join(m.value for m in app.markdown)
    assert "112" in text and "182" not in text


def test_llm_error_keeps_message_and_offers_retry(app, monkeypatch):
    from psycalm.llm import LLMError, MockLLM

    calls = {"n": 0}

    def boom(self, **kwargs):
        calls["n"] += 1
        raise LLMError("Şu an çok fazla istek var ya da günlük kota doldu. Biraz sonra tekrar dene.")
        yield  # pragma: no cover

    monkeypatch.setattr(MockLLM, "stream_reply", boom)
    app.run()
    u = _ready_user(_storage())
    app.session_state["uid"] = u.id
    app.run()
    app.chat_input[0].set_value("merhaba").run()
    assert not app.exception
    assert any("kota" in e.value for e in app.error)
    msgs = _storage().get_messages(u.id, app.session_state["conv_id"])
    assert [m["role"] for m in msgs] == ["user"]  # mesaj kaybolmadı
    retry = next(b for b in app.button if b.label == "Tekrar dene")
    monkeypatch.undo()
    retry.click().run()
    msgs = _storage().get_messages(u.id, app.session_state["conv_id"])
    assert [m["role"] for m in msgs] == ["user", "assistant"]


def test_open_mode_falls_back_without_consent(app):
    app.run()
    store = _storage()
    u = _ready_user(store)
    store.update_user(u.id, default_mode="acik")  # rıza kaydı yok
    app.session_state["uid"] = u.id
    app.run()
    assert not app.exception
    from views.chat import _active_mode

    assert _active_mode(store.get_user(u.id)).key == "dengeli"
