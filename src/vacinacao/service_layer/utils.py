import hashlib


def hash_content(file_content: bytes):
    return hashlib.md5(file_content).hexdigest()
