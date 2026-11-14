"""Argon2id password hashing."""

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError

_hasher = PasswordHasher()
# Verified against when the email is unknown, so timing does not leak it.
_DUMMY_HASH = _hasher.hash("rafaga-dummy-password")


def hash_password(password: str) -> str:
    """Return the argon2id hash of a password."""
    return _hasher.hash(password)


def verify_password(password: str, password_hash: str | None) -> bool:
    """Return whether the password matches; a missing hash never does."""
    try:
        _hasher.verify(password_hash or _DUMMY_HASH, password)
    except (VerificationError, InvalidHashError):
        return False
    return password_hash is not None
