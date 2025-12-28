"""
Store model for storing Shopify credentials
"""
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from cryptography.fernet import Fernet
from base64 import b64encode
import os
from .database import Base

class Store(Base):
    __tablename__ = "stores"
    
    id = Column(Integer, primary_key=True, index=True)
    shop_domain = Column(String, unique=True, nullable=False, index=True)
    access_token_encrypted = Column(String, nullable=False)
    scope = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    @staticmethod
    def get_cipher():
        """Get Fernet cipher for encryption/decryption"""
        secret_key = os.getenv("SECRET_KEY")
        if not secret_key:
            raise ValueError("SECRET_KEY environment variable is required")
        
        # Ensure key is properly formatted for Fernet
        if len(secret_key) < 32:
            secret_key = secret_key.ljust(32, '0')
        
        # Fernet requires base64-encoded 32-byte key
        key = b64encode(secret_key[:32].encode())
        return Fernet(key)
    
    @property
    def access_token(self):
        """Decrypt and return access token"""
        cipher = self.get_cipher()
        return cipher.decrypt(self.access_token_encrypted.encode()).decode()
    
    @access_token.setter
    def access_token(self, value):
        """Encrypt and store access token"""
        cipher = self.get_cipher()
        self.access_token_encrypted = cipher.encrypt(value.encode()).decode()
    
    @staticmethod
    def normalize_shop_domain(domain: str) -> str:
        """Normalize shop domain to standard format"""
        # Remove protocol
        domain = domain.replace('https://', '').replace('http://', '')
        # Remove trailing slash
        domain = domain.rstrip('/')
        # Ensure .myshopify.com suffix
        if not domain.endswith('.myshopify.com'):
            if '.' not in domain:
                domain = f"{domain}.myshopify.com"
        return domain
