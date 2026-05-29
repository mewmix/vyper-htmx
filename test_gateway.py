import unittest

from gateway import (
    ZERO_ADDRESS,
    decode_string,
    encode_dynamic,
    encode_render_call,
    keccak256,
    parse_data,
    uint256,
)


class GatewayAbiTests(unittest.TestCase):
    def test_keccak_selector_matches_ethereum_abi(self):
        self.assertEqual(keccak256(b"transfer(address,uint256)")[:4].hex(), "a9059cbb")

    def test_encode_render_call_contains_dynamic_arguments(self):
        calldata = encode_render_call("home", ZERO_ADDRESS, b"")
        self.assertTrue(calldata.startswith("0x"))
        self.assertEqual(calldata[10:74], uint256(96).hex())
        self.assertEqual(calldata[74:138], ZERO_ADDRESS[2:].rjust(64, "0"))
        self.assertIn(encode_dynamic(b"home").hex(), calldata)
        self.assertTrue(calldata.endswith(encode_dynamic(b"").hex()))

    def test_decode_string(self):
        encoded = "0x" + (uint256(32) + encode_dynamic(b"<main>ok</main>")).hex()
        self.assertEqual(decode_string(encoded), "<main>ok</main>")

    def test_parse_data_accepts_hex_or_url_encoded_bytes(self):
        self.assertEqual(parse_data("0x0102"), b"\x01\x02")
        self.assertEqual(parse_data("pool%2042"), b"pool 42")


if __name__ == "__main__":
    unittest.main()
