// Copyright (C) 2024 Nautilus Technologies, Inc.
// SPDX-License-Identifier: MIT

// Re-export the main components for Python bindings

use crate::config::LighterConfig;
use pyo3::prelude::*;

#[pymodule]
fn lighter(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<LighterConfig>()?;
    Ok(())
}
