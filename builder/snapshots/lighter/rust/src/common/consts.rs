pub const VENUE_NAME: &str = "LIGHTER";

/// REST API version prefix
pub const API_VERSION: &str = "v1";

/// WebSocket heartbeat interval in seconds
pub const WS_HEARTBEAT_INTERVAL_SECS: u64 = 30;

/// Maximum WebSocket message size (10 MB)
pub const WS_MAX_MESSAGE_SIZE: usize = 10 * 1024 * 1024;

/// Default HTTP request timeout in seconds
pub const DEFAULT_HTTP_TIMEOUT_SECS: u64 = 10;

/// Maximum number of HTTP request retries
pub const MAX_RETRIES: u32 = 3;

/// Delay between retries in seconds
pub const RETRY_DELAY_SECS: f64 = 1.0;
