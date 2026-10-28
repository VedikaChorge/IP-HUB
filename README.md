# IP EVIDENCE HUB
### A Blockchain-Based Platform for Intellectual Property Evidence Management

> **Academic Project Presentation**  
> **Student:** Vedika  
> **Institution:** Savitribai Phule Pune University (SPPU)  
> **Degree Program:** First-Year B.Sc. Blockchain  
> **Prepared for:** MST Blockchain Student Evaluation  

---

## 1. Executive Summary & Purpose

In the digital era, designers, photographers, developers, students, and businesses face a critical vulnerability: **digital assets can be copied, altered, and redistributed in milliseconds without attribution**. When disputes arise over original authorship or unauthorized derivative works, standard operating system timestamps are easily manipulated, and creators often lack an organized, unforgeable audit trail of their creative process.

**IP Evidence Hub** is a full-stack intellectual property evidence platform built to demonstrate how cryptographic hashing, steganography, and Ethereum-compatible smart contracts can provide tamper-evident, decentralized proof of existence.

### ⚠️ Legal Scope Clarification
> **Important:** Registering a digital asset in IP Evidence Hub creates an immutable, mathematical proof of prior possession and file integrity at a specific timestamp. It does **not** automatically grant statutory copyright ownership under national copyright registries (such as the Indian Copyright Act, 1957). It serves as technical evidence to substantiate independent creation and defend against claims of copying.

---

## 2. Implemented Features & Architecture

The application contains **11 complete, fully functional navigation modules**:

| # | Navigation Module | Description & Technical Capability |
|---|---|---|
| 1 | **Dashboard** | Real-time statistics calculated from live SQLite database queries (Total Records, Successful Matches, Blockchain Anchors, Active Shares), recent activity tables, and quick-action shortcuts. Zero fake data. |
| 2 | **Register Evidence** | Accepts PNG, JPG, JPEG, and WEBP image uploads. Generates a unique Evidence ID (`IPE-2026-XXXX`), calculates the exact 64-character SHA-256 hash of original file bytes, records ISO UTC timestamp, and saves the file in an isolated private vault outside the static directory. |
| 3 | **Verify Evidence** | Performs 1-to-1 comparison against a chosen registered asset, or automatic reverse search across the entire vault. Visually displays `MATCH` (100% bit-for-bit identical) or `NO MATCH` (mismatch/altered file) with plain-English forensic explanations of the cryptographic avalanche effect. |
| 4 | **My Evidence Records** | Filterable evidence vault allowing search by title, creator, category, Evidence ID, or SHA-256 hash. Displays full forensic metadata and links to actions. |
| 5 | **Invisible Watermark & Trace** | Implements Least Significant Bit (LSB) steganography on lossless PNG images. Embeds the Evidence ID into pixel bit channels, saves the derivative copy separately with its own distinct SHA-256 hash, and provides an extraction tool that scans uploaded suspected files to trace the original registry record. |
| 6 | **Smart Evidence Gap Checker** | Interactive 7-point audit checklist assessing supporting evidence (Master File, Drafts/Sketches, Work Logs, Project Files, Correspondence, Publication Records, Identity Proof). Dynamically calculates a completeness percentage and saves recommendations against the record. |
| 7 | **Evidence Pack Generator** | Generates and streams a downloadable, high-resolution PDF dossier using ReportLab containing cryptographic digests, timestamps, metadata, checklist breakdown, and an embedded verification QR code. |
| 8 | **Shared Evidence Room** | Provides tokenized, controlled read-only access links for clients or lawyers. Protects private server storage while displaying certified proof. Links can be activated or revoked instantly. |
| 9 | **QR Verification** | Generates mobile-scannable QR codes encoding a public certificate link (`/public/verify/<evidence_id>`). Demonstrates how mobile verification functions locally and in production. |
| 10 | **Blockchain Verification** | Features `EvidenceRegistry.sol` (Solidity ^0.8.20). Integrates Web3.py with graceful fallback and connection detection. Displays complete smart contract code with 1-click copy for Remix IDE, along with beginner deployment instructions for Sepolia testnet. |
| 11 | **About Project** | Comprehensive academic report detailing the IP protection problem, cryptographic solution, off-chain vs. on-chain architecture, commercial business models, and legal distinctions. |

---

## 3. Technology Stack

- **Backend:** Python 3.14+, Flask 3.1+
- **Frontend:** HTML5, CSS3 (Custom Navy `#0f172a` & Royal Purple `#7c3aed` Design System), JavaScript (Vanilla ES6), Jinja2 templates
- **Database:** SQLite3 with parameterized queries and relational schema
- **Cryptographic Hashing:** Python standard library `hashlib` (SHA-256)
- **Image Processing & Steganography:** Pillow 13.0+ (LSB binary pixel manipulation)
- **PDF Report Generation:** ReportLab 5.1+
- **QR Code Generation:** Python `qrcode` library
- **Smart Contract & Blockchain:** Solidity ^0.8.20, Web3.py 8.0+

---

## 4. Beginner-Friendly Windows PowerShell Setup Guide

Follow these exact step-by-step commands in **Windows PowerShell**:

### Step 1: Open the Project Directory
In PowerShell, navigate to the project directory:
```powershell
cd "c:\Users\vedika\OneDrive\Desktop\MST BLOCKCHAIN"
```

### Step 2: Set PowerShell Script Execution Policy (If Needed)
If your PowerShell restricts running scripts, allow script execution for the current process:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Step 3: Activate the Virtual Environment
The virtual environment has already been created in `.venv/`. Activate it with:
```powershell
.\.venv\Scripts\Activate.ps1
```
*(You will see `(.venv)` appear in front of your command prompt).*

### Step 4: Verify Dependencies
All dependencies are installed. You can check them anytime:
```powershell
pip list
```

### Step 5: Run Automated Tests
Execute the automated test suite to confirm that all 11 routes, hashing functions, watermarking, PDF generation, and QR generation pass:
```powershell
python -m unittest tests/test_app.py
```
*(Expected output: `Ran 6 tests ... OK`)*

### Step 6: Start the IP Evidence Hub Web Server
Start the Flask application:
```powershell
python app.py
```

### Step 7: Open the Application in Your Browser
Open any web browser (Chrome, Edge, Firefox) and visit:
```
http://127.0.0.1:5000
```

---

## 5. Step-by-Step Feature Demonstration Guide

### A. Register an Evidence Record
1. Click **Register New Evidence** on the dashboard.
2. Enter a project title (e.g. `MST Genesis Logo Design`).
3. Enter creator name (e.g. `Vedika - SPPU`).
4. Select a category (e.g. `Brand Identity & Logos`).
5. Upload an image (`.png` recommended).
6. Keep **"Automatically generate an Invisible LSB Watermarked Copy"** checked.
7. Click **Calculate Fingerprint & Register Evidence**.
8. Notice that you are redirected to the Evidence Record Detail page displaying your unique Evidence ID (e.g. `IPE-2026-A1B2`), the exact 64-character SHA-256 hash, and timestamp.

### B. Demonstrate File Verification (Integrity Match vs. Mismatch)
1. Go to **Verify Evidence** in the sidebar.
2. Select your registered record in the dropdown.
3. **Test 1 (Exact Match):** Upload the exact same original image and click **Audit**. The system will display a bright green **MATCH CONFIRMED (100% Bit-for-Bit Identical)** banner.
4. **Test 2 (Integrity Mismatch):** Open your image in Microsoft Paint, change 1 tiny pixel or crop by 1 pixel, save it as a new file, and upload it to the Verify page. Click **Audit**. The system will display a red **NO MATCH (Integrity Mismatch)** banner, showing how altering a single pixel completely alters the SHA-256 fingerprint (the *avalanche effect*).

### C. Test Invisible LSB Watermarking & Trace
1. Go to **Invisible Watermark & Trace** in the sidebar.
2. Notice your watermarked PNG derivative is ready for download.
3. In **Step 2 (Detect & Trace)**, upload your watermarked PNG file and click **Scan Pixel Bitstream for Watermark**.
4. The system will extract the embedded Evidence ID from the least significant bits and display **"WATERMARK IDENTIFIER DETECTED & TRACED!"** with a direct link back to the registered evidence record.

### D. Audit Supporting Evidence with the Gap Checker
1. Go to **Smart Evidence Gap Checker**.
2. Select your registered creation.
3. Check the supporting evidence you possess (e.g., Original Master Asset, Early Drafts, Creation Notes, Project Files).
4. Watch the completeness score update in real-time. Click **Save Evidence Audit Checklist**.

### E. Download the PDF Evidence Pack
1. Go to **Evidence Pack Generator**.
2. Select your record and click **Download Official Evidence Pack (.PDF)**.
3. Open the downloaded PDF in Adobe Acrobat or browser to see the formatted dossier with cryptographic hashes, checklist matrix, and embedded verification QR code.

### F. Test Controlled-Access Sharing
1. Go to **Shared Evidence Room**.
2. Click **Enable Sharing** on any record.
3. Click the generated link (`/shared/<token>`) to view the public guest proof page.
4. Click **Revoke Link** to immediately invalidate the URL.

---

## 6. Smart Contract & Blockchain Deployment Guide (Remix IDE & MetaMask)

The smart contract is located at `contracts/EvidenceRegistry.sol` and its compiled artifact is at `contracts/EvidenceRegistry.json`.

### How Genuine Blockchain Integration Operates:
1. **Decentralized Execution:** The Solidity contract `EvidenceRegistry.sol` is deployed to the **Ethereum Sepolia Testnet**.
2. **MetaMask Signing:** Users click **"Submit via MetaMask"** directly on the Evidence Detail page. MetaMask pops up, prompts the user to sign the transaction, and broadcasts it to Sepolia. **No private keys are ever shared with Python or stored on the server.**
3. **On-Chain Receipt Verification:** Once mined, Flask's **Web3.py** service inspects the Ethereum transaction receipt on-chain to verify `status == 1` before marking the database record as `CONFIRMED`.
4. **Live On-Chain Querying:** The Blockchain Verification page (`/blockchain`) queries the smart contract directly using Web3.py (`getEvidenceById` and `verifyHash`) to display the live on-chain state side-by-side with local database records.

---

### Step-by-Step Guide: Deploying to Sepolia Testnet via Remix IDE

#### Step 1: Set Up MetaMask for Sepolia Testnet
1. Open your browser with the MetaMask extension installed.
2. In MetaMask, click the network dropdown in the top-left corner.
3. Toggle **"Show test networks"** to ON, and select **Sepolia**.
4. Copy your test account address (starts with `0x...`).
5. Obtain free Sepolia test ETH from any public faucet (e.g., [https://sepoliafaucet.com/](https://sepoliafaucet.com/) or [https://cloud.google.com/application/web3/faucet/ethereum/sepolia](https://cloud.google.com/application/web3/faucet/ethereum/sepolia)).

#### Step 2: Open Remix IDE and Create the Contract
1. In your browser, open [https://remix.ethereum.org](https://remix.ethereum.org).
2. Under the File Explorer on the left, navigate to `contracts/` and click the **New File** icon. Name it `EvidenceRegistry.sol`.
3. Copy the contract code from `contracts/EvidenceRegistry.sol` (or click **"Copy Solidity Source Code"** on the IP Evidence Hub Blockchain page).
4. Paste the code into Remix.

#### Step 3: Compile the Contract
1. Click the **Solidity Compiler** icon on the left navigation bar (the third icon).
2. Set the **Compiler** version to `0.8.20`.
3. Click the blue button: **Compile EvidenceRegistry.sol**.
4. A green checkmark will appear, confirming successful compilation with zero errors.

#### Step 4: Deploy Using Injected Provider (MetaMask)
1. Click the **Deploy & Run Transactions** icon on the left (the fourth icon).
2. In the **Environment** dropdown, change from *Remix VM* to **Injected Provider - MetaMask**.
3. MetaMask will prompt you to connect your test account. Approve the connection.
4. Verify that the Network shows **Sepolia (11155111)**.
5. In the **Contract** dropdown, ensure **EvidenceRegistry** is selected.
6. Click the orange **Deploy** button.
7. MetaMask will pop up showing the estimated gas fee in Sepolia test ETH. Click **Confirm**.
8. In the Remix terminal at the bottom, wait 10–15 seconds until you see the green checkmark: `creation of EvidenceRegistry pending... [block mined]`.

#### Step 5: Link the Deployed Contract to IP Evidence Hub
1. In Remix, look at the bottom of the left sidebar under **Deployed Contracts**.
2. Expand `EvidenceRegistry at 0x...` and click the small copy icon next to the contract address (e.g. `0x3a4b...`).
3. Open your project's `.env` file in your editor and paste the contract address:
   ```env
   CONTRACT_ADDRESS=0xYourCopiedContractAddressHere
   ```
4. Restart your Flask server (`python app.py`).
5. Open `http://127.0.0.1:5000/blockchain`. You will see:
   - **Contract Deployed & Verified** (Green badge)
   - Live on-chain records count retrieved directly via Web3.py!

---

### Step-by-Step Guide: Notarizing Evidence on the Blockchain

1. Register an image on the website (`http://127.0.0.1:5000/register`).
2. On the Evidence Detail page, look at the **Ethereum Blockchain Testnet Notarization** card.
3. Click **"🦊 Submit to Ethereum Smart Contract via MetaMask"**.
4. MetaMask will pop up with the transaction calling `registerEvidence` with your Evidence ID and SHA-256 hash.
5. Click **Confirm** in MetaMask.
6. Watch the button update: *Mining transaction on Sepolia...* -> *Transaction Confirmed in Block #...*!
7. The page will reload showing:
   - Status: **On-Chain Confirmed**
   - Direct link to **Sepolia Etherscan** (`https://sepolia.etherscan.io/tx/0x...`)
   - Block number and smart contract address!
8. Click **"Verify Live on Smart Contract"** to see your record queried directly from the Ethereum blockchain state!

---

## 7. Security and Privacy Architecture

- **Private Upload Vault:** Original user uploads are stored strictly in `data/private_originals/` outside the web root (`static/`), preventing public direct-file access.
- **Sanitized Filenames:** Server storage filenames are generated using UUIDv4 hex strings; user-uploaded filenames are recorded strictly as metadata.
- **SQL Injection Prevention:** All database operations utilize parameterized queries (`?` placeholders in SQLite).
- **Controlled Sharing:** Guest access utilizes cryptographically random URL tokens (`secrets.token_urlsafe(16)`) which can be revoked at any time.
- **Git Hygiene:** The `.gitignore` file strictly excludes virtual environments, private uploads, local databases, and environment keys from version control.

---

## 8. Demonstration Video Script (2-3 Minutes)

Use this concise speaking script for your project presentation video:

### [0:00 - 0:30] Introduction & Problem
> *"Respected evaluators and mentors at MST Blockchain, my name is Vedika, a first-year B.Sc. Blockchain student at Savitribai Phule Pune University.  
> Today, I am proud to present **IP Evidence Hub**, a blockchain-based platform for intellectual property evidence management.  
> For digital creators, designers, and students, proving that you created a file first has always been difficult because operating system dates can be forged and files can be easily plagiarized. IP Evidence Hub solves this by turning digital creations into verifiable cryptographic evidence."*

### [0:30 - 1:15] Registration & Cryptographic Hashing
> *(Screen shows Dashboard and Registration Page)*  
> *"Here on the dashboard, all statistics reflect live database records. Let's register a new creation.  
> I will enter the title 'Genesis Brand Guide', author 'Vedika SPPU', and upload our original artwork.  
> When I click 'Register Evidence', the system immediately computes the SHA-256 digital fingerprint of the exact file bytes, assigns a unique Evidence ID, saves the file privately, and generates an invisible LSB watermarked derivative."*

### [1:15 - 1:55] File Verification & Invisible Watermark Detection
> *(Screen shows Verify Evidence and Watermark Page)*  
> *"Now, let's verify file integrity. In the Verify Evidence module, if I upload the exact original image, the system confirms a 100% cryptographic **MATCH**.  
> But if I upload a version where even one single pixel was altered, the SHA-256 avalanche effect occurs, producing a completely different hash and triggering a clear **NO MATCH** result.  
> Furthermore, using our **Invisible Watermark & Trace** tool, we can upload a derivative image, scan its pixel bitstream using Least Significant Bit steganography, and extract the embedded Evidence ID to trace back the original creator."*

### [1:55 - 2:30] Evidence Pack, Blockchain Role & Conclusion
> *(Screen shows Evidence Pack PDF, QR Code, and Blockchain Page)*  
> *"With our **Smart Evidence Gap Checker**, creators can audit supporting drafts and work logs, and with one click, generate an official **Evidence Pack PDF** containing hashes, timestamps, and a verification QR code.  
> Finally, our Solidity smart contract, `EvidenceRegistry.sol`, allows anchoring only the 32-byte SHA-256 hash onto the Ethereum Sepolia testnet, ensuring decentralized proof of existence without exposing confidential creative files.  
> IP Evidence Hub demonstrates how cryptographic hashing, steganography, and smart contracts work together to build practical IP evidence protection. Thank you!"*

---

## 9. Troubleshooting & FAQ

- **Error: `Set-ExecutionPolicy` when activating `.venv`:**  
  Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` in your PowerShell window, then run `.\.venv\Scripts\Activate.ps1` again.
- **Why does the QR code point to `127.0.0.1:5000`?**  
  In local development, the server runs on localhost. When deployed to a cloud hosting provider, the QR code automatically encodes your live public HTTPS domain.
- **Can JPEG images be watermarked with LSB?**  
  LSB steganography requires lossless storage like PNG. JPEG uses lossy compression which quantizes high frequencies, disrupting the least significant bit values. The platform automatically converts and saves watermarked derivatives as lossless PNG.

---

**Developed with academic rigor at Savitribai Phule Pune University for MST Blockchain.**
