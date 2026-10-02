"""Credential access. Never log or return secret values."""

from __future__ import annotations

import sys
from collections.abc import Mapping
from getpass import getpass
from typing import Protocol

from manaba.errors import SecretInputError

KEYCHAIN_SERVICE = "manaba.cli"
USERID_ITEM = "userid"
PASSWORD_ITEM = "password"


class SecretStore(Protocol):
    def get(self, name: str) -> str | None: ...

    def set(self, name: str, value: str) -> None: ...

    def delete(self, name: str) -> None: ...


class MemoryStore:
    def __init__(self, initial: Mapping[str, str] | None = None) -> None:
        self.data = dict(initial or {})

    def get(self, name: str) -> str | None:
        value = self.data.get(name)
        return value if value else None

    def set(self, name: str, value: str) -> None:
        self.data[name] = value

    def delete(self, name: str) -> None:
        self.data.pop(name, None)


class KeyringStore:
    def get(self, name: str) -> str | None:
        try:
            import keyring
        except ImportError:
            return None
        try:
            value = keyring.get_password(KEYCHAIN_SERVICE, name)
        except Exception:
            return None
        return value or None

    def set(self, name: str, value: str) -> None:
        import keyring

        keyring.set_password(KEYCHAIN_SERVICE, name, value)

    def delete(self, name: str) -> None:
        try:
            import keyring

            keyring.delete_password(KEYCHAIN_SERVICE, name)
        except Exception:
            return


def default_store() -> SecretStore:
    return KeyringStore()


def stdin_is_tty() -> bool:
    return bool(getattr(sys.stdin, "isatty", lambda: False)())


def read_tty_secret(prompt: str) -> str:
    if not stdin_is_tty():
        raise SecretInputError(
            "拒絕讀取密碼：stdin 不是終端機。請在本機 Terminal 執行 manaba login。"
        )
    try:
        value = getpass(prompt)
    except Exception as exc:
        raise SecretInputError("拒絕以可見方式輸入密碼。") from exc
    secret = (value or "").strip()
    if not secret:
        raise SecretInputError("沒有輸入密碼。")
    return secret


def read_tty_userid(prompt: str) -> str:
    if not stdin_is_tty():
        raise SecretInputError(
            "拒絕讀取ユーザID：stdin 不是終端機。請在本機 Terminal 執行 manaba login。"
        )
    try:
        value = input(prompt)
    except Exception as exc:
        raise SecretInputError("無法讀取ユーザID。") from exc
    userid = value.strip()
    if not userid:
        raise SecretInputError("沒有輸入ユーザID。")
    return userid


def resolve_login(store: SecretStore) -> tuple[str, str, bool]:
    """Return userid, password, and whether the password came from the Keychain.

    Environment variables are ignored so a chat agent cannot inject a password.
    A missing password is read from a TTY only.
    """

    userid = (store.get(USERID_ITEM) or "").strip()
    password = store.get(PASSWORD_ITEM)
    password_from_store = bool(password)
    if not userid:
        userid = read_tty_userid("ユーザID：")
    if not password:
        password = read_tty_secret("密碼：")
    return userid, password, password_from_store
