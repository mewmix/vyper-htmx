from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gateway import encode_dynamic, uint256


CONTRACT = "0x1111111111111111111111111111111111111111"


def encode_string(value: str) -> str:
    return "0x" + (uint256(32) + encode_dynamic(value.encode("utf-8"))).hex()


def decode_path(calldata: str) -> str:
    raw = bytes.fromhex(calldata[2:])
    args = raw[4:]
    path_offset = int.from_bytes(args[:32], "big")
    path_size = int.from_bytes(args[path_offset : path_offset + 32], "big")
    start = path_offset + 32
    return args[start : start + path_size].decode("utf-8")


def render(path: str) -> str:
    if path == "home":
        return (
            "<script src='https://unpkg.com/htmx.org@2.0.4'></script>"
            "<main>"
            "<h1>Vyper HTMX</h1>"
            "<p>The contract is the hypermedia controller.</p>"
            f"<nav><a href='/vx/{CONTRACT}/pool?data=' hx-get='/vx/{CONTRACT}/pool?data=' hx-target='main'>Pool</a> "
            f"<a href='/vx/{CONTRACT}/risk?data=' hx-get='/vx/{CONTRACT}/risk?data=' hx-target='main'>Risk</a></nav>"
            "</main>"
        )
    if path == "pool":
        return (
            "<main><section>"
            "<h2>Pool</h2>"
            "<p>Pool view rendered through eth_call.</p>"
            f"<button hx-get='/vx/{CONTRACT}/claim?data=0x01' hx-target='main'>Claim</button>"
            "</section></main>"
        )
    if path == "claim":
        return "<main><section><h2>Claim</h2><p>Claim view rendered through eth_call.</p></section></main>"
    if path == "risk":
        return "<main><section><h2>Risk</h2><p>Risk view rendered through eth_call.</p></section></main>"
    return "<main><h1>Not found</h1></main>"


class MockRpcHandler(BaseHTTPRequestHandler):
    def do_POST(self) -> None:
        size = int(self.headers.get("content-length", "0"))
        request = json.loads(self.rfile.read(size).decode("utf-8"))

        try:
            params = request.get("params", [{}])
            call = params[0]
            path = decode_path(call["data"])
            result = encode_string(render(path))
            response = {"jsonrpc": "2.0", "id": request.get("id"), "result": result}
        except Exception as exc:
            response = {
                "jsonrpc": "2.0",
                "id": request.get("id"),
                "error": {"code": -32000, "message": str(exc)},
            }

        payload = json.dumps(response).encode("utf-8")
        self.send_response(200)
        self.send_header("content-type", "application/json")
        self.send_header("content-length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)


def main() -> None:
    server = ThreadingHTTPServer(("127.0.0.1", 8545), MockRpcHandler)
    print(f"mock contract {CONTRACT}")
    print("mock rpc http://127.0.0.1:8545")
    server.serve_forever()


if __name__ == "__main__":
    main()
