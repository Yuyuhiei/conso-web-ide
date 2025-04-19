# server.py

from fastapi import FastAPI, HTTPException, Body, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional, Tuple
import uvicorn
import copy
import re
import os
import tempfile
import subprocess
import sys
import shutil
import traceback # Import traceback for detailed error logging

# Import your existing compiler components
from lexer import Lexer, LexerError
from parser import parse, ParserError
from semantic import SemanticAnalyzer, SemanticError
import definitions

# Import the updated transpiler function and error class
from transpiler import transpile_from_tokens, TranspilerError

app = FastAPI(title="Conso Language Server")

# --- CORS Configuration --- (Keep as is)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"],
)

# --- Request/Response Models --- (Update InputPrompt)

class CodeRequest(BaseModel):
    code: str

class RunWithInputRequest(BaseModel):
    code: str
    inputs: Dict[str, str] = Field(default_factory=dict)

class TokenResponse(BaseModel):
    value: str; type: str; line: int; column: int

class LexerResponse(BaseModel):
    tokens: List[TokenResponse]; success: bool; errors: List[str]

class ParserResponse(BaseModel):
    success: bool; errors: List[str]; syntaxValid: bool

class SemanticResponse(BaseModel):
    success: bool; errors: List[str]

# --- MODIFIED InputPrompt Model ---
class InputPrompt(BaseModel):
    variable_name: str
    prompt_text: str
    line: int
    variable_type: str # <-- ADDED: Expected type (e.g., 'nt', 'dbl', 'strng')

# --- InputRequiredResponse Model (No change needed) ---
class InputRequiredResponse(BaseModel):
    status: str = "input_required"
    prompts: List[InputPrompt] # Will now contain prompts with variable_type

# --- ExecutionResult Model (No change needed) ---
class ExecutionResult(BaseModel):
    status: str = "completed"; success: bool; phase: str
    errors: List[str] = Field(default_factory=list)
    transpiledCode: Optional[str] = None; output: Optional[str] = None

# --- Helper Functions ---

# normalize_code (Keep revised version from previous step)
def normalize_code(code: str) -> str:
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    lines = code.split('\n')
    normalized_lines = [line.rstrip() for line in lines]
    normalized_code = '\n'.join(normalized_lines)
    return normalized_code

# --- MODIFIED scan_for_npt ---
# It now needs the symbol table to look up types
def scan_for_npt(tokens: List[Tuple[str, Any, int, int]], symbol_table) -> List[InputPrompt]:
    """
    Scans the token list for 'npt' assignments and extracts variable names,
    prompts, line numbers, AND variable types using the provided symbol table.

    Args:
        tokens: List of (type, value, line, column) tuples.
        symbol_table: The symbol table scope (e.g., function scope) where
                      the variables are expected to be defined.

    Returns:
        A list of InputPrompt objects including variable_type.
    """
    prompts = []
    i = 0
    while i < len(tokens):
        # Pattern: id = npt ( string_literal ) ;
        if tokens[i][0] == 'id' and i + 6 < len(tokens):
            var_name = tokens[i][1]
            line_num = tokens[i][2]
            if tokens[i+1][0] == '=' and \
               tokens[i+2][0] == 'npt' and \
               tokens[i+3][0] == '(' and \
               tokens[i+4][0] == 'strnglit' and \
               tokens[i+5][0] == ')' and \
               tokens[i+6][0] == ';':

                prompt_text = tokens[i+4][1]
                var_type = "unknown" # Default type if lookup fails

                # --- Look up variable type in the provided symbol table ---
                if symbol_table and hasattr(symbol_table, 'lookup'):
                    symbol_entry = symbol_table.lookup(var_name)
                    if symbol_entry and hasattr(symbol_entry, 'data_type'):
                        var_type = symbol_entry.data_type
                    else:
                        print(f"Warning: Variable '{var_name}' for npt prompt not found in provided symbol table scope during scan.")
                else:
                     print(f"Warning: Symbol table not available or no lookup method during npt scan for '{var_name}'.")
                # --- End type lookup ---

                prompts.append(InputPrompt(
                    variable_name=var_name,
                    prompt_text=prompt_text,
                    line=line_num,
                    variable_type=var_type # Include the type
                ))
                i += 7
                continue
        i += 1
    return prompts

# compile_and_run_c (Keep as is)
def compile_and_run_c(c_code: str) -> Tuple[bool, str, str]:
    # ... (implementation remains the same) ...
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix="conso_run_")
        c_file = os.path.join(temp_dir, "program.c")
        executable = os.path.join(temp_dir, "program.exe" if sys.platform == 'win32' else "program")
        with open(c_file, 'w', encoding='utf-8') as f: f.write(c_code)
        compile_cmd = ['gcc', c_file, '-o', executable, '-lm']
        compile_result = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace')
        if compile_result.returncode != 0:
            error_details = compile_result.stderr.replace(f'{c_file}:', f'Line ')
            return False, "", f"Compilation Error:\n{error_details}"
        run_result = subprocess.run([executable], capture_output=True, text=True, timeout=10, encoding='utf-8', errors='replace')
        if run_result.returncode != 0:
            runtime_error_details = f"Runtime Error (Exit Code {run_result.returncode}):\n"
            if run_result.stdout: runtime_error_details += f"--- stdout ---\n{run_result.stdout}\n"
            if run_result.stderr: runtime_error_details += f"--- stderr ---\n{run_result.stderr}\n"
            return False, run_result.stdout, runtime_error_details.strip()
        return True, run_result.stdout, run_result.stderr
    except subprocess.TimeoutExpired as e:
        phase = "Execution" if 'executable' in locals() and e.cmd == [executable] else "Compilation"
        return False, "", f"{phase} Timed Out ({e.timeout}s limit)."
    except FileNotFoundError:
        return False, "", "Compilation Error: 'gcc' command not found. Ensure GCC is installed and in PATH."
    except Exception as e:
        print(f"Unexpected Server Error during C execution: {str(e)}\n{traceback.format_exc()}")
        return False, "", f"Unexpected Server Error during C execution: {str(e)}"
    finally:
        if temp_dir and os.path.exists(temp_dir):
            try: shutil.rmtree(temp_dir)
            except Exception as cleanup_error: print(f"Warning: Failed to cleanup temp dir {temp_dir}: {cleanup_error}")


# --- API Endpoints ---

# /api/lexer, /api/parser, /api/semantic (Keep as is)
@app.post("/api/lexer", response_model=LexerResponse)
async def lexical_analysis(request: CodeRequest):
    # ... (implementation remains the same) ...
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip(): return LexerResponse(tokens=[], success=True, errors=[])
        lexer = Lexer(input_code)
        tokens_data, errors = lexer.make_tokens()
        token_responses = [TokenResponse(value=tok.value if tok.value is not None else "", type=tok.type, line=tok.line, column=tok.column) for tok in tokens_data]
        return LexerResponse(tokens=token_responses, success=not errors, errors=[str(err) for err in errors])
    except Exception as e: print(f"Lexical Analysis Server Error: {str(e)}"); return LexerResponse(tokens=[], success=False, errors=[f"Internal Server Error: {str(e)}"])

@app.post("/api/parser", response_model=ParserResponse)
async def syntax_analysis(request: CodeRequest):
    # ... (implementation remains the same) ...
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
    except Exception as e: print(f"Syntax Analysis Server Error: {str(e)}\n{traceback.format_exc()}"); return ParserResponse(success=False, errors=[f"Internal Server Error: {str(e)}"], syntaxValid=False)

@app.post("/api/semantic", response_model=SemanticResponse)
async def semantic_analysis_endpoint(request: CodeRequest):
    # ... (implementation remains the same) ...
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
    except Exception as e: print(f"Semantic Analysis Server Error: {str(e)}\n{traceback.format_exc()}"); return SemanticResponse(success=False, errors=[f"Internal Server Error: {str(e)}"])


# --- MODIFIED Run Endpoint (Step 1: Validate and Check for Input) ---
@app.post("/api/run/initiate", response_model=InputRequiredResponse | ExecutionResult)
async def initiate_run(request: CodeRequest, response: Response):
    input_code = normalize_code(request.code)
    if not input_code.strip(): return ExecutionResult(success=True, phase="validation", output="No code provided.")

    # 1. Lexical Analysis
    lexer = Lexer(input_code)
    tokens_data, lexer_errors = lexer.make_tokens()
    if lexer_errors:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ExecutionResult(success=False, phase="lexical", errors=[str(err) for err in lexer_errors])

    # Prepare tokens
    definitions.token.clear()
    detailed_tokens = []
    for tok in tokens_data:
        definitions.token.append((tok.type, tok.line, tok.column))
        detailed_tokens.append((tok.type, tok.value, tok.line, tok.column))

    # 2. Syntax Analysis
    try:
        _, parser_errors, syntax_valid = parse()
        if not syntax_valid:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ExecutionResult(success=False, phase="syntax", errors=parser_errors or ["Syntax error detected."])
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        print(f"Parser Internal Error: {str(e)}\n{traceback.format_exc()}")
        return ExecutionResult(success=False, phase="syntax", errors=[f"Parser Internal Error: {str(e)}"])

    # 3. Semantic Analysis
    symbol_table_for_transpiler = None
    analyzer = None
    try:
        analyzer = SemanticAnalyzer()
        semantic_valid, semantic_errors = analyzer.analyze(detailed_tokens)
        if not semantic_valid:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ExecutionResult(success=False, phase="semantic", errors=semantic_errors)

        # Get the correct symbol table scope (e.g., 'mn' function scope)
        mn_scope_table = analyzer.function_scopes.get("mn")
        if mn_scope_table is None:
            print("Warning: 'mn' function scope not found, checking global scope for transpiler.")
            mn_scope_table = analyzer.global_scope
            if mn_scope_table is None:
                print("Error: Neither 'mn' function scope nor global scope found after semantic analysis.")
                response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                return ExecutionResult(success=False, phase="semantic", errors=["Internal Server Error: Cannot find valid symbol table scope."])
        symbol_table_for_transpiler = mn_scope_table # Use the determined scope

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        print(f"Semantic Analysis Internal Error: {str(e)}\n{traceback.format_exc()}")
        return ExecutionResult(success=False, phase="semantic", errors=[f"Semantic Analyzer Internal Error: {str(e)}"])

    # --- MODIFIED npt Scan ---
    # 4. Scan for 'npt' calls using the detailed token list AND the correct symbol table
    required_prompts = scan_for_npt(detailed_tokens, symbol_table_for_transpiler)
    # --- End MODIFIED npt Scan ---

    # 5. Decide action based on prompts
    if required_prompts:
        print(f"Input required: {required_prompts}")
        return InputRequiredResponse(prompts=required_prompts) # Prompts now include type
    else:
        # No input needed, proceed directly to transpilation and execution
        print("No input required, proceeding to direct execution.")
        try:
            transpiled_code = transpile_from_tokens(detailed_tokens, symbol_table_for_transpiler, user_inputs={})
            if transpiled_code.startswith("// TRANSPILER ERROR") or transpiled_code.startswith("// UNEXPECTED"):
                 print(f"Transpilation failed: {transpiled_code}")
                 response.status_code = status.HTTP_400_BAD_REQUEST
                 error_msg = transpiled_code.split(":", 1)[-1].strip() if ":" in transpiled_code else transpiled_code
                 return ExecutionResult(success=False, phase="transpilation", errors=[error_msg])
        except Exception as e:
             response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
             print(f"Transpiler Internal Error: {str(e)}\n{traceback.format_exc()}")
             return ExecutionResult(success=False, phase="transpilation", errors=[f"Transpiler Internal Error: {str(e)}"])

        # 6. Compile and Run C code
        success, output, error_msg = compile_and_run_c(transpiled_code)
        if not success:
            print(f"C Compilation/Execution failed: {error_msg}")
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ExecutionResult(success=False, phase="compilation/execution", errors=[error_msg], transpiledCode=transpiled_code, output=output)
        else:
            print(f"Direct execution successful. Output:\n{output}\nWarnings:\n{error_msg}")
            return ExecutionResult(success=True, phase="execution", transpiledCode=transpiled_code, output=output, errors=[error_msg] if error_msg else [])


# /api/run/execute (Keep as is, it already re-runs semantic analysis to get scope)
@app.post("/api/run/execute", response_model=ExecutionResult)
async def execute_run_with_input(request: RunWithInputRequest, response: Response):
    # ... (implementation remains the same - it already gets the correct scope for transpilation) ...
    input_code = normalize_code(request.code)
    user_inputs = request.inputs
    print(f"Executing run with inputs: {user_inputs}")
    if not input_code.strip(): response.status_code = status.HTTP_400_BAD_REQUEST; return ExecutionResult(success=False, phase="validation", errors=["No code provided."])
    lexer = Lexer(input_code)
    tokens_data, lexer_errors = lexer.make_tokens()
    if lexer_errors: response.status_code = status.HTTP_400_BAD_REQUEST; return ExecutionResult(success=False, phase="lexical", errors=[f"Error during re-lexing: {str(err)}" for err in lexer_errors])
    detailed_tokens = [(tok.type, tok.value, tok.line, tok.column) for tok in tokens_data]
    symbol_table_for_transpiler = None; analyzer = None
    try:
        analyzer = SemanticAnalyzer(); semantic_valid, semantic_errors = analyzer.analyze(detailed_tokens)
        if not semantic_valid: response.status_code = status.HTTP_400_BAD_REQUEST; return ExecutionResult(success=False, phase="semantic", errors=[f"Error during re-analysis: {err}" for err in semantic_errors])
        mn_scope_table = analyzer.function_scopes.get("mn")
        if mn_scope_table is None:
             print("Warning: 'mn' function scope not found during re-analysis, checking global scope."); mn_scope_table = analyzer.global_scope
             if mn_scope_table is None: print("Error: Neither 'mn' function scope nor global scope found during re-analysis."); response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR; return ExecutionResult(success=False, phase="semantic", errors=["Internal Server Error: Cannot find valid symbol table scope during re-analysis."])
        symbol_table_for_transpiler = mn_scope_table
    except Exception as e: response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR; print(f"Semantic Analyzer Internal Error during re-analysis: {str(e)}\n{traceback.format_exc()}"); return ExecutionResult(success=False, phase="semantic", errors=[f"Semantic Analyzer Internal Error during re-analysis: {str(e)}"])
    try:
        transpiled_code = transpile_from_tokens(detailed_tokens, symbol_table_for_transpiler, user_inputs)
        if transpiled_code.startswith("// TRANSPILER ERROR") or transpiled_code.startswith("// UNEXPECTED"):
             print(f"Transpilation failed: {transpiled_code}"); response.status_code = status.HTTP_400_BAD_REQUEST; error_msg = transpiled_code.split(":", 1)[-1].strip() if ":" in transpiled_code else transpiled_code; return ExecutionResult(success=False, phase="transpilation", errors=[error_msg])
    except Exception as e: response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR; print(f"Transpiler Internal Error: {str(e)}\n{traceback.format_exc()}"); return ExecutionResult(success=False, phase="transpilation", errors=[f"Transpiler Internal Error: {str(e)}"])
    success, output, error_msg = compile_and_run_c(transpiled_code)
    if not success: print(f"C Compilation/Execution failed: {error_msg}"); response.status_code = status.HTTP_400_BAD_REQUEST; return ExecutionResult(success=False, phase="compilation/execution", errors=[error_msg], transpiledCode=transpiled_code, output=output)
    else: print(f"Execution with input successful. Output:\n{output}\nWarnings:\n{error_msg}"); return ExecutionResult(success=True, phase="execution", transpiledCode=transpiled_code, output=output, errors=[error_msg] if error_msg else [])


# /api/health (Keep as is)
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Conso Language Server is running"}

# --- Run Server --- (Keep as is)
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
