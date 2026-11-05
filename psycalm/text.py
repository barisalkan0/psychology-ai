"""Türkçe metin yardımcıları.

Python'un `str.lower()` fonksiyonu Türkçe için yanlıştır: "İ".lower() → "i̇" (i + birleşik
nokta) ve "I".lower() → "i" (doğrusu "ı"). Anahtar kelime eşleştirmesi bu yüzden
sessizce kaçırabilir. Burada önce Türkçeye uygun küçültme, sonra ASCII'ye katlama
yapıyoruz ki "ÖLMEK", "ölmek" ve Türkçe karakter kullanmadan yazılmış "olmek"
aynı şekilde yakalansın.
"""

from __future__ import annotations

import re
import unicodedata

_TR_UPPER = str.maketrans({"I": "ı", "İ": "i"})
_FOLD = str.maketrans({"ç": "c", "ğ": "g", "ı": "i", "ö": "o", "ş": "s", "ü": "u", "â": "a", "î": "i", "û": "u"})
_SPACE = re.compile(r"\s+")


def tr_lower(text: str) -> str:
    return text.translate(_TR_UPPER).lower()


def fold(text: str) -> str:
    """Türkçe küçült, aksanları kaldır, boşlukları sadeleştir."""
    lowered = tr_lower(text).translate(_FOLD)
    # Kalan birleşik işaretleri (ör. kopyala-yapıştırdan gelen) temizle
    decomposed = unicodedata.normalize("NFKD", lowered)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return _SPACE.sub(" ", stripped).strip()


def truncate(text: str, limit: int) -> str:
    text = _SPACE.sub(" ", text).strip()
    if len(text) <= limit:
        return text
    cut = text[: limit - 1].rsplit(" ", 1)[0]
    return (cut or text[: limit - 1]) + "…"
