import hmac
from hashlib import sha1

import bcrypt

_BCRYPT_ROUNDS = 12
_BCRYPT_PREFIXES = ("$2a$", "$2b$", "$2y$")
_BCRYPT_MAX_BYTES = 72


def _legacy_sha1_hash(password: str, email: str) -> str:
    """Deprecated SHA-1 scheme kept only to verify/migrate old accounts."""
    return sha1(f"{password}{email}".encode()).hexdigest()


def _encode(password: str) -> bytes:
    return password.encode("utf-8")[:_BCRYPT_MAX_BYTES]


def is_bcrypt_hash(password_hash: str | None) -> bool:
    if not password_hash:
        return False
    return password_hash.startswith(_BCRYPT_PREFIXES)


def hash_password(password: str, email: str) -> str:
    """Hash a password with bcrypt and a per-password salt."""
    return bcrypt.hashpw(
        _encode(password), bcrypt.gensalt(rounds=_BCRYPT_ROUNDS)
    ).decode("utf-8")


def verify_password(password: str, password_hash: str | None, email: str) -> bool:
    """Verify a password against a bcrypt hash, falling back to legacy SHA-1."""
    if not password_hash:
        return False

    if is_bcrypt_hash(password_hash):
        try:
            return bcrypt.checkpw(_encode(password), password_hash.encode("utf-8"))
        except ValueError:
            return False

    return hmac.compare_digest(password_hash, _legacy_sha1_hash(password, email))


def needs_rehash(password_hash: str | None) -> bool:
    """True when the stored hash uses the deprecated SHA-1 scheme."""
    return not is_bcrypt_hash(password_hash)
