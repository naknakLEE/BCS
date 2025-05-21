
class TransactionOutput:
    def __init__(self, recipient_address, amount, parent_transaction_id=None, index=None):
        self.recipient_address = recipient_address # 받을 사람 주소
        self.amount = amount
        self.parent_transaction_id = parent_transaction_id # 이 UTXO를 생성한 트랜잭션 ID
        self.index_in_parent = index # 부모 트랜잭션 내에서의 출력 인덱스
        self.id = self.calculate_id() if parent_transaction_id and index is not None else None # UTXO의 고유 ID

    def calculate_id(self):
        if self.parent_transaction_id is not None and self.index_in_parent is not None:
            return f"{self.parent_transaction_id}_{self.index_in_parent}"
        return None

    def is_mine(self, address):
        return self.recipient_address == address

    def __repr__(self):
        return f"Output(To: {self.recipient_address[:10]}..., Amount: {self.amount}, ID: {self.id[:10]}... if self.id else 'N/A')"

