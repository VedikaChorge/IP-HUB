import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file if present
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ipevidencehub-student-prototype-secret-2026')
    
    # Private storage folders - explicitly outside the static directory
    DATA_DIR = os.path.join(BASE_DIR, 'data')
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'private_originals')
    WATERMARK_FOLDER = os.path.join(DATA_DIR, 'watermarked')
    QR_FOLDER = os.path.join(DATA_DIR, 'qr_codes')
    REPORTS_FOLDER = os.path.join(DATA_DIR, 'reports')
    
    # SQLite Database path
    DATABASE_PATH = os.path.join(DATA_DIR, 'ip_evidence_hub.db')
    
    # Upload limits: 16 MB max
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Blockchain settings
    # Default to public Sepolia testnet RPC
    BLOCKCHAIN_RPC_URL = os.environ.get('BLOCKCHAIN_RPC_URL', 'https://ethereum-sepolia-rpc.publicnode.com')
    # Deployed EvidenceRegistry smart contract address (e.g. 0x...)
    CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS', '')
    # Chain ID: 11155111 for Sepolia, 80002 for Polygon Amoy, 1337 for Local
    CHAIN_ID = int(os.environ.get('CHAIN_ID', '11155111'))
    # Network name display
    NETWORK_NAME = os.environ.get('NETWORK_NAME', 'Ethereum Sepolia Testnet')
    # Etherscan explorer base URL
    EXPLORER_URL = os.environ.get('EXPLORER_URL', 'https://sepolia.etherscan.io')
    # Optional deployer private key (for backend automated submission mode)
    # Users should never commit their private key to git; store strictly in local .env
    DEPLOYER_PRIVATE_KEY = os.environ.get('DEPLOYER_PRIVATE_KEY', '')
