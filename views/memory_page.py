"""Hafıza: şeffaf, düzenlenebilir, tek tuşla silinebilir."""

from __future__ import annotations

import streamlit as st

from psikorehber import consent

from . import ui


def page() -> None:
    user = ui.current_user()
    if user is None:
        return
    store = ui.storage()
    on = store.has_consent(user.id, "memory", consent.MEMORY.version)

    st.title("Hafıza")
    st.markdown(
        "Hafıza açıkken, bir sohbetten çıktığında (yeni sohbet başlattığında ya da başka bir sohbete geçtiğinde) "
        "o sohbetten birkaç kısa not çıkarılır. Sonraki sohbetlerde seni baştan anlatmak zorunda bırakmamak için "
        "kullanılır. **Model önceki sohbetlerinden yalnızca burada gördüğün notları bilir** (en yeni 20 not); "
        "bunlara ek olarak tanışma cevaplarını görür. Sohbetlerin tam metni yeni sohbete aktarılmaz."
    )

    new_state = st.toggle("Hafıza açık", value=on, help=consent.MEMORY.detail)
    if new_state != on:
        store.record_consent(user.id, "memory", consent.MEMORY.version, new_state)
        if not new_state:
            store.clear_memories(user.id)
            st.toast("Hafıza kapatıldı ve tüm notlar silindi.", icon=":material/delete:")
        st.rerun()

    if not on:
        st.info("Hafıza kapalı. Sohbetlerin yine kaydedilir ama yeni bir sohbet önceki sohbetleri bilmez.",
                icon=":material/bookmark_remove:")
        return

    with st.form("add_note", clear_on_submit=True, border=True):
        text = st.text_input(
            "Kendin bir not ekle", max_chars=200,
            placeholder="ör. Kullanıcı sınav döneminde ve uyku düzeni bozuk.",
            help="Modelin bilmesini istediğin bir şey. Kimliğini belirleyecek bilgiler yazma.",
        )
        if st.form_submit_button("Ekle", icon=":material/add:") and text.strip():
            store.add_memories(user.id, [text], None)
            st.rerun()

    notes = store.list_memories(user.id)
    if not notes:
        st.caption("Henüz not yok.")
        return
    st.caption(f"{len(notes)} not · En yeniler üstte")
    for n in notes:
        with st.container(border=True):
            c1, c2 = st.columns([6, 1], vertical_alignment="center")
            edited = c1.text_input(
                "Not", value=n["text"], key=f"mem_{n['id']}", label_visibility="collapsed", max_chars=200
            )
            if c2.button("Sil", key=f"del_{n['id']}", icon=":material/delete:", type="tertiary"):
                store.delete_memory(user.id, n["id"])
                st.rerun()
            if edited.strip() and edited != n["text"]:
                store.update_memory(user.id, n["id"], edited)
                st.toast("Not güncellendi.", icon=":material/check:")
    with st.popover("Tüm notları sil", icon=":material/delete_sweep:"):
        st.markdown("Bu işlem geri alınamaz.")
        if st.button("Evet, hepsini sil", type="primary"):
            store.clear_memories(user.id)
            st.rerun()
