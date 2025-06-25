#!/usr/bin/env python3
"""
Generate RSA key pair for JWT signing in Vista API X Mock
"""

import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

def generate_rsa_keys(key_dir: str = "../keys"):
    """Generate RSA key pair for JWT signing"""
    
    # Create keys directory if it doesn't exist
    os.makedirs(key_dir, exist_ok=True)
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Generate public key
    public_key = private_key.public_key()
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    # Write keys to files
    private_key_path = os.path.join(key_dir, "private_key.pem")
    public_key_path = os.path.join(key_dir, "public_key.pem")
    
    with open(private_key_path, 'wb') as f:
        f.write(private_pem)
    print(f"Private key written to: {private_key_path}")
    
    with open(public_key_path, 'wb') as f:
        f.write(public_pem)
    print(f"Public key written to: {public_key_path}")
    
    # Set appropriate permissions
    os.chmod(private_key_path, 0o600)
    os.chmod(public_key_path, 0o644)
    
    print("\nRSA key pair generated successfully!")
    print("Make sure to keep the private key secure and never commit it to version control.")

if __name__ == "__main__":
    generate_rsa_keys()