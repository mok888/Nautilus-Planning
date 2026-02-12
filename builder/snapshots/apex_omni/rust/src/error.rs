use thiserror::Error;

#[derive(Error, Debug)]
pub enum ApexOmniError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::ApexOmniHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::ApexOmniWebSocketError),
}
