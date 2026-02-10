use thiserror::Error;

#[derive(Error, Debug)]
pub enum StandXError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::StandXHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::StandXWebSocketError),
}
