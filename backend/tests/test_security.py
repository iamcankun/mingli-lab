from app.security import SecretCipher


def test_secret_cipher_round_trip_without_plaintext_storage(tmp_path):
    cipher = SecretCipher.from_data_dir(tmp_path)
    encrypted = cipher.encrypt("secret-value")
    assert encrypted != "secret-value"
    assert cipher.decrypt(encrypted) == "secret-value"

