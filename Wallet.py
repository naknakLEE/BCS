
import hashlib
from ecdsa import SigningKey, VerifyingKey, NIST256p, BadSignatureError # NIST256p는 secp256k1과 유사한 타원 곡선
import binascii # 바이트 <-> 16진수 문자열 변환



class Wallet:
    def __init__(self):
        self.private_key = SigningKey.generate(curve=NIST256p)
        self.public_key = self.private_key.get_verifying_key()
        self.address = self.generate_address(self.public_key)

    def generate_address(self, public_key):
        """공개키로부터 주소를 생성합니다 (간단한 방식)."""
        # 실제 비트코인은 여러 단계의 해싱과 인코딩(Base58Check)을 거침
        public_key_bytes = public_key.to_string()
        sha256_hash = hashlib.sha256(public_key_bytes).digest()
        ripemd160_hash = hashlib.new('ripemd160', sha256_hash).hexdigest() # hex string으로 주소 표현
        return ripemd160_hash # 단순화를 위해 ripemd160 해시 자체를 주소로 사용

    def sign_transaction(self, transaction_data_str):
        """트랜잭션 데이터에 서명합니다."""
        signature_bytes = self.private_key.sign(transaction_data_str.encode())
        return binascii.hexlify(signature_bytes).decode('ascii') # 16진수 문자열로 변환

    @staticmethod
    def verify_signature(public_key_hex, signature_hex, data_str):
        """서명을 검증합니다."""
        try:
            public_key_bytes = binascii.unhexlify(public_key_hex)
            signature_bytes = binascii.unhexlify(signature_hex)
            vk = VerifyingKey.from_string(public_key_bytes, curve=NIST256p)
            return vk.verify(signature_bytes, data_str.encode())
        except (BadSignatureError, binascii.Error):
            return False

    def get_public_key_hex(self):
        return binascii.hexlify(self.public_key.to_string()).decode('ascii')

    def __repr__(self):
        return f"Wallet(Address: {self.address[:10]}...)"

