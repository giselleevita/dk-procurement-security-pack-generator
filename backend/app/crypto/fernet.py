from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from app.core.settings import get_settings


def _fernet() -> Fernet:
    settings = get_settings()
    return Fernet(settings.fernet_key.encode("utf-8"))


def encrypt_str(value: str) -> str:
    return _fernet().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_str(value: str) -> str:
    try:
        return _fernet().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken as e:
        raise ValueError("Invalid encrypted token") from e

