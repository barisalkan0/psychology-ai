"""Uygulama ayarları.

Değerler önce ortam değişkenlerinden (.env), sonra Streamlit secrets'tan okunur.
Böylece hem yerelde (`.env`) hem Streamlit Community Cloud'da (`secrets.toml`) çalışır.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

ROOT = Path(__file__).resolve().parent.parent

# Model adı sabit kodlanmıyor: Google eski modelleri kapattığında (ör. gemini-2.5-flash
# için 2026 sonu kapatma duyuruları var) uygulama 404 ile çökmesin diye
# varsayılan "latest" takma adı kullanılıyor. Üretimde sabit sürüm adı verilmesi önerilir.
DEFAULT_MODEL = "gemini-flash-latest"


def _secret(name: str) -> str | None:
    value = os.getenv(name)
    if value:
        return value
    try:  # Streamlit yoksa veya secrets dosyası yoksa sessizce geç
        import streamlit as st

        return st.secrets.get(name)  # type: ignore[no-any-return]
    except Exception:
        return None


def _flag(name: str, default: bool = False) -> bool:
    raw = _secret(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "evet", "on"}


@dataclass(frozen=True)
class Settings:
    api_key: str | None
    model: str
    db_path: Path
    # Ücretli Gemini API kotası mı kullanılıyor? Ücretsiz kotada Google içerikleri ürün
    # geliştirmek için kullanabilir ve insan değerlendiriciler okuyabilir; rıza metni buna
    # göre değişir. Emin değilsen False bırak.
    paid_tier: bool
    # API anahtarı yoksa ya da açıkça istenirse örnek cevaplarla çalışan demo modu.
    mock: bool
    # Rıza metnindeki veri sorumlusu bilgisi (KVKK aydınlatma yükümlülüğü).
    controller_name: str
    controller_contact: str

    @property
    def demo_mode(self) -> bool:
        return self.mock or not self.api_key


def load_settings() -> Settings:
    api_key = _secret("GEMINI_API_KEY") or _secret("API_KEY")  # API_KEY: eski sürümle uyum
    db = _secret("PSYCALM_DB") or str(ROOT / "data" / "psycalm.db")
    return Settings(
        api_key=api_key,
        model=_secret("GEMINI_MODEL") or DEFAULT_MODEL,
        db_path=Path(db),
        paid_tier=_flag("GEMINI_PAID_TIER"),
        mock=_flag("PSYCALM_MOCK"),
        controller_name=_secret("VERI_SORUMLUSU") or "Psycalm geliştiricisi",
        controller_contact=_secret("VERI_SORUMLUSU_ILETISIM") or "(iletişim adresi eklenmedi)",
    )
