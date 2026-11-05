"""Giriş ve hesap oluşturma."""

from __future__ import annotations

import time

import streamlit as st

from psycalm.profile import AGE_BANDS
from psycalm.storage import MIN_PASSWORD, StorageError

from . import ui

MAX_FAILURES = 5
LOCK_SECONDS = 30


def _youth_message() -> None:
    st.warning(
        "**Psycalm şu an yalnızca 18 yaş ve üzeri için.** Bunun iki nedeni var: reşit olmayanların sağlık "
        "verileri için veli onayı gerekiyor ve kullandığımız yapay zekâ hizmetinin şartları 18 yaş altını "
        "kapsamıyor.",
        icon=":material/info:",
    )
    st.markdown(
        "Konuşacak birine ihtiyacın varsa:\n"
        "- Okulundaki **rehber öğretmen** ya da güvendiğin bir yetişkin\n"
        "- **[183](tel:183)** — ALO 183 Sosyal Destek Hattı, çocuklar için de 7/24 ve ücretsiz\n"
        "- Acil bir durumda **[112](tel:112)**"
    )


def _login_tab() -> None:
    locked_until = st.session_state.get("login_locked_until", 0)
    with st.form("login", border=False):
        username = st.text_input("Kullanıcı adı", autocomplete="username", max_chars=24)
        password = st.text_input("Şifre", type="password", autocomplete="current-password")
        submitted = st.form_submit_button("Giriş yap", type="primary", width="stretch")
    if not submitted:
        return
    if time.time() < locked_until:
        st.error(f"Çok fazla hatalı deneme. {int(locked_until - time.time())} saniye sonra tekrar dene.")
        return
    if not username or not password:
        st.error("Kullanıcı adı ve şifre gerekli.")
        return
    user = ui.storage().authenticate(username, password)
    if user is None:
        failures = st.session_state.get("login_failures", 0) + 1
        st.session_state.login_failures = failures
        if failures >= MAX_FAILURES:
            st.session_state.login_locked_until = time.time() + LOCK_SECONDS
            st.session_state.login_failures = 0
        st.error("Kullanıcı adı ya da şifre hatalı.")
        return
    st.session_state.login_failures = 0
    st.session_state.uid = user.id
    st.rerun()


def _register_tab() -> None:
    with st.form("register", border=False):
        username = st.text_input(
            "Kullanıcı adı",
            help="3–24 karakter; küçük harf, rakam, nokta, tire ve alt çizgi. Gerçek adın olmak zorunda değil.",
            autocomplete="username",
            max_chars=24,
        )
        password = st.text_input(
            "Şifre", type="password", help=f"En az {MIN_PASSWORD} karakter.", autocomplete="new-password"
        )
        password2 = st.text_input("Şifre (tekrar)", type="password", autocomplete="new-password")
        age = st.selectbox(
            "Yaş aralığın",
            options=list(AGE_BANDS),
            format_func=AGE_BANDS.get,
            index=None,
            placeholder="Seç",
            help="Tam yaşını değil, aralığını soruyoruz: ihtiyaç duyduğumuzdan fazla veri toplamamak için.",
        )
        st.caption(
            "E-posta istemiyoruz. Bu yüzden şifreni unutursan hesabını kurtaramayız; şifreni güvenli bir yere not et."
        )
        submitted = st.form_submit_button("Hesap oluştur", type="primary", width="stretch")
    if not submitted:
        return
    if age is None:
        st.error("Yaş aralığını seçmen gerekiyor.")
        return
    if age == "<18":
        _youth_message()
        return
    if password != password2:
        st.error("Şifreler birbirini tutmuyor.")
        return
    try:
        user = ui.storage().register(username, password, age)
    except StorageError as exc:
        st.error(str(exc))
        return
    st.session_state.uid = user.id
    st.rerun()


def page() -> None:
    st.title("Psycalm")
    st.markdown(
        "Ne yaşadığını anlamana, **güvenilir bilgiye** ve **doğru uzmana** ulaşmana yardım eden bir yapay zekâ "
        "yönlendirme asistanı. Söylediklerinin neye dayandığını her zaman gösterir."
    )
    st.caption(
        "Psycalm bir terapist, doktor ya da acil servis değildir. Acil bir durumdaysan **[112](tel:112)**'yi ara."
    )
    ui.demo_banner()
    login, register = st.tabs(["Giriş yap", "Hesap oluştur"])
    with login:
        _login_tab()
    with register:
        _register_tab()
    st.caption("Güvenlik için oturum yalnızca bu sekmede açık kalır; sayfayı yenilersen yeniden giriş yapman gerekir.")
