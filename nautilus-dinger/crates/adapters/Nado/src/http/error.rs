use thiserror::Error;

#[derive(Error, Debug)]
pub enum NadoHttpError {
    #[error("Request failed: {0}")]
    RequestFailed(String),
}
