# pragma version 0.5.0a2

counter: public(uint256)
last_block_updated: public(uint256)
message_count: public(uint256)
messages: public(HashMap[uint256, String[64]])

@external
def increment():
    self.counter += 1
    self.last_block_updated = block.number

@external
def add_message(text: String[64]):
    self.messages[self.message_count] = text
    self.message_count += 1

@external
@view
def render(path: String[64], caller: address, data: Bytes[4096]) -> String[4096]:
    if path == "home":
        p1: String[2048] = concat(
            "<script src='https://unpkg.com/htmx.org@2.0.4'></script>",
            "<main style='font-family: monospace; max-width: 800px; margin: 2rem auto; padding: 1rem; border: 1px solid #333; border-radius: 8px;'>",
            "<h2>Vyper HTMX - Dynamic State Explorer</h2>",
            "<div style='display: flex; gap: 2rem;'>"
        )
        p2: String[2048] = concat(
            "<div style='flex: 1;' hx-get='stats?data=' hx-trigger='load, every 2s'>Loading stats...</div>",
            "<div style='flex: 1;'><h3>Message Board</h3>",
            "<div hx-get='messages?data=' hx-trigger='load, every 2s'>Loading messages...</div>",
            "</div></div></main>"
        )
        return concat(p1, p2)

    if path == "stats":
        return concat(
            "<div style='padding: 1rem; background: #f9f9f9; border-radius: 4px;'>",
            "<h3>Network Stats</h3>",
            "<p><strong>Block Number:</strong> ", uint2str(block.number), "</p>",
            "<p><strong>Timestamp:</strong> ", uint2str(block.timestamp), "</p>",
            "<hr style='border: 0; border-top: 1px solid #ccc;' />",
            "<h3>Contract State</h3>",
            "<p><strong>Counter:</strong> ", uint2str(self.counter), "</p>",
            "<p><strong>Last Updated Block:</strong> ", uint2str(self.last_block_updated), "</p>",
            "</div>"
        )

    if path == "messages":
        count: uint256 = self.message_count
        html: String[256] = "<ul style='padding-left: 1rem;'>"
        
        start: uint256 = 0
        if count > 5:
            start = count - 5
            
        m0: String[128] = ""
        m1: String[128] = ""
        m2: String[128] = ""
        m3: String[128] = ""
        m4: String[128] = ""
        
        if count > 0: m0 = concat("<li>", self.messages[start], "</li>")
        if count > 1: m1 = concat("<li>", self.messages[start + 1], "</li>")
        if count > 2: m2 = concat("<li>", self.messages[start + 2], "</li>")
        if count > 3: m3 = concat("<li>", self.messages[start + 3], "</li>")
        if count > 4: m4 = concat("<li>", self.messages[start + 4], "</li>")

        if count == 0:
            return concat(html, "<li><em>No messages yet.</em></li></ul>")
            
        return concat(html, m0, m1, m2, m3, m4, "</ul>")

    return "<main>Not found</main>"
