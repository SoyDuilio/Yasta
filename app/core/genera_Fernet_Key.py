from cryptography.fernet import Fernet
Fernet.generate_key()

print("Fernet key generated successfully. Please store it securely.", Fernet.generate_key().decode('utf-8'))