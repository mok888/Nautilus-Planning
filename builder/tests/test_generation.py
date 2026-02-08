from unittest.mock import patch
import json
from builder.pipeline.generate import generate_python_layer, generate_rust_core
from builder.models import ExchangeSpec, Endpoint

@patch("builder.pipeline.generate.ask_llm")
def test_generate_python_layer(mock_ask_llm):
    # Setup mock return value
    mock_response = {
        "python_files": {
            "data.py": "class TestExchangeDataClient(LiveMarketDataClient): pass"
        }
    }
    mock_ask_llm.return_value = json.dumps(mock_response)
    
    spec = ExchangeSpec(
        name="TestExchange",
        rest_base="https://api.test.com",
        ws_base="wss://ws.test.com",
        auth="API Key",
        endpoints=[
            Endpoint(path="/order", method="POST", purpose="Place order")
        ]
    )
    
    # Test Python Generation
    files = generate_python_layer(spec)
    
    assert mock_ask_llm.called
    assert "data.py" in files
    assert "TestExchange" in files["data.py"]
    
    # Verify prompt contains spec
    args, _ = mock_ask_llm.call_args
    prompt = args[0]
    assert "TestExchange" in prompt
    assert "NautilusTrader" in prompt or "adapter" in prompt

@patch("builder.pipeline.generate.ask_llm")
def test_generate_rust_core(mock_ask_llm):
    mock_response = {
        "rust_files": {
            "src/lib.rs": "pub struct TestExchange;"
        }
    }
    mock_ask_llm.return_value = json.dumps(mock_response)
    
    spec = ExchangeSpec(
        name="TestExchange",
        rest_base="https://api.test.com",
        ws_base="wss://ws.test.com",
        auth="API Key",
        endpoints=[]
    )
    
    files = generate_rust_core(spec, "## Markdown Research")
    
    assert "src/lib.rs" in files
    assert "TestExchange" in files["src/lib.rs"]
