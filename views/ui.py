"""Sayfalar arasında paylaşılan arayüz parçaları ve servisler."""

from __future__ import annotations

import itertools

import streamlit as st

from psikorehber import citations
from psikorehber.config import Settings, load_settings
from psikorehber.llm import LLM, make_llm
from psikorehber.resources import ABROAD_NOTE, EMERGENCY_ROOM_NOTE, HELPLINES, KADES_NOTE
from psikorehber.safety import Assessment
from psikorehber.storage import Storage, User

_counter = itertools.count()


@st.cache_resource
def settings() -> Settings:
    return load_settings()


@st.cache_resource
def storage() -> Storage:
    return Storage(settings().db_path)


@st.cache_resource
def llm() -> LLM:
    return make_llm(settings())


def current_user() -> User | None:
    uid = st.session_state.get("uid")
    if uid is None:
        return None
    user = storage().get_user(uid)
    if user is None:  # hesap silinmiş
        logout()
    return user


def logout() -> None:
    for key in list(st.session_state.keys()):
        del st.session_state[key]


CSS = """
<style>
/* Okunabilir satır uzunluğu */
.block-container { max-width: 52rem; padding-top: 2.2rem; }
h1, h2, h3 { letter-spacing: -0.01em; }
/* Kriz kartı: rengin yanında ikon ve metin de var (yalnızca renge dayanmıyor) */
[class*="st-key-crisis"] {
  border: 1.5px solid #B42318; border-left-width: 6px; border-radius: 0.75rem;
  padding: 0.9rem 1.1rem; background: rgba(180, 35, 24, 0.07);
}
[class*="st-key-crisis"] p, [class*="st-key-crisis"] li { margin-bottom: 0.15rem; }
/* Dayanak notları biraz daha sakin */
[data-testid="stChatMessage"] em { opacity: 0.92; }
/* Dokunmatik hedefler en az 44px */
.stButton button, .stLinkButton a, [data-testid="stBaseButton-pills"] { min-height: 44px; }
/* Kaynak dipnotu */
[data-testid="stChatMessage"] hr { margin: 0.8rem 0 0.4rem; }
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: 0.01ms !important; transition-duration: 0.01ms !important; }
}
</style>
"""


# Koyu temada birincil renk (#7FC8BD) açık; Streamlit buton yazısını beyaz yapıyor ve kontrast
# ~1.9:1 kalıyor. Tek bir renk hem koyu zeminde hem beyaz yazıyla 4.5:1 sağlayamadığı için yazıyı koyulaştır.
DARK_CSS = """
<style>
[data-testid="stBaseButton-primary"], [data-testid="stBaseButton-primaryFormSubmit"],
[data-testid="stBaseButton-primary"] *, [data-testid="stBaseButton-primaryFormSubmit"] * { color: #0B1110 !important; }
</style>
"""


def inject_css() -> None:
    st.html(CSS)
    try:
        dark = st.context.theme.type == "dark"
    except Exception:  # noqa: BLE001
        dark = False
    if dark:
        st.html(DARK_CSS)


def demo_banner() -> None:
    if settings().demo_mode:
        st.info(
            "**Demo modu:** API anahtarı tanımlı değil, cevaplar gerçek değil, sabit örnek. "
            "Gerçek kullanım için `.env` dosyasına `GEMINI_API_KEY` ekle.",
            icon=":material/science:",
        )


def assistant_markdown(raw: str, *, streaming: bool = False) -> str:
    rendered = citations.render(raw, streaming=streaming)
    return rendered.text if streaming else rendered.full_markdown()


def helpline_lines(numbers: tuple[str, ...]) -> list[str]:
    by_number = {h.number: h for h in HELPLINES}
    return [f"📞 **[{n}](tel:{n})** — {by_number[n].name} ({by_number[n].hours})" for n in numbers]


def crisis_card(a: Assessment, *, compact: bool = False, from_onboarding: bool = False) -> None:
    """Modelden bağımsız, sabit ve doğrulanmış kriz bilgisi."""
    if not a.needs_card:
        return
    key = f"crisis-{next(_counter)}"
    with st.container(key=key):
        if a.level == "concern" and not (a.categories & {"violence", "overdose", "harm_to_others"}):
            st.markdown(
                "**Bunları taşımak ağır olabilir.** Eğer kendine zarar verme düşünceleri belirirse **[112](tel:112)** her zaman "
                "açık; en yakın acil servise de gidebilirsin."
            )
            return
        if compact:
            st.markdown("**Hatırlatma:** Tehlikedeysen **[112](tel:112)**'yi ara ya da en yakın acil servise git.")
            return

        lines: list[str] = []
        if from_onboarding:
            st.markdown("**Tanışma sorularında son zamanlarda zor düşünceler yaşadığını belirttin.**")
        else:
            st.markdown("**Şu an tehlikedeysen yalnız değilsin, hemen destek alabilirsin.**")
        lines += helpline_lines(("112",))
        if a.categories & {"self_harm", "self_harm_concern"}:
            lines.append(f"🏥 {EMERGENCY_ROOM_NOTE}")
            lines.append("🤝 Güvendiğin birine şimdi haber ver; mümkünse yalnız kalma.")
            lines.append("🧰 Kendine zarar verebileceğin şeyleri (ilaç, kesici alet) kendinden uzaklaştır.")
        if "violence" in a.categories:
            lines += helpline_lines(("183",))
            lines.append(f"📱 {KADES_NOTE}")
        if "overdose" in a.categories:
            lines += helpline_lines(("114",))
        if "harm_to_others" in a.categories:
            lines.append("🚶 Biri zarar görebilecekse önce ortamdan uzaklaş ve 112'yi ara.")
        st.markdown("\n".join(f"- {line}" for line in lines))
        st.caption(
            f"{ABROAD_NOTE} · Bu kutu, yazdıklarındaki bazı ifadeler nedeniyle otomatik gösterildi; "
            "yanlış alarm olabilir."
        )


def sidebar_footer(user: User | None) -> None:
    with st.sidebar:
        st.space("small")
        st.caption("Acil durumda **[112](tel:112)** · Psikorehber bir terapist ya da acil servis değildir.")
        if user is not None:
            if st.button("Çıkış yap", icon=":material/logout:", type="tertiary", key="logout_btn"):
                logout()
                st.rerun()
