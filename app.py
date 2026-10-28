import os
import sys

# Ensure the application directory is always in sys.path
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import secrets
import uuid
from datetime import datetime
from flask import (
    Flask, render_template, request, redirect, url_for, flash,
    send_file, abort, jsonify
)
from werkzeug.utils import secure_filename
from werkzeug.middleware.proxy_fix import ProxyFix

from config import Config
from database import (
    init_db, get_dashboard_stats, insert_evidence_record,
    get_evidence_by_id, get_evidence_by_hash, get_all_evidence_records,
    update_watermark_info, update_blockchain_info, toggle_share,
    get_evidence_by_share_token, record_verification, get_gap_checklist,
    save_gap_checklist
)
from services.hashing import calculate_file_hash, calculate_stream_hash, compare_hashes
from services.watermarking import embed_watermark, extract_watermark
from services.qr_service import generate_qr_code_file, get_qr_base64
from services.evidence_reports import generate_evidence_pdf
from services.blockchain_service import (
    check_blockchain_status, get_solidity_source,
    query_onchain_evidence, query_onchain_hash,
    verify_tx_receipt_onchain, submit_evidence_backend,
    EVIDENCE_REGISTRY_ABI
)

# Initialize Flask application
app = Flask(__name__)
app.config.from_object(Config)

# Enable ProxyFix to correctly detect HTTPS when running behind Render's reverse proxy
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)

# Ensure required directories and SQLite schema are created on boot
with app.app_context():
    init_db()

def allowed_file(filename):
    """Check if uploaded file has a supported image extension."""
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in Config.ALLOWED_EXTENSIONS

@app.context_processor
def inject_global_template_vars():
    """Make common utility functions and blockchain status available to all templates."""
    bc_info = check_blockchain_status()
    import json
    return {
        'blockchain_status': bc_info,
        'contract_address': Config.CONTRACT_ADDRESS,
        'contract_abi_json': json.dumps(EVIDENCE_REGISTRY_ABI),
        'chain_id': Config.CHAIN_ID,
        'network_name': Config.NETWORK_NAME,
        'explorer_url': Config.EXPLORER_URL,
        'has_backend_signer': bool(Config.DEPLOYER_PRIVATE_KEY),
        'round': round
    }

# ==========================================
# 1. DASHBOARD
# ==========================================
@app.route('/')
def dashboard():
    """Main dashboard displaying live database statistics, recent records, and audits."""
    stats = get_dashboard_stats()
    return render_template('dashboard.html', stats=stats)

# ==========================================
# 2. REGISTER EVIDENCE
# ==========================================
@app.route('/register', methods=['GET', 'POST'])
def register():
    """Register a new digital creation, compute SHA-256, and store in private vault."""
    if request.method == 'POST':
        title = request.form.get('title', '').strip()
        creator_name = request.form.get('creator_name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', 'General Digital Asset')
        embed_wm = request.form.get('embed_watermark') == '1'

        if not title or not creator_name:
            flash('Creation title and creator name are required fields.', 'danger')
            return redirect(url_for('register'))

        if 'evidence_file' not in request.files:
            flash('No file was uploaded.', 'danger')
            return redirect(url_for('register'))

        file = request.files['evidence_file']
        if file.filename == '':
            flash('No file selected. Please choose an image to register.', 'danger')
            return redirect(url_for('register'))

        if not allowed_file(file.filename):
            flash('Unsupported file format. Please upload PNG, JPG, JPEG, or WEBP images.', 'danger')
            return redirect(url_for('register'))

        # Generate unique, cryptographically random Evidence ID
        unique_suffix = secrets.token_hex(3).upper()
        evidence_id = f"IPE-2026-{unique_suffix}"

        # Generate safe server-side storage filename to prevent path traversal
        orig_filename = secure_filename(file.filename) or "asset.png"
        file_ext = orig_filename.rsplit('.', 1)[1].lower() if '.' in orig_filename else 'png'
        storage_filename = f"{uuid.uuid4().hex}.{file_ext}"
        storage_path = os.path.join(Config.UPLOAD_FOLDER, storage_filename)

        # Save original file securely in private vault (strictly outside static/)
        file.save(storage_path)
        file_size = os.path.getsize(storage_path)

        # Calculate exact SHA-256 digital fingerprint
        sha256_hash = calculate_file_hash(storage_path)

        # Generate secure share token for controlled sharing room
        share_token = secrets.token_urlsafe(16)

        # Record evidence in SQLite database
        created_at_iso = datetime.now().isoformat()
        insert_evidence_record({
            'evidence_id': evidence_id,
            'title': title,
            'creator_name': creator_name,
            'description': description,
            'category': category,
            'original_filename': orig_filename,
            'stored_filename': storage_filename,
            'file_size': file_size,
            'sha256_hash': sha256_hash,
            'mime_type': file.content_type or f"image/{file_ext}",
            'created_at': created_at_iso,
            'share_token': share_token
        })

        # Generate verification QR code image
        qr_output_path = os.path.join(Config.QR_FOLDER, f"{evidence_id}.png")
        verification_url = url_for('public_verify', evidence_id=evidence_id, _external=True)
        generate_qr_code_file(verification_url, qr_output_path)

        # Optional: Generate LSB invisible watermarked copy
        if embed_wm:
            wm_storage_filename = f"wm_{uuid.uuid4().hex}.png"
            wm_storage_path = os.path.join(Config.WATERMARK_FOLDER, wm_storage_filename)
            success, wm_hash, _ = embed_watermark(storage_path, wm_storage_path, evidence_id, sha256_hash[:16])
            if success:
                update_watermark_info(evidence_id, wm_storage_filename, wm_hash)

        flash(f"Digital creation registered successfully! Evidence ID: {evidence_id}", "success")
        return redirect(url_for('evidence_detail', evidence_id=evidence_id))

    return render_template('register.html')

# ==========================================
# 3. VERIFY EVIDENCE
# ==========================================
@app.route('/verify', methods=['GET', 'POST'])
def verify():
    """Verify file integrity by recalculating SHA-256 and matching against vault records."""
    all_records = get_all_evidence_records()
    preselected_id = request.args.get('preselect', '')
    result = None

    if request.method == 'POST':
        evidence_id = request.form.get('evidence_id', '').strip()
        if 'verify_file' not in request.files:
            flash('No file uploaded for verification.', 'danger')
            return redirect(url_for('verify'))

        file = request.files['verify_file']
        if file.filename == '':
            flash('Please select a file to verify.', 'danger')
            return redirect(url_for('verify'))

        # Calculate hash of uploaded verification file directly from stream
        tested_filename = secure_filename(file.filename) or "uploaded_file"
        tested_hash = calculate_stream_hash(file.stream)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC")

        if evidence_id:
            # 1-to-1 comparison against selected record
            target_record = get_evidence_by_id(evidence_id)
            if target_record:
                is_match, analysis = compare_hashes(target_record['sha256_hash'], tested_hash)
                record_verification(evidence_id, tested_filename, tested_hash, 'MATCH' if is_match else 'NO_MATCH', analysis)
                result = {
                    'is_match': is_match,
                    'analysis': analysis,
                    'tested_filename': tested_filename,
                    'uploaded_hash': tested_hash,
                    'registered_record': target_record,
                    'timestamp': now_str
                }
            else:
                flash(f"Evidence ID {evidence_id} not found in database.", 'danger')
        else:
            # Reverse lookup: search if this exact hash exists anywhere in the database
            matched_record = get_evidence_by_hash(tested_hash)
            if matched_record:
                is_match = True
                analysis = (
                    f"CRYPTOGRAPHIC MATCH FOUND: This file matches registered creation '{matched_record['title']}' "
                    f"by {matched_record['creator_name']} (Evidence ID: {matched_record['evidence_id']})."
                )
                record_verification(matched_record['evidence_id'], tested_filename, tested_hash, 'MATCH', analysis)
                result = {
                    'is_match': True,
                    'analysis': analysis,
                    'tested_filename': tested_filename,
                    'uploaded_hash': tested_hash,
                    'registered_record': matched_record,
                    'timestamp': now_str
                }
            else:
                is_match = False
                analysis = (
                    "NO RECORD FOUND: No registered evidence in the vault matches this file's SHA-256 fingerprint. "
                    "This file has either not been registered, or has been altered from its original version."
                )
                record_verification(None, tested_filename, tested_hash, 'NO_MATCH', analysis)
                result = {
                    'is_match': False,
                    'analysis': analysis,
                    'tested_filename': tested_filename,
                    'uploaded_hash': tested_hash,
                    'registered_record': None,
                    'timestamp': now_str
                }

    return render_template(
        'verify.html',
        all_records=all_records,
        preselected_id=preselected_id,
        result=result
    )

# ==========================================
# 4. MY EVIDENCE RECORDS & EVIDENCE DETAIL
# ==========================================
@app.route('/records')
def records():
    """List all registered evidence records with optional search and category filters."""
    query = request.args.get('q', '').strip()
    category = request.args.get('category', 'All')
    records_list = get_all_evidence_records(search_query=query, category=category)
    return render_template(
        'records.html',
        records=records_list,
        search_query=query,
        selected_category=category
    )

@app.route('/evidence/<evidence_id>')
def evidence_detail(evidence_id):
    """View forensic details, cryptographic certificates, QR code, and actions for a record."""
    rec = get_evidence_by_id(evidence_id)
    if not rec:
        flash(f"Evidence ID '{evidence_id}' does not exist.", 'danger')
        return redirect(url_for('records'))

    gap_data = get_gap_checklist(evidence_id)
    verification_url = url_for('public_verify', evidence_id=evidence_id, _external=True)
    qr_base64 = get_qr_base64(verification_url)

    return render_template(
        'evidence_detail.html',
        record=rec,
        gap_data=gap_data,
        qr_base64=qr_base64,
        verification_url=verification_url
    )

# ==========================================
# 5. INVISIBLE WATERMARK & IMAGE TRACE
# ==========================================
@app.route('/watermark')
def watermark():
    """Invisible watermark generation and extraction dashboard."""
    records_list = get_all_evidence_records()
    return render_template('watermark.html', records=records_list, detection_result=None)

@app.route('/watermark/generate', methods=['POST'])
def generate_watermark_route():
    """Embed an invisible LSB watermark into an existing evidence image."""
    evidence_id = request.form.get('evidence_id', '').strip()
    rec = get_evidence_by_id(evidence_id)
    if not rec:
        flash("Invalid evidence record selected.", "danger")
        return redirect(url_for('watermark'))

    original_path = os.path.join(Config.UPLOAD_FOLDER, rec['stored_filename'])
    if not os.path.exists(original_path):
        flash("Original file missing from vault storage.", "danger")
        return redirect(url_for('watermark'))

    wm_storage_filename = f"wm_{uuid.uuid4().hex}.png"
    wm_storage_path = os.path.join(Config.WATERMARK_FOLDER, wm_storage_filename)

    success, wm_hash, msg = embed_watermark(original_path, wm_storage_path, evidence_id, rec['sha256_hash'][:16])
    if success:
        update_watermark_info(evidence_id, wm_storage_filename, wm_hash)
        flash(f"LSB Invisible watermark embedded successfully into PNG derivative for {evidence_id}!", "success")
        return redirect(url_for('evidence_detail', evidence_id=evidence_id))
    else:
        flash(f"Watermark embedding failed: {msg}", "danger")
        return redirect(url_for('watermark'))

@app.route('/watermark/detect', methods=['POST'])
def detect_watermark_route():
    """Upload a suspected image and attempt to extract embedded LSB watermark identifier."""
    records_list = get_all_evidence_records()
    if 'detect_image' not in request.files:
        flash("No image provided for watermark scanning.", "danger")
        return redirect(url_for('watermark'))

    file = request.files['detect_image']
    if file.filename == '':
        flash("Please select an image file to scan.", "danger")
        return redirect(url_for('watermark'))

    temp_filename = f"temp_detect_{uuid.uuid4().hex}.png"
    temp_path = os.path.join(Config.WATERMARK_FOLDER, temp_filename)
    file.save(temp_path)

    found, extracted_id, details = extract_watermark(temp_path)

    # Clean up temporary file
    if os.path.exists(temp_path):
        os.remove(temp_path)

    matched_record = None
    if found and extracted_id:
        matched_record = get_evidence_by_id(extracted_id)

    detection_result = {
        'found': found,
        'evidence_id': extracted_id,
        'details': details,
        'matched_record': matched_record
    }

    return render_template('watermark.html', records=records_list, detection_result=detection_result)

# ==========================================
# 6. SMART EVIDENCE GAP CHECKER
# ==========================================
@app.route('/gap-checker')
def gap_checker():
    """Smart evidence gap checklist for organizing supporting documentation."""
    records_list = get_all_evidence_records()
    selected_id = request.args.get('id', '')
    selected_record = None
    checklist = None

    if selected_id:
        selected_record = get_evidence_by_id(selected_id)
        if selected_record:
            checklist = get_gap_checklist(selected_id)
    elif records_list:
        selected_record = records_list[0]
        checklist = get_gap_checklist(selected_record['evidence_id'])

    return render_template(
        'gap_checker.html',
        records=records_list,
        selected_record=selected_record,
        checklist=checklist
    )

@app.route('/gap-checker/<evidence_id>/save', methods=['POST'])
def save_gap_checker(evidence_id):
    """Save updated supporting evidence checklist to database."""
    rec = get_evidence_by_id(evidence_id)
    if not rec:
        flash(f"Evidence ID '{evidence_id}' not found.", 'danger')
        return redirect(url_for('gap_checker'))

    checklist_data = {
        'has_original_file': 1 if request.form.get('has_original_file') else 0,
        'has_drafts': 1 if request.form.get('has_drafts') else 0,
        'has_creation_notes': 1 if request.form.get('has_creation_notes') else 0,
        'has_working_files': 1 if request.form.get('has_working_files') else 0,
        'has_correspondence': 1 if request.form.get('has_correspondence') else 0,
        'has_publication_records': 1 if request.form.get('has_publication_records') else 0,
        'has_identity_proof': 1 if request.form.get('has_identity_proof') else 0,
        'notes': request.form.get('notes', '').strip()
    }
    score = save_gap_checklist(evidence_id, checklist_data)
    flash(f"Evidence checklist updated! Completeness score: {score}%", "success")
    return redirect(url_for('gap_checker', id=evidence_id))

# ==========================================
# 7. ONE-CLICK EVIDENCE PACK GENERATOR (PDF)
# ==========================================
@app.route('/evidence-pack')
def evidence_pack():
    """Evidence pack generator view."""
    records_list = get_all_evidence_records()
    selected_id = request.args.get('id', '')
    selected_record = get_evidence_by_id(selected_id) if selected_id else None
    return render_template('evidence_pack.html', records=records_list, selected_record=selected_record)

@app.route('/evidence-pack/<evidence_id>/download')
def download_evidence_pack(evidence_id):
    """Compile and stream an official ReportLab PDF evidence report."""
    rec = get_evidence_by_id(evidence_id)
    if not rec:
        flash("Evidence record not found.", "danger")
        return redirect(url_for('records'))

    gap_data = get_gap_checklist(evidence_id)
    qr_image_path = os.path.join(Config.QR_FOLDER, f"{evidence_id}.png")
    if not os.path.exists(qr_image_path):
        verification_url = url_for('public_verify', evidence_id=evidence_id, _external=True)
        generate_qr_code_file(verification_url, qr_image_path)

    pdf_filename = f"{evidence_id}_Evidence_Pack.pdf"
    pdf_path = os.path.join(Config.REPORTS_FOLDER, pdf_filename)

    success, out_path, msg = generate_evidence_pdf(rec, gap_data, qr_image_path, pdf_path)
    if success and os.path.exists(out_path):
        return send_file(out_path, as_attachment=True, download_name=pdf_filename, mimetype='application/pdf')
    else:
        flash(f"Could not generate PDF report: {msg}", "danger")
        return redirect(url_for('evidence_detail', evidence_id=evidence_id))

# ==========================================
# 8. SHARED EVIDENCE ROOM
# ==========================================
@app.route('/shared-room')
def shared_room():
    """Manage shareable evidence room links."""
    records_list = get_all_evidence_records()
    return render_template('shared_room.html', records=records_list)

@app.route('/shared/toggle/<evidence_id>', methods=['POST'])
def toggle_share_route(evidence_id):
    """Activate or revoke an evidence record's public share token."""
    action = request.form.get('action')
    toggle_share(evidence_id, active_state=(action == 'activate'))
    status_str = "activated" if action == 'activate' else "revoked"
    flash(f"Share link for {evidence_id} has been {status_str}.", "info")
    return redirect(request.referrer or url_for('shared_room'))

@app.route('/shared/<token>')
def view_shared(token):
    """Public read-only evidence view for recipients with a valid token."""
    rec = get_evidence_by_share_token(token)
    if not rec:
        abort(404, description="This shared evidence room link is either invalid or has been revoked by the creator.")
    gap_data = get_gap_checklist(rec['evidence_id'])
    return render_template('view_shared.html', record=rec, gap_data=gap_data)

# ==========================================
# 9. QR VERIFICATION & PUBLIC VERIFICATION
# ==========================================
@app.route('/qr-verification')
def qr_verification():
    """QR code generator and preview hub."""
    records_list = get_all_evidence_records()
    selected_id = request.args.get('id', '')
    selected_record = None
    qr_base64 = None
    target_url = None

    if selected_id:
        selected_record = get_evidence_by_id(selected_id)
    elif records_list:
        selected_record = records_list[0]

    if selected_record:
        target_url = url_for('public_verify', evidence_id=selected_record['evidence_id'], _external=True)
        qr_base64 = get_qr_base64(target_url)

    return render_template(
        'qr_verification.html',
        records=records_list,
        selected_record=selected_record,
        qr_base64=qr_base64,
        target_url=target_url
    )

@app.route('/public/verify/<evidence_id>')
def public_verify(evidence_id):
    """Public certificate verification page loaded when scanning a QR code."""
    rec = get_evidence_by_id(evidence_id)
    if not rec:
        abort(404, description="Evidence record not found in vault.")
    return render_template('public_verify.html', record=rec)

# ==========================================
# 10. BLOCKCHAIN VERIFICATION & SMART CONTRACT
# ==========================================
@app.route('/blockchain')
def blockchain_page():
    """Blockchain verification, smart contract viewer, deployment guide, and live on-chain query."""
    bc_info = check_blockchain_status()
    contract_source = get_solidity_source()
    all_records = get_all_evidence_records()

    query_term = request.args.get('query_term', '').strip()
    onchain_record = None
    query_error = None
    sqlite_match = None

    if query_term:
        if query_term.startswith('IPE-'):
            # Query by Evidence ID
            onchain_record, query_error = query_onchain_evidence(query_term)
            sqlite_match = get_evidence_by_id(query_term)
        elif len(query_term) == 64:
            # Query by SHA-256 Hash
            is_reg, matched_id, time_str, creator, err = query_onchain_hash(query_term)
            if is_reg and matched_id:
                onchain_record, query_error = query_onchain_evidence(matched_id)
            else:
                query_error = err or "No on-chain record found for this SHA-256 hash."
            sqlite_match = get_evidence_by_hash(query_term)
        else:
            query_error = "Please enter a valid Evidence ID (e.g. IPE-2026-XXXX) or a 64-character SHA-256 hash."

    return render_template(
        'blockchain.html',
        bc_info=bc_info,
        contract_source=contract_source,
        records=all_records,
        query_term=query_term,
        onchain_record=onchain_record,
        query_error=query_error,
        sqlite_match=sqlite_match
    )

@app.route('/blockchain/notarize/<evidence_id>', methods=['POST'])
def notarize_blockchain(evidence_id):
    """
    Record an Ethereum testnet transaction hash.
    Strictly verifies the transaction receipt on-chain using Web3.py before recording.
    """
    rec = get_evidence_by_id(evidence_id)
    if not rec:
        flash("Evidence record not found.", "danger")
        return redirect(url_for('records'))

    tx_hash = request.form.get('tx_hash', '').strip()
    network = request.form.get('blockchain_network', Config.NETWORK_NAME).strip()

    is_valid, receipt_data, msg = verify_tx_receipt_onchain(tx_hash)
    if not is_valid:
        flash(f"Blockchain verification failed: {msg} (No fake or unconfirmed transactions are permitted).", "danger")
        return redirect(url_for('evidence_detail', evidence_id=evidence_id))

    update_blockchain_info(
        evidence_id,
        tx_hash,
        network,
        block_number=receipt_data.get('block_number'),
        status='CONFIRMED'
    )
    flash(f"Blockchain transaction verified and confirmed on-chain in block #{receipt_data.get('block_number')}! Tx: {tx_hash}", "success")
    return redirect(url_for('evidence_detail', evidence_id=evidence_id))

@app.route('/api/blockchain/confirm-registration', methods=['POST'])
def api_confirm_registration():
    """
    API endpoint invoked after a user completes a transaction via MetaMask in the browser.
    Validates transaction receipt on-chain before persisting into SQLite.
    """
    data = request.get_json() or {}
    evidence_id = data.get('evidence_id')
    tx_hash = data.get('tx_hash')
    network = data.get('network', Config.NETWORK_NAME)

    if not evidence_id or not tx_hash:
        return jsonify({'success': False, 'message': 'Missing evidence_id or tx_hash'}), 400

    rec = get_evidence_by_id(evidence_id)
    if not rec:
        return jsonify({'success': False, 'message': 'Evidence record not found in database'}), 404

    is_valid, receipt_data, msg = verify_tx_receipt_onchain(tx_hash)
    if not is_valid:
        return jsonify({'success': False, 'message': f'On-chain validation failed: {msg}'}), 400

    update_blockchain_info(
        evidence_id,
        tx_hash,
        network,
        block_number=receipt_data.get('block_number'),
        status='CONFIRMED'
    )
    return jsonify({
        'success': True,
        'message': f'Confirmed on blockchain in block #{receipt_data.get("block_number")}',
        'tx_hash': tx_hash,
        'block_number': receipt_data.get('block_number')
    })

@app.route('/blockchain/auto-submit/<evidence_id>', methods=['POST'])
def auto_submit_blockchain(evidence_id):
    """
    (Optional Backend Mode)
    Submit evidence registration transaction using the deployer private key configured in .env.
    """
    rec = get_evidence_by_id(evidence_id)
    if not rec:
        flash("Evidence record not found.", "danger")
        return redirect(url_for('records'))

    success, tx_hash, block_number, msg = submit_evidence_backend(
        rec['evidence_id'],
        rec['sha256_hash'],
        rec['creator_name'],
        rec['title']
    )
    if success:
        update_blockchain_info(
            evidence_id,
            tx_hash,
            Config.NETWORK_NAME,
            block_number=block_number,
            status='CONFIRMED'
        )
        flash(f"Transaction successfully broadcasted and mined on {Config.NETWORK_NAME}! Block #{block_number}, Tx: {tx_hash}", "success")
    else:
        flash(f"Backend blockchain submission failed: {msg}", "danger")

    return redirect(url_for('evidence_detail', evidence_id=evidence_id))

# ==========================================
# 11. ABOUT PROJECT
# ==========================================
@app.route('/about')
def about():
    """Project background, problem, solution, blockchain role, and legal realities."""
    return render_template('about.html')

# ==========================================
# SAFE FILE DOWNLOAD ENDPOINTS
# ==========================================
@app.route('/download/original/<evidence_id>')
def download_original(evidence_id):
    """Safely stream the private original file with its original human-readable filename."""
    rec = get_evidence_by_id(evidence_id)
    if not rec:
        abort(404)
    file_path = os.path.join(Config.UPLOAD_FOLDER, rec['stored_filename'])
    if not os.path.exists(file_path):
        abort(404)
    return send_file(file_path, as_attachment=True, download_name=rec['original_filename'])

@app.route('/download/watermarked/<evidence_id>')
def download_watermarked(evidence_id):
    """Stream the watermarked PNG copy."""
    rec = get_evidence_by_id(evidence_id)
    if not rec or not rec['watermark_stored_filename']:
        abort(404)
    file_path = os.path.join(Config.WATERMARK_FOLDER, rec['watermark_stored_filename'])
    if not os.path.exists(file_path):
        abort(404)
    download_name = f"watermarked_{rec['evidence_id']}.png"
    return send_file(file_path, as_attachment=True, download_name=download_name, mimetype='image/png')

@app.route('/download/qr/<evidence_id>')
def download_qr(evidence_id):
    """Stream the verification QR code PNG."""
    file_path = os.path.join(Config.QR_FOLDER, f"{evidence_id}.png")
    if not os.path.exists(file_path):
        verification_url = url_for('public_verify', evidence_id=evidence_id, _external=True)
        generate_qr_code_file(verification_url, file_path)
    return send_file(file_path, as_attachment=True, download_name=f"{evidence_id}_QR.png", mimetype='image/png')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    host = '0.0.0.0' if (os.environ.get('RENDER') or os.environ.get('PORT')) else '127.0.0.1'
    is_render = bool(os.environ.get('RENDER'))
    
    print("==================================================")
    print(f" IP EVIDENCE HUB &bull; Server Starting on {host}:{port}")
    if not is_render:
        print(" Local URL: http://127.0.0.1:5000")
    print("==================================================")
    app.run(host=host, port=port, debug=not is_render)
