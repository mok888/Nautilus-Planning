use thiserror::Error;

#[derive(Error, Debug)]
pub enum {{EXCHANGE_NAME}}WebSocketError {
    #[error("Connection failed")]
    ConnectionFailed,
}
