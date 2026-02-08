use thiserror::Error;

pub type Result<T> = std::result::Result<T, LighterError>;

#[derive(Debug, Error)]
pub enum LighterError {
    #[error("Network error: {0}")]
    Network(#[from] hyper::Error),
    
    #[error("HTTP error: {0}")]
    Http(String),
    
    #[error("Serialization error: {0}")]
    Serialization(#[from] serde_json::Error),
    
    #[error("Signing error: {0}")]
    Signing(String),
    
    #[error("Rate limit exceeded")]
    RateLimitExceeded,
    
    #[error("Authentication failed")]
    Authentication,
    
    #[error("Invalid response from exchange: {0}")]
    InvalidResponse(String),
    
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] tokio_tungstenite::tungstenite::Error),
}