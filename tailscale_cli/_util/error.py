from enum import Enum


class TailscaleError(Enum):
    OTHER = 0
    CONNECTION_ERROR = 1
    UNAUTHORIZED = 2
    HTTP_ERROR = 3
    ACCESS_DENIED = 4


class TailscaleException(Exception):
    error: TailscaleError
    message: str

    def __init__(self, error: TailscaleError, message: str):
        self.error = error
        self.message = message

    @staticmethod
    def connection_error():
        return TailscaleException(
            TailscaleError.CONNECTION_ERROR, "could not connect to Tailscale socket"
        )

    @staticmethod
    def from_status_code(code: int, message: str = ""):
        if code == 401:
            return TailscaleException(
                TailscaleError.UNAUTHORIZED,
                "unauthorized API access, try running as root",
            )
        elif code == 403:
            return TailscaleException(
                TailscaleError.ACCESS_DENIED,
                f"access denied (HTTP 403): {message.strip() or 'insufficient permissions'}. "
                "This endpoint requires elevated privileges — try running as root or "
                "ensuring the connecting process has the required tailscaled permission level.",
            )
        else:
            return TailscaleException(
                TailscaleError.HTTP_ERROR,
                f"got unexpected HTTP status code: {code}: {message}",
            )

    @staticmethod
    def other(message: str):
        return TailscaleException(TailscaleError.OTHER, message)
