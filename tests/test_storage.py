import pytest

from psycalm.storage import Storage, StorageError


@pytest.fixture()
def store(tmp_path):
    return Storage(tmp_path / "t.db")


def test_register_and_login(store):
    u = store.register("Deniz_1", "guclu-sifre", "18-24")
    assert u.username == "deniz_1" and u.is_adult
    assert store.authenticate("DENIZ_1", "guclu-sifre").id == u.id
    assert store.authenticate("deniz_1", "yanlis-sifre") is None
    assert store.authenticate("yok-boyle-biri", "guclu-sifre") is None


def test_register_validation(store):
    with pytest.raises(StorageError):
        store.register("ab", "guclu-sifre", "18-24")
    with pytest.raises(StorageError):
        store.register("deniz", "kisa", "18-24")
    with pytest.raises(StorageError):
        store.register("cocuk", "guclu-sifre", "<18")
    store.register("deniz", "guclu-sifre", "18-24")
    with pytest.raises(StorageError):
        store.register("Deniz", "baska-sifre", "25-34")


def test_password_is_not_stored_plain(store, tmp_path):
    store.register("deniz", "cok-gizli-sifre", "18-24")
    raw = (tmp_path / "t.db").read_bytes()
    assert b"cok-gizli-sifre" not in raw


def test_consent_log_latest_wins(store):
    u = store.register("deniz", "guclu-sifre", "18-24")
    store.record_consent(u.id, "memory", "1", True)
    assert store.has_consent(u.id, "memory", "1")
    store.record_consent(u.id, "memory", "1", False)
    assert not store.has_consent(u.id, "memory", "1")
    # Metin sürümü değişince eski onay geçersiz
    store.record_consent(u.id, "processing", "1", True)
    assert not store.has_consent(u.id, "processing", "2")


def test_users_cannot_touch_each_others_conversations(store):
    a = store.register("ayse", "guclu-sifre", "18-24")
    b = store.register("bora", "guclu-sifre", "25-34")
    cid = store.create_conversation(a.id, "Sohbet", "dengeli")
    store.add_message(a.id, cid, "user", "merhaba")
    assert store.get_conversation(b.id, cid) is None
    assert store.get_messages(b.id, cid) == []
    with pytest.raises(StorageError):
        store.add_message(b.id, cid, "user", "sızma")
    store.delete_conversation(b.id, cid)  # başkasınınkini silememeli
    assert store.get_conversation(a.id, cid) is not None


def test_delete_user_cascades(store):
    u = store.register("deniz", "guclu-sifre", "18-24")
    cid = store.create_conversation(u.id, "S", "dengeli")
    store.add_message(u.id, cid, "user", "x")
    store.add_memories(u.id, ["not"], cid)
    store.save_profile(u.id, {"risk": "hayir"})
    store.record_consent(u.id, "processing", "2", True)
    store.delete_user(u.id)
    with store._conn() as c:
        for table in ("users", "profiles", "consents", "conversations", "messages", "memories"):
            assert c.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0] == 0


def test_export_contains_everything(store):
    u = store.register("deniz", "guclu-sifre", "18-24")
    cid = store.create_conversation(u.id, "S", "dengeli")
    store.add_message(u.id, cid, "user", "merhaba")
    store.add_memories(u.id, ["sınav dönemi"], cid)
    data = store.export_user(u.id)
    assert data["hesap"]["kullanici_adi"] == "deniz"
    assert data["sohbetler"][0]["mesajlar"][0]["icerik"] == "merhaba"
    assert data["hafiza_notlari"][0]["not"] == "sınav dönemi"
    assert "pw_hash" not in str(data)
