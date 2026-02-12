use thiserror::Error;

#[derive(Error, Debug)]
pub enum EdgexError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::EdgexHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::EdgexWebSocketError),
}
