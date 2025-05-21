import hashlib
import time
import json
from TransactionOutput import TransactionOutput
from Wallet import Wallet

class Transaction:
    sequence = 0 # 트랜잭션 고유 ID 생성을 위한 카운터 (단순화)

    def __init__(self, sender_wallet, recipient_address, amount, inputs):
        self.sender_address = sender_wallet.address
        self.sender_public_key = sender_wallet.get_public_key_hex() # 서명 검증에 필요
        self.recipient_address = recipient_address
        self.amount = amount
        self.inputs = inputs # TransactionInput 객체들의 리스트
        self.outputs = [] # TransactionOutput 객체들의 리스트 (생성 시 계산)
        self.timestamp = time.time()
        self.transaction_id = self.calculate_hash() # 트랜잭션 데이터 기반 해시
        self.signature = None # 서명은 별도로 추가

    def calculate_hash(self):
        """트랜잭션의 핵심 내용을 해시합니다."""
        Transaction.sequence += 1
        # 입력, 출력, 타임스탬프 등을 조합하여 해시 (서명 전 데이터)
        # 실제로는 입력 UTXO ID, 출력 (수신자, 금액) 등을 정렬하여 일관성 있게 만듦
        data_to_hash = {
            "sender": self.sender_address,
            "recipient": self.recipient_address,
            "amount": self.amount,
            "inputs_refs": sorted([inp.transaction_output_id for inp in self.inputs]), # 입력 UTXO ID 정렬
            "timestamp": self.timestamp,
            "sequence": Transaction.sequence # 해시 충돌 방지용 (간단한 방법)
        }
        return hashlib.sha256(json.dumps(data_to_hash, sort_keys=True).encode()).hexdigest()

    def get_data_to_sign(self):
        """서명할 데이터를 생성합니다. 트랜잭션 ID와 유사하지만, 서명 후 ID가 확정될 수도 있음."""
        # 이 예제에서는 transaction_id 계산에 사용된 데이터와 동일하게 사용
        data_to_sign = {
            "sender": self.sender_address,
            "recipient": self.recipient_address,
            "amount": self.amount,
            "inputs_refs": sorted([inp.transaction_output_id for inp in self.inputs]),
            "timestamp": self.timestamp,
            "sequence": Transaction.sequence # 생성 시점의 sequence 사용
        }
        return json.dumps(data_to_sign, sort_keys=True)

    def sign(self, sender_wallet):
        """트랜잭션에 서명합니다."""
        if sender_wallet.address != self.sender_address:
            print("오류: 서명하려는 지갑이 송신자 주소와 일치하지 않습니다.")
            return False
        data_to_sign = self.get_data_to_sign()
        self.signature = sender_wallet.sign_transaction(data_to_sign)
        return True

    def is_signature_valid(self):
        """트랜잭션 서명을 검증합니다."""
        if not self.signature:
            return False
        data_to_sign = self.get_data_to_sign()
        return Wallet.verify_signature(self.sender_public_key, self.signature, data_to_sign)

    def process_transaction(self, utxo_pool):
        """
        트랜잭션을 처리하고 UTXO를 업데이트합니다.
        1. 입력 UTXO가 유효하고 소유주가 맞는지 확인 (서명으로).
        2. 입력 UTXO의 총합이 보내는 금액보다 크거나 같은지 확인.
        3. 새로운 출력 UTXO (수신자에게, 거스름돈)를 생성.
        4. 사용된 입력 UTXO는 UTXO 풀에서 제거, 새로운 출력 UTXO는 추가.
        """
        if not self.is_signature_valid():
            print(f"트랜잭션 {self.transaction_id[:10]}... 서명 검증 실패")
            return False

        # 1. 입력 UTXO 유효성 검사 (UTXO 풀에 있는지, 이미 사용되지 않았는지)
        #    이 예제에서는 UTXO를 생성 시점에 전달받으므로, 풀에 있는지 여부는 상위 로직에서 처리
        for tx_input in self.inputs:
            if tx_input.UTXO.recipient_address != self.sender_address:
                print(f"오류: 입력 UTXO {tx_input.transaction_output_id[:10]}...의 소유주가 송신자와 다릅니다.")
                return False

        # 2. 총 입력 금액 계산
        total_input_value = sum(inp.UTXO.amount for inp in self.inputs)
        if total_input_value < self.amount:
            print(f"오류: 입력 금액({total_input_value})이 송금액({self.amount})보다 적습니다.")
            return False

        # 3. 새로운 출력 UTXO 생성
        # 3a. 수신자에게 보내는 UTXO
        self.outputs.append(TransactionOutput(self.recipient_address, self.amount, self.transaction_id, 0))
        # 3b. 거스름돈 UTXO
        change = total_input_value - self.amount
        if change > 0:
            self.outputs.append(TransactionOutput(self.sender_address, change, self.transaction_id, 1))
        elif change < 0 : # 이 경우는 위에서 이미 걸러졌어야 함
             print("오류: 거스름돈 계산 오류 (음수)")
             return False

        # 4. UTXO 풀 업데이트 (이 함수는 생성만 하고, 실제 업데이트는 Blockchain 클래스에서)
        #    여기서는 생성된 output에 ID를 부여하는 역할 추가
        for i, output in enumerate(self.outputs):
            output.parent_transaction_id = self.transaction_id
            output.index_in_parent = i
            output.id = output.calculate_id()

        return True

    def __repr__(self):
        return (f"Transaction(ID: {self.transaction_id[:10]}..., "
                f"From: {self.sender_address[:10]}..., To: {self.recipient_address[:10]}..., "
                f"Amount: {self.amount}, Inputs: {len(self.inputs)}, Outputs: {len(self.outputs)})")
