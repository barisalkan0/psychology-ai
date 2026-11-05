"""Tanışma soruları: tek ekranda tek soru, geri dönülebilir, özetle biten bir sihirbaz.

Eski sürümdeki tipik mantık hatalarına karşı:
- Geri dönünce cevaplar kaybolmaz (cevaplar widget durumunda değil, ayrı bir sözlükte tutulur).
- Hiç dokunulmayan bir soru için varsayılan değer kaydedilmez (kaydırıcı yerine boş başlayan seçimler).
- Zorunlu soru cevaplanmadan ilerlenemez; çoklu seçim sınırı aşılırsa hemen uyarılır.
- Sonda bir özet ekranı var; her cevap oradan düzenlenebilir.
"""

from __future__ import annotations

import streamlit as st

from psycalm import profile
from psycalm.profile import QUESTIONS
from psycalm.safety import assess_onboarding

from . import ui

NICK_STEP = 0
SUMMARY_STEP = len(QUESTIONS) + 1


def _state() -> dict:
    if "ob" not in st.session_state:
        user = ui.current_user()
        answers = ui.storage().get_profile(user.id) if user else {}
        st.session_state.ob = {"step": 0, "answers": dict(answers), "nickname": user.nickname if user else ""}
    return st.session_state.ob


def _go(step: int) -> None:
    st.session_state.ob["step"] = max(0, min(SUMMARY_STEP, step))
    st.rerun()


def _nickname_step(ob: dict) -> None:
    st.subheader("Sana nasıl hitap edelim?")
    st.caption("Sohbet biraz daha kişisel olsun diye. Gerçek adın olmak zorunda değil; boş da bırakabilirsin.")
    value = st.text_input("Hitap", value=ob["nickname"], max_chars=30, placeholder="ör. Deniz", key="ob_nick")
    if st.button("İleri", type="primary", icon=":material/arrow_forward:", icon_position="right"):
        ob["nickname"] = profile.clean_nickname(value)
        _go(1)


def _question_step(ob: dict, index: int) -> None:
    q = QUESTIONS[index - 1]
    saved = ob["answers"].get(q.key)
    st.subheader(q.title)
    st.caption(f"**Neden soruyoruz?** {q.why}")

    keys = list(q.options)
    if q.multi:
        value = st.pills(
            q.title, keys, selection_mode="multi", default=saved or [], format_func=q.options.get,
            key=f"ob_{q.key}", label_visibility="collapsed",
        )
    else:
        value = st.radio(
            q.title, keys, index=keys.index(saved) if saved in keys else None, format_func=q.options.get,
            key=f"ob_{q.key}", label_visibility="collapsed",
        )

    too_many = bool(q.max_select and value and len(value) > q.max_select)
    if too_many:
        st.error(f"En fazla {q.max_select} seçenek seçebilirsin; şu an {len(value)} seçili.", icon=":material/error:")

    if q.key == "risk" and value:
        a = assess_onboarding(value)
        if a.needs_card:
            st.markdown("Bunu paylaşman önemli. Sohbette de bu konuyu dikkate alacağız.")
            ui.crisis_card(a)

    missing_required = not q.optional and not value
    cols = st.columns([1, 1, 2])
    with cols[0]:
        if st.button("Geri", icon=":material/arrow_back:", width="stretch"):
            ob["answers"][q.key] = value or None
            _go(index - 1)
    with cols[1]:
        if q.optional and st.button("Atla", type="tertiary", width="stretch"):
            ob["answers"][q.key] = None
            _go(index + 1)
    with cols[2]:
        if st.button(
            "İleri", type="primary", icon=":material/arrow_forward:", icon_position="right",
            disabled=too_many or missing_required, width="stretch",
        ):
            ob["answers"][q.key] = value or None
            _go(index + 1)
    if missing_required:
        st.caption("Bu soru zorunlu; istemiyorsan “Cevaplamak istemiyorum”u seçebilirsin.")


def _summary_step(ob: dict) -> None:
    st.subheader("Özet")
    st.caption("Cevaplarını kontrol et. Hepsini daha sonra Ayarlar'dan da değiştirebilirsin.")
    rows = [("Hitap", ob["nickname"] or "—", NICK_STEP)]
    rows += [(q.title, profile.label(q.key, ob["answers"].get(q.key)), i) for i, q in enumerate(QUESTIONS, start=1)]
    for title, answer, step in rows:
        with st.container(border=True):
            c1, c2 = st.columns([5, 1], vertical_alignment="center")
            c1.markdown(f"**{title}**  \n{answer}")
            if c2.button("Düzenle", key=f"edit_{step}", type="tertiary"):
                _go(step)

    errors = profile.validate(ob["answers"])
    for e in errors:
        st.error(e)
    c1, c2 = st.columns([1, 2])
    with c1:
        if st.button("Geri", icon=":material/arrow_back:", width="stretch"):
            _go(SUMMARY_STEP - 1)
    with c2:
        if st.button("Kaydet ve devam et", type="primary", disabled=bool(errors), width="stretch"):
            user = ui.current_user()
            clean = {k: v for k, v in ob["answers"].items() if v}
            ui.storage().save_profile(user.id, clean)
            ui.storage().update_user(user.id, nickname=ob["nickname"], onboarding_done=1)
            del st.session_state["ob"]
            st.rerun()


def page() -> None:
    if ui.current_user() is None:
        return
    ob = _state()
    st.title("Tanışalım")
    st.progress(2 / 3, text="Adım 2 / 3 · Tanışma")
    step = ob["step"]
    if step < SUMMARY_STEP:
        st.caption(f"Soru {step + 1} / {SUMMARY_STEP} · Çoğu soru isteğe bağlı, yaklaşık 1 dakika sürer.")
    if step == NICK_STEP:
        _nickname_step(ob)
    elif step == SUMMARY_STEP:
        _summary_step(ob)
    else:
        _question_step(ob, step)
