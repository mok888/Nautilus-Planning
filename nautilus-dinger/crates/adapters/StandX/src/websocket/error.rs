use thiserror::Error;

#[derive(Error, Debug)]
pub enum StandXWebSocketError {
    #[error("Connection failed")]
    ConnectionFailed,
}
