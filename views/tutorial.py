"""Uygulama tanıtımı: kısa, atlanabilir, istendiğinde tekrar açılabilir.

Mantık: Adım sınırların dışına çıkılamaz; "Atla" da "Bitir" de tanıtımı tamamlanmış sayar;
Ayarlar'dan tekrar açıldığında her zaman ilk adımdan başlar.
"""

from __future__ import annotations

import streamlit as st

from psycalm.citations import render
from psycalm.modes import MODES

from . import ui

SAMPLE_REPLY = (
    "Bir süredir gece uyanıp tekrar uyuyamamak gerçekten yıpratıcı, özellikle de gün içinde derslere "
    "odaklanman gerekiyorsa.\n\n"
    "Kronik uykusuzlukta en çok önerilen yaklaşım ilaçtan önce uykuya özgü bir terapi (BDT-U). Küçük bir "
    "başlangıç olarak bu hafta her sabah aynı saatte kalkmayı deneyebilirsin, gece ne kadar uyumuş olursan ol.\n\n"
    "*Dayanak: 🟢 Güçlü dayanak — klinik kılavuzlar uykusuzlukta ilk basamak olarak BDT-U'yu öneriyor.* "
    "[kaynak:acp-insomnia] [kaynak:nhs-insomnia]"
)


def _step_what() -> None:
    st.markdown(
        "Psycalm bir **yönlendirme asistanı**. Üç şeyde iyi olmaya çalışır:\n\n"
        "1. **Anlamak:** Ne yaşadığını toparlamana ve adını koymana yardım eder.\n"
        "2. **Güvenilir bilgi:** Önerilerinin neye dayandığını söyler, doğrulanmış kaynak gösterir.\n"
        "3. **Doğru yönlendirme:** Gerektiğinde kime, nereye ve nasıl başvuracağını somut olarak anlatır."
    )


def _step_not() -> None:
    st.markdown(
        "Dürüst olmak gerekirse sınırları da var:\n\n"
        "- **Terapist ya da doktor değil.** Teşhis koymaz, ilaç önermez.\n"
        "- **Bir yapay zekâ.** Yanılabilir; önemli kararları tek başına ona dayandırma.\n"
        "- **Acil servis değil.** Kendini tehlikede hissedersen **112**'yi ara. Uygulama böyle bir durumu fark "
        "ederse ekranda acil durum bilgisi gösterir."
    )


def _step_how() -> None:
    st.markdown(
        "Anlattıkların ne kadar somutsa yönlendirme o kadar isabetli olur: ne zamandır, ne sıklıkta, hayatını "
        "nasıl etkiliyor. Bir cevap örneği:"
    )
    with st.chat_message("assistant", avatar=":material/spa:"):
        st.markdown(render(SAMPLE_REPLY).full_markdown())
    st.markdown(
        "- **Dayanak** satırı önerinin ne kadar sağlam bir temele dayandığını söyler (🟢 güçlü, 🟡 sınırlı, "
        "⚪ yaygın uygulama).\n"
        "- **¹ ²** numaraları alttaki kaynaklara karşılık gelir. Kaynaklar elle doğrulanmış bir listeden gelir; "
        "yapay zekâ link uyduramaz."
    )


def _step_modes() -> None:
    st.markdown("Sohbetin tonunu sağ üstteki **Mod** menüsünden istediğin an değiştirebilirsin:")
    for m in MODES.values():
        with st.container(border=True):
            st.markdown(f"**{m.icon} {m.name}** — {m.tagline}  \n{m.description}")
    st.caption("Açık sözlü mod ayrı bir onay ister. Hiçbir mod güvenlik kurallarını kapatmaz.")


def _step_tools() -> None:
    st.markdown(
        "Sol menüde:\n\n"
        "- **Sohbet:** Yeni sohbet başlat, eski sohbetlerine dön.\n"
        "- **Nefes:** Kanıt düzeyi belirtilmiş, rehberli nefes egzersizleri.\n"
        "- **Yardım ve Kaynaklar:** Acil hatlar, kime başvurmalı rehberi, okuma listesi. Giriş yapmadan da açılır.\n"
        "- **Hafıza:** İzin verdiysen sohbetlerden çıkarılan notlar; hepsini görebilir ve silebilirsin.\n"
        "- **Ayarlar:** Cevaplarını düzenle, izinlerini yönet, verilerini indir ya da hesabını sil."
    )
    st.info(
        "Gizliliğin için: adını, adresini, T.C. kimlik numaranı ya da seni tanıtacak başka bilgileri yazmana "
        "gerek yok.",
        icon=":material/lock:",
    )


STEPS = (
    ("Psycalm nedir?", _step_what),
    ("Ne değildir?", _step_not),
    ("Nasıl kullanılır?", _step_how),
    ("Modlar", _step_modes),
    ("Araçlar ve gizlilik", _step_tools),
)


def _finish() -> None:
    user = ui.current_user()
    ui.storage().update_user(user.id, tutorial_done=1)
    st.session_state.pop("tour_step", None)
    st.rerun()


def page() -> None:
    if ui.current_user() is None:
        return
    step = max(0, min(len(STEPS) - 1, st.session_state.get("tour_step", 0)))
    title, body = STEPS[step]
    st.title("Hoş geldin")
    st.progress(3 / 3, text="Adım 3 / 3 · Kısa tanıtım")
    st.caption(f"{step + 1} / {len(STEPS)}  " + " ".join("●" if i == step else "○" for i in range(len(STEPS))))
    st.subheader(title)
    body()

    st.space("small")
    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        if step > 0 and st.button("Geri", icon=":material/arrow_back:", width="stretch"):
            st.session_state.tour_step = step - 1
            st.rerun()
    with c2:
        if step < len(STEPS) - 1 and st.button("Atla", type="tertiary", width="stretch"):
            _finish()
    with c3:
        last = step == len(STEPS) - 1
        label = "Sohbete başla" if last else "İleri"
        if st.button(label, type="primary", icon=":material/arrow_forward:", icon_position="right",
                     width="stretch"):
            if last:
                _finish()
            else:
                st.session_state.tour_step = step + 1
                st.rerun()
