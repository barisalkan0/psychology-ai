"""Rehberli nefes egzersizleri.

Her tekniğin yanında dürüst bir dayanak notu var. Nefes egzersizleri stresi küçük-orta
düzeyde azaltabilir, ama tedavi değildir; özellikle "en iyi teknik" iddiası araştırmayla
desteklenmiyor (bir çalışmada yavaş nefes plaseboya üstün çıkmadı).
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import streamlit as st
import streamlit.components.v1 as components

from psycalm.citations import render
from psycalm.resources import EVIDENCE

TEMPLATE = (Path(__file__).resolve().parent.parent / "assets" / "breathing.html").read_text(encoding="utf-8")

PALETTES = {
    "light": {"BG": "#FAF8F4", "FG": "#1F2A2A", "MUTED": "#5B6764", "ACCENT": "#2F6F6A",
              "ACCENT_SOFT": "#7FB8AF", "RING": "#DDD7CB", "BTN_FG": "#FFFFFF"},
    "dark": {"BG": "#121816", "FG": "#E6ECEA", "MUTED": "#A3B0AC", "ACCENT": "#4FA397",
             "ACCENT_SOFT": "#9AD8CE", "RING": "#2C3934", "BTN_FG": "#0B1110"},
}


@dataclass(frozen=True)
class Technique:
    key: str
    name: str
    summary: str
    phases: tuple[dict, ...]
    evidence: str
    basis: str
    caution: str = ""


TECHNIQUES = (
    Technique(
        "uzun-verme", "Uzun nefes verme (4–6)",
        "4 saniye al, 6 saniye ver: dakikada 6 nefes. Başlamak için en kolay teknik.",
        (
            {"name": "Nefes al", "hint": "Burnundan yavaşça, karnın şişecek şekilde nefes al", "seconds": 4, "scale": 1.0},
            {"name": "Nefes ver", "hint": "Burnundan ya da hafif aralık dudaklarından yavaşça ver", "seconds": 6, "scale": 0.42},
        ),
        "orta",
        "Dakikada 10'dan az nefesle yapılan yavaş nefes, sakinleşmeyle ilişkili beden tepkileriyle bağlantılı "
        "bulunmuş [kaynak:slow-breathing-review]. Nefes çalışmalarını birleştiren bir analizde stres küçük-orta "
        "düzeyde azalmış; ama çalışmalar az ve bir çalışmada bu teknik sahte (plasebo) nefes egzersizinden üstün "
        "çıkmamış [kaynak:breathwork-meta].",
    ),
    Technique(
        "ic-cekis", "Döngüsel iç çekiş",
        "Burnundan iki aşamalı nefes al, ağzından uzun uzun ver. Günde 5 dakika önerilir.",
        (
            {"name": "Nefes al", "hint": "Burnundan derin bir nefes al", "seconds": 2.5, "scale": 0.85},
            {"name": "Biraz daha", "hint": "Burnundan kısa bir nefes daha ekle, ciğerlerini doldur", "seconds": 1.0, "scale": 1.0},
            {"name": "Nefes ver", "hint": "Ağzından yavaşça, sonuna kadar ver", "seconds": 6.0, "scale": 0.42},
        ),
        "orta",
        "Bir ay boyunca günde 5 dakika yapılan döngüsel iç çekiş, ruh hâlini farkındalık meditasyonundan daha "
        "fazla iyileştirmiş [kaynak:cyclic-sighing]. Umut verici ama tek bir çalışma; tekrarlanması gerekiyor.",
    ),
    Technique(
        "kutu", "Kutu nefesi (4–4–4–4)",
        "Al, tut, ver, bekle; her biri 4 saniye. Dikkati toparlamak için sık kullanılır.",
        (
            {"name": "Nefes al", "hint": "Burnundan 4 saniyede nefes al", "seconds": 4, "scale": 1.0},
            {"name": "Tut", "hint": "Nefesini zorlamadan, rahatça tut", "seconds": 4, "scale": 1.0},
            {"name": "Nefes ver", "hint": "4 saniyede yavaşça ver", "seconds": 4, "scale": 0.42},
            {"name": "Bekle", "hint": "Boş ciğerle rahatça bekle", "seconds": 4, "scale": 0.42},
        ),
        "deneyim",
        "Yaygın kullanılan bir teknik. Aynı çalışmada etkili bulunmuş ama döngüsel iç çekişin gerisinde kalmış "
        "[kaynak:cyclic-sighing]; doğrudan araştırması sınırlı.",
        caution="Nefes tutma içerdiği için astım, KOAH gibi bir solunum rahatsızlığın ya da kalp rahatsızlığın varsa "
        "tutma bölümlerini kısalt veya atla.",
    ),
)
BY_KEY = {t.key: t for t in TECHNIQUES}
DURATIONS = {1: "1 dk", 3: "3 dk", 5: "5 dk"}


def _theme_type() -> str:
    try:
        t = st.context.theme.type
    except Exception:  # noqa: BLE001
        t = None
    return t if t in PALETTES else "light"


def _component_html(t: Technique, minutes: int) -> str:
    cfg = {"phases": list(t.phases), "totalSeconds": minutes * 60}
    html = TEMPLATE.replace("__CONFIG__", json.dumps(cfg, ensure_ascii=False))
    for k, v in PALETTES[_theme_type()].items():
        html = html.replace(f"__{k}__", v)
    return html


def page() -> None:
    st.title("Nefes")
    st.markdown(
        "Gerginlik anında birkaç dakikalık yavaş nefes, bedenin sakinleşmesine yardım edebilir. "
        "Tedavi değildir; ama elinin altında olan, ücretsiz bir araçtır."
    )
    key = st.segmented_control(
        "Teknik", [t.key for t in TECHNIQUES], format_func=lambda k: BY_KEY[k].name,
        default="uzun-verme", required=True, key="breath_tech",
    )
    minutes = st.segmented_control(
        "Süre", list(DURATIONS), format_func=DURATIONS.get, default=3, required=True, key="breath_min",
    )
    t = BY_KEY[key or "uzun-verme"]
    st.caption(t.summary)
    components.html(_component_html(t, minutes or 3), height=500)

    ev = EVIDENCE[t.evidence]
    with st.container(border=True):
        rendered = render(t.basis)
        st.markdown(f"**Neye dayanıyor?** {ev.icon} {ev.label}\n\n{rendered.text}{rendered.footer_markdown()}")
    with st.expander("Güvenli kullanım", icon=":material/health_and_safety:"):
        st.markdown(
            "- Başın dönerse, karıncalanma ya da nefes darlığı hissedersen dur ve normal nefesine dön.\n"
            "- Zorlama: süreler bir öneri, rahat edeceğin şekilde kısaltabilirsin.\n"
            "- Araç kullanırken ya da suya girerken yapma.\n"
            + (f"- {t.caution}\n" if t.caution else "")
            + "- Panik atak benzeri yakınmalar ilk kez oluyorsa ya da göğüs ağrısı varsa önce bir hekime görün; "
            "acil durumda **112**."
        )
    st.caption("Ekran okuyucu kullanıyorsan yönergeler ses olarak okunur. Boşluk tuşuyla başlatıp duraklatabilirsin.")
