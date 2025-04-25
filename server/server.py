# server.py

# --- Imports ---
from fastapi import FastAPI, HTTPException, Body, Response, status, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
import uvicorn
import copy
import re
import os
import tempfile
import subprocess # Keep standard subprocess
import sys
import shutil
import traceback
import asyncio
import uuid
import json
# Import WebSocketState for cleanup check
from starlette.websockets import WebSocketState


# --- Event Loop Policy for Windows ---
# Must be set BEFORE the event loop is created
if sys.platform == "win32":
    print("Detected Windows platform. Setting asyncio event loop policy to SelectorEventLoop.")
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    except Exception as policy_e:
        print(f"Warning: Could not set WindowsSelectorEventLoopPolicy - {policy_e}")
# --- End Event Loop Policy ---


# Import your existing compiler components
# Ensure these imports are correct relative to server.py's location
try:
    from lexer import Lexer, LexerError
    from parser import parse, ParserError
    from semantic import SemanticAnalyzer, SemanticError
    import definitions
    from transpiler import transpile_from_tokens, TranspilerError
    print("Successfully imported compiler components.")
except ImportError as e:
    print(f"ERROR: Failed to import compiler components: {e}")
    print("Please ensure lexer.py, parser.py, semantic.py, definitions.py, and transpiler.py are accessible.")
    sys.exit(1)


app = FastAPI(title="Conso Language Server")
print("FastAPI app created.")

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)
print("CORS middleware added.")

# --- Process Storage ---
run_sessions: Dict[str, str] = {}
print("Run sessions dictionary initialized.")

# --- Request/Response Models ---
class CodeRequest(BaseModel): code: str
class TokenResponse(BaseModel): value: str; type: str; line: int; column: int
class LexerResponse(BaseModel): tokens: List[TokenResponse]; success: bool; errors: List[str]
class ParserResponse(BaseModel): success: bool; errors: List[str]; syntaxValid: bool
class SemanticResponse(BaseModel): success: bool; errors: List[str]
class PrepareRunResponse(BaseModel):
    success: bool
    runId: Optional[str] = None
    websocketUrl: Optional[str] = None
    phase: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    transpiledCode: Optional[str] = None

print("Pydantic models defined.")

# --- Helper Functions ---
def normalize_code(code: str) -> str:
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    lines = code.split('\n')
    normalized_lines = [line.rstrip() for line in lines]
    normalized_code = '\n'.join(normalized_lines)
    return normalized_code

def compile_c_code(c_code: str, run_id: str) -> Tuple[bool, Optional[str], str]:
    print(f"[compile_c_code] Starting compilation for run_id: {run_id}")
    temp_dir = None; executable_path = None
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"conso_run_{run_id}_")
        c_file = os.path.join(temp_dir, "program.c")
        executable_path = os.path.join(temp_dir, "program.exe" if sys.platform == 'win32' else "program")
        with open(c_file, 'w', encoding='utf-8') as f: f.write(c_code)
        compile_cmd = ['gcc', c_file, '-o', executable_path, '-lm']
        print(f"[compile_c_code] Running command: {' '.join(compile_cmd)}")
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace')
        print(f"[compile_c_code] GCC Return Code: {compile_result.returncode}")
        if compile_result.stdout: print(f"[compile_c_code] GCC stdout:\n{compile_result.stdout}")
        if compile_result.stderr: print(f"[compile_c_code] GCC stderr:\n{compile_result.stderr}")
        if compile_result.returncode != 0:
            error_details = compile_result.stderr.replace(f'{c_file}:', f'Line ')
            if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
            return False, None, f"Compilation Error:\n{error_details}"
        print(f"[compile_c_code] Compilation successful. Executable: {executable_path}")
        return True, executable_path, ""
    except subprocess.TimeoutExpired:
        if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return False, None, "Compilation Timed Out (15s limit)."
    except FileNotFoundError:
        if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return False, None, "Compilation Error: 'gcc' command not found. Ensure GCC is installed and in PATH."
    except Exception as e:
        print(f"[compile_c_code] Unexpected error: {e}\n{traceback.format_exc()}")
        if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return False, None, f"Unexpected Server Error during C compilation: {str(e)}"


# --- API Endpoints ---
@app.post("/api/lexer", response_model=LexerResponse)
async def lexical_analysis(request: CodeRequest):
    print("[/api/lexer] Request received.")
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip(): return LexerResponse(tokens=[], success=True, errors=[])
        lexer = Lexer(input_code)
        tokens_data, errors = lexer.make_tokens()
        token_responses = [TokenResponse(value=tok.value if tok.value is not None else "", type=tok.type, line=tok.line, column=tok.column) for tok in tokens_data]
        return LexerResponse(tokens=token_responses, success=not errors, errors=[str(err) for err in errors])
    except Exception as e: print(f"[/api/lexer] Error: {str(e)}"); return LexerResponse(tokens=[], success=False, errors=[f"Internal Server Error: {str(e)}"])

@app.post("/api/parser", response_model=ParserResponse)
async def syntax_analysis(request: CodeRequest):
    print("[/api/parser] Request received.")
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip(): return ParserResponse(success=True, errors=[], syntaxValid=True)
        lexer = Lexer(input_code)
        tokens_data, lexer_errors = lexer.make_tokens()
        if lexer_errors: return ParserResponse(success=False, errors=[f"Lexical Error: {str(err)}" for err in lexer_errors], syntaxValid=False)
        definitions.token.clear()
        for tok in tokens_data: definitions.token.append((tok.type, tok.line, tok.column))
        result, error_messages, syntax_valid = parse()
        return ParserResponse(success=syntax_valid, errors=error_messages or [], syntaxValid=syntax_valid)
    except Exception as e: print(f"[/api/parser] Error: {str(e)}\n{traceback.format_exc()}"); return ParserResponse(success=False, errors=[f"Internal Server Error: {str(e)}"], syntaxValid=False)

@app.post("/api/semantic", response_model=SemanticResponse)
async def semantic_analysis_endpoint(request: CodeRequest):
    print("[/api/semantic] Request received.")
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip(): return SemanticResponse(success=True, errors=[])
        lexer = Lexer(input_code)
        tokens_data, lexer_errors = lexer.make_tokens()
        if lexer_errors: return SemanticResponse(success=False, errors=[f"Lexical Error: {str(err)}" for err in lexer_errors])
        semantic_tokens = [(tok.type, tok.value, tok.line, tok.column) for tok in tokens_data]
        analyzer = SemanticAnalyzer()
        success, errors = analyzer.analyze(semantic_tokens)
        return SemanticResponse(success=success, errors=errors)
    except Exception as e: print(f"[/api/semantic] Error: {str(e)}\n{traceback.format_exc()}"); return SemanticResponse(success=False, errors=[f"Internal Server Error: {str(e)}"])


# --- Prepare Run Endpoint ---
@app.post("/api/run/prepare", response_model=PrepareRunResponse)
async def prepare_interactive_run(request: CodeRequest, response: Response):
    print("[/api/run/prepare] Request received.")
    input_code = normalize_code(request.code)
    if not input_code.strip():
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PrepareRunResponse(success=False, phase="validation", errors=["No code provided."])

    # 1. Lexical Analysis
    print("[/api/run/prepare] Starting Lexical Analysis...")
    lexer = Lexer(input_code)
    tokens_data, lexer_errors = lexer.make_tokens()
    if lexer_errors:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PrepareRunResponse(success=False, phase="lexical", errors=[str(err) for err in lexer_errors])
    print("[/api/run/prepare] Lexical Analysis OK.")

    # Prepare tokens
    definitions.token.clear()
    detailed_tokens = []
    for tok in tokens_data:
        definitions.token.append((tok.type, tok.line, tok.column))
        detailed_tokens.append((tok.type, tok.value, tok.line, tok.column))

    # 2. Syntax Analysis
    print("[/api/run/prepare] Starting Syntax Analysis...")
    try:
        _, parser_errors, syntax_valid = parse()
        if not syntax_valid:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return PrepareRunResponse(success=False, phase="syntax", errors=parser_errors or ["Syntax error detected."])
        print("[/api/run/prepare] Syntax Analysis OK.")
    except Exception as e:
        print(f"[/api/run/prepare] Parser Internal Error: {str(e)}\n{traceback.format_exc()}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return PrepareRunResponse(success=False, phase="syntax", errors=[f"Parser Internal Error: {str(e)}"])

    # 3. Semantic Analysis
    print("[/api/run/prepare] Starting Semantic Analysis...")
    symbol_table_for_transpiler = None
    analyzer = None
    try:
        analyzer = SemanticAnalyzer()
        semantic_valid, semantic_errors = analyzer.analyze(detailed_tokens)
        if not semantic_valid:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return PrepareRunResponse(success=False, phase="semantic", errors=semantic_errors)
        mn_scope_table = analyzer.function_scopes.get("mn")
        if mn_scope_table is None:
            print("[/api/run/prepare] Warning: 'mn' scope not found, using global.")
            mn_scope_table = analyzer.global_scope
            if mn_scope_table is None:
                 response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                 return PrepareRunResponse(success=False, phase="semantic", errors=["Cannot find valid symbol table scope."])
        symbol_table_for_transpiler = mn_scope_table
        print("[/api/run/prepare] Semantic Analysis OK.")
    except Exception as e:
        print(f"[/api/run/prepare] Semantic Analysis Internal Error: {str(e)}\n{traceback.format_exc()}")
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        return PrepareRunResponse(success=False, phase="semantic", errors=[f"Semantic Analyzer Internal Error: {str(e)}"])

    # 4. Transpilation
    print("[/api/run/prepare] Starting Transpilation...")
    transpiled_code = ""
    try:
        transpiled_code = transpile_from_tokens(detailed_tokens, symbol_table_for_transpiler)
        print("--- Transpiled C Code ---")
        print(transpiled_code)
        print("--- End Transpiled C Code ---")
        if transpiled_code.startswith("// TRANSPILER ERROR") or transpiled_code.startswith("// UNEXPECTED"):
             response.status_code = status.HTTP_400_BAD_REQUEST
             error_msg = transpiled_code.split(":", 1)[-1].strip() if ":" in transpiled_code else transpiled_code
             return PrepareRunResponse(success=False, phase="transpilation", errors=[error_msg])
        print("[/api/run/prepare] Transpilation OK.")
    except Exception as e:
         print(f"[/api/run/prepare] Transpiler Internal Error: {str(e)}\n{traceback.format_exc()}")
         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
         return PrepareRunResponse(success=False, phase="transpilation", errors=[f"Transpiler Internal Error: {str(e)}"])

    # 5. Compile C code
    print("[/api/run/prepare] Starting C Compilation...")
    run_id = str(uuid.uuid4())
    compile_success, executable_path, compile_error = compile_c_code(transpiled_code, run_id)

    if not compile_success:
        print(f"[/api/run/prepare] Compilation Failed. Error: {compile_error}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        print(f"!!! Compilation Error Logged: {compile_error}")
        return PrepareRunResponse(success=False, phase="compilation", errors=[compile_error])
    print("[/api/run/prepare] C Compilation OK.")

    # Store executable path and return connection details
    run_sessions[run_id] = executable_path
    ws_host = "localhost"
    ws_port = 5000 # Assuming FastAPI runs on 5000
    ws_protocol = "ws"
    ws_url = f"{ws_protocol}://{ws_host}:{ws_port}/ws/run/{run_id}"
    print(f"[/api/run/prepare] Run prepared. ID: {run_id}, Executable: {executable_path}, WS URL: {ws_url}")

    return PrepareRunResponse(
        success=True,
        runId=run_id,
        websocketUrl=ws_url,
        transpiledCode=transpiled_code
    )


# --- WebSocket Endpoint for Interactive Run ---
@app.websocket("/ws/run/{run_id}")
async def websocket_run_endpoint(websocket: WebSocket, run_id: str):
    await websocket.accept()
    print(f"[/ws/run/{run_id}] WebSocket connection accepted.")

    executable_path = run_sessions.get(run_id)
    if not executable_path or not os.path.exists(executable_path):
        print(f"[/ws/run/{run_id}] Error: Executable not found.")
        await websocket.send_json({"type": "error", "message": "Executable not found or run session expired."})
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    process = None
    loop = asyncio.get_running_loop() # Get the current loop

    try:
        print(f"[/ws/run/{run_id}] Starting process using Popen in thread: {executable_path}")

        # Use asyncio.to_thread to run Popen
        process = await asyncio.to_thread(
            subprocess.Popen,
            [executable_path],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=0, # Unbuffered
        )

        print(f"[/ws/run/{run_id}] Started C process (PID: {process.pid})")

        # Tasks for handling I/O
        async def forward_stream(stream, stream_name, ws):
            print(f"[/ws/run/{run_id}] {stream_name} forwarder started.")
            try:
                while True:
                    line = await loop.run_in_executor(None, stream.readline)
                    if not line: break
                    try:
                        decoded_data = line.decode('utf-8', errors='replace')
                        await ws.send_json({"type": stream_name, "data": decoded_data})
                    except (WebSocketDisconnect, ConnectionResetError): print(f"[/ws/run/{run_id}] WebSocket disconnected ({stream_name})."); break
                    except Exception as send_e: print(f"[/ws/run/{run_id}] Error sending {stream_name}: {send_e}"); break
            except Exception as read_e: print(f"[/ws/run/{run_id}] Error reading {stream_name}: {read_e}")
            finally: print(f"[/ws/run/{run_id}] {stream_name} forwarder finished.")

        async def receive_stdin(ws):
            print(f"[/ws/run/{run_id}] stdin receiver started.")
            try:
                while True:
                    ws_data_raw = await ws.receive_text()
                    ws_data = json.loads(ws_data_raw)
                    if ws_data.get("type") == "stdin" and process.stdin:
                        input_data = ws_data.get("data", "")
                        try:
                            process.stdin.write(input_data.encode('utf-8'))
                            process.stdin.flush()
                        except (BrokenPipeError, ValueError, OSError) as write_e: print(f"[/ws/run/{run_id}] Error writing to process stdin (Process likely exited): {write_e}"); break
            except WebSocketDisconnect: print(f"[/ws/run/{run_id}] WebSocket disconnected by client.")
            except json.JSONDecodeError: print(f"[/ws/run/{run_id}] Invalid JSON received.")
            except Exception as e: print(f"[/ws/run/{run_id}] Error receiving stdin: {e}")
            finally: print(f"[/ws/run/{run_id}] stdin receiver finished.")

        # Run I/O tasks concurrently
        stdout_task = asyncio.create_task(forward_stream(process.stdout, "stdout", websocket))
        stderr_task = asyncio.create_task(forward_stream(process.stderr, "stderr", websocket))
        stdin_task = asyncio.create_task(receive_stdin(websocket))

        # --- FIX: Create Task for process.wait() ---
        process_wait_task = asyncio.create_task(asyncio.to_thread(process.wait), name=f"process_wait_{run_id}")
        # --- End Fix ---

        # Wait for process completion or I/O task failure
        all_tasks = {stdout_task, stderr_task, stdin_task, process_wait_task}
        done, pending = await asyncio.wait(
            all_tasks,
            return_when=asyncio.FIRST_COMPLETED
        )

        # Check which task completed first
        exit_code = None
        if process_wait_task in done:
            exit_code = process_wait_task.result() # Get exit code if process finished
            print(f"[/ws/run/{run_id}] Process exited first with code {exit_code}.")
        else:
            print(f"[/ws/run/{run_id}] I/O task finished first. Waiting for process exit status...")
            exit_code = process.poll() # Check current status without waiting

        # Wait briefly for final I/O
        await asyncio.sleep(0.2)

        # Cancel remaining tasks
        for task in pending: task.cancel()
        await asyncio.gather(*pending, return_exceptions=True)
        print(f"[/ws/run/{run_id}] I/O tasks finished/cancelled.")

        # Get the final exit code
        final_exit_code = process.returncode if process else exit_code # Use process.returncode if available

        # Send exit code to client
        if final_exit_code is not None:
             print(f"[/ws/run/{run_id}] Sending exit code {final_exit_code} to client.")
             try: await websocket.send_json({"type": "exit", "exit_code": final_exit_code})
             except (WebSocketDisconnect, ConnectionResetError): print(f"[/ws/run/{run_id}] WebSocket already closed when sending exit code.")
        else:
             print(f"[/ws/run/{run_id}] Process exit code unknown, not sending exit message.")


    except WebSocketDisconnect: print(f"[/ws/run/{run_id}] WebSocket disconnected unexpectedly.")
    except Exception as e: print(f"[/ws/run/{run_id}] Error in WebSocket handler: {e}\n{traceback.format_exc()}")
    finally:
        print(f"[/ws/run/{run_id}] Cleaning up session...")
        # Ensure process is terminated if still running
        if process and process.poll() is None:
            print(f"[/ws/run/{run_id}] Terminating process {process.pid}")
            try: process.terminate()
            except ProcessLookupError: pass
            except Exception as term_e: print(f"Error terminating process {process.pid}: {term_e}")
            try: process.wait(timeout=1.0)
            except subprocess.TimeoutExpired: print(f"Process {process.pid} did not terminate gracefully, killing."); process.kill()
            except Exception as wait_e: print(f"Error waiting for process {process.pid} termination: {wait_e}")

        # Close WebSocket if still open
        if websocket.client_state != WebSocketState.DISCONNECTED:
             print(f"[/ws/run/{run_id}] Closing WebSocket connection.")
             try: await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
             except: pass

        # Clean up temp directory
        executable_dir = os.path.dirname(executable_path) if executable_path else None
        if run_id in run_sessions: del run_sessions[run_id]
        if executable_dir and os.path.exists(executable_dir):
            try:
                shutil.rmtree(executable_dir)
                print(f"[/ws/run/{run_id}] Cleaned up temp directory: {executable_dir}")
            except Exception as cleanup_error: print(f"Error cleaning up temp directory {executable_dir}: {cleanup_error}")


# /api/health (Keep as is)
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Conso Language Server is running"}

# --- Run Server ---
if __name__ == "__main__":
    print("Starting Uvicorn server...")
    # Run using standard uvicorn command from terminal is recommended
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True) # Keep reload for development if desired

