/// WebSocket replay utility for testing Nado message handling.
///
/// Reads recorded WebSocket messages from a file and replays them
/// through the handler for deterministic testing.
pub struct NadoWsReplay {
    pub messages: Vec<String>,
}

impl NadoWsReplay {
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

impl Default for NadoWsReplay {
    fn default() -> Self {
        Self::new()
    }
}
