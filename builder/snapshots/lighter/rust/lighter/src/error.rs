// Copyright (C) 2024 Nautilus Technologies, Inc.
// SPDX-License-Identifier: MIT

use thiserror::Error;

/// Represents errors that can occur within the Lighter adapter.
#[derive(Debug, Error)]
pub enum LighterAdapterError {
    #[error("Configuration error: {0}")]
    Config(String),

    #[error("HTTP client error: {0}")]
    HttpClient(String),

    #[error("WebSocket error: {0}")]
    WebSocket(String),

    #[error("Signing error: {0}")]
    Signing(String),

    #[error("Parsing error: {0}")]
    Parsing(String),

    #[error("Exchange error: {code} - {msg}")]
    Exchange { code: String, msg: String },

    #[error("Unsupported operation: {0}")]
    Unsupported(String),

    #[error(transparent)]
    Io(#[from] std::io::Error),

    #[error(transparent)]
    SerdeJson(#[from] serde_json::Error),
}

pub type Result<T> = std::result::Result<T, LighterAdapterError>;
