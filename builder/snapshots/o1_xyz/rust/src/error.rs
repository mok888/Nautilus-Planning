use thiserror::Error;

#[derive(Error, Debug)]
pub enum O1XyzError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::O1XyzHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::O1XyzWebSocketError),
}
