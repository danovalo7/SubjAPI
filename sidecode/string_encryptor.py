import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

STRING_TO_ENCRYPT = """"""


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
    print("SALT: ", salt.hex())
    print("ENCRYPTED: ", result)
    return salt.hex(), result


if __name__ == '__main__':
    string_encrypt(input("Password: "), STRING_TO_ENCRYPT if STRING_TO_ENCRYPT != "" else input("String to encrypt: "))
    # with open("toencrypt.txt") as file:
    #     to_enc = file.read()
    # res = string_encrypt(input("Password: "), to_enc)
