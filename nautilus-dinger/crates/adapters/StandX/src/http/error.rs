use thiserror::Error;

#[derive(Error, Debug)]
pub enum StandXHttpError {
    #[error("Request failed: {0}")]
    RequestFailed(String),
}
