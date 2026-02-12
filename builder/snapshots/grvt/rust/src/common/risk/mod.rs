pub mod models;

use serde::{Deserialize, Serialize};

/// Risk parameters for an Grvt market.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct GrvtRiskParams {
    /// Initial margin fraction
    pub imf: f64,
    /// Maintenance margin fraction
    pub mmf: f64,
    /// Clearing margin fraction
    pub cmf: f64,
}
