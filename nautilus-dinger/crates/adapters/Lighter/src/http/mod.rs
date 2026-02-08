pub mod client;
pub mod error;
pub mod models;

use crate::common::credential::LighterCredential;

pub struct LighterHttpClient {
    credential: Option<LighterCredential>,
}
