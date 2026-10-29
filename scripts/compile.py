#!/usr/bin/env python3
"""
Solidity Contract Compilation Script
====================================
Compiles EvidenceRegistry.sol to contracts/EvidenceRegistry.json
using solcx (Solidity 0.8.20).
"""

import os
import sys
import json

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, BASE_DIR)

import solcx

def compile_contract():
    sol_path = os.path.join(BASE_DIR, 'contracts', 'EvidenceRegistry.sol')
    json_path = os.path.join(BASE_DIR, 'contracts', 'EvidenceRegistry.json')

    print(f"[+] Compiling {sol_path} using solc 0.8.20...")
    if not solcx.get_installed_solc_versions():
        print("[+] Installing solc 0.8.20...")
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
    if contract_key not in compiled:
        # Fallback search
        for k in compiled.keys():
            if 'EvidenceRegistry' in k:
                contract_key = k
                break

    abi = compiled[contract_key]['abi']
    bin_code = compiled[contract_key]['bin']

    artifact = {
        'contractName': 'EvidenceRegistry',
        'abi': abi,
        'bin': bin_code
    }

    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(artifact, f, indent=2)

    print(f"[+] Successfully compiled! Artifact written to {json_path}")
    print(f"[+] ABI Functions: {len([x for x in abi if x.get('type') == 'function'])}")
    print(f"[+] Bytecode Length: {len(bin_code)} hex chars")

if __name__ == '__main__':
    compile_contract()
