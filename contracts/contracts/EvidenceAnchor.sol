// SPDX-License-Identifier: MIT
pragma solidity ^0.8.24;
/// @notice Anchors evidence digests only. It does not prove factual truth or lawful provenance.
contract EvidenceAnchor {
 event DigestAnchored(bytes32 indexed evidenceId,bytes32 indexed digest,address indexed submitter,uint256 timestamp);
 mapping(bytes32=>bytes32) public digestByEvidenceId;
 mapping(bytes32=>uint256) public anchoredAt;
 function anchor(bytes32 evidenceId,bytes32 digest) external {
  require(evidenceId!=bytes32(0),"empty evidence id");require(digest!=bytes32(0),"empty digest");
  require(digestByEvidenceId[evidenceId]==bytes32(0),"already anchored");
  digestByEvidenceId[evidenceId]=digest;anchoredAt[evidenceId]=block.timestamp;
  emit DigestAnchored(evidenceId,digest,msg.sender,block.timestamp);
 }
 function verify(bytes32 evidenceId,bytes32 digest) external view returns(bool){return digestByEvidenceId[evidenceId]==digest&&digest!=bytes32(0);}
}