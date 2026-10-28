// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/**
 * @title EvidenceRegistry
 * @dev Intellectual Property Evidence Registry Smart Contract for IP Evidence Hub.
 * Savitribai Phule Pune University - B.Sc. Blockchain Student Project.
 *
 * PURPOSE:
 * Provides an immutable, decentralized proof-of-existence registry for digital creations.
 * Only the cryptographic SHA-256 fingerprint, metadata, and timestamps are recorded on-chain.
 * Confidential files and images are strictly kept OFF-CHAIN to guarantee privacy and minimize gas fees.
 */
contract EvidenceRegistry {
    
    // Contract Owner (deployer)
    address public owner;

    // Struct defining an immutable evidence record on the blockchain
    struct Evidence {
        string evidenceId;       // Unique application ID (e.g., IPE-2026-ABCD)
        string sha256Hash;       // 64-character SHA-256 hash of the exact file bytes
        string creatorName;      // Creator or rights-holder display name
        string title;            // Title or brief project description
        uint256 timestamp;       // Block timestamp when registered on-chain
        address registrant;      // Ethereum address that submitted the transaction
        bool exists;             // Verification flag
    }

    // Mapping from unique Evidence ID -> Evidence Struct
    mapping(string => Evidence) private recordsById;

    // Mapping from SHA-256 Hash -> Evidence ID (for direct hash reverse lookups)
    mapping(string => string) private hashToEvidenceId;

    // Total count of records registered on this smart contract
    uint256 public totalRecordsCount;

    // Event emitted upon successful registration
    event EvidenceRegistered(
        string indexed evidenceId,
        string indexed sha256Hash,
        address indexed registrant,
        string creatorName,
        uint256 timestamp
    );

    constructor() {
        owner = msg.sender;
    }

    /**
     * @notice Register a digital creation's cryptographic proof on the blockchain.
     * @param _evidenceId The unique platform identifier.
     * @param _sha256Hash The 64-character SHA-256 hash calculated from the original file.
     * @param _creatorName Name of the creator or organization.
     * @param _title Title of the digital creation.
     */
    function registerEvidence(
        string memory _evidenceId,
        string memory _sha256Hash,
        string memory _creatorName,
        string memory _title
    ) external {
        require(bytes(_evidenceId).length > 0, "Evidence ID cannot be empty");
        require(bytes(_sha256Hash).length == 64, "SHA-256 hash must be exactly 64 hex characters");
        require(!recordsById[_evidenceId].exists, "Evidence ID already registered on-chain");

        // Record the evidence
        recordsById[_evidenceId] = Evidence({
            evidenceId: _evidenceId,
            sha256Hash: _sha256Hash,
            creatorName: _creatorName,
            title: _title,
            timestamp: block.timestamp,
            registrant: msg.sender,
            exists: true
        });

        // Store hash index for fast integrity lookups
        hashToEvidenceId[_sha256Hash] = _evidenceId;
        totalRecordsCount++;

        emit EvidenceRegistered(
            _evidenceId,
            _sha256Hash,
            msg.sender,
            _creatorName,
            block.timestamp
        );
    }

    /**
     * @notice Look up an evidence record by its Evidence ID.
     */
    function getEvidenceById(string memory _evidenceId) external view returns (
        string memory evidenceId,
        string memory sha256Hash,
        string memory creatorName,
        string memory title,
        uint256 timestamp,
        address registrant,
        bool exists
    ) {
        Evidence memory rec = recordsById[_evidenceId];
        return (
            rec.evidenceId,
            rec.sha256Hash,
            rec.creatorName,
            rec.title,
            rec.timestamp,
            rec.registrant,
            rec.exists
        );
    }

    /**
     * @notice Verify whether a given SHA-256 hash was previously registered.
     */
    function verifyHash(string memory _sha256Hash) external view returns (
        bool isRegistered,
        string memory evidenceId,
        uint256 timestamp,
        string memory creatorName
    ) {
        string memory matchedId = hashToEvidenceId[_sha256Hash];
        if (bytes(matchedId).length > 0 && recordsById[matchedId].exists) {
            Evidence memory rec = recordsById[matchedId];
            return (true, rec.evidenceId, rec.timestamp, rec.creatorName);
        }
        return (false, "", 0, "");
    }
}
