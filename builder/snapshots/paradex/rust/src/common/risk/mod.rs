pub mod models;

use serde::{Deserialize, Serialize};

/// Risk parameters for an Paradex market.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexRiskParams {
    /// Initial margin fraction
    pub imf: f64,
    /// Maintenance margin fraction
    pub mmf: f64,
    /// Clearing margin fraction
    pub cmf: f64,
}
