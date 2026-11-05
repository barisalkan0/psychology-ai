"""Psikorehber — giriş noktası.

Çalıştırmak için:  streamlit run app.py

Akış (her adım bir öncekini gerektirir):
    Giriş / Kayıt → İzinler (KVKK) → Tanışma soruları → Kısa tanıtım → Uygulama
"Yardım ve Kaynaklar" her adımda, giriş yapmadan da erişilebilir.
"""

from __future__ import annotations

import logging

import streamlit as st

from views import auth, breathing, chat, consent_page, help_page, memory_page, onboarding, settings_page, tutorial, ui
from views.consent_page import required_consents_ok

logging.basicConfig(level=logging.INFO)

st.set_page_config(page_title="Psikorehber", page_icon=":material/spa:", layout="centered")
ui.inject_css()

HELP = st.Page(help_page.page, title="Yardım ve Kaynaklar", icon=":material/support:", url_path="yardim")


def _gate(page_fn, title: str, icon: str) -> st.Page:
    # Kapı sayfaları hep kök adreste: durum değişince adres çubuğunda eski sayfa kalmasın
    return st.Page(page_fn, title=title, icon=icon, default=True)


user = ui.current_user()
if user is None:
    pages = [_gate(auth.page, "Giriş", ":material/login:"), HELP]
elif not required_consents_ok(user.id):
    pages = [_gate(consent_page.page, "Başlamadan önce", ":material/verified_user:"), HELP]
elif not user.onboarding_done:
    pages = [_gate(onboarding.page, "Tanışalım", ":material/waving_hand:"), HELP]
elif not user.tutorial_done:
    pages = [_gate(tutorial.page, "Tanıtım", ":material/school:"), HELP]
else:
    pages = {
        "": [
            _gate(chat.page, "Sohbet", ":material/chat:"),
            st.Page(breathing.page, title="Nefes", icon=":material/air:", url_path="nefes"),
            HELP,
        ],
        "Hesabım": [
            st.Page(memory_page.page, title="Hafıza", icon=":material/bookmark:", url_path="hafiza"),
            st.Page(settings_page.page, title="Ayarlar", icon=":material/settings:", url_path="ayarlar"),
        ],
    }

nav = st.navigation(pages)
nav.run()
ui.sidebar_footer(user)  # sayfanın kendi kenar çubuğu içeriğinden sonra, en altta
