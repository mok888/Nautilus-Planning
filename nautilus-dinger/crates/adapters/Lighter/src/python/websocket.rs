use pyo3::prelude::*;

#[pyclass]
pub struct PyWebSocketClient {}

#[pymethods]
impl PyWebSocketClient {
    #[new]
    fn new() -> Self {
        PyWebSocketClient {}
    }
}
