# from google.oauth2.service_account import Credentials
# creds = Credentials.from_service_account_info(info)
# import json
#
# with open("credentials.json") as file:
#    info = json.load(file)
# creds = Credentials.from_service_account_info(info)
import base64
import os
from cryptography.fernet import Fernet
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt


def mkey(password, salt):
    password = bytes(password, "utf-8")
    kdf = Scrypt(
        salt=salt,
        backend=default_backend(),
        length=32,
        n=2 ** 16,
        r=8,
        p=1
    )
    return base64.urlsafe_b64encode(kdf.derive(password))


salt = bytes.fromhex('[REDACTED]')

with open("credentials.json", encoding="utf-8") as file:
    creds = bytes(file.read(), "utf-8")

key = mkey(input("Password: "), salt)
f = Fernet(key)
result = f.encrypt(creds)
print(f.decrypt(result)[:200])
