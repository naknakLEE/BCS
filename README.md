# BCS (Block Chain System)

This project is a simple blockchain system implemented in Python. It simulates the basic components and Soperation of a blockchain.

## Key Features

- **Block:** Contains an index, timestamp, list of transactions, previous hash, nonce, Merkle root, and current hash.
- **Blockchain:** A chain of blocks that performs Proof of Work, block addition, UTXO management, balance calculation, and chain validation.
- **Transaction:** Includes sender, recipient, amount, list of inputs, list of outputs, timestamp, transaction ID, and signature.
- **UTXO (Unspent Transaction Output):** Represents transaction outputs that have not yet been spent, serving as the basic unit of a transaction. `TransactionInput` references UTXOs, and `TransactionOutput` creates new UTXOs.
- **Wallet:** Provides functionality to generate private keys, public keys, addresses, and to sign and verify transactions.
- **NetworkNode:** Each node has its own wallet, blockchain instance, and mempool. It performs transaction creation, propagation, reception, block mining, propagation, and reception, and connects to other nodes as peers. Conflicts are resolved by selecting the longest chain (`resolve_conflicts`).
- **Proof of Work (PoW):** Iteratively performs hash calculations by changing the nonce value to find a hash value that meets specific difficulty conditions.
- **P2P Network Simulation:** Simulates the process of transaction and block propagation by creating and connecting multiple network nodes.

## Components (Python Files)

- `Block.py`: Defines the structure of a block and hash calculation (including Merkle root).
- `Blockchain.py`: Implements blockchain logic (block addition, PoW, UTXO management, chain validation, etc.).
- `Transaction.py`: Handles the structure, hash calculation, signing, and verification logic for transactions.
- `TransactionInput.py`: Defines the inputs of a transaction (UTXOs to be used).
- `TransactionOutput.py`: Defines the outputs of a transaction (new UTXOs).
- `Wallet.py`: Provides functionality for cryptographic key pair (private key, public key) and address generation, and transaction signing/verification.
- `NetworkNode.py`: Acts as a node in the P2P network and includes logic for the creation, propagation, processing of transactions and blocks, and blockchain synchronization.
- `main.py`: The main script for running the simulation. It creates and connects network nodes and runs scenarios for transaction creation and block mining.
- `const.py`: Defines constant values such as blockchain difficulty (`INITIAL_DIFFICULTY`) and mining reward (`MINING_REWARD`).
- `requirements.txt`: Specifies the required Python packages (currently only `ecdsa`).
- `.gitignore`: Specifies files and folders to be excluded from Git version control.
- `LICENSE`: Contains project license information (MIT License).
- `README.md`: This project description file.

## How to Run

1.  **Install required packages:**

    ```bash
    pip install -r requirements.txt
    ```

    (Note: `ecdsa` should be included in the `requirements.txt` file. Please check and add it if it's missing from your current file.)

2.  **Run the simulation:**
    ```bash
    python main.py
    ```
    The `main.py` file creates multiple network nodes, simulates transaction sending and block mining processes, and prints the blockchain status and balance for each node.

## Simulation Main Process (`main.py`)

1.  Creates multiple network nodes (`Node1`, `Node2`, `Node3`) and sets the difficulty for each node.
2.  Connects the created nodes as peers to each other.
3.  `Node1` mines the first block (containing only the coinbase transaction).
4.  Other nodes synchronize to `Node1`'s chain via `resolve_conflicts`.
5.  `Node1` creates a transaction to send coins to `Node2` and propagates it to the network.
6.  `Node3` mines a new block containing the above transaction.
7.  All nodes synchronize their chains again.
8.  `Node2` creates a transaction to send coins to `Node1` and propagates it to the network.
9.  `Node1` mines a block containing that transaction.
10. All nodes synchronize their chains.
11. Prints the final blockchain summary, wallet balance, and mempool size for each node, and validates the chain of a representative node.

## Notes

- This project is a simple blockchain simulation implemented for educational and learning purposes. Many aspects are simplified in terms of security and scalability for use in a real production environment.
- Uses the `ecdsa` library for elliptic curve cryptography.
- Processes transactions based on the UTXO model.
- The Merkle root is calculated simply by combining transaction IDs.
- The P2P network is simulated through direct object references.
