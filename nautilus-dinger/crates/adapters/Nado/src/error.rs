use thiserror::Error;

#[derive(Error, Debug)]
pub enum NadoError {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::NadoHttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::NadoWebSocketError),
}
