use thiserror::Error;

#[derive(Error, Debug)]
pub enum NadoWebSocketError {
    #[error("Connection failed")]
    ConnectionFailed,
}
