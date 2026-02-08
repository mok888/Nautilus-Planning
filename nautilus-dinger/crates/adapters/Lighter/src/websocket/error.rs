use thiserror::Error;

#[derive(Error, Debug)]
pub enum LighterWebSocketError {
    #[error("Connection failed")]
    ConnectionFailed,
}
