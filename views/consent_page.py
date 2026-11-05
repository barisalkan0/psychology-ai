"""Aydınlatma metni ve rızalar. Tanışma sorularından ÖNCE gelir: sağlık verisi toplamadan önce
açık rıza alınmalı."""

from __future__ import annotations

import streamlit as st

from psycalm import consent

from . import ui


def required_consents_ok(user_id: int) -> bool:
    store = ui.storage()
    return all(store.has_consent(user_id, c.kind, c.version) for c in consent.REQUIRED)


def page() -> None:
    user = ui.current_user()
    if user is None:
        return
    s = ui.settings()
    st.title("Başlamadan önce")
    st.progress(1 / 3, text="Adım 1 / 3 · İzinler")
    st.markdown(
        "Burada konuşacakların kişisel ve hassas olabilir. Bu yüzden verilerinle ne yapıldığını açıkça anlatıyor, "
        "her izni **ayrı ayrı** istiyoruz. Hiçbiri önceden işaretli değil."
    )
    if not s.paid_tier:
        st.warning(consent.provider_notice(s), icon=":material/visibility:")
    with st.expander("Aydınlatma metninin tamamı (KVKK)", icon=":material/description:"):
        st.markdown(consent.information_notice(s))

    st.subheader("Zorunlu", divider="gray")
    d = st.checkbox(consent.DISCLAIMER.label, key="c_disclaimer")
    st.caption(consent.DISCLAIMER.detail)
    p = st.checkbox(consent.PROCESSING.label, key="c_processing")
    st.caption(consent.PROCESSING.detail)

    st.subheader("İsteğe bağlı", divider="gray")
    m = st.checkbox(consent.MEMORY.label, key="c_memory")
    st.caption(consent.MEMORY.detail)
    st.caption("“Açık sözlü” mod için ayrı bir izni, o modu seçtiğinde soracağız.")

    st.space("small")
    ready = d and p
    if st.button("Onayla ve devam et", type="primary", disabled=not ready, width="stretch"):
        store = ui.storage()
        store.record_consent(user.id, "disclaimer", consent.DISCLAIMER.version, True)
        store.record_consent(user.id, "processing", consent.PROCESSING.version, True)
        store.record_consent(user.id, "memory", consent.MEMORY.version, bool(m))
        st.rerun()
    if not ready:
        st.caption("Devam etmek için iki zorunlu kutuyu işaretlemen gerekiyor.")

    with st.expander("Onay vermek istemiyorum"):
        st.markdown(
            "Sorun değil. Zorunlu izinler olmadan sohbet çalışamaz ama **Yardım ve Kaynaklar** sayfasını kullanmaya "
            "devam edebilirsin. Oluşturduğun hesabı şimdi tamamen silebilirsin."
        )
        if st.button("Hesabımı sil ve çık", icon=":material/delete:"):
            store = ui.storage()
            store.delete_user(user.id)
            ui.logout()
            st.rerun()
