import re

from psycalm import citations
from psycalm.resources import EVIDENCE, HELPLINES, SOURCES, SOURCES_BY_ID, SPECIALISTS, THERAPIST_TIPS


def test_known_markers_become_numbers_and_footer():
    r = citations.render("Yürüyüş iyi gelebilir [kaynak:exercise-depression]. Uyku [kaynak:acp-insomnia].")
    assert "[kaynak" not in r.text
    assert "¹" in r.text and "²" in r.text and "¹,²" not in r.text  # ayrı cümlelerde virgül yok
    assert [s.id for s in r.sources] == ["exercise-depression", "acp-insomnia"]
    footer = r.footer_markdown()
    assert "https://doi.org/10.1136/bmj-2023-075847" in footer


def test_unknown_markers_are_dropped_not_shown():
    r = citations.render("Bu kesin doğru [kaynak:uydurma-makale-2099].")
    assert "uydurma" not in r.text
    assert r.sources == []
    assert r.dropped == ["uydurma-makale-2099"]
    assert r.footer_markdown() == ""


def test_repeated_source_keeps_same_number():
    r = citations.render("A [kaynak:who-depression] B [kaynak:who-depression]")
    assert r.text.count("¹") == 2 and len(r.sources) == 1
    # Arada geçersiz bir işaret olsa da bitişik geçerliler virgülle ayrılır
    assert citations.render("X [kaynak:who-depression] [kaynak:yok] [kaynak:who-anxiety]").text == "X¹,²"


def test_partial_marker_hidden_while_streaming():
    for partial in ["Metin [", "Metin [ka", "Metin [kaynak:", "Metin [kaynak:who-dep"]:
        assert citations.render(partial, streaming=True).text == "Metin"
    # Normal köşeli parantez akış bitince korunur
    assert citations.render("Seçenek [a]", streaming=False).text == "Seçenek [a]"


def test_catalog_integrity():
    ids = [s.id for s in SOURCES]
    assert len(ids) == len(set(ids)), "kaynak kimlikleri benzersiz olmalı"
    for s in SOURCES:
        assert re.fullmatch(r"[a-z0-9\-]+", s.id)
        assert s.url.startswith("https://")
        assert s.evidence in EVIDENCE
    for sp in SPECIALISTS:
        for sid in sp.sources:
            assert sid in SOURCES_BY_ID
    for tip in THERAPIST_TIPS:
        assert not citations.render(tip).dropped


def test_helplines_are_correct():
    by_number = {h.number: h for h in HELPLINES}
    assert by_number["112"].is_emergency
    # Eski sürümdeki kritik hata: 182 kriz hattı değil, MHRS randevu hattı
    assert "MHRS" in by_number["182"].name
    assert not by_number["182"].is_emergency
    assert "DEĞİLDİR" in by_number["182"].note


def test_footer_never_turns_previous_line_into_heading():
    # Regresyon: "---" bir önceki satırın hemen altına gelirse markdown o satırı H2 yapar
    # ve "Dayanak" notu dev bir başlık olarak görünürdü.
    r = citations.render("*Dayanak: güçlü* [kaynak:acp-insomnia]")
    md = r.full_markdown()
    assert "\n\n---\n" in md
    assert not re.search(r"[^\n]\n---", md)


def test_emphasis_closing_star_is_not_glued_to_superscript():
    # Regresyon: "*Dayanak…*¹" markdown'da italik olmuyor, yıldızlar çıplak görünüyordu
    r = citations.render("*Dayanak: güçlü.* [kaynak:acp-insomnia] [kaynak:nhs-insomnia]")
    assert r.text == "*Dayanak: güçlü.* ¹,²"
    # Normal metinde boşluk yutulur: "uyku¹"
    assert citations.render("uyku [kaynak:acp-insomnia]").text == "uyku¹"
