use serde::{Deserialize, Serialize};

/// Position risk model for Paradex margin calculations.
#[derive(Debug, Clone, Serialize, Deserialize)]
pub struct ParadexPositionRisk {
    pub market_id: u32,
    pub size: f64,
    pub entry_price: f64,
    pub mark_price: f64,
    pub unrealized_pnl: f64,
    pub margin_requirement: f64,
}
