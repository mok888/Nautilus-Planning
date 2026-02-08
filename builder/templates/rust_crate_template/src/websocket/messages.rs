use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct {{EXCHANGE_NAME}}TradeMessage {
    pub price: f64,
    pub size: f64,
}
