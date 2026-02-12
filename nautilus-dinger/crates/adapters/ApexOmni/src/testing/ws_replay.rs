/// WebSocket replay utility for testing ApexOmni message handling.
///
/// Reads recorded WebSocket messages from a file and replays them
/// through the handler for deterministic testing.
pub struct ApexOmniWsReplay {
    pub messages: Vec<String>,
}

impl ApexOmniWsReplay {
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

impl Default for ApexOmniWsReplay {
    fn default() -> Self {
        Self::new()
    }
}
