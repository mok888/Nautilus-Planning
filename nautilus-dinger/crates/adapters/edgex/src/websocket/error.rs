use thiserror::Error;

#[derive(Error, Debug)]
pub enum edgexWebSocketError {
    #[error("Connection failed")]
    ConnectionFailed,
}
