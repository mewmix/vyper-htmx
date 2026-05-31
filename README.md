# Vyper HTMX

`VyperHTMXView.vy` is a small experiment in making a Vyper contract the hypermedia controller.

The reusable interface is:

```vyper
interface IVyperHTMXView:
    def render(path: String[INF], caller: address, data: Bytes[INF]) -> String[INF]: view
```

Any app contract can expose routes like:

```vyper
render("home", user, b"")
render("pool", user, abi_encoded_pool_id)
render("claim", user, abi_encoded_epoch)
render("risk", user, b"")
```

The gateway exposes:

```text
GET /vx/<contract>/<path>?data=...
```

and returns:

```text
content-type: text/html
```

The weird intrinsic: the contract is the hypermedia controller.

## Files

- `VyperHTMXView.vy`: reusable interface target for Vyper `v0.5.0a2`.
- `ExampleHTMXView.vy`: minimal app contract with `home`, `pool`, `claim`, and `risk` views.
- `DynamicHTMXView.vy`: stateful contract demonstrating HTMX auto-refresh polling (`hx-trigger="every 2s"`) of on-chain state mutations.
- `MainnetExplorer.vy`: advanced DeFi dashboard that fetches real-time Chainlink, Uniswap V2, and Aave V3 data via `staticcall` when deployed to a mainnet fork.
- `gateway.py`: stdlib HTTP gateway that ABI-encodes `render(path, caller, data)`, performs `eth_call`, decodes the returned string, and serves it as HTML.
- `mock_rpc.py`: local JSON-RPC mock for browser testing without deploying a chain.
- `test_gateway.py`: ABI, Keccak selector, and data parsing tests.

`ExampleHTMXView.vy` uses concrete bounds (`String[64]`, `Bytes[4096]`, `String[4096]`) because `vyper==0.5.0a2` can compile the unbounded interface but panics during codegen when a concrete function body uses `String[INF]` / `Bytes[INF]`. The public ABI remains `render(string,address,bytes) returns (string)`.

## Prerequisites

- Python 3.11 or newer.
- Git.
- Optional for real local-chain deployment: Foundry tools (`anvil` and `cast`).

Official install references:

- Vyper install docs: https://docs.vyperlang.org/en/stable/installing-vyper.html
- Vyper `v0.5.0a2` release: https://github.com/vyperlang/vyper/releases/tag/v0.5.0a2
- Foundry install docs: https://www.getfoundry.sh/introduction/installation/

## Setup

From this repository:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Verify Vyper:

```powershell
vyper --version
```

Expected version:

```text
0.5.0a2
```

Run the Python tests:

```powershell
python -m unittest -v
```

Compile the interface and example contract:

```powershell
vyper VyperHTMXView.vy
vyper -f abi ExampleHTMXView.vy
vyper ExampleHTMXView.vy
```

## Fast End-to-End Browser Test

This path tests:

```text
browser -> gateway -> JSON-RPC -> ABI decode/encode -> HTML response
```

It does not require a blockchain node.

Terminal 1:

```powershell
.\.venv\Scripts\Activate.ps1
python mock_rpc.py
```

Terminal 2:

```powershell
.\.venv\Scripts\Activate.ps1
python gateway.py --port 8080 --rpc-url http://127.0.0.1:8545
```

Open this URL:

```text
http://127.0.0.1:8080/vx/0x1111111111111111111111111111111111111111/home?data=
```

You should see the `home` HTML returned by the mock contract path. Click `Pool`, `Risk`, then `Claim` to exercise HTMX requests through the gateway.

If the HTMX CDN is blocked, the raw pages still render, but `hx-get` swaps will not run. Direct route URLs still work, for example:

```text
http://127.0.0.1:8080/vx/0x1111111111111111111111111111111111111111/pool?data=
```

## Real Local-Chain End-to-End Test

Install Foundry first. On Windows, the official Foundry docs currently list the Rust/Cargo install path:

```powershell
cargo install --git https://github.com/foundry-rs/foundry --profile release --locked forge cast chisel anvil
```

Verify:

```powershell
anvil --version
cast --version
```

Terminal 1, start a local chain:

```powershell
anvil
```

Terminal 2, compile and deploy the Vyper view contract:

```powershell
.\.venv\Scripts\Activate.ps1
$bytecode = vyper -f bytecode ExampleHTMXView.vy
cast send `
  --rpc-url http://127.0.0.1:8545 `
  --private-key 0xac0974bec39a17e36ba4a6b4d238ff944bacb478cbed5efcae784d7bf4f2ff80 `
  --create $bytecode
```

Copy the `contractAddress` from the `cast send` output.

Terminal 3, start the gateway against Anvil:

```powershell
.\.venv\Scripts\Activate.ps1
python gateway.py --port 8080 --rpc-url http://127.0.0.1:8545
```

Open:

```text
http://127.0.0.1:8080/vx/<contractAddress>/home?data=
```

Example with an explicit caller:

```text
http://127.0.0.1:8080/vx/<contractAddress>/claim?caller=0xf39fd6e51aad88f6f4ce6ab8827279cfffb92266&data=0x01
```

## Gateway Contract

The gateway calls:

```text
render(path: string, caller: address, data: bytes) -> string
```

`data` accepts either hex bytes:

```text
?data=0x000000000000000000000000000000000000000000000000000000000000002a
```

or URL-encoded bytes:

```text
?data=pool%2042
```

`caller` defaults to `0x0000000000000000000000000000000000000000` when omitted.
