from __future__ import annotations

import argparse
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


ADDRESS_RE = re.compile(r"^0x[0-9a-fA-F]{40}$")
ZERO_ADDRESS = "0x0000000000000000000000000000000000000000"
MASK_64 = (1 << 64) - 1


KECCAK_ROUND_CONSTANTS = (
    0x0000000000000001,
    0x0000000000008082,
    0x800000000000808A,
    0x8000000080008000,
    0x000000000000808B,
    0x0000000080000001,
    0x8000000080008081,
    0x8000000000008009,
    0x000000000000008A,
    0x0000000000000088,
    0x0000000080008009,
    0x000000008000000A,
    0x000000008000808B,
    0x800000000000008B,
    0x8000000000008089,
    0x8000000000008003,
    0x8000000000008002,
    0x8000000000000080,
    0x000000000000800A,
    0x800000008000000A,
    0x8000000080008081,
    0x8000000000008080,
    0x0000000080000001,
    0x8000000080008008,
)

KECCAK_ROTATION_OFFSETS = (
    1,
    3,
    6,
    10,
    15,
    21,
    28,
    36,
    45,
    55,
    2,
    14,
    27,
    41,
    56,
    8,
    25,
    43,
    62,
    18,
    39,
    61,
    20,
    44,
)

KECCAK_PI_LANES = (
    10,
    7,
    11,
    17,
    18,
    3,
    5,
    16,
    8,
    21,
    24,
    4,
    15,
    23,
    19,
    13,
    12,
    2,
    20,
    14,
    22,
    9,
    6,
    1,
)


def rotate_left(value: int, shift: int) -> int:
    return ((value << shift) | (value >> (64 - shift))) & MASK_64


def keccak_f1600(state: list[int]) -> None:
    for round_constant in KECCAK_ROUND_CONSTANTS:
        column = [0] * 5
        for index in range(5):
            column[index] = (
                state[index]
                ^ state[index + 5]
                ^ state[index + 10]
                ^ state[index + 15]
                ^ state[index + 20]
            )

        for index in range(5):
            theta = column[(index + 4) % 5] ^ rotate_left(column[(index + 1) % 5], 1)
            for lane in range(index, 25, 5):
                state[lane] ^= theta

        current = state[1]
        for index in range(24):
            lane = KECCAK_PI_LANES[index]
            state[lane], current = rotate_left(current, KECCAK_ROTATION_OFFSETS[index]), state[lane]

        for row in range(0, 25, 5):
            row_values = state[row : row + 5]
            for index in range(5):
                state[row + index] ^= (~row_values[(index + 1) % 5]) & row_values[(index + 2) % 5]

        state[0] ^= round_constant


def keccak256(value: bytes) -> bytes:
    rate = 136
    state = [0] * 25

    padded = bytearray(value)
    padded.append(0x01)
    padded.extend(b"\x00" * ((rate - (len(padded) % rate)) % rate))
    padded[-1] ^= 0x80

    for offset in range(0, len(padded), rate):
        block = padded[offset : offset + rate]
        for lane in range(rate // 8):
            state[lane] ^= int.from_bytes(block[lane * 8 : lane * 8 + 8], "little")
        keccak_f1600(state)

    output = bytearray()
    while len(output) < 32:
        for lane in range(rate // 8):
            output.extend(state[lane].to_bytes(8, "little"))
        if len(output) < 32:
            keccak_f1600(state)
    return bytes(output[:32])


RENDER_SELECTOR = keccak256(b"render(string,address,bytes)")[:4]


def pad32(value: bytes) -> bytes:
    remainder = len(value) % 32
    if remainder == 0:
        return value
    return value + (b"\x00" * (32 - remainder))


def uint256(value: int) -> bytes:
    if value < 0:
        raise ValueError("uint256 cannot encode negative values")
    return value.to_bytes(32, "big")


def encode_dynamic(value: bytes) -> bytes:
    return uint256(len(value)) + pad32(value)


def encode_render_call(path: str, caller: str, data: bytes) -> str:
    if not ADDRESS_RE.match(caller):
        raise ValueError("caller must be a 20-byte hex address")

    path_bytes = path.encode("utf-8")
    caller_bytes = bytes.fromhex(caller[2:])
    head_size = 32 * 3
    path_tail = encode_dynamic(path_bytes)
    data_tail = encode_dynamic(data)

    calldata = (
        RENDER_SELECTOR
        + uint256(head_size)
        + (b"\x00" * 12)
        + caller_bytes
        + uint256(head_size + len(path_tail))
        + path_tail
        + data_tail
    )
    return "0x" + calldata.hex()


def decode_string(result: str) -> str:
    if not result.startswith("0x"):
        raise ValueError("JSON-RPC result must be hex")
    raw = bytes.fromhex(result[2:])
    if len(raw) < 64:
        raise ValueError("ABI string result is too short")

    offset = int.from_bytes(raw[:32], "big")
    if offset + 32 > len(raw):
        raise ValueError("ABI string offset is out of bounds")

    size = int.from_bytes(raw[offset : offset + 32], "big")
    start = offset + 32
    end = start + size
    if end > len(raw):
        raise ValueError("ABI string length is out of bounds")
    return raw[start:end].decode("utf-8")


def parse_data(value: str) -> bytes:
    if value == "":
        return b""
    if value.startswith("0x"):
        return bytes.fromhex(value[2:])
    return urllib.parse.unquote_to_bytes(value)


class Gateway:
    def __init__(self, rpc_url: str) -> None:
        self.rpc_url = rpc_url
        self.request_id = 0

    def eth_call(self, contract: str, calldata: str) -> str:
        self.request_id += 1
        body = json.dumps(
            {
                "jsonrpc": "2.0",
                "id": self.request_id,
                "method": "eth_call",
                "params": [{"to": contract, "data": calldata}, "latest"],
            }
        ).encode("utf-8")

        request = urllib.request.Request(
            self.rpc_url,
            data=body,
            headers={"content-type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            payload = json.loads(response.read().decode("utf-8"))

        if "error" in payload:
            message = payload["error"].get("message", "eth_call failed")
            raise RuntimeError(message)
        return payload["result"]

    def render(self, contract: str, path: str, caller: str, data: bytes) -> str:
        calldata = encode_render_call(path, caller, data)
        return decode_string(self.eth_call(contract, calldata))


class VyperHTMXHandler(BaseHTTPRequestHandler):
    gateway: Gateway

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        parts = [part for part in parsed.path.split("/") if part]
        query = urllib.parse.parse_qs(parsed.query, keep_blank_values=True)

        if len(parts) != 3 or parts[0] != "vx":
            self.send_error(404, "expected /vx/<contract>/<path>")
            return

        contract = parts[1]
        path = urllib.parse.unquote(parts[2])
        caller = query.get("caller", [ZERO_ADDRESS])[0]
        data_value = query.get("data", [""])[0]

        if not ADDRESS_RE.match(contract):
            self.send_error(400, "contract must be a 20-byte hex address")
            return
        if not ADDRESS_RE.match(caller):
            self.send_error(400, "caller must be a 20-byte hex address")
            return

        try:
            data = parse_data(data_value)
        except ValueError as exc:
            self.send_error(400, str(exc))
            return

        try:
            html = self.gateway.render(contract, path, caller, data)
        except (ValueError, RuntimeError, urllib.error.URLError) as exc:
            self.send_error(502, str(exc))
            return

        payload = html.encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "text/html; charset=utf-8")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=os.getenv("VX_HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("VX_PORT", "8080")))
    parser.add_argument("--rpc-url", default=os.getenv("ETH_RPC_URL", "http://127.0.0.1:8545"))
    args = parser.parse_args()

    VyperHTMXHandler.gateway = Gateway(args.rpc_url)
    server = ThreadingHTTPServer((args.host, args.port), VyperHTMXHandler)
    print(f"serving http://{args.host}:{args.port}/vx/<contract>/<path>?data=...")
    print(f"rpc {args.rpc_url}")
    server.serve_forever()


if __name__ == "__main__":
    main()
