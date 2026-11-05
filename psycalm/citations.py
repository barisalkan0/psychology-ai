"""Model çıktısındaki [kaynak:kimlik] işaretlerini numaralı kaynaklara çevirir.

- Katalogda olmayan kimlikler sessizce atılır: uydurma kaynak ekrana çıkamaz.
- Aynı kaynak birden çok kez geçerse aynı numarayı alır.
- Akış (streaming) sırasında yarım kalmış "[kayn" gibi parçalar gizlenir, kullanıcı
  ekranda ham işaret görmez.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from .resources import EVIDENCE, SOURCES_BY_ID, Source

MARKER = re.compile(r"\s?\[kaynak:\s*([a-z0-9\-]+)\s*\]", re.IGNORECASE)
# Metnin sonunda yarım kalmış bir işaret: "[", "[ka", "[kaynak:who-dep" ...
_PARTIAL = re.compile(r"\s?\[(?:k(?:a(?:y(?:n(?:a(?:k(?::[a-z0-9\-\s]*)?)?)?)?)?)?)?$", re.IGNORECASE)
SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


@dataclass
class Rendered:
    text: str
    sources: list[Source]
    dropped: list[str]

    def footer_markdown(self) -> str:
        if not self.sources:
            return ""
        # "---" satırından önce BOŞ satır şart: yoksa markdown bir önceki satırı H2 başlığa çevirir
        # (setext başlık kuralı) ve "Dayanak" notu dev bir başlık olarak görünür.
        lines = ["", "", "---", "**📚 Kaynaklar**"]
        for i, s in enumerate(self.sources, start=1):
            ev = EVIDENCE[s.evidence]
            lang = "" if s.language == "tr" else " · İngilizce"
            lines.append(f"{i}. [{s.title}]({s.url}) — {s.publisher} · {ev.icon} {ev.label}{lang}")
        return "\n".join(lines)

    def full_markdown(self) -> str:
        return self.text + self.footer_markdown()


def render(text: str, *, streaming: bool = False) -> Rendered:
    if streaming:
        text = _PARTIAL.sub("", text)

    order: dict[str, int] = {}
    sources: list[Source] = []
    dropped: list[str] = []

    last_end = -1  # bir önceki geçerli işaretin bittiği yer

    def _replace(match: re.Match[str]) -> str:
        nonlocal last_end
        sid = match.group(1).lower()
        source = SOURCES_BY_ID.get(sid)
        if source is None:
            dropped.append(sid)
            if last_end >= 0 and not text[last_end : match.start()].strip():
                last_end = match.end()  # bitişiklik zinciri kopmasın
            return ""
        if sid not in order:
            order[sid] = len(order) + 1
            sources.append(source)
        sup = str(order[sid]).translate(SUPERSCRIPT)
        adjacent = last_end >= 0 and not text[last_end : match.start()].strip()
        last_end = match.end()
        if adjacent:  # "¹²" on iki gibi okunur; "¹,²" yaz
            return "," + sup
        # "*Dayanak…* [kaynak:x]" → "*Dayanak…*¹" olursa kapanış yıldızı markdown'da geçersiz kalır
        # (ardından boşluk/noktalama gelmeli) ve yıldızlar çıplak görünür. Böyle durumda boşluğu koru.
        start = match.start()
        if start > 0 and match.group(0)[:1].isspace() and text[start - 1] in "*_":
            return " " + sup
        return sup

    out = MARKER.sub(_replace, text)
    return Rendered(text=out, sources=sources, dropped=dropped)


def strip_markers(text: str) -> str:
    """Hafıza özeti gibi yerlerde işaretleri tamamen kaldır."""
    return MARKER.sub("", text)
