use thiserror::Error;

#[derive(Error, Debug)]
pub enum LighterWebSocketError {
    #[error("Connection failed: {0}")]
    ConnectionFailed(String),
    #[error("Message parse error: {0}")]
    ParseError(String),
    #[error("Authentication failed: {0}")]
    AuthenticationFailed(String),
    #[error("Subscription error: channel={channel}, reason={reason}")]
    SubscriptionError { channel: String, reason: String },
    #[error("Connection closed unexpectedly")]
    ConnectionClosed,
}
