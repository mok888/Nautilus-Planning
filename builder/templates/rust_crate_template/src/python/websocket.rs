use pyo3::prelude::*;

#[pyclass]
pub class PyWebSocketClient {
    #[new]
    fn new() -> Self {
        PyWebSocketClient {}
    }
}
