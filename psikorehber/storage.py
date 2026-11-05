"""SQLite depolama.

- Şifreler scrypt ile tuzlanıp özetlenir (standart kütüphane; ek bağımlılık yok).
- Her çağrı kendi bağlantısını açar: Streamlit her oturumu ayrı bir iş parçacığında
  çalıştırdığı için paylaşılan bağlantı güvenli değildir.
- Hesap silme tüm ilişkili satırları siler (ON DELETE CASCADE) — KVKK silme hakkı.
- Rıza kayıtları ekle-sadece (append-only) tutulur: kim, hangi metin sürümünü, ne zaman
  verdi ya da geri aldı, sonradan gösterilebilsin.

Bilinen sınır: Veriler diskte şifrelenmeden durur. Gerçek kullanıcılara açmadan önce disk
şifrelemesi ya da alan bazında şifreleme düşünülmeli (bkz. docs/HUKUKI_NOTLAR.md).
"""

from __future__ import annotations

import hashlib
import hmac
import json
import os
import re
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    username TEXT NOT NULL UNIQUE,
    pw_hash BLOB NOT NULL,
    pw_salt BLOB NOT NULL,
    age_band TEXT NOT NULL,
    nickname TEXT NOT NULL DEFAULT '',
    default_mode TEXT NOT NULL DEFAULT 'dengeli',
    onboarding_done INTEGER NOT NULL DEFAULT 0,
    tutorial_done INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS profiles (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    answers_json TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS consents (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    kind TEXT NOT NULL,
    version TEXT NOT NULL,
    granted INTEGER NOT NULL,
    at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS conversations (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    title TEXT NOT NULL,
    mode TEXT NOT NULL,
    memory_extracted INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY,
    conversation_id INTEGER NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
    content TEXT NOT NULL,
    risk_level TEXT NOT NULL DEFAULT 'none',
    risk_categories TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    text TEXT NOT NULL,
    source_conversation_id INTEGER REFERENCES conversations(id) ON DELETE SET NULL,
    created_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_conv_user ON conversations(user_id, updated_at);
CREATE INDEX IF NOT EXISTS idx_msg_conv ON messages(conversation_id, id);
CREATE INDEX IF NOT EXISTS idx_consent_user ON consents(user_id, kind, id);
"""

USERNAME_RE = re.compile(r"^[a-z0-9_.\-]{3,24}$")
MIN_PASSWORD = 8
_SCRYPT = {"n": 2**14, "r": 8, "p": 1, "dklen": 32}


class StorageError(Exception):
    pass


@dataclass
class User:
    id: int
    username: str
    age_band: str
    nickname: str
    default_mode: str
    onboarding_done: bool
    tutorial_done: bool

    @property
    def is_adult(self) -> bool:
        return self.age_band != "<18"


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _hash(password: str, salt: bytes) -> bytes:
    return hashlib.scrypt(password.encode("utf-8"), salt=salt, **_SCRYPT)


def normalize_username(raw: str) -> str:
    return raw.strip().lower()


class Storage:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._conn() as c:
            c.executescript(SCHEMA)

    @contextmanager
    def _conn(self):
        conn = sqlite3.connect(self.path, timeout=10)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    # ───────────── Kullanıcılar ─────────────
    def register(self, username: str, password: str, age_band: str) -> User:
        username = normalize_username(username)
        if not USERNAME_RE.match(username):
            raise StorageError("Kullanıcı adı 3–24 karakter olmalı; yalnızca küçük harf, rakam, nokta, tire ve alt çizgi.")
        if len(password) < MIN_PASSWORD:
            raise StorageError(f"Şifre en az {MIN_PASSWORD} karakter olmalı.")
        if age_band == "<18":
            raise StorageError("Psikorehber 18 yaş ve üzeri içindir.")
        salt = os.urandom(16)
        try:
            with self._conn() as c:
                cur = c.execute(
                    "INSERT INTO users (username, pw_hash, pw_salt, age_band, created_at) VALUES (?, ?, ?, ?, ?)",
                    (username, _hash(password, salt), salt, age_band, _now()),
                )
                uid = cur.lastrowid
        except sqlite3.IntegrityError as exc:
            raise StorageError("Bu kullanıcı adı alınmış.") from exc
        return self.get_user(uid)  # type: ignore[arg-type]

    def authenticate(self, username: str, password: str) -> User | None:
        username = normalize_username(username)
        with self._conn() as c:
            row = c.execute("SELECT id, pw_hash, pw_salt FROM users WHERE username = ?", (username,)).fetchone()
        if row is None:
            # Kullanıcı yokken de aynı süre harca: zamanlama farkından kullanıcı adı tahmin edilmesin
            _hash(password, b"0" * 16)
            return None
        if not hmac.compare_digest(_hash(password, row["pw_salt"]), row["pw_hash"]):
            return None
        return self.get_user(row["id"])

    def get_user(self, user_id: int) -> User | None:
        with self._conn() as c:
            r = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if r is None:
            return None
        return User(
            r["id"], r["username"], r["age_band"], r["nickname"], r["default_mode"],
            bool(r["onboarding_done"]), bool(r["tutorial_done"]),
        )

    def update_user(self, user_id: int, **fields) -> None:
        allowed = {"nickname", "default_mode", "onboarding_done", "tutorial_done"}
        bad = set(fields) - allowed
        if bad:
            raise ValueError(f"Güncellenemez alan: {bad}")
        if not fields:
            return
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._conn() as c:
            c.execute(f"UPDATE users SET {cols} WHERE id = ?", (*fields.values(), user_id))

    def delete_user(self, user_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM users WHERE id = ?", (user_id,))

    # ───────────── Profil ─────────────
    def save_profile(self, user_id: int, answers: dict) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO profiles (user_id, answers_json, updated_at) VALUES (?, ?, ?) "
                "ON CONFLICT(user_id) DO UPDATE SET answers_json = excluded.answers_json, updated_at = excluded.updated_at",
                (user_id, json.dumps(answers, ensure_ascii=False), _now()),
            )

    def get_profile(self, user_id: int) -> dict:
        with self._conn() as c:
            r = c.execute("SELECT answers_json FROM profiles WHERE user_id = ?", (user_id,)).fetchone()
        return json.loads(r["answers_json"]) if r else {}

    # ───────────── Rızalar ─────────────
    def record_consent(self, user_id: int, kind: str, version: str, granted: bool) -> None:
        with self._conn() as c:
            c.execute(
                "INSERT INTO consents (user_id, kind, version, granted, at) VALUES (?, ?, ?, ?, ?)",
                (user_id, kind, version, int(granted), _now()),
            )

    def consent_status(self, user_id: int) -> dict[str, dict]:
        """Her rıza türü için son kayıt: {'kind': {'granted': bool, 'version': str, 'at': str}}"""
        with self._conn() as c:
            rows = c.execute(
                "SELECT kind, version, granted, at FROM consents WHERE user_id = ? ORDER BY id", (user_id,)
            ).fetchall()
        status: dict[str, dict] = {}
        for r in rows:
            status[r["kind"]] = {"granted": bool(r["granted"]), "version": r["version"], "at": r["at"]}
        return status

    def has_consent(self, user_id: int, kind: str, version: str) -> bool:
        s = self.consent_status(user_id).get(kind)
        return bool(s and s["granted"] and s["version"] == version)

    # ───────────── Sohbetler ─────────────
    def create_conversation(self, user_id: int, title: str, mode: str) -> int:
        now = _now()
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO conversations (user_id, title, mode, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
                (user_id, title, mode, now, now),
            )
            return int(cur.lastrowid)

    def list_conversations(self, user_id: int, limit: int = 50) -> list[sqlite3.Row]:
        with self._conn() as c:
            return c.execute(
                "SELECT id, title, mode, updated_at, memory_extracted FROM conversations "
                "WHERE user_id = ? ORDER BY updated_at DESC, id DESC LIMIT ?",
                (user_id, limit),
            ).fetchall()

    def get_conversation(self, user_id: int, conversation_id: int) -> sqlite3.Row | None:
        # user_id kontrolü: bir kullanıcı başkasının sohbetini kimlik numarasıyla açamasın
        with self._conn() as c:
            return c.execute(
                "SELECT * FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id)
            ).fetchone()

    def update_conversation(self, user_id: int, conversation_id: int, **fields) -> None:
        allowed = {"title", "mode", "memory_extracted"}
        if set(fields) - allowed:
            raise ValueError("Güncellenemez alan")
        fields["updated_at"] = _now()
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self._conn() as c:
            c.execute(
                f"UPDATE conversations SET {cols} WHERE id = ? AND user_id = ?",
                (*fields.values(), conversation_id, user_id),
            )

    def delete_conversation(self, user_id: int, conversation_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM conversations WHERE id = ? AND user_id = ?", (conversation_id, user_id))

    def add_message(
        self, user_id: int, conversation_id: int, role: str, content: str,
        risk_level: str = "none", risk_categories: str = "",
    ) -> int:
        if self.get_conversation(user_id, conversation_id) is None:
            raise StorageError("Sohbet bulunamadı.")
        with self._conn() as c:
            cur = c.execute(
                "INSERT INTO messages (conversation_id, role, content, risk_level, risk_categories, created_at) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (conversation_id, role, content, risk_level, risk_categories, _now()),
            )
            c.execute("UPDATE conversations SET updated_at = ? WHERE id = ?", (_now(), conversation_id))
            return int(cur.lastrowid)

    def get_messages(self, user_id: int, conversation_id: int) -> list[sqlite3.Row]:
        with self._conn() as c:
            return c.execute(
                "SELECT m.* FROM messages m JOIN conversations c ON c.id = m.conversation_id "
                "WHERE m.conversation_id = ? AND c.user_id = ? ORDER BY m.id",
                (conversation_id, user_id),
            ).fetchall()

    def delete_last_assistant_message(self, user_id: int, conversation_id: int) -> None:
        msgs = self.get_messages(user_id, conversation_id)
        if msgs and msgs[-1]["role"] == "assistant":
            with self._conn() as c:
                c.execute("DELETE FROM messages WHERE id = ?", (msgs[-1]["id"],))

    # ───────────── Hafıza ─────────────
    def add_memories(self, user_id: int, notes: list[str], conversation_id: int | None) -> int:
        notes = [n.strip() for n in notes if n and n.strip()]
        if not notes:
            return 0
        now = _now()
        with self._conn() as c:
            c.executemany(
                "INSERT INTO memories (user_id, text, source_conversation_id, created_at) VALUES (?, ?, ?, ?)",
                [(user_id, n[:200], conversation_id, now) for n in notes],
            )
        return len(notes)

    def list_memories(self, user_id: int) -> list[sqlite3.Row]:
        with self._conn() as c:
            return c.execute(
                "SELECT id, text, created_at FROM memories WHERE user_id = ? ORDER BY id DESC", (user_id,)
            ).fetchall()

    def update_memory(self, user_id: int, memory_id: int, text: str) -> None:
        with self._conn() as c:
            c.execute("UPDATE memories SET text = ? WHERE id = ? AND user_id = ?", (text.strip()[:200], memory_id, user_id))

    def delete_memory(self, user_id: int, memory_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM memories WHERE id = ? AND user_id = ?", (memory_id, user_id))

    def clear_memories(self, user_id: int) -> None:
        with self._conn() as c:
            c.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))

    # ───────────── Dışa aktarma (KVKK m.11) ─────────────
    def export_user(self, user_id: int) -> dict:
        user = self.get_user(user_id)
        if user is None:
            raise StorageError("Kullanıcı bulunamadı.")
        convs = []
        for conv in self.list_conversations(user_id, limit=10_000):
            convs.append({
                "baslik": conv["title"],
                "mod": conv["mode"],
                "guncellendi": conv["updated_at"],
                "mesajlar": [
                    {"rol": m["role"], "icerik": m["content"], "zaman": m["created_at"]}
                    for m in self.get_messages(user_id, conv["id"])
                ],
            })
        return {
            "disa_aktarma_zamani": _now(),
            "hesap": {"kullanici_adi": user.username, "yas_araligi": user.age_band, "hitap": user.nickname,
                      "varsayilan_mod": user.default_mode},
            "tanisma_cevaplari": self.get_profile(user_id),
            "rizalar": self.consent_status(user_id),
            "hafiza_notlari": [{"not": m["text"], "zaman": m["created_at"]} for m in self.list_memories(user_id)],
            "sohbetler": convs,
        }
