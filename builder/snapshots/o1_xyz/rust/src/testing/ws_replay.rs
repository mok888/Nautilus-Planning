/// WebSocket replay utility for testing O1Xyz message handling.
///
/// Reads recorded WebSocket messages from a file and replays them
/// through the handler for deterministic testing.
pub struct O1XyzWsReplay {
    pub messages: Vec<String>,
}

impl O1XyzWsReplay {
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

impl Default for O1XyzWsReplay {
    fn default() -> Self {
        Self::new()
    }
}
