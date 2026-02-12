/// WebSocket replay utility for testing StandX message handling.
///
/// Reads recorded WebSocket messages from a file and replays them
/// through the handler for deterministic testing.
pub struct StandXWsReplay {
    pub messages: Vec<String>,
}

impl StandXWsReplay {
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

impl Default for StandXWsReplay {
    fn default() -> Self {
        Self::new()
    }
}
