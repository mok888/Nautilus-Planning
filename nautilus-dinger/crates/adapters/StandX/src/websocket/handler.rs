pub struct StandXWebSocketHandler {}

impl StandXWebSocketHandler {
    pub fn handle_message(&self, msg: String) {
        println!("Received: {}", msg);
    }
}
