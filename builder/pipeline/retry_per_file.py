import json
from builder.pipeline.entropy_state import FileEntropyState
from builder.pipeline.ast.validate_with_report import validate_files_with_report
from builder.infra.llm import ask_llm # Using established utility
from builder.pipeline.exceptions import CodegenFailure


def regenerate_failed_files(
    initial_files: dict[str, str], # Starting point
    prompts: dict[str, str], # Prompt *per file*? Or a strategy to get one?
    max_rounds: int = 6,
) -> dict[str, str]:
    """
    Retry logic that selectively regenerates failed files.
    
    Args:
        initial_files: The initial set of generated files.
        prompts: A mapping of 'filename' -> 'prompt string' used to regenerate that specific file.
                 If we can't easily generate per-file prompts, this strategy requires adjustment.
    """
    entropy = FileEntropyState()
    files = initial_files.copy()
    
    # First validation pass
    ok, failed = validate_files_with_report(files)
    if ok:
        return files
        
    for path in failed:
        entropy.record_failure(path)

    for _ in range(max_rounds):
        # We only need to regenerate 'failed' files
        current_failed = failed
        
        # If no failures, we are done
        if not current_failed:
            return files

        for path in current_failed:
            prompt = prompts.get(path)
            if not prompt:
                # If we don't have a specific prompt, we might skip or fail.
                # Or warn and keep the broken file?
                # For now, assuming prompts provided.
                continue

            temp = entropy.temperature_for(path)
            
            # Call LLM for single file
            # We assume the prompt is engineered to return just the content or a JSON wrapper
            try:
                raw = ask_llm(prompt, temperature=temp, cache=True)
                
                # Adapting to likely output format. 
                # If the prompt asks for JSON { "content": ... }
                try:
                    clean_resp = raw.replace("```json", "").replace("```", "").strip()
                    payload = json.loads(clean_resp)
                    if isinstance(payload, str):
                        content = payload # Unexpected but possible
                    elif "content" in payload:
                        content = payload["content"]
                    elif "code" in payload:
                        content = payload["code"]
                    else:
                        # Fallback: maybe the whole response is the code? 
                        # Or it's the dict structure { filename: content }
                        content = payload.get(path, raw)
                except json.JSONDecodeError:
                    content = raw # Fallback to raw string

                files[path] = content
            except Exception:
                # LLM failure or parse failure, count as failure
                pass

        # Re-validate locally (only the ones we touched + others)
        # Actually validate ALL because interdependencies might exist? 
        # AST is per-file, so checking all is fine.
        ok, failed = validate_files_with_report(files)

        if ok:
            return files

        for path in failed:
            entropy.record_failure(path)
            # We don't pop() because we need the old file if we fail to regen?
            # User snippet used pop(), so effectively removing broken files if they stay broken.
            # "files.pop(path, None)" implies strictly discarding invalid.
            # But we want to retry. "if path in files: continue" in user loop implies 
            # they treat 'files' as the set of *valid* files?
            # User loop:
            # for path, prompt in prompt_by_file:
            #   if path in files: continue (Skip valid)
            #   ... generate ...
            #   files[path] = content
            # validate
            # for path in failed: pop()
            
            # This logic means 'files' only holds valid files between rounds.
            
            files.pop(path, None)

    raise CodegenFailure(
        f"Failed files after retries: {failed}"
    )
