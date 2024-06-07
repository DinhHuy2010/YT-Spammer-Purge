import base64
import io
import os
from getpass import getpass
from hmac import compare_digest
from typing import Union

from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.kdf.scrypt import Scrypt

from Scripts.constants import F

SALT_BYTES = 64
SCRYPT_N = 2**18

# Generic encryption functions

def derive_key_from_password(password: bytes, salt: bytes) -> bytes:
    # Derive a key from the password and salt
    # n = 2**18 is 256MB of memory, r = 8 is 8 parallel threads, p = 1 is 1 iteration
    kdf = Scrypt(salt=salt, length=32, n=SCRYPT_N, r=8, p=1)
    key = kdf.derive(password)
    return base64.urlsafe_b64encode(key)

# Use 64 Bytes (512 bits) of salt (random data) - Unless changed above
def generate_salt() -> bytes:
    return os.urandom(SALT_BYTES)

def encrypt_data(data: bytes, password: bytes) -> bytes:
    salt = generate_salt()
    key = derive_key_from_password(password, salt)
    fer = Fernet(key)
    return salt + fer.encrypt(data)

def decrypt_data(data: bytes, password: bytes) -> bytes:
    salt = data[:SALT_BYTES]
    blob = data[SALT_BYTES:]
    key = derive_key_from_password(password, salt)
    fer = Fernet(key)
    return fer.decrypt(blob)

def encrypt_file(
    target_fp: Union[io.BufferedReader, io.BytesIO],
    dest_fp: Union[io.BufferedWriter, io.BytesIO],
    password: bytes
) -> Union[io.BufferedWriter, io.BytesIO]:
    td = target_fp.read()
    dest_fp.write(encrypt_data(td, password))
    return dest_fp

def decrypt_file(
    target_fp: Union[io.BufferedReader, io.BytesIO],
    dest_fp: Union[io.BufferedWriter, io.BytesIO],
    password: bytes
) -> Union[io.BufferedWriter, io.BytesIO]:
    td = target_fp.read()
    dest_fp.write(decrypt_data(td, password))
    return dest_fp

# Password function

def get_password(*, include_confirmation = False) -> bytes:
    while True:
        pwd = getpass(prompt="Password: ")
        if not include_confirmation:
            return pwd.encode()
        cpwd = getpass(prompt="Confirm password: ")
        if compare_digest(pwd, cpwd):
            return cpwd.encode()
        else:
            print(f"{F.RED} Password does not matched! Try again.")
