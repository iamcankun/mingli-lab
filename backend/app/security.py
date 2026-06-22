from pathlib import Path

from cryptography.fernet import Fernet


class SecretCipher:
    def __init__(self, key: bytes):
        self._fernet = Fernet(key)

    @classmethod
    def from_data_dir(cls, data_dir: Path):
        data_dir = Path(data_dir)
        data_dir.mkdir(parents=True, exist_ok=True)
        key_path = data_dir / ".secret_key"
        if key_path.exists():
            key = key_path.read_bytes().strip()
        else:
            key = Fernet.generate_key()
            key_path.write_bytes(key)
        return cls(key)

    def encrypt(self, value: str) -> str:
        return self._fernet.encrypt(value.encode("utf-8")).decode("ascii")

    def decrypt(self, value: str) -> str:
        return self._fernet.decrypt(value.encode("ascii")).decode("utf-8")

