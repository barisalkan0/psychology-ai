"""Ayarlar: profil, mod, izinler, verilerim, hesap."""

from __future__ import annotations

import json

import streamlit as st

from psikorehber import consent, modes, profile
from psikorehber.profile import AGE_BANDS, QUESTIONS

from . import ui


def _profile_tab(user) -> None:
    answers = ui.storage().get_profile(user.id)
    st.markdown(f"**Kullanıcı adı:** {user.username}  \n**Yaş aralığı:** {AGE_BANDS.get(user.age_band, user.age_band)}  \n"
                f"**Hitap:** {user.nickname or '—'}")
    for q in QUESTIONS:
        st.markdown(f"**{q.title}**  \n{profile.label(q.key, answers.get(q.key))}")
    if st.button("Tanışma cevaplarını düzenle", icon=":material/edit:"):
        st.session_state.pop("ob", None)
        ui.storage().update_user(user.id, onboarding_done=0)
        st.rerun()
    if st.button("Tanıtımı tekrar göster", icon=":material/school:", type="tertiary"):
        st.session_state.pop("tour_step", None)
        ui.storage().update_user(user.id, tutorial_done=0)
        st.rerun()


def _consent_tab(user) -> None:
    store = ui.storage()
    status = store.consent_status(user.id)
    st.markdown("Verdiğin izinler ve tarihleri. Metin değişirse izin yeniden istenir.")
    for item in consent.ALL_ITEMS.values():
        s = status.get(item.kind)
        active = bool(s and s["granted"] and s["version"] == item.version)
        state = "✅ Verildi" if active else "— Verilmedi / geri alındı"
        when = f" · {s['at'][:16].replace('T', ' ')} UTC" if s else ""
        with st.container(border=True):
            st.markdown(f"**{state}**{when}  \n{item.label}")
            if active and item.kind == "open_mode":
                if st.button("Açık sözlü mod iznini geri al", key="revoke_open"):
                    store.record_consent(user.id, "open_mode", item.version, False)
                    if user.default_mode == "acik":
                        store.update_user(user.id, default_mode=modes.DEFAULT_MODE)
                    st.rerun()
            if active and item.kind == "memory":
                st.caption("Hafıza iznini Hafıza sayfasından kapatabilirsin; kapatınca notlar silinir.")
            if item.required and active:
                st.caption("Bu izni geri almak sohbeti durdurur. Geri almak yerine hesabını silmeyi de seçebilirsin.")
                if st.button("Bu izni geri al", key=f"revoke_{item.kind}"):
                    store.record_consent(user.id, item.kind, item.version, False)
                    st.rerun()
    with st.expander("Aydınlatma metni"):
        st.markdown(consent.information_notice(ui.settings()))


def _data_tab(user) -> None:
    store = ui.storage()
    st.markdown("Kayıtlı tüm verilerini (hesap, cevaplar, izinler, hafıza, sohbetler) JSON olarak indirebilirsin.")
    data = json.dumps(store.export_user(user.id), ensure_ascii=False, indent=2)
    st.download_button("Verilerimi indir", data=data, file_name="psikorehber-verilerim.json",
                       mime="application/json", icon=":material/download:")
    st.divider()
    convs = store.list_conversations(user.id)
    st.markdown(f"**Sohbetler** ({len(convs)})")
    for c in convs:
        c1, c2 = st.columns([5, 1], vertical_alignment="center")
        c1.markdown(f"{c['title']}  \n<small>{c['updated_at'][:16].replace('T', ' ')} UTC</small>", unsafe_allow_html=True)
        if c2.button("Sil", key=f"delconv_{c['id']}", icon=":material/delete:", type="tertiary"):
            store.delete_conversation(user.id, c["id"])
            if st.session_state.get("conv_id") == c["id"]:
                st.session_state.conv_id = None
            st.rerun()


def _account_tab(user) -> None:
    st.markdown(
        "Hesabını silmek hesabını, cevaplarını, izin kayıtlarını, hafıza notlarını ve tüm sohbetlerini kalıcı olarak "
        "siler. Bu işlem geri alınamaz."
    )
    confirm = st.text_input("Onaylamak için **SİL** yaz", max_chars=3, key="del_confirm")
    if st.button("Hesabımı kalıcı olarak sil", type="primary", icon=":material/delete_forever:",
                 disabled=confirm.strip().upper() not in {"SİL", "SIL"}):
        ui.storage().delete_user(user.id)
        ui.logout()
        st.rerun()


def page() -> None:
    user = ui.current_user()
    if user is None:
        return
    st.title("Ayarlar")
    t1, t2, t3, t4 = st.tabs(["Profil", "İzinler", "Verilerim", "Hesap"])
    with t1:
        _profile_tab(user)
    with t2:
        _consent_tab(user)
    with t3:
        _data_tab(user)
    with t4:
        _account_tab(user)
