"""Sohbet ekranı.

Akış:
1. Kullanıcı mesajı → deterministik risk taraması → mesaj kaydedilir.
2. Risk varsa modelden bağımsız kriz kartı gösterilir; modele de durum notu gider.
3. Cevap akışla gelir; yarım kaynak işaretleri gizlenir; bitince kaynaklar eklenir.
4. Hata olursa kullanıcının mesajı kaybolmaz; "Tekrar dene" ile aynı mesaj için yeniden üretilir.
"""

from __future__ import annotations

import streamlit as st

from psikorehber import consent, modes, profile
from psikorehber.llm import ChatTurn, LLMError
from psikorehber.prompts import build_system_prompt
from psikorehber.safety import Assessment, assess, assess_onboarding, prompt_note
from psikorehber.storage import User
from psikorehber.text import truncate

from . import ui

AVATARS = {"user": ":material/person:", "assistant": ":material/spa:"}

STARTERS = {
    "uyku": "Bir süredir doğru düzgün uyuyamıyorum",
    "kaygi": "Sürekli endişeliyim ve bunu durduramıyorum",
    "ruh-hali": "Hiçbir şeyden eskisi gibi keyif alamıyorum",
    "stres": "Çok bunaldım, her şey üst üste geldi",
    "iliskiler": "İlişkimde zorlanıyorum",
    "yalnizlik": "Kendimi çok yalnız hissediyorum",
    "okul-is": "Ders ya da iş baskısı beni eziyor",
    "kayip": "Birini kaybettim ve toparlanamıyorum",
    "ofke": "Öfkemi kontrol etmekte zorlanıyorum",
    "bagimlilik": "Kullanımımı kontrol edemiyor gibiyim",
    "beden-yeme": "Yemek ve bedenimle ilgili zorlanıyorum",
    "travma": "Yaşadığım bir olay aklımdan çıkmıyor",
}
DEFAULT_STARTERS = (
    "Kendimi iyi hissetmiyorum ama nereden başlayacağımı bilmiyorum",
    "Kime başvurmam gerektiğini bilmiyorum",
    "Sadece biraz anlatmak istiyorum",
)


# ─────────────────────────── yardımcılar ───────────────────────────
def _consents(user: User) -> dict:
    return ui.storage().consent_status(user.id)


def _memory_on(user: User) -> bool:
    return ui.storage().has_consent(user.id, "memory", consent.MEMORY.version)


def _open_mode_ok(user: User) -> bool:
    return ui.storage().has_consent(user.id, "open_mode", consent.OPEN_MODE.version)


def _active_mode(user: User) -> modes.Mode:
    return modes.resolve(user.default_mode, open_mode_consent=_open_mode_ok(user), is_adult=user.is_adult)


def _maybe_extract_memory(user: User, conv_id: int | None) -> None:
    """Sohbetten çıkarken (yeni sohbet / başka sohbete geçiş) hafıza notu çıkar."""
    if conv_id is None or not _memory_on(user):
        return
    store = ui.storage()
    conv = store.get_conversation(user.id, conv_id)
    if conv is None or conv["memory_extracted"]:
        return
    msgs = store.get_messages(user.id, conv_id)
    if sum(1 for m in msgs if m["role"] == "user") < 2:
        return
    transcript = "\n".join(
        f"{'Kullanıcı' if m['role'] == 'user' else 'Psikorehber'}: {m['content']}" for m in msgs[-30:]
    )
    try:
        with st.spinner("Önceki sohbetten hafıza notları çıkarılıyor…"):
            notes = ui.llm().extract_memory(transcript)
    except LLMError:
        st.toast("Hafıza notu çıkarılamadı; sohbetin kaydedildi.", icon=":material/warning:")
        return
    added = store.add_memories(user.id, notes, conv_id)
    store.update_conversation(user.id, conv_id, memory_extracted=1)
    if added:
        st.toast(f"Hafızana {added} not eklendi. Hafıza sayfasından görebilir ya da silebilirsin.",
                 icon=":material/bookmark_added:")


def _switch_conversation(user: User, target: int | None) -> None:
    current = st.session_state.get("conv_id")
    if current != target:
        _maybe_extract_memory(user, current)
    st.session_state.conv_id = target
    st.session_state.pop("gen_error", None)


def _recent_risk(msgs) -> Assessment:
    """Son birkaç kullanıcı mesajındaki risk; model bir sonraki mesajda konuyu bırakmasın diye."""
    result = Assessment()
    users = [m for m in msgs if m["role"] == "user"][-3:]
    for m in users:
        if m["risk_level"] != "none":
            cats = set(filter(None, m["risk_categories"].split(",")))
            result = result.merge(Assessment(m["risk_level"], cats, []))
    return result


# ─────────────────────────── kenar çubuğu ───────────────────────────
def _sidebar(user: User) -> None:
    store = ui.storage()
    with st.sidebar:
        if st.button("Yeni sohbet", icon=":material/add_comment:", type="primary", width="stretch"):
            _switch_conversation(user, None)
            st.rerun()
        convs = store.list_conversations(user.id)
        if convs:
            st.caption("Geçmiş sohbetler")
        active = st.session_state.get("conv_id")
        for conv in convs:
            is_active = conv["id"] == active
            if st.button(
                truncate(conv["title"], 34),
                key=f"conv_{conv['id']}",
                type="secondary" if is_active else "tertiary",
                icon=":material/chat_bubble:" if is_active else ":material/chat_bubble_outline:",
                width="stretch",
            ):
                _switch_conversation(user, conv["id"])
                st.rerun()


# ─────────────────────────── mod seçimi ───────────────────────────
@st.dialog("Açık sözlü mod", width="medium")
def _open_mode_dialog(user_id: int) -> None:
    m = modes.MODES["acik"]
    st.markdown(m.description)
    st.markdown("**Ne değişir?**\n" + "\n".join(f"- {c}" for c in m.changes))
    st.markdown("**Ne değişmez?**\n" + "\n".join(f"- {c}" for c in modes.SAFETY_UNCHANGED))
    agreed = st.checkbox(consent.OPEN_MODE.label)
    st.caption(consent.OPEN_MODE.detail)
    if st.button("Açık sözlü modu aç", type="primary", disabled=not agreed, width="stretch"):
        store = ui.storage()
        store.record_consent(user_id, "open_mode", consent.OPEN_MODE.version, True)
        store.update_user(user_id, default_mode="acik")
        st.rerun()


def _pick_mode(user_id: int, mode_key: str, needs_consent: bool) -> None:
    # Geri çağırma (callback) betikten önce çalışır: menüyü burada kapatmak mümkün. Aksi hâlde
    # onay penceresi açıldığında menü pencerenin üstünde açık kalıyordu.
    st.session_state["mode_popover"] = False
    if needs_consent:
        st.session_state["show_open_mode_dialog"] = True
    else:
        ui.storage().update_user(user_id, default_mode=mode_key)


def _mode_menu(user: User) -> None:
    current = _active_mode(user)
    consent_ok = _open_mode_ok(user) and user.is_adult
    with st.popover(f"{current.icon} {current.name}", help="Sohbet modunu değiştir", width="stretch",
                    key="mode_popover", on_change="rerun"):
        for m in modes.MODES.values():
            selected = m.key == current.key
            st.button(
                f"{m.icon} {m.name}" + ("  ✓" if selected else ""),
                key=f"mode_{m.key}",
                type="primary" if selected else "secondary",
                width="stretch",
                on_click=_pick_mode,
                args=(user.id, m.key, m.requires_consent and not consent_ok),
            )
            st.caption(m.tagline)
        st.caption("Mod değişikliği bir sonraki mesajdan itibaren geçerli olur.")
    if st.session_state.pop("show_open_mode_dialog", False):
        _open_mode_dialog(user.id)


# ─────────────────────────── karşılama ───────────────────────────
def _welcome(user: User, answers: dict) -> None:
    hello = f"Merhaba {user.nickname}" if user.nickname else "Merhaba"
    st.markdown(f"### {hello}, seni dinliyorum.")
    st.markdown(
        "Ne yaşadığını kendi kelimelerinle anlatabilirsin. Ne kadar somut olursa (ne zamandır, ne sıklıkla, "
        "hayatını nasıl etkiliyor) yönlendirme o kadar isabetli olur."
    )
    onboarding_risk = assess_onboarding(answers.get("risk"))
    if onboarding_risk.level == "high":
        ui.crisis_card(onboarding_risk, from_onboarding=True)

    topics = answers.get("topics") or []
    starters = [STARTERS[t] for t in topics if t in STARTERS][:3]
    starters += [s for s in DEFAULT_STARTERS if s not in starters][: 4 - len(starters)]
    st.caption("Başlamak için bir şey seçebilir ya da aşağıya yazabilirsin:")
    cols = st.columns(2)
    for i, text in enumerate(starters):
        if cols[i % 2].button(text, key=f"starter_{i}", width="stretch", wrap=True):
            st.session_state.pending_prompt = text
            st.rerun()


# ─────────────────────────── üretim ───────────────────────────
def _generate(user: User, conv_id: int, answers: dict, current: Assessment) -> None:
    store = ui.storage()
    msgs = store.get_messages(user.id, conv_id)
    history = [ChatTurn(m["role"], m["content"]) for m in msgs]

    risk = current.merge(_recent_risk(msgs))
    if len([m for m in msgs if m["role"] == "user"]) == 1:
        risk = risk.merge(assess_onboarding(answers.get("risk")))

    mode = _active_mode(user)
    memories = [m["text"] for m in store.list_memories(user.id)][:20] if _memory_on(user) else []
    system_prompt = build_system_prompt(
        mode=mode,
        profile_json=profile.summary_for_prompt(user.nickname, user.age_band, answers),
        memory_notes=memories,
        risk_note=prompt_note(risk),
    )

    with st.chat_message("assistant", avatar=AVATARS["assistant"]):
        placeholder = st.empty()
        buffer = ""
        try:
            with st.spinner("Düşünüyor…", show_time=False):
                stream = ui.llm().stream_reply(
                    system_prompt=system_prompt, history=history, temperature=mode.temperature
                )
                first = next(stream, "")
            buffer = first
            placeholder.markdown(ui.assistant_markdown(buffer, streaming=True) + " ▍")
            for piece in stream:
                buffer += piece
                placeholder.markdown(ui.assistant_markdown(buffer, streaming=True) + " ▍")
        except LLMError as exc:
            if buffer:  # yarım cevap varsa kaybetme, sonuna not düş
                buffer += "\n\n*(Cevap yarıda kesildi.)*"
            else:
                placeholder.empty()
                st.session_state.gen_error = exc.user_message
                st.rerun()
        if not buffer.strip():
            buffer = "Şu an bir cevap üretemedim. Mesajını biraz farklı yazıp tekrar dener misin?"
        placeholder.markdown(ui.assistant_markdown(buffer))
    store.add_message(user.id, conv_id, "assistant", buffer)
    store.update_conversation(user.id, conv_id, mode=mode.key)


def _handle_new_message(user: User, text: str, answers: dict) -> None:
    store = ui.storage()
    text = text.strip()
    if not text:
        return
    conv_id = st.session_state.get("conv_id")
    if conv_id is None or store.get_conversation(user.id, conv_id) is None:
        conv_id = store.create_conversation(user.id, truncate(text, 60), _active_mode(user).key)
        st.session_state.conv_id = conv_id
    a = assess(text)
    store.add_message(
        user.id, conv_id, "user", text, risk_level=a.level, risk_categories=",".join(sorted(a.categories))
    )
    st.session_state.pop("gen_error", None)
    st.rerun()  # mesaj geçmişte görünsün, üretim bir sonraki çalıştırmada başlasın


# ─────────────────────────── sayfa ───────────────────────────
def page() -> None:
    user = ui.current_user()
    if user is None:
        return
    store = ui.storage()
    answers = store.get_profile(user.id)
    _sidebar(user)

    conv_id = st.session_state.get("conv_id")
    conv = store.get_conversation(user.id, conv_id) if conv_id else None
    if conv_id and conv is None:  # silinmiş ya da başkasına ait
        st.session_state.conv_id = conv_id = None

    head_l, head_r = st.columns([3, 1.2], vertical_alignment="center")
    with head_l:
        st.markdown(f"#### {conv['title'] if conv else 'Yeni sohbet'}")
    with head_r:
        _mode_menu(user)
    ui.demo_banner()

    msgs = store.get_messages(user.id, conv_id) if conv else []
    if not msgs:
        _welcome(user, answers)

    # Aynı sohbette aynı uyarıyı tekrar tekrar tam göstermemek için: tam kartla gösterilmiş
    # kategoriler sonraki mesajlarda kısa hatırlatmaya döner. YENİ bir kategori (ör. önce intihar,
    # sonra şiddet) çıkarsa kart yine tam gösterilir; yoksa 183/KADES gibi bilgiler kaybolurdu.
    covered: set[str] = set()
    for m in msgs:
        with st.chat_message(m["role"], avatar=AVATARS[m["role"]]):
            if m["role"] == "user":
                st.text(m["content"])  # kullanıcı metni markdown/HTML olarak yorumlanmaz
            else:
                st.markdown(ui.assistant_markdown(m["content"]))
        if m["role"] == "user" and m["risk_level"] != "none":
            cats = set(filter(None, m["risk_categories"].split(","))) - {"minor"}
            a = Assessment(m["risk_level"], cats, [])
            is_repeat = a.level == "high" and cats <= covered
            ui.crisis_card(a, compact=is_repeat)
            if a.level == "high":
                covered |= cats

    # Son mesaj kullanıcıdansa cevap bekleniyor: ya üret ya da hata göster
    if msgs and msgs[-1]["role"] == "user":
        error = st.session_state.get("gen_error")
        if error:
            st.error(error, icon=":material/cloud_off:")
            if st.button("Tekrar dene", icon=":material/refresh:", type="primary"):
                st.session_state.pop("gen_error", None)
                st.rerun()
        else:
            last = msgs[-1]
            current = Assessment(last["risk_level"], set(filter(None, last["risk_categories"].split(","))), [])
            _generate(user, conv_id, answers, current)

    prompt = st.chat_input("Aklından geçenleri yaz…", max_chars=4000)
    pending = st.session_state.pop("pending_prompt", None)
    text = prompt or pending
    if text:
        _handle_new_message(user, text, answers)
