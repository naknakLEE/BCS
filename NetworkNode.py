from Wallet import Wallet
from Blockchain import Blockchain
from Transaction import Transaction
from const import INITIAL_DIFFICULTY


class NetworkNode:
    def __init__(self, node_id, difficulty=INITIAL_DIFFICULTY):
        self.node_id = node_id
        self.wallet = Wallet() # 각 노드는 자신의 지갑을 가짐
        self.blockchain = Blockchain(node_id, difficulty)
        self.mempool = {} # {tx_id: Transaction 객체}
        self.peers = [] # 다른 NetworkNode 객체들 (P2P 시뮬레이션용)
        print(f"네트워크 노드 {self.node_id} 생성됨. 지갑 주소: {self.wallet.address[:10]}...")

    def add_peer(self, peer_node):
        if peer_node not in self.peers and peer_node != self:
            self.peers.append(peer_node)
            print(f"Node {self.node_id}: 피어 {peer_node.node_id} 추가됨.")

    def create_transaction(self, recipient_address, amount):
        """새로운 트랜잭션을 생성하고 서명한 후 자신의 멤풀에 추가하고 전파합니다."""
        balance = self.blockchain.get_balance(self.wallet.address)
        if balance < amount:
            print(f"Node {self.node_id}: 잔액 부족 ({balance})으로 {amount} 전송 불가.")
            return None

        inputs_for_tx, total_input_value = self.blockchain.get_spendable_outputs(self.wallet.address, amount)
        if not inputs_for_tx:
            print(f"Node {self.node_id}: 거래에 사용할 충분한 UTXO가 없습니다.")
            return None

        new_tx = Transaction(self.wallet, recipient_address, amount, inputs_for_tx)
        if not new_tx.process_transaction(self.blockchain.UTXOs): # UTXO 풀은 아직 변경 안함, 유효성만 체크
            print(f"Node {self.node_id}: 트랜잭션 처리 중 오류 발생.")
            return None
        if not new_tx.sign(self.wallet):
            print(f"Node {self.node_id}: 트랜잭션 서명 실패.")
            return None

        print(f"Node {self.node_id}: 트랜잭션 생성: {new_tx.transaction_id[:10]}... (From: {self.wallet.address[:10]}, To: {recipient_address[:10]}, Amount: {amount})")
        self.add_transaction_to_mempool(new_tx) # 자신의 멤풀에 추가
        self.broadcast_transaction(new_tx)    # 다른 피어에게 전파
        return new_tx

    def add_transaction_to_mempool(self, transaction):
        """유효한 트랜잭션을 멤풀에 추가합니다."""
        # 여기서 더 많은 검증이 필요 (예: 이중 지불 방지, 이미 처리된 트랜잭션인지 등)
        if transaction.transaction_id not in self.mempool:
            # 서명 검증 (이미 생성 시 했을 수 있지만, 수신 시 다시 확인)
            if not transaction.is_signature_valid():
                print(f"Node {self.node_id}: 멤풀 추가 시 트랜잭션 {transaction.transaction_id[:10]} 서명 무효.")
                return False

            # 입력 UTXO가 현재 블록체인의 UTXO 풀에 실제로 존재하는지 확인 (매우 중요)
            # 이 예제에서는 create_transaction 에서 이미 확인했으므로, 수신된 트랜잭션에 대해 더 중요
            required_input_value = 0
            for tx_input in transaction.inputs:
                if tx_input.transaction_output_id not in self.blockchain.UTXOs:
                    print(f"Node {self.node_id}: 멤풀 추가 시 트랜잭션 {transaction.transaction_id[:10]}의 입력 UTXO {tx_input.transaction_output_id[:10]}가 UTXO 풀에 없음.")
                    return False
                # 이미 멤풀의 다른 트랜잭션에 의해 소비될 예정인 UTXO인지 확인 (이중 지불 방지)
                for mem_tx_id, mem_tx in self.mempool.items():
                    for mem_tx_input in mem_tx.inputs:
                        if mem_tx_input.transaction_output_id == tx_input.transaction_output_id:
                            print(f"Node {self.node_id}: 이중 지불 시도 감지! UTXO {tx_input.transaction_output_id[:10]}가 이미 멤풀의 다른 트랜잭션({mem_tx_id[:10]})에 의해 사용될 예정입니다.")
                            return False
                required_input_value += self.blockchain.UTXOs[tx_input.transaction_output_id].amount

            # 보내는 금액과 출력 금액 일치 확인
            total_output_value = sum(out.amount for out in transaction.outputs)
            # 입력 총액이 출력 총액과 같거나, (입력총액 - 출력총액)이 수수료 개념일 수 있음.
            # 여기서는 정확히 일치하는지만 (거스름돈 포함)
            if required_input_value != total_output_value : # 거스름돈이 sender에게 정확히 가는지 확인
                 # amount (보내는돈) + change (거스름돈) = total_output_value
                 # 실제로는 (total_input_value - total_output_value) = 수수료 > 0 이어야 함
                 # 이 코드에서는 수수료 개념이 없으므로, 입력=출력 이어야 함
                 is_change_correct = False
                 if len(transaction.outputs) == 1 and transaction.outputs[0].recipient_address == transaction.recipient_address and transaction.outputs[0].amount == transaction.amount and required_input_value == transaction.amount:
                     is_change_correct = True # 거스름돈 없음
                 elif len(transaction.outputs) == 2:
                     to_recipient = False
                     change_to_sender = False
                     for out in transaction.outputs:
                         if out.recipient_address == transaction.recipient_address and out.amount == transaction.amount:
                             to_recipient = True
                         if out.recipient_address == transaction.sender_address and out.amount == (required_input_value - transaction.amount):
                             change_to_sender = True
                     if to_recipient and change_to_sender:
                         is_change_correct = True

                 if not is_change_correct:
                    print(f"Node {self.node_id}: 멤풀 추가 시 트랜잭션 {transaction.transaction_id[:10]}의 입출력 금액 불일치 또는 거스름돈 오류.")
                    return False


            self.mempool[transaction.transaction_id] = transaction
            # print(f"Node {self.node_id}: 트랜잭션 {transaction.transaction_id[:10]} 멤풀에 추가됨.")
            return True
        return False # 이미 멤풀에 있음


    def broadcast_transaction(self, transaction):
        """트랜잭션을 모든 피어에게 전파합니다."""
        print(f"Node {self.node_id}: 트랜잭션 {transaction.transaction_id[:10]} 전파 중...")
        for peer in self.peers:
            peer.receive_transaction(transaction, self) # 송신자 정보도 전달 (루프 방지)

    def receive_transaction(self, transaction, sender_peer):
        """다른 노드로부터 트랜잭션을 수신합니다."""
        # print(f"Node {self.node_id}: {sender_peer.node_id}로부터 트랜잭션 {transaction.transaction_id[:10]} 수신.")
        if self.add_transaction_to_mempool(transaction): # 유효하면 멤풀에 추가
            # 자신이 이미 받은 트랜잭션이 아니라면 다른 피어에게도 전파 (중복 전파 방지 로직 필요)
            # 이 예제에서는 간단히 모든 피어에게 다시 전파하지 않음 (broadcast_transaction에서만 전파)
            pass


    def mine_new_block(self):
        """자신의 멤풀에서 트랜잭션을 가져와 새로운 블록을 채굴하고 전파합니다."""
        # 멤풀이 비어있더라도 코인베이스 트랜잭션을 포함한 블록을 채굴할 수 있어야 합니다.
        # 예를 들어, 첫 블록은 코인베이스 트랜잭션만 가질 수 있습니다.
        # print(f"Node {self.node_id}: 채굴 시도. 현재 멤풀 크기: {len(self.mempool)}") # 디버깅용 로그

        # 멤풀에서 트랜잭션 선택 (실제로는 수수료 기반 등으로 선택)
        # 여기서는 멤풀의 모든 트랜잭션을 가져옴 (간단화)
        transactions_to_mine = list(self.mempool.values()) # 멤풀이 비어있으면 빈 리스트가 됨

        # 채굴 시도
        new_block = self.blockchain.mine_block(transactions_to_mine, self.wallet)

        if new_block:
            # 채굴 성공 시, 멤풀에서 해당 트랜잭션들 제거
            for tx in transactions_to_mine:
                if tx.transaction_id in self.mempool:
                    del self.mempool[tx.transaction_id]
            print(f"Node {self.node_id}: 블록 채굴 후 멤풀 정리. 남은 멤풀 크기: {len(self.mempool)}")
            self.broadcast_block(new_block)
            return new_block
        return None

    def broadcast_block(self, block):
        """새로운 블록을 모든 피어에게 전파합니다."""
        print(f"Node {self.node_id}: 블록 #{block.index} (해시: {block.hash[:10]}...) 전파 중...")
        for peer in self.peers:
            peer.receive_block(block, self)

    def receive_block(self, block, sender_peer):
        """다른 노드로부터 블록을 수신합니다."""
        print(f"Node {self.node_id}: {sender_peer.node_id}로부터 블록 #{block.index} (해시: {block.hash[:10]}...) 수신.")

        # 현재 체인보다 긴 체인인지, 또는 현재 체인의 다음 블록인지 확인
        current_last_block = self.blockchain.get_last_block()

        if block.previous_hash == current_last_block.hash and block.index == current_last_block.index + 1:
            # 정상적인 다음 블록
            if self.blockchain.add_block(block):
                # 성공적으로 추가되면, 이 블록에 포함된 트랜잭션들을 자신의 멤풀에서 제거
                for tx in block.transactions:
                    if tx.transaction_id in self.mempool:
                        del self.mempool[tx.transaction_id]
                print(f"Node {self.node_id}: 수신한 블록 #{block.index} 체인에 추가 완료. 멤풀 업데이트.")
                # 자신이 받은 블록이므로 다시 전파할 필요는 없음 (네트워크 정책에 따라 다를 수 있음)
            else:
                print(f"Node {self.node_id}: 수신한 블록 #{block.index} 추가 실패 (유효성 검사 등).")
        elif block.index > current_last_block.index:
            # 더 긴 체인을 받았을 가능성 (체인 재구성 필요)
            print(f"Node {self.node_id}: 현재 체인보다 긴 블록(인덱스 {block.index})을 수신. 체인 교체 시도 필요 (미구현).")
            # 실제로는 해당 sender_peer에게 이전 블록들을 요청하여 전체 체인을 받아와 검증 후 교체 (resolve_conflicts)
            # 여기서는 간단히 더 긴 체인이면 무조건 받아들이지 않음 (가장 기본적인 PoW만 따름)
            # 실제로는 복잡한 체인 동기화 및 가장 긴 유효한 체인 선택 로직 필요
        else:
            # 이미 가지고 있는 블록이거나, 이전 블록일 수 있음
            # print(f"Node {self.node_id}: 수신한 블록 #{block.index}은 현재 체인에 적합하지 않음 (너무 오래되었거나 이미 처리됨).")
            pass


    def resolve_conflicts(self, network_nodes_list):
        """네트워크의 다른 노드들과 체인을 비교하여 가장 긴 유효한 체인으로 교체합니다 (Longest Chain Rule)."""
        longest_chain = list(self.blockchain.chain) # 자신의 체인으로 시작
        current_max_length = len(longest_chain)
        new_utxo_pool = dict(self.blockchain.UTXOs) # 교체될 경우의 UTXO 풀

        for peer_node in network_nodes_list:
            if peer_node == self: continue

            peer_chain = peer_node.blockchain.chain
            if len(peer_chain) > current_max_length:
                # 더 긴 체인을 찾았으면, 해당 체인이 유효한지 검사해야 함
                # 유효성 검사는 해당 노드의 difficulty를 사용해야 하지만, 여기서는 자신의 difficulty 사용
                temp_blockchain_for_validation = Blockchain(f"temp_validator_for_{peer_node.node_id}", self.blockchain.difficulty)
                temp_blockchain_for_validation.chain = [] # 비우고

                # 제네시스 블록 복사
                if peer_chain:
                    # 제네시스 블록은 UTXO 변경 없이 그대로 추가
                    temp_blockchain_for_validation.chain.append(peer_chain[0])

                    # 나머지 블록들을 순차적으로 add_block하며 UTXO 재구성
                    valid_so_far = True
                    temp_utxos_for_validation = {} # 초기 UTXO 풀 (제네시스 이후)

                    for i in range(1, len(peer_chain)):
                        block_to_add = peer_chain[i]
                        # add_block은 내부적으로 UTXO를 업데이트하므로, 임시 UTXO 풀을 사용해야 함
                        # add_block전에 temp_blockchain_for_validation.UTXOs 를 temp_utxos_for_validation 로 설정
                        original_utxos = dict(temp_blockchain_for_validation.UTXOs) # 백업
                        temp_blockchain_for_validation.UTXOs = dict(temp_utxos_for_validation) # 현재까지 재구성된 UTXO로 설정

                        if not temp_blockchain_for_validation.add_block(block_to_add):
                            print(f"Node {self.node_id}: 피어 {peer_node.node_id}의 체인 검증 중 블록 {block_to_add.index} 유효성 실패.")
                            valid_so_far = False
                            temp_blockchain_for_validation.UTXOs = original_utxos # 복원
                            break
                        else:
                            # 성공적으로 추가되었으면, 업데이트된 UTXO 풀을 다음 검증에 사용
                            temp_utxos_for_validation = dict(temp_blockchain_for_validation.UTXOs)
                            temp_blockchain_for_validation.UTXOs = original_utxos # 복원 (add_block은 내부 UTXO를 바꾸므로)


                    if valid_so_far:
                        print(f"Node {self.node_id}: 피어 {peer_node.node_id}의 체인(길이 {len(peer_chain)})이 더 길고 유효함. 교체 대상으로 설정.")
                        current_max_length = len(peer_chain)
                        longest_chain = list(peer_chain) # 리스트 복사
                        new_utxo_pool = dict(temp_utxos_for_validation) # 유효성 검증을 통해 재구성된 UTXO 풀
                    else:
                        print(f"Node {self.node_id}: 피어 {peer_node.node_id}의 체인이 길지만 유효하지 않음.")

        if longest_chain != self.blockchain.chain: # 자신의 체인과 다르면 (즉, 다른 노드의 체인이 선택되었으면)
            print(f"Node {self.node_id}: 체인 충돌 해결. 새로운 체인(길이 {len(longest_chain)})으로 교체합니다.")
            self.blockchain.chain = longest_chain
            self.blockchain.UTXOs = new_utxo_pool # 재구성된 UTXO 풀로 교체

            # 체인이 바뀌었으므로 멤풀의 트랜잭션들을 다시 검증해야 할 수 있음 (새 체인의 UTXO 기준)
            # 여기서는 간단히 멤풀을 비우는 것으로 처리
            self.mempool.clear()
            print(f"Node {self.node_id}: 체인 교체 후 멤풀 초기화됨.")
            return True
        else:
            # print(f"Node {self.node_id}: 현재 체인이 가장 김. 변경 없음.")
            return False
