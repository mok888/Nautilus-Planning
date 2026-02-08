use serde::{Deserialize, Serialize};

#[derive(Debug, Serialize, Deserialize)]
pub struct PlaceOrderRequest {
    pub symbol: String,
    pub quantity: f64,
}
