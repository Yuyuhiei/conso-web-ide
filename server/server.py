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
    # Ensure you are using the transpiler version with fflush calls
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
    allow_origins=["*"], # Allows all origins
    allow_credentials=True,
    allow_methods=["*"], # Allows all methods
    allow_headers=["*"], # Allows all headers
)
print("CORS middleware added.")

# --- Process Storage ---
# Stores mapping from run_id (str) to executable_path (str)
run_sessions: Dict[str, str] = {}
print("Run sessions dictionary initialized.")

# --- Request/Response Models ---
class CodeRequest(BaseModel):
    code: str

class TokenResponse(BaseModel):
    value: str
    type: str
    line: int
    column: int

class LexerResponse(BaseModel):
    tokens: List[TokenResponse]
    success: bool
    errors: List[str]

class ParserResponse(BaseModel):
    success: bool
    errors: List[str]
    syntaxValid: bool

class SemanticResponse(BaseModel):
    success: bool
    errors: List[str]

class PrepareRunResponse(BaseModel):
    success: bool
    runId: Optional[str] = None
    websocketUrl: Optional[str] = None
    phase: Optional[str] = None # Stage where error occurred (lexical, syntax, etc.)
    errors: List[str] = Field(default_factory=list)
    transpiledCode: Optional[str] = None # Include transpiled C code

print("Pydantic models defined.")

# --- Helper Functions ---
def normalize_code(code: str) -> str:
    """Normalizes line endings and removes trailing whitespace."""
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    lines = code.split('\n')
    normalized_lines = [line.rstrip() for line in lines]
    normalized_code = '\n'.join(normalized_lines)
    return normalized_code

def compile_c_code(c_code: str, run_id: str) -> Tuple[bool, Optional[str], str]:
    """Compiles the given C code using GCC."""
    print(f"[compile_c_code] Starting compilation for run_id: {run_id}")
    temp_dir = None
    executable_path = None
    try:
        temp_dir = tempfile.mkdtemp(prefix=f"conso_run_{run_id}_")
        c_file = os.path.join(temp_dir, "program.c")
        executable_path = os.path.join(temp_dir, "program.exe" if sys.platform == 'win32' else "program")

        with open(c_file, 'w', encoding='utf-8') as f:
            f.write(c_code)

        compile_cmd = ['gcc', c_file, '-o', executable_path, '-lm']
        print(f"[compile_c_code] Running command: {' '.join(compile_cmd)}")

        compile_result = subprocess.run(
            compile_cmd, capture_output=True, text=True, timeout=30,
            encoding='utf-8', errors='replace'
        )

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
        print(f"[compile_c_code] Compilation timed out for run_id: {run_id}")
        if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return False, None, "Compilation Timed Out (30s limit)."
    except FileNotFoundError:
        print("[compile_c_code] GCC command not found.")
        if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return False, None, "Compilation Error: 'gcc' command not found. Ensure GCC is installed and in your system's PATH."
    except Exception as e:
        print(f"[compile_c_code] Unexpected error: {e}\n{traceback.format_exc()}")
        if temp_dir and os.path.exists(temp_dir): shutil.rmtree(temp_dir)
        return False, None, f"Unexpected Server Error during C compilation: {str(e)}"

# --- API Endpoints (Lexer, Parser, Semantic) ---
# (Keep these endpoints as they were in your provided file)
@app.post("/api/lexer", response_model=LexerResponse)
async def lexical_analysis(request: CodeRequest):
    print("[/api/lexer] Request received.")
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip():
            return LexerResponse(tokens=[], success=True, errors=[])
        lexer = Lexer(input_code)
        tokens_data, errors = lexer.make_tokens()
        token_responses = [
            TokenResponse(
                value=tok.value if tok.value is not None else "",
                type=tok.type, line=tok.line, column=tok.column
            ) for tok in tokens_data
        ]
        return LexerResponse(tokens=token_responses, success=not errors, errors=[str(err) for err in errors])
    except LexerError as e:
         print(f"[/api/lexer] Lexer Error: {str(e)}")
         raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"[/api/lexer] Internal Server Error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")

@app.post("/api/parser", response_model=ParserResponse)
async def syntax_analysis(request: CodeRequest):
    print("[/api/parser] Request received.")
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip():
            return ParserResponse(success=True, errors=[], syntaxValid=True)
        lexer = Lexer(input_code)
        tokens_data, lexer_errors = lexer.make_tokens()
        if lexer_errors:
            return ParserResponse(success=False, errors=[f"Lexical Error: {str(err)}" for err in lexer_errors], syntaxValid=False)
        definitions.token.clear()
        for tok in tokens_data:
            definitions.token.append((tok.type, tok.line, tok.column))
        _, error_messages, syntax_valid = parse()
        return ParserResponse(success=syntax_valid, errors=error_messages or [], syntaxValid=syntax_valid)
    except ParserError as e:
        print(f"[/api/parser] Parser Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"[/api/parser] Internal Server Error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")

@app.post("/api/semantic", response_model=SemanticResponse)
async def semantic_analysis_endpoint(request: CodeRequest):
    print("[/api/semantic] Request received.")
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip():
            return SemanticResponse(success=True, errors=[])
        lexer = Lexer(input_code)
        tokens_data, lexer_errors = lexer.make_tokens()
        if lexer_errors:
            return SemanticResponse(success=False, errors=[f"Lexical Error: {str(err)}" for err in lexer_errors])
        semantic_tokens = [(tok.type, tok.value, tok.line, tok.column) for tok in tokens_data]
        analyzer = SemanticAnalyzer()
        success, errors = analyzer.analyze(semantic_tokens)
        return SemanticResponse(success=success, errors=errors)
    except SemanticError as e:
        print(f"[/api/semantic] Semantic Error: {str(e)}")
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"[/api/semantic] Internal Server Error: {str(e)}\n{traceback.format_exc()}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Internal Server Error: {str(e)}")

# --- Prepare Run Endpoint ---
@app.post("/api/run/prepare", response_model=PrepareRunResponse)
async def prepare_interactive_run(request: CodeRequest, response: Response):
    """Analyzes, transpiles, and compiles Conso code, preparing it for interactive execution."""
    print("[/api/run/prepare] Request received.")
    input_code = normalize_code(request.code)
    if not input_code.strip():
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PrepareRunResponse(success=False, phase="validation", errors=["No code provided."])

    symbol_table_for_transpiler = None; analyzer = None
    # 1. Lexical Analysis
    print("[/api/run/prepare] Starting Lexical Analysis...")
    lexer = Lexer(input_code)
    tokens_data, lexer_errors = lexer.make_tokens()
    if lexer_errors:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return PrepareRunResponse(success=False, phase="lexical", errors=[str(err) for err in lexer_errors])
    print("[/api/run/prepare] Lexical Analysis OK.")
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
    try:
        analyzer = SemanticAnalyzer()
        semantic_valid, semantic_errors = analyzer.analyze(detailed_tokens)
        if not semantic_valid:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return PrepareRunResponse(success=False, phase="semantic", errors=semantic_errors)
        if hasattr(analyzer, 'function_scopes') and "mn" in analyzer.function_scopes:
             symbol_table_for_transpiler = analyzer.function_scopes["mn"]
             print("[/api/run/prepare] Using 'mn' function scope for transpiler.")
        elif hasattr(analyzer, 'global_scope'):
             symbol_table_for_transpiler = analyzer.global_scope
             print("[/api/run/prepare] Warning: 'mn' scope not found, using global scope for transpiler.")
        else:
             response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
             return PrepareRunResponse(success=False, phase="semantic", errors=["Cannot find suitable symbol table scope for transpilation."])
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
        if transpiled_code.strip().startswith("// TRANSPILER ERROR") or transpiled_code.strip().startswith("// UNEXPECTED"):
             response.status_code = status.HTTP_400_BAD_REQUEST
             error_msg = transpiled_code.split(":", 1)[-1].strip() if ":" in transpiled_code else transpiled_code
             return PrepareRunResponse(success=False, phase="transpilation", errors=[error_msg])
        print("[/api/run/prepare] Transpilation OK.")
    except TranspilerError as e:
         print(f"[/api/run/prepare] Transpiler Error: {str(e)}")
         response.status_code = status.HTTP_400_BAD_REQUEST
         return PrepareRunResponse(success=False, phase="transpilation", errors=[str(e)])
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
        print(f"--- Failed C Code (run_id: {run_id}) ---")
        print(transpiled_code)
        print("--- End Failed C Code ---")
        return PrepareRunResponse(success=False, phase="compilation", errors=[compile_error], transpiledCode=transpiled_code)
    print("[/api/run/prepare] C Compilation OK.")

    run_sessions[run_id] = executable_path
    ws_host = "localhost"; ws_port = 5000; ws_protocol = "ws"
    ws_url = f"{ws_protocol}://{ws_host}:{ws_port}/ws/run/{run_id}"
    print(f"[/api/run/prepare] Run prepared. ID: {run_id}, Executable: {executable_path}, WS URL: {ws_url}")
    return PrepareRunResponse(success=True, runId=run_id, websocketUrl=ws_url, transpiledCode=transpiled_code)


# --- WebSocket Endpoint for Interactive Run ---
@app.websocket("/ws/run/{run_id}")
async def websocket_run_endpoint(websocket: WebSocket, run_id: str):
    """Handles the interactive execution session over WebSocket."""
    await websocket.accept()
    print(f"[/ws/run/{run_id}] WebSocket connection accepted.")

    executable_path = run_sessions.get(run_id)
    if not executable_path or not os.path.exists(executable_path):
        print(f"[/ws/run/{run_id}] Error: Executable not found or run session invalid.")
        await websocket.send_json({"type": "error", "message": "Executable not found or run session expired."})
        await websocket.close(code=status.WS_1011_INTERNAL_ERROR)
        return

    process = None
    loop = asyncio.get_running_loop()
    stdout_task = None
    stderr_task = None
    stdin_task = None
    process_wait_future = None
    final_exit_code = None # Initialize exit code

    try:
        print(f"[/ws/run/{run_id}] Starting process using Popen in thread: {executable_path}")
        process = await asyncio.to_thread(
            subprocess.Popen,
            [executable_path], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        print(f"[/ws/run/{run_id}] Started C process (PID: {process.pid})")

        # --- forward_stream reads chunks ---
        async def forward_stream(stream, stream_name, ws):
            """Reads chunks from the stream and forwards them over WebSocket."""
            print(f"[/ws/run/{run_id}] {stream_name} forwarder started.")
            # --- Reverted CHUNK_SIZE ---
            CHUNK_SIZE = 1 # Read byte by byte for responsiveness
            # --- END ---
            try:
                while True:
                    chunk = await loop.run_in_executor(None, stream.read, CHUNK_SIZE)
                    if not chunk:
                        print(f"[/ws/run/{run_id}] {stream_name} EOF reached.")
                        break # End of stream
                    try:
                        decoded_data = chunk.decode('utf-8', errors='replace')
                        if ws.client_state == WebSocketState.CONNECTED:
                             await ws.send_json({"type": stream_name, "data": decoded_data})
                        else:
                             print(f"[/ws/run/{run_id}] WebSocket closed, stopping {stream_name} forwarder.")
                             break
                    except (WebSocketDisconnect, ConnectionResetError):
                        print(f"[/ws/run/{run_id}] WebSocket disconnected during {stream_name} send.")
                        break
                    except Exception as send_e:
                        print(f"[/ws/run/{run_id}] Error sending {stream_name} chunk: {send_e}")
                        break
            except asyncio.CancelledError:
                 print(f"[/ws/run/{run_id}] {stream_name} forwarder cancelled.")
            except Exception as read_e:
                 if isinstance(read_e, ValueError) and "I/O operation on closed file" in str(read_e):
                      print(f"[/ws/run/{run_id}] {stream_name} stream closed.")
                 else:
                      print(f"[/ws/run/{run_id}] Error reading {stream_name}: {type(read_e).__name__} - {read_e}")
            finally:
                print(f"[/ws/run/{run_id}] {stream_name} forwarder finished.")
        # --- END forward_stream ---

        async def receive_stdin(ws, proc_stdin):
            """Receives stdin data from WebSocket and writes to process."""
            print(f"[/ws/run/{run_id}] stdin receiver started.")
            try:
                while True:
                    if ws.client_state != WebSocketState.CONNECTED:
                         print(f"[/ws/run/{run_id}] WebSocket closed, stopping stdin receiver.")
                         break
                    ws_data_raw = await ws.receive_text()
                    ws_data = json.loads(ws_data_raw)
                    if ws_data.get("type") == "stdin" and proc_stdin:
                        input_data = ws_data.get("data", "")
                        try:
                            if not proc_stdin.closed:
                                await loop.run_in_executor(None, proc_stdin.write, input_data.encode('utf-8'))
                                await loop.run_in_executor(None, proc_stdin.flush)
                                print(f"[/ws/run/{run_id}] Wrote to stdin: {input_data!r}")
                            else:
                                 print(f"[/ws/run/{run_id}] Attempted write to closed stdin pipe.")
                                 break
                        except (BrokenPipeError, ValueError, OSError) as write_e:
                            print(f"[/ws/run/{run_id}] Error writing to process stdin (Process likely exited or closed pipe): {write_e}")
                            break
            except WebSocketDisconnect:
                print(f"[/ws/run/{run_id}] WebSocket disconnected by client.")
            except json.JSONDecodeError:
                print(f"[/ws/run/{run_id}] Invalid JSON received from client.")
            except asyncio.CancelledError:
                 print(f"[/ws/run/{run_id}] stdin receiver cancelled.")
            except Exception as e:
                print(f"[/ws/run/{run_id}] Error in stdin receiver: {type(e).__name__} - {e}")
            finally:
                print(f"[/ws/run/{run_id}] stdin receiver finished.")
                if proc_stdin and not proc_stdin.closed:
                    try:
                        print(f"[/ws/run/{run_id}] Closing process stdin pipe.")
                        await loop.run_in_executor(None, proc_stdin.close)
                    except Exception as close_e:
                         print(f"[/ws/run/{run_id}] Error closing process stdin: {close_e}")

        # Create I/O tasks
        stdout_task = asyncio.create_task(forward_stream(process.stdout, "stdout", websocket), name=f"stdout_{run_id}")
        stderr_task = asyncio.create_task(forward_stream(process.stderr, "stderr", websocket), name=f"stderr_{run_id}")
        stdin_task = asyncio.create_task(receive_stdin(websocket, process.stdin), name=f"stdin_{run_id}")

        # Get the Future for process.wait directly
        process_wait_future = loop.run_in_executor(None, process.wait)

        # --- MODIFIED WAITING LOGIC ---
        # 1. Wait for the process itself to finish
        print(f"[/ws/run/{run_id}] Waiting for process {process.pid} to exit...")
        try:
            final_exit_code = await process_wait_future
            print(f"[/ws/run/{run_id}] Process exited with code {final_exit_code}.")
        except Exception as wait_err:
             print(f"[/ws/run/{run_id}] Error waiting for process: {wait_err}")
             final_exit_code = process.poll() # Poll after error
             print(f"[/ws/run/{run_id}] Polled exit code after wait error: {final_exit_code}")

        # 2. Wait for stdout and stderr streams to be fully drained
        print(f"[/ws/run/{run_id}] Waiting for stdout/stderr tasks to complete...")
        try:
            # Use gather to wait for both tasks, allow exceptions
            await asyncio.gather(stdout_task, stderr_task, return_exceptions=True)
            print(f"[/ws/run/{run_id}] stdout/stderr tasks finished.")
        except Exception as gather_err:
             print(f"[/ws/run/{run_id}] Error gathering stdout/stderr tasks: {gather_err}")

        # 3. Cancel the stdin task (it might be waiting for input)
        if stdin_task and not stdin_task.done():
            print(f"[/ws/run/{run_id}] Cancelling stdin task.")
            stdin_task.cancel()
            try:
                await stdin_task # Wait for cancellation to complete
            except asyncio.CancelledError:
                 print(f"[/ws/run/{run_id}] stdin task successfully cancelled.")
            except Exception as cancel_err:
                 print(f"[/ws/run/{run_id}] Error during stdin task cancellation: {cancel_err}")
        # --- END MODIFIED WAITING LOGIC ---

        # Send exit code if known and WS is connected
        if final_exit_code is not None and websocket.client_state == WebSocketState.CONNECTED:
             print(f"[/ws/run/{run_id}] Sending final exit code {final_exit_code} to client.")
             try:
                 await websocket.send_json({"type": "exit", "exit_code": final_exit_code})
             except Exception as send_exit_e:
                  print(f"[/ws/run/{run_id}] Error sending exit code: {send_exit_e}")
        elif final_exit_code is None:
             print(f"[/ws/run/{run_id}] Process final exit code unknown, not sending exit message.")

    except WebSocketDisconnect:
        print(f"[/ws/run/{run_id}] WebSocket disconnected by client during setup or main loop.")
        # Terminate process if WS disconnects early
        if process and process.poll() is None:
            print(f"[/ws/run/{run_id}] Terminating process due to WebSocket disconnect.")
            process.terminate()
            try: await loop.run_in_executor(None, process.wait, 1.0)
            except subprocess.TimeoutExpired: process.kill()
            except ProcessLookupError: pass
            except Exception as term_e: print(f"[/ws/run/{run_id}] Error during process termination after WS disconnect: {term_e}")

    except Exception as e:
        print(f"[/ws/run/{run_id}] Error in WebSocket handler: {type(e).__name__} - {e}\n{traceback.format_exc()}")
        if websocket.client_state == WebSocketState.CONNECTED:
            try: await websocket.send_json({"type": "error", "message": f"Server error: {type(e).__name__}"})
            except Exception as send_err_e: print(f"[/ws/run/{run_id}] Failed to send error to client: {send_err_e}")

    finally:
        print(f"[/ws/run/{run_id}] Final cleanup phase...")
        # Cancel any remaining I/O tasks
        tasks_to_cancel = [t for t in [stdout_task, stderr_task, stdin_task] if t and not t.done()]
        if tasks_to_cancel:
            print(f"[/ws/run/{run_id}] Cancelling remaining I/O tasks in finally block...")
            for task in tasks_to_cancel: task.cancel()
            await asyncio.gather(*tasks_to_cancel, return_exceptions=True)
            print(f"[/ws/run/{run_id}] Remaining I/O tasks cancelled.")

        # Ensure process is terminated
        if process and process.poll() is None:
            print(f"[/ws/run/{run_id}] Terminating process {process.pid} in final cleanup.")
            try:
                process.terminate()
                await loop.run_in_executor(None, process.wait, 1.0)
            except subprocess.TimeoutExpired:
                print(f"Process {process.pid} did not terminate gracefully, killing.")
                try: process.kill()
                except ProcessLookupError: pass
                except Exception as kill_e: print(f"Error killing process {process.pid}: {kill_e}")
            except ProcessLookupError: pass
            except Exception as term_e: print(f"Error terminating process {process.pid}: {term_e}")

        # Close WebSocket
        if websocket.client_state != WebSocketState.DISCONNECTED:
             print(f"[/ws/run/{run_id}] Closing WebSocket connection.")
             try: await websocket.close(code=status.WS_1000_NORMAL_CLOSURE)
             except Exception as ws_close_e: print(f"[/ws/run/{run_id}] Error closing WebSocket: {ws_close_e}")

        # Clean up temp directory
        executable_dir = os.path.dirname(executable_path) if executable_path else None
        if run_id in run_sessions:
            print(f"[/ws/run/{run_id}] Removing session entry.")
            del run_sessions[run_id]
        if executable_dir and os.path.exists(executable_dir):
            try:
                shutil.rmtree(executable_dir)
                print(f"[/ws/run/{run_id}] Cleaned up temp directory: {executable_dir}")
            except Exception as cleanup_error: print(f"Error cleaning up temp directory {executable_dir}: {cleanup_error}")
        print(f"[/ws/run/{run_id}] Cleanup complete.")


# /api/health (Keep as is)
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Conso Language Server is running"}

# --- Run Server ---
if __name__ == "__main__":
    print("Starting Uvicorn server...")
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=False)

