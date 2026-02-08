use thiserror::Error;

#[derive(Error, Debug)]
pub enum {{EXCHANGE_NAME}}Error {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::HttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::WebSocketError),
}
