/**
 * IP Evidence Hub - Frontend Interactivity Script
 */

document.addEventListener('DOMContentLoaded', () => {
    // 1. Copy-to-clipboard functionality
    window.copyToClipboard = function(text, btnElement) {
        if (!navigator.clipboard) {
            // Fallback for older browsers
            const textArea = document.createElement("textarea");
            textArea.value = text;
            document.body.appendChild(textArea);
            textArea.select();
            try {
                document.execCommand('copy');
                showCopiedFeedback(btnElement);
            } catch (err) {
                console.error('Fallback copy failed', err);
            }
            document.body.removeChild(textArea);
            return;
        }

        navigator.clipboard.writeText(text).then(() => {
            showCopiedFeedback(btnElement);
        }).catch(err => {
            console.error('Copy failed: ', err);
        });
    };

    function showCopiedFeedback(btnElement) {
        if (!btnElement) return;
        const originalText = btnElement.innerHTML;
        btnElement.innerHTML = '✓ Copied!';
        btnElement.style.color = '#059669';
        setTimeout(() => {
            btnElement.innerHTML = originalText;
            btnElement.style.color = '';
        }, 1800);
    }

    // 2. Drag & Drop File Upload Zones
    const dropzones = document.querySelectorAll('.dropzone');
    dropzones.forEach(zone => {
        const input = zone.querySelector('input[type="file"]');
        if (!input) return;

        zone.addEventListener('click', () => input.click());

        zone.addEventListener('dragover', (e) => {
            e.preventDefault();
            zone.classList.add('dragover');
        });

        zone.addEventListener('dragleave', () => {
            zone.classList.remove('dragover');
        });

        zone.addEventListener('drop', (e) => {
            e.preventDefault();
            zone.classList.remove('dragover');
            if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
                input.files = e.dataTransfer.files;
                updateDropzoneDisplay(zone, input.files[0]);
            }
        });

        input.addEventListener('change', () => {
            if (input.files && input.files[0]) {
                updateDropzoneDisplay(zone, input.files[0]);
            }
        });
    });

    function updateDropzoneDisplay(zone, file) {
        const titleEl = zone.querySelector('.dropzone-title');
        const subEl = zone.querySelector('.dropzone-sub');
        if (titleEl) {
            titleEl.textContent = `Selected: ${file.name}`;
        }
        if (subEl) {
            const sizeKb = (file.size / 1024).toFixed(1);
            subEl.textContent = `File Size: ${sizeKb} KB (${file.type || 'binary/image'})`;
        }

        // Preview image if applicable
        let preview = zone.querySelector('.image-preview');
        if (file.type.startsWith('image/')) {
            if (!preview) {
                preview = document.createElement('img');
                preview.className = 'image-preview';
                preview.style.maxHeight = '140px';
                preview.style.marginTop = '12px';
                preview.style.borderRadius = '8px';
                preview.style.border = '1px solid #cbd5e1';
                zone.appendChild(preview);
            }
            const reader = new FileReader();
            reader.onload = (e) => {
                preview.src = e.target.result;
            };
            reader.readAsDataURL(file);
        }
    }

    // 3. Dynamic Gap Checker Score Calculator
    const gapForm = document.getElementById('gap-checker-form');
    if (gapForm) {
        const checkboxes = gapForm.querySelectorAll('input[type="checkbox"]');
        const scoreDisplay = document.getElementById('gap-score-display');
        const scoreBar = document.getElementById('gap-score-bar');

        function updateGapScore() {
            let checkedCount = 0;
            checkboxes.forEach(cb => {
                if (cb.checked) checkedCount++;
            });
            const percent = Math.round((checkedCount / checkboxes.length) * 100);
            if (scoreDisplay) scoreDisplay.textContent = `${percent}%`;
            if (scoreBar) scoreBar.style.width = `${percent}%`;
        }

        checkboxes.forEach(cb => {
            cb.addEventListener('change', updateGapScore);
        });
        updateGapScore();
    }

    // 4. MetaMask Web3 Smart Contract Registration
    window.submitToBlockchainWithMetaMask = async function(evidenceId, fileHash, creatorName, title, contractAddress, abiJson, targetChainId) {
        const btn = document.getElementById('metamask-submit-btn');
        const statusBox = document.getElementById('metamask-status-box');

        function setStatus(msg, isError = false) {
            if (statusBox) {
                statusBox.style.display = 'block';
                statusBox.style.backgroundColor = isError ? '#fef2f2' : '#eff6ff';
                statusBox.style.color = isError ? '#dc2626' : '#1e40af';
                statusBox.style.borderColor = isError ? '#fecaca' : '#bfdbfe';
                statusBox.innerHTML = msg;
            }
        }

        if (!window.ethereum) {
            alert("MetaMask browser extension not detected!\n\nPlease install MetaMask from https://metamask.io/ or use a Web3-compatible browser to sign transactions directly with your wallet.");
            return;
        }

        if (!contractAddress || contractAddress.length < 42) {
            alert("Smart contract address not configured yet!\n\nPlease deploy EvidenceRegistry.sol in Remix IDE and add the contract address in your .env file or settings.");
            return;
        }

        try {
            if (btn) {
                btn.disabled = true;
                btn.innerHTML = '⏳ Connecting MetaMask...';
            }
            setStatus("Connecting to MetaMask wallet...");

            // Parse ABI
            const abi = typeof abiJson === 'string' ? JSON.parse(abiJson) : abiJson;

            // Initialize browser provider
            const provider = new ethers.BrowserProvider(window.ethereum);
            
            // Request accounts
            const accounts = await provider.send("eth_requestAccounts", []);
            if (!accounts || accounts.length === 0) {
                throw new Error("No Ethereum account connected.");
            }

            // Verify network (Sepolia chainId = 11155111 = 0xaa36a7)
            const network = await provider.getNetwork();
            const currentChainId = Number(network.chainId);
            const expectedChainId = Number(targetChainId || 11155111);

            if (currentChainId !== expectedChainId && expectedChainId === 11155111) {
                setStatus("Requesting network switch to Ethereum Sepolia Testnet in MetaMask...");
                try {
                    await window.ethereum.request({
                        method: 'wallet_switchEthereumChain',
                        params: [{ chainId: '0xaa36a7' }]
                    });
                } catch (switchError) {
                    if (switchError.code === 4902) {
                        await window.ethereum.request({
                            method: 'wallet_addEthereumChain',
                            params: [{
                                chainId: '0xaa36a7',
                                chainName: 'Sepolia Testnet',
                                rpcUrls: ['https://ethereum-sepolia-rpc.publicnode.com'],
                                nativeCurrency: { name: 'Sepolia ETH', symbol: 'ETH', decimals: 18 },
                                blockExplorerUrls: ['https://sepolia.etherscan.io']
                            }]
                        });
                    } else {
                        throw switchError;
                    }
                }
            }

            // Get signer
            const signer = await provider.getSigner();
            const contract = new ethers.Contract(contractAddress, abi, signer);

            if (btn) btn.innerHTML = '⏳ Confirm in MetaMask...';
            setStatus(`Signing smart contract transaction for Evidence ID <b>${evidenceId}</b>. Please approve in your MetaMask popup window...`);

            // Execute registerEvidence call on the smart contract
            const tx = await contract.registerEvidence(evidenceId, fileHash, creatorName, title);

            if (btn) btn.innerHTML = '⏳ Mining on Sepolia...';
            setStatus(`Transaction broadcasted to Ethereum network!<br>Tx Hash: <code>${tx.hash}</code><br>Waiting for block confirmation...`);

            // Wait for 1 confirmation
            const receipt = await tx.wait(1);

            setStatus(`✅ Transaction Confirmed in Block #${receipt.blockNumber}! Synchronizing with IP Evidence Hub...`);

            // Send receipt to Flask backend to verify on-chain and record
            const res = await fetch('/api/blockchain/confirm-registration', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    evidence_id: evidenceId,
                    tx_hash: tx.hash,
                    network: 'Ethereum Sepolia Testnet'
                })
            });
            const data = await res.json();

            if (data.success) {
                setStatus(`🎉 Verified On-Chain! Block #${receipt.blockNumber}. Reloading...`);
                setTimeout(() => {
                    window.location.reload();
                }, 1500);
            } else {
                throw new Error(data.message || "Failed to synchronize on-chain confirmation with server.");
            }

        } catch (err) {
            console.error("MetaMask Error:", err);
            const errMsg = err.reason || err.message || "MetaMask transaction failed.";
            setStatus(`❌ Error: ${errMsg}`, true);
            if (btn) {
                btn.disabled = false;
                btn.innerHTML = '🦊 Try Again with MetaMask';
            }
        }
    };
});
