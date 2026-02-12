pub mod models;

use serde::{Deserialize, Serialize};

/// Risk parameters for an Lighter market.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct LighterRiskParams {
    /// Initial margin fraction
    pub imf: f64,
    /// Maintenance margin fraction
    pub mmf: f64,
    /// Clearing margin fraction
    pub cmf: f64,
}
