import sqlite3
import os
from datetime import datetime
from config import Config

def get_db_connection():
    """Establish a connection to the SQLite database with Row factory."""
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)
    conn = sqlite3.connect(Config.DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initialize database tables with secure schema design."""
    # Ensure all data directories exist
    os.makedirs(Config.UPLOAD_FOLDER, exist_ok=True)
    os.makedirs(Config.WATERMARK_FOLDER, exist_ok=True)
    os.makedirs(Config.QR_FOLDER, exist_ok=True)
    os.makedirs(Config.REPORTS_FOLDER, exist_ok=True)
    os.makedirs(os.path.dirname(Config.DATABASE_PATH), exist_ok=True)

    conn = get_db_connection()
    cursor = conn.cursor()

    # Evidence Records Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS evidence_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            creator_name TEXT NOT NULL,
            description TEXT,
            category TEXT,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_size INTEGER NOT NULL,
            sha256_hash TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            created_at TEXT NOT NULL,
            watermark_enabled INTEGER DEFAULT 0,
            watermark_stored_filename TEXT,
            watermark_sha256 TEXT,
            blockchain_status TEXT DEFAULT 'NOT_REGISTERED',
            blockchain_tx_hash TEXT,
            blockchain_network TEXT,
            blockchain_block_number INTEGER,
            share_token TEXT UNIQUE,
            share_active INTEGER DEFAULT 0
        )
    ''')

    # Verification Logs Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS verifications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT,
            tested_filename TEXT,
            tested_hash TEXT NOT NULL,
            result TEXT NOT NULL,
            verified_at TEXT NOT NULL,
            details TEXT
        )
    ''')

    # Smart Evidence Gap Checklists Table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS gap_checklists (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            evidence_id TEXT UNIQUE NOT NULL,
            has_original_file INTEGER DEFAULT 1,
            has_drafts INTEGER DEFAULT 0,
            has_creation_notes INTEGER DEFAULT 0,
            has_working_files INTEGER DEFAULT 0,
            has_correspondence INTEGER DEFAULT 0,
            has_publication_records INTEGER DEFAULT 0,
            has_identity_proof INTEGER DEFAULT 0,
            score_percent INTEGER DEFAULT 14,
            notes TEXT,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (evidence_id) REFERENCES evidence_records (evidence_id)
        )
    ''')

    conn.commit()
    conn.close()

def get_dashboard_stats():
    """Retrieve actual, live database metrics for the dashboard."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('SELECT COUNT(*) AS count FROM evidence_records')
    total_records = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) AS count FROM verifications WHERE result = "MATCH"')
    successful_verifications = cursor.fetchone()['count']

    cursor.execute('SELECT COUNT(*) AS count FROM verifications')
    total_verifications = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM evidence_records WHERE blockchain_status = 'CONFIRMED'")
    blockchain_registered = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) AS count FROM evidence_records WHERE share_active = 1")
    active_shares = cursor.fetchone()['count']

    cursor.execute('''
        SELECT evidence_id, title, creator_name, created_at, sha256_hash, category, blockchain_status
        FROM evidence_records
        ORDER BY id DESC
        LIMIT 5
    ''')
    recent_records = cursor.fetchall()

    cursor.execute('''
        SELECT id, evidence_id, tested_filename, tested_hash, result, verified_at
        FROM verifications
        ORDER BY id DESC
        LIMIT 5
    ''')
    recent_verifications = cursor.fetchall()

    conn.close()

    return {
        'total_records': total_records,
        'successful_verifications': successful_verifications,
        'total_verifications': total_verifications,
        'blockchain_registered': blockchain_registered,
        'active_shares': active_shares,
        'recent_records': recent_records,
        'recent_verifications': recent_verifications
    }

def insert_evidence_record(data):
    """Insert a new evidence record into the database."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO evidence_records (
            evidence_id, title, creator_name, description, category,
            original_filename, stored_filename, file_size, sha256_hash,
            mime_type, created_at, share_token
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['evidence_id'], data['title'], data['creator_name'],
        data.get('description', ''), data.get('category', 'General Digital Asset'),
        data['original_filename'], data['stored_filename'], data['file_size'],
        data['sha256_hash'], data['mime_type'], data['created_at'],
        data['share_token']
    ))
    
    # Initialize default gap checklist for this evidence
    cursor.execute('''
        INSERT OR IGNORE INTO gap_checklists (
            evidence_id, has_original_file, has_drafts, has_creation_notes,
            has_working_files, has_correspondence, has_publication_records,
            has_identity_proof, score_percent, updated_at
        ) VALUES (?, 1, 0, 0, 0, 0, 0, 0, 14, ?)
    ''', (data['evidence_id'], data['created_at']))

    conn.commit()
    conn.close()

def get_evidence_by_id(evidence_id):
    """Fetch an evidence record by its unique evidence ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evidence_records WHERE evidence_id = ?', (evidence_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_evidence_by_hash(sha256_hash):
    """Find evidence records that match an exact SHA-256 hash."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM evidence_records WHERE sha256_hash = ?', (sha256_hash,))
    row = cursor.fetchone()
    conn.close()
    return row

def get_all_evidence_records(search_query=None, category=None):
    """Retrieve all evidence records with optional filtering."""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = 'SELECT * FROM evidence_records WHERE 1=1'
    params = []

    if search_query:
        query += ' AND (title LIKE ? OR creator_name LIKE ? OR evidence_id LIKE ? OR sha256_hash LIKE ?)'
        wildcard = f'%{search_query}%'
        params.extend([wildcard, wildcard, wildcard, wildcard])

    if category and category != 'All':
        query += ' AND category = ?'
        params.append(category)

    query += ' ORDER BY id DESC'
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return rows

def update_watermark_info(evidence_id, watermark_filename, watermark_sha256):
    """Update watermark metadata for an evidence record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE evidence_records
        SET watermark_enabled = 1,
            watermark_stored_filename = ?,
            watermark_sha256 = ?
        WHERE evidence_id = ?
    ''', (watermark_filename, watermark_sha256, evidence_id))
    conn.commit()
    conn.close()

def update_blockchain_info(evidence_id, tx_hash, network, block_number=None, status='CONFIRMED'):
    """Record verified blockchain transaction details."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE evidence_records
        SET blockchain_status = ?,
            blockchain_tx_hash = ?,
            blockchain_network = ?,
            blockchain_block_number = ?
        WHERE evidence_id = ?
    ''', (status, tx_hash, network, block_number, evidence_id))
    conn.commit()
    conn.close()

def toggle_share(evidence_id, active_state):
    """Toggle sharing status of an evidence record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE evidence_records
        SET share_active = ?
        WHERE evidence_id = ?
    ''', (1 if active_state else 0, evidence_id))
    conn.commit()
    conn.close()

def get_evidence_by_share_token(share_token):
    """Fetch an active shared record by token."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM evidence_records 
        WHERE share_token = ? AND share_active = 1
    ''', (share_token,))
    row = cursor.fetchone()
    conn.close()
    return row

def record_verification(evidence_id, tested_filename, tested_hash, result, details=''):
    """Log file verification attempt."""
    conn = get_db_connection()
    cursor = conn.cursor()
    now_iso = datetime.now().isoformat()
    cursor.execute('''
        INSERT INTO verifications (
            evidence_id, tested_filename, tested_hash, result, verified_at, details
        ) VALUES (?, ?, ?, ?, ?, ?)
    ''', (evidence_id, tested_filename, tested_hash, result, now_iso, details))
    conn.commit()
    conn.close()

def get_gap_checklist(evidence_id):
    """Fetch the gap checklist for an evidence record."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM gap_checklists WHERE evidence_id = ?', (evidence_id,))
    row = cursor.fetchone()
    conn.close()
    return row

def save_gap_checklist(evidence_id, checklist_data):
    """Save or update checklist status for an evidence record."""
    items = [
        checklist_data.get('has_original_file', 0),
        checklist_data.get('has_drafts', 0),
        checklist_data.get('has_creation_notes', 0),
        checklist_data.get('has_working_files', 0),
        checklist_data.get('has_correspondence', 0),
        checklist_data.get('has_publication_records', 0),
        checklist_data.get('has_identity_proof', 0),
    ]
    completed_count = sum(items)
    # 7 categories -> each is ~14.28% -> total 100% when all 7 checked
    score_percent = int(round((completed_count / 7.0) * 100))
    now_iso = datetime.now().isoformat()

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO gap_checklists (
            evidence_id, has_original_file, has_drafts, has_creation_notes,
            has_working_files, has_correspondence, has_publication_records,
            has_identity_proof, score_percent, notes, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(evidence_id) DO UPDATE SET
            has_original_file = excluded.has_original_file,
            has_drafts = excluded.has_drafts,
            has_creation_notes = excluded.has_creation_notes,
            has_working_files = excluded.has_working_files,
            has_correspondence = excluded.has_correspondence,
            has_publication_records = excluded.has_publication_records,
            has_identity_proof = excluded.has_identity_proof,
            score_percent = excluded.score_percent,
            notes = excluded.notes,
            updated_at = excluded.updated_at
    ''', (
        evidence_id,
        items[0], items[1], items[2], items[3], items[4], items[5], items[6],
        score_percent, checklist_data.get('notes', ''), now_iso
    ))
    conn.commit()
    conn.close()
    return score_percent
