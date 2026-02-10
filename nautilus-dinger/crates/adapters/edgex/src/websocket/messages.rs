use serde::Deserialize;

#[derive(Debug, Deserialize)]
pub struct edgexTradeMessage {
    pub price: f64,
    pub size: f64,
}
