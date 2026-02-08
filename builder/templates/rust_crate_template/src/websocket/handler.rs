pub struct {{EXCHANGE_NAME}}WebSocketHandler {}

impl {{EXCHANGE_NAME}}WebSocketHandler {
    pub fn handle_message(&self, msg: String) {
        println!("Received: {}", msg);
    }
}
