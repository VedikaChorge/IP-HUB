#!/usr/bin/env python3
"""
MST Testnet Smart Contract Deployment Script
===========================================
Compiles EvidenceRegistry.sol and deploys it to the MST Testnet.

Network Details:
- Network Name: MST Testnet
- RPC URL: https://testnetrpc.mstblockchain.com
- Chain ID: 91562037
- Currency: tMSTC
- Explorer: https://testnet.mstscan.com

Usage:
    python scripts/deploy.py
    python scripts/deploy.py --check
    python scripts/deploy.py --private-key 0x...
"""

import os
import sys
import json
import argparse

# Ensure project root is on sys.path
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

from config import Config
from web3 import Web3

def load_or_compile_contract():
    """Load or compile EvidenceRegistry.sol and return ABI + Bytecode."""
    json_path = os.path.join(BASE_DIR, 'contracts', 'EvidenceRegistry.json')
    sol_path = os.path.join(BASE_DIR, 'contracts', 'EvidenceRegistry.sol')

    if os.path.exists(json_path):
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('bin') and data.get('abi'):
                    return data['abi'], data['bin']
        except Exception:
            pass

    # Compile using solcx if JSON is missing
    try:
        import solcx
        if not solcx.get_installed_solc_versions():
            solcx.install_solc('0.8.20')
        solcx.set_solc_version('0.8.20')
        
        with open(sol_path, 'r', encoding='utf-8') as f:
            source = f.read()

        compiled = solcx.compile_source(
            source,
            output_values=['abi', 'bin'],
            solc_version='0.8.20'
        )
        contract_key = '<stdin>:EvidenceRegistry'
        abi = compiled[contract_key]['abi']
        bin_code = compiled[contract_key]['bin']

        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({'abi': abi, 'bin': bin_code}, f, indent=2)

        return abi, bin_code
    except Exception as e:
        print(f"[-] Compilation error: {e}")
        sys.exit(1)

def update_env_contract_address(contract_address):
    """Safely update CONTRACT_ADDRESS in local .env without overwriting other keys."""
    env_path = os.path.join(BASE_DIR, '.env')
    if not os.path.exists(env_path):
        with open(env_path, 'w', encoding='utf-8') as f:
            f.write(f"CONTRACT_ADDRESS={contract_address}\n")
        return

    with open(env_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated = False
    new_lines = []
    for line in lines:
        if line.strip().startswith('CONTRACT_ADDRESS='):
            new_lines.append(f"CONTRACT_ADDRESS={contract_address}\n")
            updated = True
        else:
            new_lines.append(line)

    if not updated:
        new_lines.append(f"\nCONTRACT_ADDRESS={contract_address}\n")

    with open(env_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    print(f"[+] Updated CONTRACT_ADDRESS in {env_path}")

def main():
    parser = argparse.ArgumentParser(description="Deploy EvidenceRegistry.sol to MST Testnet")
    parser.add_argument('--check', action='store_true', help="Check network and account readiness without deploying")
    parser.add_argument('--private-key', type=str, default=None, help="Deployer private key (overrides .env)")
    args = parser.parse_args()

    print("==================================================")
    print("  MST BLOCKCHAIN - SMART CONTRACT DEPLOYMENT")
    print("==================================================")
    print(f"Network:  {Config.NETWORK_NAME}")
    print(f"RPC URL:  {Config.BLOCKCHAIN_RPC_URL}")
    print(f"Chain ID: {Config.CHAIN_ID}")
    print(f"Explorer: {Config.EXPLORER_URL}")
    print("--------------------------------------------------")

    # 1. Connect to RPC
    w3 = Web3(Web3.HTTPProvider(Config.BLOCKCHAIN_RPC_URL, request_kwargs={'timeout': 15}))
    if not w3.is_connected():
        print(f"[-] ERROR: Could not connect to RPC endpoint: {Config.BLOCKCHAIN_RPC_URL}")
        print("    Please verify your internet connection or check if the MST Testnet RPC is online.")
        sys.exit(1)

    node_chain_id = w3.eth.chain_id
    latest_block = w3.eth.block_number
    print(f"[+] Connected to RPC successfully!")
    print(f"[+] Node Chain ID: {node_chain_id} (Config expected: {Config.CHAIN_ID})")
    print(f"[+] Latest Block:  #{latest_block}")

    if node_chain_id != Config.CHAIN_ID:
        print(f"[!] Warning: Connected node chain ID ({node_chain_id}) differs from Config.CHAIN_ID ({Config.CHAIN_ID})")

    # 2. Check Account
    private_key = args.private_key or Config.DEPLOYER_PRIVATE_KEY.strip()
    if not private_key:
        print("\n[!] No deployer private key found in .env or passed via --private-key.")
        print("    To deploy using this script:")
        print("    1. Add your deployer wallet private key to .env:")
        print("       DEPLOYER_PRIVATE_KEY=0xYourPrivateKeyHere")
        print("    2. Fund the wallet with test tMSTC coins.")
        print("    3. Run: python scripts/deploy.py")
        print("\n    Alternatively, deploy using Remix IDE via MetaMask Injected Provider (see README.md).")
        sys.exit(0)

    try:
        account = w3.eth.account.from_key(private_key)
        balance_wei = w3.eth.get_balance(account.address)
        balance_eth = w3.from_wei(balance_wei, 'ether')
        print(f"[+] Deployer Address: {account.address}")
        print(f"[+] Deployer Balance: {balance_eth} tMSTC")
    except Exception as e:
        print(f"[-] Invalid private key format: {e}")
        sys.exit(1)

    if args.check:
        print("\n[+] Pre-deployment check complete.")
        return

    if balance_wei == 0:
        print(f"\n[-] Insufficient funds: Account {account.address} has 0 tMSTC.")
        print(f"    Please fund this account with test tMSTC coins on MST Testnet before deploying.")
        sys.exit(1)

    # 3. Load ABI & Bytecode
    print("\n[+] Loading contract artifact...")
    abi, bin_code = load_or_compile_contract()
    if not bin_code or not abi:
        print("[-] Contract bytecode or ABI is empty.")
        sys.exit(1)

    # 4. Deploy Contract
    print("[+] Building deployment transaction...")
    contract_factory = w3.eth.contract(abi=abi, bytecode=bin_code)
    nonce = w3.eth.get_transaction_count(account.address)
    gas_price = w3.eth.gas_price or w3.to_wei(1, 'gwei')

    deploy_tx = contract_factory.constructor().build_transaction({
        'from': account.address,
        'nonce': nonce,
        'chainId': Config.CHAIN_ID,
        'gas': 1500000,
        'gasPrice': int(gas_price * 1.2)
    })

    print("[+] Signing transaction locally...")
    signed_tx = w3.eth.account.sign_transaction(deploy_tx, private_key=private_key)

    print("[+] Broadcasting transaction to MST Testnet...")
    tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
    tx_hash_hex = w3.to_hex(tx_hash)
    print(f"[+] Transaction Hash: {tx_hash_hex}")
    print(f"[+] Tracking on Explorer: {Config.EXPLORER_URL}/tx/{tx_hash_hex}")
    print("[+] Waiting for block confirmation...")

    receipt = w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180)
    if receipt.get('status') == 1:
        deployed_address = receipt.get('contractAddress')
        print("==================================================")
        print("  🎉 DEPLOYMENT SUCCESSFUL!")
        print("==================================================")
        print(f"Contract Address:  {deployed_address}")
        print(f"Mined in Block:    #{receipt.get('blockNumber')}")
        print(f"Gas Used:          {receipt.get('gasUsed')}")
        print(f"Explorer URL:      {Config.EXPLORER_URL}/address/{deployed_address}")
        print("--------------------------------------------------")

        update_env_contract_address(deployed_address)
        print("\n[+] Setup complete! The application will now use this contract for on-chain notarization.")
    else:
        print(f"[-] Deployment failed! Receipt status: {receipt.get('status')}")
        sys.exit(1)

if __name__ == '__main__':
    main()
