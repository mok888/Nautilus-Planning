pub mod models;

use serde::{Deserialize, Serialize};

/// Risk parameters for an Nado market.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct NadoRiskParams {
    /// Initial margin fraction
    pub imf: f64,
    /// Maintenance margin fraction
    pub mmf: f64,
    /// Clearing margin fraction
    pub cmf: f64,
}
