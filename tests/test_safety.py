import pytest

from psycalm.safety import assess, assess_onboarding, prompt_note
from psycalm.text import fold, tr_lower


def test_turkish_lowercase_is_correct():
    # Python'un kendi lower()'ı "İ"yi "i̇" (iki karakter) yapar; bizimki doğru çevirmeli
    assert tr_lower("İSTANBUL") == "istanbul"
    assert tr_lower("ILIK") == "ılık"
    assert fold("ÖLMEK İSTİYORUM") == "olmek istiyorum"
    assert fold("  çok   yorgunum ") == "cok yorgunum"


@pytest.mark.parametrize(
    "text",
    [
        "Artık ölmek istiyorum",
        "OLMEK ISTIYORUM",  # Türkçe karakter ve büyük harf olmadan
        "intihar etmeyi düşünüyorum",
        "Kendimi öldürmek istiyorum",
        "bazen kendime zarar veriyorum",
        "kendimi kesiyorum",
        "yaşamak istemiyorum artık",
        "canıma kıymak istiyorum",
        "hayatıma son vermek istiyorum",
        "köprüden atlamayı düşünüyorum",
        "keşke ölsem",
        "ölesim geliyor",
    ],
)
def test_self_harm_is_high(text):
    a = assess(text)
    assert a.level == "high"
    assert "self_harm" in a.categories


@pytest.mark.parametrize(
    "text",
    [
        "artık dayanamıyorum",
        "her şey anlamsız geliyor",
        "yok olmak istiyorum",
        "keşke bir daha uyanmasam",
        "herkes bensiz daha iyi olur",
        "ailemize yük oluyorum",
    ],
)
def test_indirect_signals_are_concern(text):
    assert assess(text).level == "concern"


@pytest.mark.parametrize(
    "text",
    [
        # Eski örnek mesaj: yorgunluk, risk değil
        "derslerim kötü. ders çalışasım gelmiyor. hatta uyanasım bile gelmiyor.",
        "gülmekten öldüm",
        "olmak istediğim kişi bu değil",
        "kendimi dışarı atmak istiyorum, biraz yürüyeceğim",
        "ölüm korkum var, sağlığım için endişeleniyorum",
        "ilacımı içtim",
        "",
    ],
)
def test_ordinary_messages_are_not_flagged(text):
    assert assess(text).level == "none"


def test_violence_overdose_and_others():
    assert "violence" in assess("eşim beni dövüyor").categories
    assert "violence" in assess("babam bizi tehdit ediyor").categories
    assert "overdose" in assess("bir kutu ilaç içtim").categories
    assert "overdose" in assess("hapları fazla içtim").categories
    assert "harm_to_others" in assess("onu öldüreceğim").categories
    # "kendimi öldüreceğim" başkasına zarar değil, kendine zarar
    a = assess("kendimi öldüreceğim")
    assert "self_harm" in a.categories and "harm_to_others" not in a.categories


def test_minor_detection():
    assert assess("16 yaşındayım").minor
    assert assess("lise 2'deyim").minor
    assert not assess("26 yaşındayım").minor
    assert assess("16 yaşındayım").level == "none"


def test_onboarding_answer_mapping():
    assert assess_onboarding("su_an").level == "high"
    assert assess_onboarding("siklikla").level == "high"
    assert assess_onboarding("bazen").level == "concern"
    assert assess_onboarding("hayir").level == "none"
    assert assess_onboarding(None).level == "none"


def test_prompt_note_never_calls_182_a_crisis_line():
    note = prompt_note(assess("intihar etmek istiyorum, eşim beni dövüyor, bir kutu ilaç içtim"))
    assert "112" in note and "183" in note and "114" in note
    assert "182" not in note
