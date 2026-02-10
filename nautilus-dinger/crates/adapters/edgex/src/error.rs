use thiserror::Error;

#[derive(Error, Debug)]
pub enum edgexError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::edgexHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::edgexWebSocketError),
}
