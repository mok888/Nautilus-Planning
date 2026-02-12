use thiserror::Error;

#[derive(Error, Debug)]
pub enum GrvtError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::GrvtHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::GrvtWebSocketError),
}
