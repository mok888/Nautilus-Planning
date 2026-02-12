/// WebSocket replay utility for testing Lighter message handling.
///
/// Reads recorded WebSocket messages from a file and replays them
/// through the handler for deterministic testing.
pub struct LighterWsReplay {
    pub messages: Vec<String>,
}

impl LighterWsReplay {
    pub fn new() -> Self {
        Self {
            messages: Vec::new(),
        }
    }

    pub fn add_message(&mut self, msg: String) {
        self.messages.push(msg);
    }

    pub fn message_count(&self) -> usize {
        self.messages.len()
    }
}

impl Default for LighterWsReplay {
    fn default() -> Self {
        Self::new()
    }
}
