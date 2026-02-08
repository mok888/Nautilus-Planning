use serde::Deserialize;

#[derive(Debug, Clone, Deserialize)]
pub struct RiskSnapshot {
    pub equity: f64,
    pub balance: f64,
    pub margin_used: f64,
    pub margin_available: f64,
    pub maintenance_margin: f64,
    pub initial_margin: f64,
    pub unrealized_pnl: f64,
    pub leverage: Option<f64>,
    pub margin_ratio: Option<f64>,
}
