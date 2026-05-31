# pragma version 0.5.0a2

interface IChainlink:
    def latestRoundData() -> (uint80, int256, uint256, uint256, uint80): view

interface IUniswapV2Pair:
    def getReserves() -> (uint112, uint112, uint32): view

interface IAaveV3DataProvider:
    def getReserveData(asset: address) -> (uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint256, uint40): view

@external
@view
def render(path: String[64], caller: address, data: Bytes[4096]) -> String[4096]:
    if path == "home":
        p1: String[1024] = "<script src='https://unpkg.com/htmx.org@2.0.4'></script><style>body{background:#1a1a2e;color:#fff;font-family:monospace;padding:2rem}.card{border:1px solid #333;padding:1rem;margin:1rem 0;border-radius:8px;background:#16213e;box-shadow:0 4px 6px rgba(0,0,0,0.3)}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:2rem}h2{color:#e94560}</style>"
        p2: String[1024] = "<h2>Mainnet DeFi Explorer</h2><p>Auto-refreshing via Vyper & HTMX.</p><div hx-get='dashboard?data=' hx-trigger='load, every 2s'>Loading live mainnet state...</div>"
        return concat(p1, p2)

    if path == "dashboard":
        # Chainlink ETH/USD
        c_a: uint80 = 0
        price_int: int256 = 0
        c_c: uint256 = 0
        c_d: uint256 = 0
        c_e: uint80 = 0
        c_a, price_int, c_c, c_d, c_e = staticcall IChainlink(0x5f4eC3Df9cbd43714FE2740f5E3616155c5b8419).latestRoundData()
        price: uint256 = convert(price_int, uint256) // 100000000

        # Uniswap V2 ETH/USDC
        r0: uint112 = 0
        r1: uint112 = 0
        ts: uint32 = 0
        r0, r1, ts = staticcall IUniswapV2Pair(0xB4e16d0168e52d35CaCD2c6185b44281Ec28C9Dc).getReserves()
        weth_reserve: uint256 = convert(r1, uint256) // (10**18)
        usdc_reserve: uint256 = convert(r0, uint256) // (10**6)
        uni_price: uint256 = usdc_reserve // weth_reserve
        
        # Aave V3 USDC
        a1: uint256 = 0
        a2: uint256 = 0
        totalAToken: uint256 = 0
        a4: uint256 = 0
        totalVariableDebt: uint256 = 0
        a6: uint256 = 0
        a7: uint256 = 0
        a8: uint256 = 0
        a9: uint256 = 0
        a10: uint256 = 0
        a11: uint256 = 0
        a12: uint40 = 0
        a1, a2, totalAToken, a4, totalVariableDebt, a6, a7, a8, a9, a10, a11, a12 = staticcall IAaveV3DataProvider(0x7B4EB56E7CD4b454BA8ff71E4518426369a138a3).getReserveData(0xA0b86991c6218b36c1d19D4a2e9Eb0cE3606eB48)
        supplied_usdc: uint256 = totalAToken // (10**6)
        borrowed_usdc: uint256 = totalVariableDebt // (10**6)
        
        b_info: String[512] = concat(
            "<div class='card'><h3>Block</h3>",
            "<p>Number: ", uint2str(block.number), "</p>",
            "<p>Timestamp: ", uint2str(block.timestamp), "</p>",
            "<p>Base Fee: ", uint2str(block.basefee), " wei</p></div>"
        )
        
        c_info: String[512] = concat(
            "<div class='card'><h3>Chainlink Oracle</h3>",
            "<p>Pair: ETH/USD</p>",
            "<p style='font-size:1.5rem;color:#0f0'>$", uint2str(price), "</p></div>"
        )
        
        u_info: String[512] = concat(
            "<div class='card'><h3>Uniswap V2</h3>",
            "<p>Pair: WETH / USDC</p>",
            "<p>WETH Pool: ", uint2str(weth_reserve), "</p>",
            "<p>USDC Pool: $", uint2str(usdc_reserve), "</p>",
            "<p style='font-size:1.5rem;color:#0f0'>Spot Price: $", uint2str(uni_price), "</p></div>"
        )
        
        a_info: String[512] = concat(
            "<div class='card'><h3>Aave V3</h3>",
            "<p>Asset: USDC</p>",
            "<p>Total Supplied: $", uint2str(supplied_usdc), "</p>",
            "<p>Total Borrowed: $", uint2str(borrowed_usdc), "</p></div>"
        )
        
        return concat("<div class='grid'>", b_info, c_info, u_info, a_info, "</div>")

    return "<main>Not found</main>"
