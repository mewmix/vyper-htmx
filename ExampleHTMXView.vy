# pragma version 0.5.0a2

@external
@view
def render(path: String[64], caller: address, data: Bytes[4096]) -> String[4096]:
    if path == "home":
        return "<script src='https://unpkg.com/htmx.org@2.0.4'></script><main><h1>Vyper HTMX</h1><p>The contract is the hypermedia controller.</p><nav><a href='pool?data=' hx-get='pool?data=' hx-target='main'>Pool</a></nav></main>"

    if path == "pool":
        return "<section><h2>Pool</h2><p>Pool view rendered on-chain.</p><button hx-get='claim?data=' hx-target='main'>Claim</button></section>"

    if path == "claim":
        return "<section><h2>Claim</h2><p>Claim view rendered on-chain.</p></section>"

    if path == "risk":
        return "<section><h2>Risk</h2><p>Risk view rendered on-chain.</p></section>"

    return "<main><h1>Not found</h1></main>"
