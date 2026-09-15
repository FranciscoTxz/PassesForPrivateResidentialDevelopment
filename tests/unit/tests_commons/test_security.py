from hashlib import sha1

from commons.security import (
    hash_password,
    is_bcrypt_hash,
    needs_rehash,
    verify_password,
)


def legacy_hash(password: str, email: str) -> str:
    return sha1(f"{password}{email}".encode()).hexdigest()


class TestHashPassword:
    def test_returns_bcrypt_hash(self):
        result = hash_password("Password1!", "user@example.com")

        assert is_bcrypt_hash(result)
        assert result != legacy_hash("Password1!", "user@example.com")

    def test_uses_random_salt(self):
        first = hash_password("Password1!", "user@example.com")
        second = hash_password("Password1!", "user@example.com")

        assert first != second

    def test_handles_long_passwords(self):
        long_password = "A1!" + "a" * 200

        hashed = hash_password(long_password, "user@example.com")

        assert verify_password(long_password, hashed, "user@example.com")


class TestVerifyPassword:
    def test_verifies_bcrypt_password(self):
        hashed = hash_password("Password1!", "user@example.com")

        assert verify_password("Password1!", hashed, "user@example.com") is True
        assert verify_password("WrongPass1!", hashed, "user@example.com") is False

    def test_verifies_legacy_sha1_password(self):
        hashed = legacy_hash("Password1!", "user@example.com")

        assert verify_password("Password1!", hashed, "user@example.com") is True
        assert verify_password("WrongPass1!", hashed, "user@example.com") is False

    def test_none_hash_returns_false(self):
        assert verify_password("Password1!", None, "user@example.com") is False


class TestNeedsRehash:
    def test_legacy_hash_needs_rehash(self):
        assert needs_rehash(legacy_hash("Password1!", "user@example.com")) is True

    def test_bcrypt_hash_does_not_need_rehash(self):
        assert needs_rehash(hash_password("Password1!", "user@example.com")) is False

    def test_none_needs_rehash(self):
        assert needs_rehash(None) is True
