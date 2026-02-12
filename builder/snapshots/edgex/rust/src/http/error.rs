use thiserror::Error;

#[derive(Error, Debug)]
pub enum EdgexHttpError {
    #[error("Request failed: {0}")]
    RequestFailed(String),
    #[error("Deserialization error: {0}")]
    DeserializationError(String),
    #[error("Authentication error: {0}")]
    AuthenticationError(String),
    #[error("Rate limit exceeded")]
    RateLimitExceeded,
    #[error("Server error: status {status}, body: {body}")]
    ServerError { status: u16, body: String },
}
