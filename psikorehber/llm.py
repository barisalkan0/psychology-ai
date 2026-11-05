"""Dil modeli istemcisi.

Eski sürümün sorunları:
- API hatası, kota aşımı ya da güvenlik filtresi engeli olunca uygulama çöküyordu
  (`response.text` None dönünce ya da istisna fırlayınca kırmızı hata ekranı).
- Akış (streaming) yoktu; kullanıcı cevap gelene kadar donmuş bir ekran görüyordu.
- Her mesajda sohbet geçmişi sınırsız gönderiliyordu.

Burada:
- `stream_reply` metin parçalarını akıtır, hataları kullanıcıya uygun mesajlara çevirir.
- Güvenlik filtresi cevabı engellerse sabit ve güvenli bir yedek metin döner.
- API anahtarı yoksa `MockLLM` demo cevaplarıyla arayüz test edilebilir.
"""

from __future__ import annotations

import json
import logging
import time
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Protocol

log = logging.getLogger(__name__)

MAX_HISTORY_MESSAGES = 30

BLOCKED_FALLBACK = (
    "Bu mesaja otomatik güvenlik filtresi nedeniyle cevap üretemedim. Bu senin yazdığın şeyin yanlış olduğu "
    "anlamına gelmiyor.\n\nEğer şu an kendini güvende hissetmiyorsan lütfen **112**'yi ara ya da en yakın acil "
    "servise git. Dilersen yaşadığını biraz farklı kelimelerle anlatmayı deneyebilirsin; buradayım."
)


class LLMError(Exception):
    """Kullanıcıya gösterilebilecek, Türkçe açıklamalı hata."""

    def __init__(self, user_message: str, *, retryable: bool = True):
        super().__init__(user_message)
        self.user_message = user_message
        self.retryable = retryable


@dataclass
class ChatTurn:
    role: str  # "user" | "assistant"
    content: str


class LLM(Protocol):
    def stream_reply(
        self, *, system_prompt: str, history: list[ChatTurn], temperature: float
    ) -> Iterator[str]: ...

    def extract_memory(self, transcript: str) -> list[str]: ...


def _to_contents(history: list[ChatTurn]) -> list[dict]:
    trimmed = history[-MAX_HISTORY_MESSAGES:]
    # Gemini geçmişin kullanıcı mesajıyla başlamasını bekler
    while trimmed and trimmed[0].role != "user":
        trimmed = trimmed[1:]
    return [
        {"role": "model" if t.role == "assistant" else "user", "parts": [{"text": t.content}]} for t in trimmed
    ]


def _parse_json_list(raw: str) -> list[str]:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        raw = raw.split("\n", 1)[1] if "\n" in raw else raw
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    if not isinstance(data, list):
        return []
    notes = [str(x).strip() for x in data if isinstance(x, (str, int, float)) and str(x).strip()]
    return [n[:200] for n in notes[:5]]


class GeminiLLM:
    def __init__(self, api_key: str, model: str):
        from google import genai

        self._client = genai.Client(api_key=api_key)
        self._model = model

    def _config(self, system_prompt: str, temperature: float, **extra):
        from google.genai import types

        # Ruh sağlığı sohbetlerinde "tehlikeli içerik" filtresi kriz mesajlarına verilen cevabı bile
        # engelleyebiliyor. Yalnızca yüksek şiddette engelleme; asıl güvenlik bizim kurallarımızda ve
        # deterministik kriz katmanında.
        relaxed = types.HarmBlockThreshold.BLOCK_ONLY_HIGH
        safety = [
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HARASSMENT, threshold=relaxed),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_HATE_SPEECH, threshold=relaxed),
            types.SafetySetting(category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT, threshold=relaxed),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT,
                threshold=types.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            ),
        ]
        return types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=temperature,
            # Yeni Gemini modellerinde "düşünme" token'ları da bu sınıra sayılabiliyor; düşük tutulursa cevap kesilir
            max_output_tokens=8192,
            safety_settings=safety,
            **extra,
        )

    def stream_reply(self, *, system_prompt: str, history: list[ChatTurn], temperature: float) -> Iterator[str]:
        contents = _to_contents(history)
        config = self._config(system_prompt, temperature)
        for attempt in (1, 2):
            produced = False
            try:
                stream = self._client.models.generate_content_stream(
                    model=self._model, contents=contents, config=config
                )
                blocked = False
                for chunk in stream:
                    if chunk.prompt_feedback and chunk.prompt_feedback.block_reason:
                        blocked = True
                        break
                    text = chunk.text or ""
                    if text:
                        produced = True
                        yield text
                    cand = chunk.candidates[0] if chunk.candidates else None
                    reason = getattr(cand, "finish_reason", None)
                    if reason is not None and getattr(reason, "name", "") in {
                        "SAFETY", "PROHIBITED_CONTENT", "BLOCKLIST", "SPII"
                    }:
                        blocked = True
                if blocked and not produced:
                    yield BLOCKED_FALLBACK
                return
            except Exception as exc:  # noqa: BLE001 — SDK farklı istisna türleri fırlatabiliyor
                err = _translate(exc, self._model)
                # Yalnızca hiçbir şey üretilmeden düşen geçici hatalarda bir kez yeniden dene
                if attempt == 1 and err.retryable and not produced:
                    time.sleep(1.5)
                    continue
                raise err from exc

    def extract_memory(self, transcript: str) -> list[str]:
        from .prompts import MEMORY_EXTRACTION_PROMPT

        try:
            response = self._client.models.generate_content(
                model=self._model,
                contents=[{"role": "user", "parts": [{"text": transcript}]}],
                config=self._config(
                    MEMORY_EXTRACTION_PROMPT, 0.2, response_mime_type="application/json"
                ),
            )
            return _parse_json_list(response.text or "[]")
        except Exception as exc:  # noqa: BLE001
            raise _translate(exc, self._model) from exc


def _translate(exc: Exception, model: str) -> LLMError:
    from google.genai import errors

    log.warning("LLM hatası: %s", exc)
    if isinstance(exc, errors.APIError):
        code = getattr(exc, "code", None)
        if code in (401, 403):
            return LLMError("API anahtarı geçersiz ya da yetkisiz. `.env` dosyasındaki GEMINI_API_KEY'i kontrol et.", retryable=False)
        if code == 404:
            return LLMError(
                f"“{model}” modeli bulunamadı (kapatılmış olabilir). `.env` içinde GEMINI_MODEL'i güncel bir "
                "modelle değiştir.", retryable=False,
            )
        if code == 429:
            return LLMError("Şu an çok fazla istek var ya da günlük kota doldu. Biraz sonra tekrar dene.")
        if code == 400:
            return LLMError("İstek işlenemedi. Mesajı kısaltıp tekrar dener misin?", retryable=False)
        if code and code >= 500:
            return LLMError("Yapay zekâ servisi geçici olarak yanıt vermiyor. Birazdan tekrar dene.")
    return LLMError("Bağlantı kurulamadı. İnternet bağlantını kontrol edip tekrar dene.")


class MockLLM:
    """API anahtarı olmadan arayüzü denemek ve test etmek için sabit cevaplar."""

    def stream_reply(self, *, system_prompt: str, history: list[ChatTurn], temperature: float) -> Iterator[str]:
        last = history[-1].content if history else ""
        status = system_prompt.split("GÜNCEL DURUM NOTU", 1)[1] if "GÜNCEL DURUM NOTU" in system_prompt else ""
        if "intihar" in status:
            reply = (
                "Bunu benimle paylaştığın için iyi ki yazdın. Önce şunu sormak istiyorum: **şu an güvende misin?**\n\n"
                "Eğer kendine zarar verebileceğinden endişe ediyorsan lütfen hemen **112**'yi ara ya da en yakın acil "
                "servise git. Bu sırada yalnız kalmamaya çalış.\n\n*(Demo modu: Bu sabit bir örnek cevaptır.)*"
            )
        else:
            reply = (
                f"Yazdıklarını okudum: “{last[:80]}”. Bu demo modunda gerçek bir yapay zekâ cevabı üretilmiyor; "
                "arayüzü denemen için örnek bir cevap gösteriyorum.\n\n"
                "Gerçek modda burada önce seni anlamaya çalışan bir cevap, gerekirse küçük bir adım ve bu adımın "
                "dayanağı olurdu. Örneğin keyifsizlik dönemlerinde küçük ve keyif veren etkinlikleri planlamak işe "
                "yarayabilir.\n\n"
                "*Dayanak: 🟢 Güçlü dayanak — davranışsal aktivasyon depresif belirtilerde etkili bulunmuş.* "
                "[kaynak:behavioral-activation] [kaynak:nice-depression]"
            )
        for i in range(0, len(reply), 12):
            time.sleep(0.01)
            yield reply[i : i + 12]

    def extract_memory(self, transcript: str) -> list[str]:
        return ["Kullanıcı demo modunda bir sohbet yaptı."] if transcript.strip() else []


def make_llm(settings) -> LLM:
    if settings.demo_mode:
        return MockLLM()
    return GeminiLLM(settings.api_key, settings.model)
