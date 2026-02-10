use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct StandXTradeMessage {
    pub price: f64,
    pub size: f64,
}
