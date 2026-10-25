from web3 import Web3
from app.config import settings

ABI = [
 {"inputs":[{"internalType":"bytes32","name":"evidenceId","type":"bytes32"},{"internalType":"bytes32","name":"digest","type":"bytes32"}],"name":"anchor","outputs":[],"stateMutability":"nonpayable","type":"function"},
 {"inputs":[{"internalType":"bytes32","name":"evidenceId","type":"bytes32"},{"internalType":"bytes32","name":"digest","type":"bytes32"}],"name":"verify","outputs":[{"internalType":"bool","name":"","type":"bool"}],"stateMutability":"view","type":"function"},
 {"inputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"name":"digestByEvidenceId","outputs":[{"internalType":"bytes32","name":"","type":"bytes32"}],"stateMutability":"view","type":"function"}
]
def configured():
    return bool(settings.blockchain_rpc_url and settings.blockchain_contract_address and settings.blockchain_private_key)
def client():
    if not configured(): raise RuntimeError("Blockchain RPC URL, contract address and private key must all be configured")
    w3=Web3(Web3.HTTPProvider(settings.blockchain_rpc_url,request_kwargs={"timeout":10}))
    if not w3.is_connected(): raise RuntimeError("Blockchain RPC endpoint is unreachable")
    contract=w3.eth.contract(address=Web3.to_checksum_address(settings.blockchain_contract_address),abi=ABI)
    account=w3.eth.account.from_key(settings.blockchain_private_key)
    return w3,contract,account
def anchor_digest(evidence_id:str,sha256_hex:str):
    w3,contract,account=client()
    eid=Web3.keccak(text=evidence_id)
    digest=bytes.fromhex(sha256_hex)
    nonce=w3.eth.get_transaction_count(account.address)
    tx=contract.functions.anchor(eid,digest).build_transaction({"from":account.address,"nonce":nonce,"chainId":w3.eth.chain_id,"gasPrice":w3.eth.gas_price})
    tx["gas"]=w3.eth.estimate_gas(tx)
    signed=account.sign_transaction(tx)
    tx_hash=w3.eth.send_raw_transaction(signed.raw_transaction)
    receipt=w3.eth.wait_for_transaction_receipt(tx_hash,timeout=120)
    if receipt.status != 1: raise RuntimeError("Blockchain transaction reverted")
    return tx_hash.hex(), int(receipt.blockNumber), bool(contract.functions.verify(eid,digest).call())
def verify_digest(evidence_id:str,sha256_hex:str):
    _,contract,_=client()
    return bool(contract.functions.verify(Web3.keccak(text=evidence_id),bytes.fromhex(sha256_hex)).call())
