use thiserror::Error;

#[derive(Error, Debug)]
pub enum LighterError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::LighterHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::LighterWebSocketError),
}
