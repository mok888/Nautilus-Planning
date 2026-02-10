use thiserror::Error;

#[derive(Error, Debug)]
pub enum edgexHttpError {
    #[error("Request failed: {0}")]
    RequestFailed(String),
}
