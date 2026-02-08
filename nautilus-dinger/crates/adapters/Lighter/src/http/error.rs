use thiserror::Error;

#[derive(Error, Debug)]
pub enum LighterHttpError {
    #[error("Request failed: {0}")]
    RequestFailed(#[from] reqwest::Error),
}
