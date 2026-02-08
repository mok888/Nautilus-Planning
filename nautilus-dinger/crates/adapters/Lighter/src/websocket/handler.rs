pub struct LighterWebSocketHandler {}

impl LighterWebSocketHandler {
    pub fn handle_message(&self, msg: String) {
        println!("Received: {}", msg);
    }
}
