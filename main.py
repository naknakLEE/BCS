import time
from NetworkNode import NetworkNode



# --- 시뮬레이션 실행 ---
if __name__ == "__main__":
    # 1. 네트워크 노드 생성
    node1 = NetworkNode("Node1", difficulty=4) # 채굴 노드
    node2 = NetworkNode("Node2", difficulty=4) # 다른 노드
    node3 = NetworkNode("Node3", difficulty=4) # 또 다른 노드
    network_nodes = [node1, node2, node3]

    # 2. 피어 연결 (양방향)
    node1.add_peer(node2)
    node1.add_peer(node3)
    node2.add_peer(node1)
    node2.add_peer(node3)
    node3.add_peer(node1)
    node3.add_peer(node2)

    # 3. 초기 코인 분배 (제네시스 블록에 코인베이스가 없으므로, 첫 채굴자가 보상 받음)
    #    이 시뮬레이션에서는 채굴을 통해 코인이 생성됨.

    # --- 시나리오 ---
    print("\n--- 시뮬레이션 시작 ---")

    # 4. Node1이 첫 번째 블록 채굴 (멤풀 비어있음, 코인베이스 트랜잭션만 포함)
    print("\n[라운드 1] Node1이 첫 블록(코인베이스) 채굴 시도...")
    initial_block = node1.mine_new_block()
    time.sleep(0.1) # 전파 시간 약간 주기

    # 5. 다른 노드들이 체인 동기화 (resolve_conflicts 호출)
    print("\n[라운드 1] 체인 동기화 (resolve_conflicts)...")
    for node in network_nodes:
        node.resolve_conflicts(network_nodes)
    time.sleep(0.1)

    # node1.blockchain.print_chain_summary()
    # node2.blockchain.print_chain_summary()

    # 6. Node2가 Node3에게 코인 전송 트랜잭션 생성
    print(f"\n[라운드 2] Node2 (잔액: {node2.blockchain.get_balance(node2.wallet.address)})가 Node3에게 3 코인 전송 시도...")
    # 아직 Node2는 코인이 없음. Node1만 코인베이스로 10코인 가짐.
    # Node1이 Node2에게 보내는 트랜잭션을 먼저 만들어야 함.
    print(f"\n[라운드 2.1] Node1 (잔액: {node1.blockchain.get_balance(node1.wallet.address)})이 Node2에게 7 코인 전송 시도...")
    tx1 = node1.create_transaction(node2.wallet.address, 7)
    time.sleep(0.1)

    # print(f"Node1 멤풀: {node1.mempool}")
    # print(f"Node2 멤풀: {node2.mempool}")
    # print(f"Node3 멤풀: {node3.mempool}")


    # 7. Node3가 다음 블록 채굴 (Node1이 만든 트랜잭션 포함)
    print(f"\n[라운드 2.2] Node3 (멤풀 크기: {len(node3.mempool)})이 다음 블록 채굴 시도...")
    block_by_node3 = node3.mine_new_block()
    time.sleep(0.1)

    print("\n[라운드 2.3] 체인 동기화...")
    for node in network_nodes:
        node.resolve_conflicts(network_nodes)
    time.sleep(0.1)

    # print(f"Node1 잔액: {node1.blockchain.get_balance(node1.wallet.address)}") # 10(보상) - 7(송금) + 10(새블록보상없음) = 3
    # print(f"Node2 잔액: {node2.blockchain.get_balance(node2.wallet.address)}") # 7 (송금받음)
    # print(f"Node3 잔액: {node3.blockchain.get_balance(node3.wallet.address)}") # 10 (채굴보상)


    # 8. 이제 Node2가 Node1에게 코인 전송
    print(f"\n[라운드 3] Node2 (잔액: {node2.blockchain.get_balance(node2.wallet.address)})가 Node1에게 2 코인 전송 시도...")
    tx2 = node2.create_transaction(node1.wallet.address, 2)
    time.sleep(0.1)


    # 9. Node1이 다음 블록 채굴 (Node2가 만든 트랜잭션 포함)
    print(f"\n[라운드 3.1] Node1 (멤풀 크기: {len(node1.mempool)})이 다음 블록 채굴 시도...")
    block_by_node1_again = node1.mine_new_block()
    time.sleep(0.1)

    print("\n[라운드 3.2] 체인 동기화...")
    for node in network_nodes:
        node.resolve_conflicts(network_nodes)
    time.sleep(0.1)


    # 최종 상태 출력
    print("\n--- 최종 블록체인 상태 ---")
    for node in network_nodes:
        node.blockchain.print_chain_summary()
        print(f"  Node {node.node_id} 지갑 ({node.wallet.address[:10]}...) 잔액: {node.blockchain.get_balance(node.wallet.address)}")
        print(f"  Node {node.node_id} 멤풀 크기: {len(node.mempool)}")
        print("-" * 20)

    print("\n--- 전체 체인 유효성 검사 ---")
    # 대표로 node1의 체인만 검증 (동기화 후에는 동일해야 함)
    node1.blockchain.is_chain_valid()