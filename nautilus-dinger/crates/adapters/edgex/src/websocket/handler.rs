pub struct edgexWebSocketHandler {}

impl edgexWebSocketHandler {
    pub fn handle_message(&self, msg: String) {
        println!("Received: {}", msg);
    }
}
