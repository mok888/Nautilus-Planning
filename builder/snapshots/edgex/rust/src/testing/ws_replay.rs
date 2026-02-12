/// WebSocket replay utility for testing Edgex message handling.
///
/// Reads recorded WebSocket messages from a file and replays them
/// through the handler for deterministic testing.
pub struct EdgexWsReplay {
    pub messages: Vec<String>,
}

impl EdgexWsReplay {
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

impl Default for EdgexWsReplay {
    fn default() -> Self {
        Self::new()
    }
}
