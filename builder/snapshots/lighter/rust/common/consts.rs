//! NautilusTrader Adapter - Lighter Common Constants

/// The exchange identifier for Lighter.
pub const EXCHANGE_NAME: &str = "LIGHTER";

/// The default API version.
pub const API_VERSION: &str = "v1";

/// The default WebSocket heartbeat interval in seconds.
pub const WS_HEARTBEAT_INTERVAL_SEC: u64 = 30;

/// HTTP Header keys
pub const HEADER_CHAIN_ID: &str = "x-lighter-chain-id";
pub const HEADER_API_KEY: &str = "x-api-key";
pub const HEADER_TIMESTAMP: &str = "x-timestamp";
pub const HEADER_SIGNATURE: &str = "x-signature";

/// Rate Limits (120 requests per minute)
pub const RATE_LIMIT_LIMIT: u32 = 120;
pub const RATE_LIMIT_PERIOD_MS: u64 = 60_000;