import hashlib
import json

class Block:
    def __init__(self, index, timestamp, transactions, previous_hash, nonce=0):
        self.index = index
        self.timestamp = timestamp
        self.transactions = transactions # Transaction 객체의 리스트
        self.previous_hash = previous_hash
        self.nonce = nonce
        self.merkle_root = self.calculate_merkle_root() if transactions else ""
        self.hash = self.calculate_hash()

    def calculate_merkle_root(self):
        """간단한 머클 루트 계산 (트랜잭션 ID들을 해싱)"""
        if not self.transactions:
            return ""
        transaction_ids = [tx.transaction_id for tx in self.transactions]
        if not transaction_ids:
            return ""

        # 실제 머클 트리는 재귀적으로 두 개씩 짝지어 해싱
        # 여기서는 단순화를 위해 모든 ID를 합쳐서 한 번 해싱
        combined_ids = "".join(sorted(transaction_ids))
        return hashlib.sha256(combined_ids.encode()).hexdigest()


    def calculate_hash(self):
        block_header_data = {
            "index": self.index,
            "timestamp": self.timestamp,
            "previous_hash": self.previous_hash,
            "merkle_root": self.merkle_root,
            "nonce": self.nonce
        }
        block_header_string = json.dumps(block_header_data, sort_keys=True).encode()
        return hashlib.sha256(block_header_string).hexdigest()

    def __repr__(self):
        return (f"Block(Index: {self.index}, Hash: {self.hash[:10]}..., "
                f"Prev_Hash: {self.previous_hash[:10]}... if self.previous_hash else 'None', "
                f"Nonce: {self.nonce}, Transactions: {len(self.transactions)})")
