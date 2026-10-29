import os
import io
import unittest
from PIL import Image

# Use an in-memory or isolated test database
os.environ['DATABASE_PATH'] = ':memory:'

from app import app
from database import (
    init_db, insert_evidence_record, get_evidence_by_id,
    get_all_evidence_records, get_dashboard_stats, save_gap_checklist,
    get_gap_checklist, toggle_share, get_evidence_by_share_token,
    record_verification
)
from services.hashing import calculate_file_hash, compare_hashes
from services.watermarking import embed_watermark, extract_watermark
from services.qr_service import generate_qr_code_file
from services.evidence_reports import generate_evidence_pdf
from config import Config

class TestIPEvidenceHub(unittest.TestCase):
    def setUp(self):
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        with self.app.app_context():
            init_db()

    def test_routes_accessible(self):
        """Verify that all 11 core application routes return HTTP 200."""
        routes = [
            '/',
            '/register',
            '/verify',
            '/records',
            '/watermark',
            '/gap-checker',
            '/evidence-pack',
            '/shared-room',
            '/qr-verification',
            '/blockchain',
            '/about'
        ]
        for route in routes:
            response = self.client.get(route)
            self.assertEqual(response.status_code, 200, f"Route {route} failed with status {response.status_code}")

    def test_hashing_and_avalanche_effect(self):
        """Test cryptographic SHA-256 hashing and verify the avalanche effect."""
        # Create two slightly different files
        test_dir = os.path.join(Config.DATA_DIR, 'test_scratch')
        os.makedirs(test_dir, exist_ok=True)
        file1 = os.path.join(test_dir, 'original.txt')
        file2 = os.path.join(test_dir, 'modified.txt')

        with open(file1, 'wb') as f:
            f.write(b"MST Blockchain Student Project - IP Evidence Hub")
        with open(file2, 'wb') as f:
            # Change just 1 character
            f.write(b"MST Blockchain Student Project - IP Evidence Hub!")

        hash1 = calculate_file_hash(file1)
        hash2 = calculate_file_hash(file2)

        # Hashes must be 64 hexadecimal characters
        self.assertEqual(len(hash1), 64)
        self.assertEqual(len(hash2), 64)
        # 1 character change produces a completely different hash
        self.assertNotEqual(hash1, hash2)

        # Compare matching
        is_match, _ = compare_hashes(hash1, hash1)
        self.assertTrue(is_match)

        # Compare non-matching
        is_match, _ = compare_hashes(hash1, hash2)
        self.assertFalse(is_match)

    def test_watermark_embed_and_detect(self):
        """Test LSB invisible watermark embedding and detection."""
        test_dir = os.path.join(Config.DATA_DIR, 'test_scratch')
        os.makedirs(test_dir, exist_ok=True)
        src_img_path = os.path.join(test_dir, 'source_test.png')
        wm_img_path = os.path.join(test_dir, 'watermarked_test.png')

        # Create a small RGB test image (100x100)
        img = Image.new('RGB', (100, 100), color=(100, 150, 200))
        img.save(src_img_path, format='PNG')

        evidence_id = "IPE-2026-TEST"
        success, wm_hash, msg = embed_watermark(src_img_path, wm_img_path, evidence_id, "abc1234567890123")
        self.assertTrue(success, f"Watermarking failed: {msg}")
        self.assertTrue(os.path.exists(wm_img_path))
        self.assertEqual(len(wm_hash), 64)

        # Extract from the watermarked image
        found, extracted_id, details = extract_watermark(wm_img_path)
        self.assertTrue(found, f"Detection failed: {details}")
        self.assertEqual(extracted_id, evidence_id)

    def test_gap_checker_score_calculation(self):
        """Test smart gap checklist score calculation (out of 7 categories)."""
        evidence_id = "IPE-2026-GAP"
        # Check 4 out of 7 items -> round(4/7 * 100) = 57%
        data = {
            'has_original_file': 1,
            'has_drafts': 1,
            'has_creation_notes': 1,
            'has_working_files': 1,
            'has_correspondence': 0,
            'has_publication_records': 0,
            'has_identity_proof': 0,
            'notes': 'Test notes'
        }
        score = save_gap_checklist(evidence_id, data)
        self.assertEqual(score, 57)

        checklist = get_gap_checklist(evidence_id)
        self.assertIsNotNone(checklist)
        self.assertEqual(checklist['score_percent'], 57)

    def test_registration_and_verification_workflow(self):
        """Test full end-to-end registration and verification via Flask test client."""
        # 1. Create in-memory test image
        img_io = io.BytesIO()
        test_img = Image.new('RGB', (60, 60), color=(255, 0, 0))
        test_img.save(img_io, 'PNG')
        img_bytes = img_io.getvalue()

        # 2. Register file via POST
        data = {
            'title': 'Genesis Identity v1',
            'creator_name': 'Vedika SPPU',
            'category': 'Brand Identity & Logos',
            'description': 'Test creation description',
            'embed_watermark': '1',
            'evidence_file': (io.BytesIO(img_bytes), 'logo.png')
        }
        res = self.client.post('/register', data=data, content_type='multipart/form-data', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b"Genesis Identity v1", res.data)
        self.assertIn(b"IPE-2026-", res.data)

        # 3. Verify exact file match
        verify_data = {
            'evidence_id': '',
            'verify_file': (io.BytesIO(img_bytes), 'exact_copy.png')
        }
        res_v = self.client.post('/verify', data=verify_data, content_type='multipart/form-data')
        self.assertEqual(res_v.status_code, 200)
        self.assertIn(b"MATCH CONFIRMED", res_v.data)

        # 4. Verify altered file (1 byte change)
        altered_img_io = io.BytesIO()
        altered_img = Image.new('RGB', (60, 60), color=(254, 0, 0)) # Red 254 instead of 255
        altered_img.save(altered_img_io, 'PNG')
        altered_bytes = altered_img_io.getvalue()

        altered_data = {
            'evidence_id': '',
            'verify_file': (io.BytesIO(altered_bytes), 'altered_copy.png')
        }
        res_alt = self.client.post('/verify', data=altered_data, content_type='multipart/form-data')
        self.assertEqual(res_alt.status_code, 200)
        self.assertIn(b"NO MATCH", res_alt.data)

    def test_pdf_and_qr_generation(self):
        """Test PDF Evidence Pack and QR code generation."""
        test_dir = os.path.join(Config.DATA_DIR, 'test_scratch')
        os.makedirs(test_dir, exist_ok=True)
        qr_path = os.path.join(test_dir, 'test_qr.png')
        pdf_path = os.path.join(test_dir, 'test_evidence_pack.pdf')

        # Test QR generation
        ok_qr, _, _ = generate_qr_code_file("http://127.0.0.1:5000/public/verify/IPE-2026-TEST", qr_path)
        self.assertTrue(ok_qr)
        self.assertTrue(os.path.exists(qr_path))

        # Test ReportLab PDF generation
        mock_record = {
            'evidence_id': 'IPE-2026-TEST',
            'title': 'Test Project Dossier',
            'creator_name': 'Vedika',
            'category': 'Brand Identity',
            'description': 'Test creation notes',
            'original_filename': 'test.png',
            'file_size': 12345,
            'mime_type': 'image/png',
            'sha256_hash': 'e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855',
            'created_at': '2026-10-27T16:00:00',
            'watermark_enabled': 1,
            'watermark_sha256': 'ca978112ca1bbdcafac231b39a23dc4da786081cd1e14947e0e0e0e0e0e0e0e0',
            'blockchain_status': 'CONFIRMED',
            'blockchain_network': 'MST Testnet',
            'blockchain_tx_hash': '0x71c08a9d16b12a0f8c853e5e40e2cf93c0bc5ff81a6f87b8f9e68b3f2e1a4d0c'
        }
        mock_gap = {
            'score_percent': 71,
            'has_original_file': 1,
            'has_drafts': 1,
            'has_creation_notes': 1,
            'has_working_files': 1,
            'has_correspondence': 1,
            'has_publication_records': 0,
            'has_identity_proof': 0
        }
        ok_pdf, out_path, msg = generate_evidence_pdf(mock_record, mock_gap, qr_path, pdf_path)
        self.assertTrue(ok_pdf, f"PDF generation failed: {msg}")
        self.assertTrue(os.path.exists(pdf_path))
        self.assertGreater(os.path.getsize(pdf_path), 500)

    def test_smart_contract_evm_execution(self):
        """Test compiling, deploying and executing EvidenceRegistry.sol on EVM tester."""
        import json
        from web3 import Web3
        from web3.providers.eth_tester import EthereumTesterProvider

        contract_json_path = os.path.join(Config.BASE_DIR, 'contracts', 'EvidenceRegistry.json')
        self.assertTrue(os.path.exists(contract_json_path), "Compiled EvidenceRegistry.json artifact missing")

        with open(contract_json_path, 'r', encoding='utf-8') as f:
            artifact = json.load(f)

        w3 = Web3(EthereumTesterProvider())
        self.assertTrue(w3.is_connected())

        # Deploy contract
        Contract = w3.eth.contract(abi=artifact['abi'], bytecode=artifact['bin'])
        tx_hash = Contract.constructor().transact({'from': w3.eth.accounts[0]})
        receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
        self.assertEqual(receipt['status'], 1)
        contract_addr = receipt['contractAddress']

        instance = w3.eth.contract(address=contract_addr, abi=artifact['abi'])

        # 1. Register evidence
        test_id = "IPE-2026-BLOCKCHAIN-TEST"
        test_hash = "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
        tx = instance.functions.registerEvidence(test_id, test_hash, "Vedika", "Student Asset").transact({'from': w3.eth.accounts[0]})
        rx = w3.eth.wait_for_transaction_receipt(tx)
        self.assertEqual(rx['status'], 1)

        # 2. Total records count
        count = instance.functions.totalRecordsCount().call()
        self.assertEqual(count, 1)

        # 3. Retrieve by ID
        rec = instance.functions.getEvidenceById(test_id).call()
        self.assertEqual(rec[0], test_id)
        self.assertEqual(rec[1], test_hash)
        self.assertEqual(rec[2], "Vedika")
        self.assertEqual(rec[3], "Student Asset")
        self.assertTrue(rec[6]) # exists

        # 4. Verify duplicate prevention
        with self.assertRaises(Exception):
            instance.functions.registerEvidence(test_id, test_hash, "Duplicate", "Duplicate").transact({'from': w3.eth.accounts[0]})

        # 5. Verify hash lookup
        res = instance.functions.verifyHash(test_hash).call()
        self.assertTrue(res[0]) # isRegistered
        self.assertEqual(res[1], test_id)

    def test_blockchain_verification_api_rejects_fakes(self):
        """Verify that the API rejects fake or non-existent transaction hashes."""
        fake_tx = "0x1111222233334444555566667777888899990000aaaabbbbccccddddeeeeffff"
        payload = {
            'evidence_id': 'IPE-2026-TEST',
            'tx_hash': fake_tx
        }
        res = self.client.post('/api/blockchain/confirm-registration', json=payload)
        # Must fail because fake transaction does not exist on blockchain
        self.assertIn(res.status_code, [400, 404])
        data = res.get_json()
        self.assertFalse(data.get('success'))

if __name__ == '__main__':
    unittest.main()
