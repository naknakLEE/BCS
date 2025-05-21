
class TransactionInput:
    def __init__(self, transaction_output_id, utxo):
        self.transaction_output_id = transaction_output_id # 참조하는 UTXO의 ID (이전 트랜잭션 해시 + 출력 인덱스)
        self.UTXO = utxo # 실제 UTXO 객체 (가치와 수신자 주소 포함)

    def __repr__(self):
        return f"Input(Ref: {self.transaction_output_id[:10]}..., Value: {self.UTXO.amount})"

