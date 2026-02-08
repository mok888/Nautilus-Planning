use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct LighterTradeMessage {
    pub price: f64,
    pub size: f64,
}
