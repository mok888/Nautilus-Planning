use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct NadoTradeMessage {
    pub price: f64,
    pub size: f64,
}
