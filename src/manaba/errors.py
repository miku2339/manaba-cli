"""CLI errors. Messages must never include secrets."""


class ManabaError(Exception):
    exit_code = 1
    status = "error"

    def __init__(self, message: str, *, status: str | None = None) -> None:
        super().__init__(message)
        if status is not None:
            self.status = status


class UsageError(ManabaError):
    exit_code = 3
    status = "usage_error"


class MissingSession(ManabaError):
    exit_code = 2
    status = "unverified"


class UnrecognizedPage(ManabaError):
    exit_code = 2
    status = "unverified"


class LoginFailed(ManabaError):
    exit_code = 4
    status = "auth_failed"


class SecretInputError(ManabaError):
    exit_code = 4
    status = "secret_input_blocked"


class NetworkError(ManabaError):
    exit_code = 1
    status = "network_error"
