from threading import Thread
from typing import Optional, List

from SubjAPIExceptions import NotConnectedError, IncorrectPasswordError


class SubjAPIDatabase:
    _cache_size: int = 10
    _threaded: bool = False

    def __init__(self, cache_size: int = 10, threaded: Optional[bool] = None, password: Optional[str] = None) -> None:
        self._encrypted_credentials: bytes = b''
        self._salt: str = ''
        self._cache: list = []
        self._cache_size = cache_size
        self.connected = False
        _thread: Optional[Thread] = None
        if threaded is not None:
            self._threaded = threaded
        if self._threaded:
            self._thread = Thread()
            self._thread.start()

    def __after_init__(self, password: Optional[str] = None):
        if password is not None:
            self.connect(password=password)

    def decrypt(self, password: str) -> str:
        from base64 import urlsafe_b64encode
        from cryptography.fernet import Fernet
        from cryptography.hazmat.backends import default_backend
        from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
        from cryptography.fernet import InvalidToken
        password = bytes(password, "utf-8")
        salt = bytes.fromhex(self._salt)
        kdf = Scrypt(
            salt=salt,
            backend=default_backend(),
            length=32,
            n=2 ** 16,
            r=8,
            p=1
        )
        key = urlsafe_b64encode(kdf.derive(password))
        f = Fernet(key)
        try:
            return f.decrypt(self._encrypted_credentials).decode("utf-8")
        except InvalidToken:
            raise IncorrectPasswordError("Wrong password for builtin credentials.")

    def connect(self, password: Optional[str], other: Optional[str] = None) -> None:
        raise NotImplementedError

    def get_indexed(self) -> set:
        raise NotImplementedError

    def cache(self, subject: dict) -> None:
        if not self.connected:
            raise NotConnectedError("Database not connected; run <self>.connect() to initialize connection first.")
        self._cache.append(subject)
        if self._cache_size != 0 and len(self._cache) > self._cache_size:
            self.submit()

    def submit(self, exitting: bool = False) -> None:
        if not self.connected:
            raise NotConnectedError("Database not connected; run <self>.connect() to initialize connection first.")
        if self._threaded and not exitting:
            self._thread.join()
            working_cache = self._cache[:]
            self._cache = []
            self._thread = Thread(target=self._submit, args=(working_cache,))
            self._thread.start()
        else:
            self._submit(self._cache)
            self._cache = []
        if exitting:
            self._cleanup()

    def _submit(self, cache: List[dict]) -> None:
        raise NotImplementedError

    def _cleanup(self):
        pass
