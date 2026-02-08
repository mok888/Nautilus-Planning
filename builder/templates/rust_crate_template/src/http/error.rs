use thiserror::Error;

#[derive(Error, Debug)]
pub enum {{EXCHANGE_NAME}}HttpError {
    #[error("Request failed: {0}")]
    RequestFailed(String),
}
