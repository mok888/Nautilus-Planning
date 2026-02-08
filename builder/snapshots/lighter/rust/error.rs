//! NautilusTrader Adapter - Lighter Error Types

use thiserror::Error;

pub type Result<T> = std::result::Result<T, LighterError>;

#[derive(Error, Debug)]
pub enum LighterError {
    #[error("HTTP request failed: {0}")]
    HttpError(#[from] hyper::Error),

    #[error("JSON serialization/deserialization error: {0}")]
    JsonError(#[from] serde_json::Error),

    #[error("IO error: {0}")]
    IoError(#[from] std::io::Error),

    #[error("Authentication failed: {0}")]
    AuthError(String),

    #[error("Rate limit exceeded")]
    RateLimitExceeded,

    #[error("Invalid configuration: {0}")]
    ConfigError(String),

    #[error("WebSocket error: {0}")]
    WsError(String),

    #[error("API Error (Code {code}): {message}")]
    ApiError { code: i32, message: String },
}