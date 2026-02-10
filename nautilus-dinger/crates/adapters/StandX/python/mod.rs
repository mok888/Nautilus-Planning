use pyo3::prelude::*;
use crate::config::StandXConfig;
use crate::http::client::HttpClient;

#[pymodule]
fn standx_adapter(_py: Python, m: &PyModule) -> PyResult<()> {
    m.add_class::<StandXConfig>()?;
    m.add_class::<PyStandXClient>()?;
    Ok(())
}

#[pyclass]
pub struct PyStandXClient {
    client: HttpClient,
}

#[pymethods]
impl PyStandXClient {
    #[new]
    pub fn new(config: StandXConfig) -> PyResult<Self> {
        // Initialize blocking runtime or use the one from nautilus_common
        let client = HttpClient::new(config)
            .map_err(|e| PyErr::new::<pyo3::exceptions::PyRuntimeError, _>(e.to_string()))?;
        Ok(Self { client })
    }

    // Example exposed method
    pub fn ping(&self, py: Python) -> PyResult<String> {
        // In a real adapter, use nautilus_common::live::get_runtime().block_on
        // For this module, we simulate blocking or return a placeholder
        // Accessing self.client would require block_on inside PyO3 if methods are async
        Ok("pong".to_string())
    }
}
