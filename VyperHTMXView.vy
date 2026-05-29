# pragma version 0.5.0a2

interface IVyperHTMXView:
    def render(path: String[INF], caller: address, data: Bytes[INF]) -> String[INF]: view
