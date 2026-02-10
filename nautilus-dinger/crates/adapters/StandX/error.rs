use thiserror::Error;

#[derive(Error, Debug)]
pub enum StandXError {
    #[error("HTTP error: {0}")]
    HttpError(String),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("JSON serialization/deserialization error: {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("Signature error: {0}")]
    SignatureError(String),

    #[error("Invalid response status: {0}")]
    InvalidStatus(u16),

    #[error("Authentication missing: {0}")]
    AuthError(String),

    #[error("WebSocket error: {0}")]
    WsError(String),
}
