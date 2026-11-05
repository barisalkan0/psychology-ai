"""Yardım ve Kaynaklar. Giriş yapmadan da açılır: acil bilgi hiçbir kaydın arkasına saklanmamalı."""

from __future__ import annotations

import streamlit as st

from psikorehber.citations import render
from psikorehber.resources import (
    ABROAD_NOTE, EMERGENCY_ROOM_NOTE, EVIDENCE, HELPLINES, KADES_NOTE, SOURCES_BY_ID, SPECIALISTS,
    THERAPIST_TIPS, TOPIC_LABELS, VERIFIED_ON, sources_for_topics,
)


def _helplines() -> None:
    st.subheader("Acil bir durumdaysan", divider="red")
    st.markdown(
        f"- 📞 **[112](tel:112)** — Hayati tehlike, kendine ya da başkasına zarar verme riski, şiddet, zehirlenme. "
        f"7/24, ücretsiz.\n- 🏥 {EMERGENCY_ROOM_NOTE}"
    )
    st.subheader("Destek hatları", divider="gray")
    for h in HELPLINES:
        if h.is_emergency:
            continue
        with st.container(border=True):
            st.markdown(f"**[{h.number}](tel:{h.number}) · {h.name}**  \n{h.when}  \n*{h.hours}*")
            if h.note:
                st.caption(h.note)
    st.markdown(f"- 📱 {KADES_NOTE}\n- 🌍 {ABROAD_NOTE}")


def _specialists() -> None:
    st.subheader("Kime başvurmalıyım?", divider="gray")
    st.caption("Sıralama bir yol haritası: emin değilsen aile hekimi ya da üniversite danışma merkezi iyi bir başlangıç.")
    for sp in SPECIALISTS:
        with st.expander(sp.title):
            st.markdown(sp.who)
            st.markdown("**Ne zaman?**\n" + "\n".join(f"- {w}" for w in sp.when))
            st.markdown(f"**Nasıl ulaşılır?** {sp.how}  \n**Ücret:** {sp.cost}")
            if sp.sources:
                links = " · ".join(f"[{SOURCES_BY_ID[s].title}]({SOURCES_BY_ID[s].url})" for s in sp.sources)
                st.caption(f"Daha fazla: {links}")
    with st.expander("Terapist seçerken nelere dikkat etmeli?", icon=":material/checklist:"):
        tips = [render(t) for t in THERAPIST_TIPS]
        st.markdown("\n".join(f"- {r.text}" for r in tips))
        footer_sources = {s.id: s for r in tips for s in r.sources}
        for s in footer_sources.values():
            st.caption(f"¹ [{s.title}]({s.url}) — {s.publisher}")


def _library() -> None:
    st.subheader("Güvenilir okuma listesi", divider="gray")
    st.caption(
        "Sohbette gösterilen kaynaklar yalnızca bu listeden gelir. Her birinin dayanak düzeyi belirtildi. "
        "Kaynakların çoğu İngilizce; tarayıcının çeviri özelliğiyle okuyabilirsin."
    )
    topics = st.pills(
        "Konuya göre süz", list(TOPIC_LABELS), format_func=TOPIC_LABELS.get, selection_mode="multi", key="lib_topics"
    )
    for s in sources_for_topics(topics or []):
        ev = EVIDENCE[s.evidence]
        lang = "Türkçe" if s.language == "tr" else "İngilizce"
        st.markdown(f"**[{s.title}]({s.url})**  \n{s.publisher} · {ev.icon} {ev.label} · {lang}  \n{s.supports}")
    with st.expander("Dayanak düzeyleri ne anlama geliyor?"):
        st.markdown("\n".join(f"- {e.icon} **{e.label}:** {e.meaning}" for e in EVIDENCE.values()))


def page() -> None:
    st.title("Yardım ve Kaynaklar")
    st.caption(f"Numaralar ve bağlantılar en son {VERIFIED_ON} tarihinde kontrol edildi; değişmiş olabilir.")
    _helplines()
    _specialists()
    _library()
