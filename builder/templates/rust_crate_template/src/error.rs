use thiserror::Error;

#[derive(Error, Debug)]
pub enum {{EXCHANGE_NAME}}Error {
    #[error("HTTP error: {0}")]
    Http(#[from] crate::http::error::{{EXCHANGE_NAME}}HttpError),
    #[error("WebSocket error: {0}")]
    WebSocket(#[from] crate::websocket::error::{{EXCHANGE_NAME}}WebSocketError),
}
