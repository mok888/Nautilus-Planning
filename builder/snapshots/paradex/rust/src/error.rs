use thiserror::Error;

#[derive(Error, Debug)]
pub enum ParadexError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::ParadexHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::ParadexWebSocketError),
}
