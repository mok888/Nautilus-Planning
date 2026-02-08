use thiserror::Error;

#[derive(Error, Debug)]
pub enum LighterAdapterError {
    #[error("HTTP request failed: {0}")]
    HttpError(#[from] hyper::Error),
    #[error("JSON serialization/deserialization error: {0}")]
    JsonError(#[from] serde_json::Error),
    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),
    #[error("Invalid API Key or Secret")]
    InvalidCredentials,
    #[error("Authentication failed: {0}")]
    AuthError(String),
    #[error("Rate limit exceeded")]
    RateLimitExceeded,
    #[error("Exchange returned error: {code} - {msg}")]
    ExchangeError { code: i32, msg: String },
    #[error("WebSocket connection closed: {0}")]
    WebSocketClosed(String),
    #[error("Timestamp format error")]
    TimestampError,
    #[error("Invalid signature")]
    InvalidSignature,
    #[error("UTF-8 conversion error")]
    Utf8Error(#[from] std::string::FromUtf8Error),
}

pub type Result<T> = std::result::Result<T, LighterAdapterError>;