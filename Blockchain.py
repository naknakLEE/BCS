import time
import json
import hashlib
from Block import Block
from Transaction import Transaction
from TransactionInput import TransactionInput
from TransactionOutput import TransactionOutput
from const import INITIAL_DIFFICULTY, MINING_REWARD

class Blockchain:
    def __init__(self, node_id, difficulty=INITIAL_DIFFICULTY):
        self.node_id = node_id # 이 블록체인 인스턴스를 소유한 노드 ID (P2P 시뮬레이션용)
        self.chain = []
        self.UTXOs = {} # UTXO 풀: {utxo_id: TransactionOutput 객체}
        self.difficulty = difficulty
        self.create_genesis_block()

    def create_genesis_block(self):
        # 제네시스 블록은 특별한 코인베이스 트랜잭션 (채굴 보상)을 가질 수 있음
        # 여기서는 간단히 빈 트랜잭션으로 시작
        genesis_block = Block(0, time.time(), [], "0")
        self.chain.append(genesis_block)
        print(f"Node {self.node_id}: 제네시스 블록 생성됨: {genesis_block.hash[:10]}...")

    def get_last_block(self):
        return self.chain[-1]

    def proof_of_work(self, block_header_data_for_pow):
        """작업 증명: 해시값이 '0' * difficulty 로 시작하는 nonce 값을 찾음."""
        target_prefix = '0' * self.difficulty
        nonce = 0
        temp_hash = "" # 임시 해시 저장용
        while True:
            block_header_data_for_pow["nonce"] = nonce # Nonce 업데이트
            block_header_string = json.dumps(block_header_data_for_pow, sort_keys=True).encode()
            temp_hash = hashlib.sha256(block_header_string).hexdigest()
            if temp_hash.startswith(target_prefix):
                # print(f"  Node {self.node_id}: PoW 조건 만족! Nonce: {nonce}, 해시: {temp_hash[:10]}...")
                return nonce, temp_hash # Nonce와 최종 해시 반환
            nonce += 1
            if nonce % 500000 == 0: # 진행 상황 표시 (선택적)
                 print(f"  Node {self.node_id}: 채굴 중... Nonce: {nonce}, 현재 해시: {temp_hash[:10]}...")


    def mine_block(self, transactions_to_mine, miner_wallet):
        """
        새로운 블록을 채굴합니다.
        1. 코인베이스 트랜잭션 생성 (채굴 보상).
        2. 주어진 트랜잭션들을 블록에 포함.
        3. 작업 증명 수행.
        4. 블록을 체인에 추가하고 UTXO 업데이트.
        """
        print(f"\nNode {self.node_id}: 블록 채굴 시도 (대상 거래 수: {len(transactions_to_mine)})...")

        # 1. 코인베이스 트랜잭션 (채굴자에게 보상)
        coinbase_output = TransactionOutput(miner_wallet.address, MINING_REWARD)
        # 코인베이스 트랜잭션은 입력이 없음 (새로운 코인 생성)
        # 특별한 ID와 처리가 필요 (여기서는 단순화)
        coinbase_tx = Transaction(miner_wallet, miner_wallet.address, MINING_REWARD, []) # 입력이 없는 특별한 트랜잭션
        coinbase_tx.outputs = [coinbase_output]
        coinbase_tx.transaction_id = f"coinbase_{self.get_last_block().index + 1}_{time.time()}" # 단순 ID
        coinbase_output.parent_transaction_id = coinbase_tx.transaction_id
        coinbase_output.index_in_parent = 0
        coinbase_output.id = coinbase_output.calculate_id()

        # 포함할 트랜잭션 목록 (코인베이스 + 전달받은 트랜잭션)
        block_transactions = [coinbase_tx] + transactions_to_mine

        last_block = self.get_last_block()
        merkle_root_for_pow = Block(0,0,block_transactions,"").merkle_root # PoW용 머클루트 임시계산

        block_header_data_for_pow = {
            "index": last_block.index + 1,
            "timestamp": time.time(), # 실제로는 블록 생성 시작 시점
            "previous_hash": last_block.hash,
            "merkle_root": merkle_root_for_pow,
            # "nonce"는 proof_of_work 내부에서 설정됨
        }

        nonce, new_block_hash = self.proof_of_work(block_header_data_for_pow)

        new_block = Block(
            index=block_header_data_for_pow["index"],
            timestamp=block_header_data_for_pow["timestamp"],
            transactions=block_transactions,
            previous_hash=block_header_data_for_pow["previous_hash"],
            nonce=nonce
        )
        new_block.hash = new_block_hash # PoW에서 찾은 해시로 설정
        new_block.merkle_root = merkle_root_for_pow # PoW에서 사용한 머클루트로 설정

        # 새 블록을 체인에 추가하기 전에 유효성 검사 (선택적이지만 중요)
        if self.add_block(new_block):
            print(f"Node {self.node_id}: 블록 #{new_block.index} 채굴 성공! 해시: {new_block.hash[:10]}...")
            return new_block
        else:
            print(f"Node {self.node_id}: 채굴된 블록 추가 실패.")
            return None


    def add_block(self, new_block):
        """새로운 블록을 체인에 추가하고 UTXO를 업데이트합니다."""
        last_block = self.get_last_block()
        # 기본적인 유효성 검사
        if new_block.previous_hash != last_block.hash:
            print(f"Node {self.node_id}: 오류 - 이전 블록 해시 불일치.")
            return False
        if new_block.hash != new_block.calculate_hash(): # PoW 결과와 블록 내용 일치 확인
            print(f"Node {self.node_id}: 오류 - 블록 해시 재계산 불일치 (PoW 문제 또는 데이터 변경).")
            return False
        # PoW 유효성 검사 (난이도 만족하는지)
        if not new_block.hash.startswith('0' * self.difficulty):
            print(f"Node {self.node_id}: 오류 - 작업 증명(PoW)이 유효하지 않습니다.")
            return False

        # 블록 내 트랜잭션 유효성 검사 및 UTXO 업데이트
        temp_utxos_to_add = {}
        temp_utxos_to_remove_ids = set()

        for tx in new_block.transactions:
            # 코인베이스 트랜잭션 처리
            if not tx.inputs and tx.outputs[0].amount == MINING_REWARD and tx.transaction_id.startswith("coinbase"):
                out = tx.outputs[0]
                temp_utxos_to_add[out.id] = out
                continue # 다음 트랜잭션으로

            # 일반 트랜잭션 유효성 검사
            if not tx.is_signature_valid():
                print(f"Node {self.node_id}: 블록 내 트랜잭션 {tx.transaction_id[:10]} 서명 검증 실패. 블록 거부.")
                return False

            # 입력 UTXO가 현재 UTXO 풀에 있는지 확인 (또는 이 블록 내 이전 트랜잭션에서 생성된 것인지)
            current_inputs_value = 0
            for tx_input in tx.inputs:
                if tx_input.transaction_output_id not in self.UTXOs and tx_input.transaction_output_id not in temp_utxos_to_add:
                    # 블록 내 다른 트랜잭션의 출력인지 확인 (한 블록 내에서 체인처럼 소비될 수 있음)
                    found_in_block = False
                    for prev_tx_in_block in new_block.transactions:
                        if prev_tx_in_block == tx: break # 자기 자신 이전까지만
                        for prev_out in prev_tx_in_block.outputs:
                            if prev_out.id == tx_input.transaction_output_id:
                                current_inputs_value += prev_out.amount
                                temp_utxos_to_remove_ids.add(prev_out.id) # 블록 내에서 사용됨
                                found_in_block = True
                                break
                        if found_in_block: break
                    if not found_in_block:
                        print(f"Node {self.node_id}: 블록 내 트랜잭션 {tx.transaction_id[:10]}의 입력 UTXO {tx_input.transaction_output_id[:10]}를 찾을 수 없음. 블록 거부.")
                        return False
                elif tx_input.transaction_output_id in self.UTXOs:
                    current_inputs_value += self.UTXOs[tx_input.transaction_output_id].amount
                    temp_utxos_to_remove_ids.add(tx_input.transaction_output_id) # 사용될 UTXO
                elif tx_input.transaction_output_id in temp_utxos_to_add: # 이미 이 블록에서 추가될 예정인 UTXO
                     current_inputs_value += temp_utxos_to_add[tx_input.transaction_output_id].amount
                     # temp_utxos_to_add에서 제거하고, remove_ids에도 추가 (소비되므로)
                     del temp_utxos_to_add[tx_input.transaction_output_id]
                     temp_utxos_to_remove_ids.add(tx_input.transaction_output_id)


            # 금액 확인 (입력 총합 >= 출력 총합)
            total_output_value = sum(out.amount for out in tx.outputs)
            if current_inputs_value < total_output_value:
                print(f"Node {self.node_id}: 트랜잭션 {tx.transaction_id[:10]} 입력({current_inputs_value}) < 출력({total_output_value}). 블록 거부.")
                return False

            # 새로운 출력 UTXO를 임시 추가 목록에 넣음
            for out in tx.outputs:
                if out.id in temp_utxos_to_add or out.id in self.UTXOs: # 이미 존재하는 UTXO ID면 문제
                    print(f"Node {self.node_id}: 중복된 UTXO ID {out.id[:10]} 생성 시도. 블록 거부.")
                    return False
                temp_utxos_to_add[out.id] = out


        # 모든 검증 통과 시 체인에 블록 추가 및 UTXO 풀 업데이트
        self.chain.append(new_block)
        for utxo_id in temp_utxos_to_remove_ids:
            if utxo_id in self.UTXOs:
                del self.UTXOs[utxo_id]
            # temp_utxos_to_add 에서도 제거될 수 있으나, 위 로직에서 이미 처리됨
        self.UTXOs.update(temp_utxos_to_add)

        print(f"Node {self.node_id}: 블록 #{new_block.index} 체인에 성공적으로 추가됨. UTXO 풀 업데이트됨.")
        return True


    def get_balance(self, address):
        balance = 0
        for utxo_id, utxo in self.UTXOs.items():
            if utxo.is_mine(address):
                balance += utxo.amount
        return balance

    def get_spendable_outputs(self, address, amount_needed):
        """주어진 주소가 사용할 수 있는 UTXO 목록과 총액을 반환합니다."""
        spendable = []
        accumulated_amount = 0
        for utxo_id, utxo_obj in self.UTXOs.items():
            if utxo_obj.is_mine(address):
                spendable.append(TransactionInput(utxo_id, utxo_obj))
                accumulated_amount += utxo_obj.amount
                if accumulated_amount >= amount_needed:
                    break
        if accumulated_amount < amount_needed:
            return [], 0 # 충분한 UTXO 없음
        return spendable, accumulated_amount

    def is_chain_valid(self, chain_to_validate=None):
        """주어진 체인(또는 자신의 체인)의 유효성을 검사합니다."""
        target_chain = chain_to_validate if chain_to_validate else self.chain

        # 제네시스 블록은 스킵 (특별한 경우)
        for i in range(1, len(target_chain)):
            current_block = target_chain[i]
            previous_block = target_chain[i-1]

            if current_block.hash != current_block.calculate_hash():
                print(f"유효성 오류: 블록 {current_block.index}의 해시가 내용과 일치하지 않음.")
                return False
            if current_block.previous_hash != previous_block.hash:
                print(f"유효성 오류: 블록 {current_block.index}의 이전 해시가 이전 블록의 실제 해시와 일치하지 않음.")
                return False
            if not current_block.hash.startswith('0' * self.difficulty): # PoW 검증
                print(f"유효성 오류: 블록 {current_block.index}의 작업 증명이 유효하지 않음.")
                return False

            # 트랜잭션 유효성 검사 (여기서는 단순화. 실제로는 UTXO 상태를 재구성하며 검증해야 함)
            # 이 함수는 주로 체인 구조와 PoW만 검사하는 것으로 가정
            for tx in current_block.transactions:
                if not tx.transaction_id.startswith("coinbase_") and not tx.is_signature_valid():
                     print(f"유효성 오류: 블록 {current_block.index} 내 트랜잭션 {tx.transaction_id[:10]} 서명 무효.")
                     return False
        print(f"Node {self.node_id}: 체인 유효성 검사 통과.")
        return True

    def print_chain_summary(self):
        print(f"\n--- Node {self.node_id}의 블록체인 요약 ({len(self.chain)} 블록) ---")
        for block in self.chain:
            print(f"  {block}")
        print(f"--- UTXO 풀 크기: {len(self.UTXOs)} ---")
