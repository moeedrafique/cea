import base64
from cryptography.fernet import Fernet
from django.conf import settings


def encrypt_data(data):
    fernet = Fernet(settings.ENCRYPTION_KEY)
    return fernet.encrypt(data.encode()).decode()

def decrypt_data(encrypted_data):
    fernet = Fernet(settings.ENCRYPTION_KEY)
    return fernet.decrypt(encrypted_data.encode()).decode()