import json
from builder.pipeline.entropy import EntropyPolicy
from builder.pipeline.ast.validate_strict import validate_generated_files
from builder.infra.llm import ask_llm
from builder.pipeline.exceptions import CodegenFailure


def generate_with_retry(
    prompt: str,
    policy: EntropyPolicy,
) -> dict[str, str]:
    last_error = None

    for attempt in range(policy.max_retries):
        temperature = policy.temperature_for_attempt(attempt)

        # Using ask_llm instead of call_llm to match existing codebase interface
        raw = ask_llm(
            prompt=prompt,
            temperature=temperature,
            cache=True # Cache is handled internally but entropy changes key effectively
        )

        try:
            # Parse JSON (robustly)
            clean_resp = raw.replace("```json", "").replace("```", "").strip()
            try:
                payload = json.loads(clean_resp)
            except json.JSONDecodeError:
                start = raw.find("{")
                end = raw.rfind("}") + 1
                if start != -1 and end != -1:
                     payload = json.loads(raw[start:end])
                else:
                     raise

            files = {}
            if "python_files" in payload:
                files.update(payload["python_files"])
            if "rust_files" in payload:
                files.update(payload["rust_files"])
                
            validate_generated_files(files)
            return files

        except Exception as e:
            last_error = e
            # Log or print warning here if needed
            # print(f"Attempt {attempt} failed: {e}")

    raise CodegenFailure(
        f"Codegen failed after {policy.max_retries} attempts"
    ) from last_error
