import os
from dotenv import load_dotenv

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

# Load environment variables from .env file if present
load_dotenv(os.path.join(BASE_DIR, '.env'))

class Config:
    BASE_DIR = BASE_DIR
    SECRET_KEY = os.environ.get('SECRET_KEY', 'ipevidencehub-student-prototype-secret-2026')
    
    # Private storage folders - explicitly outside the static directory
    DATA_DIR = os.environ.get('DATA_DIR', os.path.join(BASE_DIR, 'data'))
    UPLOAD_FOLDER = os.path.join(DATA_DIR, 'private_originals')
    WATERMARK_FOLDER = os.path.join(DATA_DIR, 'watermarked')
    QR_FOLDER = os.path.join(DATA_DIR, 'qr_codes')
    REPORTS_FOLDER = os.path.join(DATA_DIR, 'reports')
    
    # SQLite Database path
    DATABASE_PATH = os.path.join(DATA_DIR, 'ip_evidence_hub.db')
    
    # Upload limits: 16 MB max
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}
    
    # Network configurations for MST Blockchain
    NETWORKS = {
        'mst_testnet': {
            'name': 'MST Testnet',
            'rpc_url': 'https://testnetrpc.mstblockchain.com',
            'chain_id': 91562037,
            'symbol': 'tMSTC',
            'explorer_url': 'https://testnet.mstscan.com'
        },
        'mst_mainnet': {
            'name': 'MST Mainnet',
            'rpc_url': 'https://mariorpc.mstblockchain.com',
            'alt_rpc_url': 'https://craftrpc.mstblockchain.com',
            'chain_id': 4646,
            'symbol': 'MSTC',
            'explorer_url': 'https://mstscan.com'
        }
    }
    
    # Active Blockchain settings (Default: MST Testnet)
    BLOCKCHAIN_RPC_URL = os.environ.get('BLOCKCHAIN_RPC_URL', NETWORKS['mst_testnet']['rpc_url'])
    CONTRACT_ADDRESS = os.environ.get('CONTRACT_ADDRESS', '')
    CHAIN_ID = int(os.environ.get('CHAIN_ID', str(NETWORKS['mst_testnet']['chain_id'])))
    NETWORK_NAME = os.environ.get('NETWORK_NAME', NETWORKS['mst_testnet']['name'])
    EXPLORER_URL = os.environ.get('EXPLORER_URL', NETWORKS['mst_testnet']['explorer_url'])
    CURRENCY_SYMBOL = os.environ.get('CURRENCY_SYMBOL', NETWORKS['mst_testnet']['symbol'])
    
    # Optional deployer private key (for backend automated submission mode)
    # Stored strictly in local .env - never committed to git or exposed in client frontend
    DEPLOYER_PRIVATE_KEY = os.environ.get('DEPLOYER_PRIVATE_KEY', '')
