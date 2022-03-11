import base64
import os

from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt
from pathlib import Path

pystr = """
from SubjAPIDatabase import SubjAPIDatabase
from typing import Optional


class SubjAPI***Database(SubjAPIDatabase):
    def __init__(self, cache_size: int = 10, threaded: Optional[bool] = None, password: Optional[str] = None):
        super().__init__(cache_size, threaded)
        self._encrypted_credentials = ---
        self._salt = '+++'
        super().__after_init.__(password=password)
        

    def connect(self, password: Optional[str], other: Optional[str] = None) -> None:
        pass

    def get_indexed(self) -> set:
        pass

    def _submit(self, cache) -> None:
        pass
"""


def string_encrypt(password, to_encrypt):
    def mkey(pwd, slt):
        pwd = bytes(pwd, "utf-8")
        kdf = Scrypt(
            salt=slt,
            backend=default_backend(),
            length=32,
            n=2 ** 16,
            r=8,
            p=1
        )
        return base64.urlsafe_b64encode(kdf.derive(pwd))

    salt = os.urandom(32)
    creds = bytes(to_encrypt, "utf-8")

    key = mkey(password, salt)
    f = Fernet(key)
    result = f.encrypt(creds)
    return salt.hex(), result


if __name__ == '__main__':
    name = input("Database module name: ").replace(" ", "").capitalize()
    fullname = "SubjAPI" + name + "Database.py"
    print(fullname)
    if Path(fullname).is_file():
        raise FileExistsError(fullname + " already exists.")
    if not Path("key.txt").is_file():
        toenc = input("File key.txt not found, input connection key: ")
    else:
        with open("key.txt") as file:
            toenc = file.read()
    salt, enc = string_encrypt(input("Password: "), toenc)
    ps = pystr.replace("***", name).replace("---", str(enc)).replace("+++", salt)
    with open(fullname, "w+t") as file:
        file.write(ps)
