# server.py

from fastapi import FastAPI, HTTPException, Body, Response, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field # Field is used for default values
from typing import List, Dict, Any, Optional, Tuple
import uvicorn
import copy
import re
import os
import tempfile
import subprocess
import sys
import shutil # For cleanup

# Import your existing compiler components
from lexer import Lexer, LexerError # Assuming LexerError exists
from parser import parse, ParserError # Assuming ParserError exists
from semantic import SemanticAnalyzer, SemanticError # Assuming SemanticError exists
import definitions # Assuming this holds global state like definitions.token if needed by parser

# Import the updated transpiler function and error class
from transpiler import transpile_from_tokens, TranspilerError

app = FastAPI(title="Conso Language Server")

# --- CORS Configuration ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow all for development, restrict in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Request/Response Models ---

class CodeRequest(BaseModel):
    code: str

class RunWithInputRequest(BaseModel):
    code: str
    inputs: Dict[str, str] = Field(default_factory=dict) # Maps var_name -> user_input_string

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

# Model for input prompts required by the frontend
class InputPrompt(BaseModel):
    variable_name: str
    prompt_text: str
    line: int # Line number where npt occurs

# Model for the response when input is required
class InputRequiredResponse(BaseModel):
    status: str = "input_required"
    prompts: List[InputPrompt]

# Model for the final execution result
class ExecutionResult(BaseModel):
    status: str = "completed" # Or "error"
    success: bool
    phase: str # Stage where error occurred (lexical, syntax, semantic, transpilation, compilation, execution)
    errors: List[str] = Field(default_factory=list)
    transpiledCode: Optional[str] = None
    output: Optional[str] = None

# --- Helper Functions ---

def normalize_code(code: str) -> str:
    """Normalizes code string for consistent processing."""
    # (Using the normalization logic from your uploaded server.py)
    code = code.replace('\r\n', '\n').replace('\r', '\n')
    code = re.sub(r'mn\s+\(', 'mn(', code)
    code = re.sub(r'{\s*\n\s+', '{ ', code)
    code = re.sub(r'\s+\n', '\n', code)
    lines = code.split('\n')
    normalized_lines = []
    for line in lines:
        left_aligned = line.lstrip()
        # Collapse multiple spaces/tabs inside the line to a single space
        collapsed = re.sub(r'[ \t]+', ' ', left_aligned)
        normalized_lines.append(collapsed)
    code = '\n'.join(normalized_lines)

    # Optionally, join lines where parentheses are open (for multi-line expressions)
    # This is a simple heuristic: join lines ending with an open parenthesis or operator
    joined_lines = []
    buffer = ''
    paren_depth = 0
    for line in normalized_lines: # Use normalized_lines here
        paren_depth += line.count('(') - line.count(')')
        if buffer:
            buffer += ' ' + line
        else:
            buffer = line
        # Only join if the line doesn't end a statement (heuristic: check for ';', '{', '}')
        # and parentheses are open
        if paren_depth == 0 or line.rstrip().endswith((';', '{', '}')):
             joined_lines.append(buffer)
             buffer = ''
    if buffer: # Append any remaining buffer content
        joined_lines.append(buffer)
    code = '\n'.join(joined_lines)

    return code


def scan_for_npt(tokens: List[Tuple[str, Any, int, int]]) -> List[InputPrompt]:
    """
    Scans the token list for 'npt' assignments and extracts variable names and prompts.
    Args: tokens: List of (type, value, line, column) tuples.
    Returns: List of InputPrompt objects.
    """
    prompts = []
    i = 0
    while i < len(tokens):
        # Pattern: id = npt ( string_literal ) ;
        # Check indices carefully
        if tokens[i][0] == 'id' and i + 6 < len(tokens): # Need up to index i+6 for semicolon
            var_name = tokens[i][1]
            line_num = tokens[i][2]
            # Check the sequence of token types
            if tokens[i+1][0] == '=' and \
               tokens[i+2][0] == 'npt' and \
               tokens[i+3][0] == '(' and \
               tokens[i+4][0] == 'strnglit' and \
               tokens[i+5][0] == ')' and \
               tokens[i+6][0] == ';':
                # Found the pattern
                prompt_text = tokens[i+4][1] # Extract prompt from string literal value
                prompts.append(InputPrompt(
                    variable_name=var_name,
                    prompt_text=prompt_text,
                    line=line_num
                ))
                # Skip ahead past this pattern (id = npt ( str ) ;) -> 7 tokens
                i += 7
                continue # Continue scanning from the new position
        i += 1 # Move to the next token if pattern not matched or bounds check failed
    return prompts

def compile_and_run_c(c_code: str) -> Tuple[bool, str, str]:
    """
    Compiles and runs the given C code in a temporary directory.
    Args: c_code: The C code string.
    Returns: Tuple (success: bool, output: str, error: str).
    """
    temp_dir = None
    try:
        temp_dir = tempfile.mkdtemp(prefix="conso_run_")
        c_file = os.path.join(temp_dir, "program.c")
        executable = os.path.join(temp_dir, "program.exe" if sys.platform == 'win32' else "program")

        # Write C code, ensuring UTF-8 encoding
        with open(c_file, 'w', encoding='utf-8') as f:
            f.write(c_code)

        # Compile using gcc, add -lm for math library just in case
        compile_cmd = ['gcc', c_file, '-o', executable, '-lm']
        compile_result = subprocess.run(
            compile_cmd, capture_output=True, text=True, timeout=15, encoding='utf-8', errors='replace'
        )

        # Check compilation result
        if compile_result.returncode != 0:
            # Clean up stderr for better display
            error_details = compile_result.stderr.replace(f'{c_file}:', f'Line ') # Make line numbers clearer
            return False, "", f"Compilation Error:\n{error_details}"

        # Run the compiled executable
        run_result = subprocess.run(
            [executable], capture_output=True, text=True, timeout=10, encoding='utf-8', errors='replace'
        )

        # Check runtime result
        if run_result.returncode != 0:
            runtime_error_details = f"Runtime Error (Exit Code {run_result.returncode}):\n"
            # Include stdout and stderr for context
            if run_result.stdout: runtime_error_details += f"--- stdout ---\n{run_result.stdout}\n"
            if run_result.stderr: runtime_error_details += f"--- stderr ---\n{run_result.stderr}\n"
            return False, run_result.stdout, runtime_error_details.strip()

        # Success - return stdout and any potential stderr warnings
        return True, run_result.stdout, run_result.stderr

    except subprocess.TimeoutExpired as e:
        # Determine if timeout occurred during compilation or execution
        phase = "Execution" if e.cmd == [executable] else "Compilation"
        return False, "", f"{phase} Timed Out ({e.timeout}s limit)."
    except FileNotFoundError:
         # Handle case where gcc might not be installed or in PATH
        return False, "", "Compilation Error: 'gcc' command not found. Please ensure GCC is installed and in your system's PATH."
    except Exception as e:
        # Catch other potential errors during the process
        import traceback
        print(f"Unexpected Server Error during C execution: {str(e)}\n{traceback.format_exc()}")
        return False, "", f"Unexpected Server Error during C execution: {str(e)}"
    finally:
        # Ensure temporary directory cleanup
        if temp_dir and os.path.exists(temp_dir):
            try:
                shutil.rmtree(temp_dir)
            except Exception as cleanup_error:
                print(f"Warning: Failed to cleanup temp directory {temp_dir}: {cleanup_error}")


# --- API Endpoints ---

# Lexer endpoint (using your existing logic)
@app.post("/api/lexer", response_model=LexerResponse)
async def lexical_analysis(request: CodeRequest):
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip():
            return LexerResponse(tokens=[], success=True, errors=[])

        lexer = Lexer(input_code)
        tokens_data, errors = lexer.make_tokens()

        token_responses = [
            TokenResponse(value=tok.value if tok.value is not None else "", type=tok.type, line=tok.line, column=tok.column)
            for tok in tokens_data
        ]
        return LexerResponse(tokens=token_responses, success=not errors, errors=[str(err) for err in errors])
    except Exception as e:
        print(f"Lexical Analysis Server Error: {str(e)}")
        return LexerResponse(tokens=[], success=False, errors=[f"Internal Server Error: {str(e)}"])

# Parser endpoint (using your existing logic)
@app.post("/api/parser", response_model=ParserResponse)
async def syntax_analysis(request: CodeRequest):
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip():
             return ParserResponse(success=True, errors=[], syntaxValid=True)

        lexer = Lexer(input_code)
        tokens_data, lexer_errors = lexer.make_tokens()
        if lexer_errors:
            return ParserResponse(success=False, errors=[f"Lexical Error: {str(err)}" for err in lexer_errors], syntaxValid=False)

        # Prepare tokens for the parser (assuming it uses definitions.token)
        definitions.token.clear()
        for tok in tokens_data:
            definitions.token.append((tok.type, tok.line, tok.column)) # Adjust format if parser expects value

        result, error_messages, syntax_valid = parse() # Your existing parse function
        return ParserResponse(success=syntax_valid, errors=error_messages or [], syntaxValid=syntax_valid)
    except Exception as e:
        print(f"Syntax Analysis Server Error: {str(e)}")
        import traceback; traceback.print_exc()
        return ParserResponse(success=False, errors=[f"Internal Server Error: {str(e)}"], syntaxValid=False)

# Semantic endpoint (using your existing logic)
@app.post("/api/semantic", response_model=SemanticResponse)
async def semantic_analysis_endpoint(request: CodeRequest):
    try:
        input_code = normalize_code(request.code)
        if not input_code.strip():
            return SemanticResponse(success=True, errors=[])

        lexer = Lexer(input_code)
        tokens_data, lexer_errors = lexer.make_tokens()
        if lexer_errors:
            return SemanticResponse(success=False, errors=[f"Lexical Error: {str(err)}" for err in lexer_errors])

        # Prepare tokens for SemanticAnalyzer (type, value, line, column)
        semantic_tokens = [(tok.type, tok.value, tok.line, tok.column) for tok in tokens_data]

        analyzer = SemanticAnalyzer()
        success, errors = analyzer.analyze(semantic_tokens) # Your existing analyze method
        return SemanticResponse(success=success, errors=errors)
    except Exception as e:
        print(f"Semantic Analysis Server Error: {str(e)}")
        import traceback; traceback.print_exc()
        return SemanticResponse(success=False, errors=[f"Internal Server Error: {str(e)}"])


# --- Run Endpoint (Step 1: Validate and Check for Input) ---
@app.post("/api/run/initiate", response_model=InputRequiredResponse | ExecutionResult)
async def initiate_run(request: CodeRequest, response: Response):
    """
    Initiates run: lex, parse, semantic analysis.
    Returns prompts if 'npt' found, else executes directly.
    Returns error if any phase fails.
    """
    input_code = normalize_code(request.code)
    if not input_code.strip():
        return ExecutionResult(success=True, phase="validation", errors=[], output="No code provided.")

    # 1. Lexical Analysis
    lexer = Lexer(input_code)
    tokens_data, lexer_errors = lexer.make_tokens()
    if lexer_errors:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ExecutionResult(success=False, phase="lexical", errors=[str(err) for err in lexer_errors])

    # Prepare tokens for parser and keep detailed tokens for later
    definitions.token.clear()
    parser_ready_tokens = [] # Tokens for parser function (assuming it uses definitions.token)
    detailed_tokens = []   # Tokens for semantic analysis and npt scan (type, value, line, col)
    for tok in tokens_data:
        parser_ready_tokens.append((tok.type, tok.line, tok.column)) # Adjust if parser needs value
        detailed_tokens.append((tok.type, tok.value, tok.line, tok.column))
    definitions.token.extend(parser_ready_tokens) # Load into global if needed by parser

    # 2. Syntax Analysis
    try:
        _, parser_errors, syntax_valid = parse() # Your existing parse function
        if not syntax_valid:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ExecutionResult(success=False, phase="syntax", errors=parser_errors or ["Syntax error detected."])
    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        print(f"Parser Internal Error: {str(e)}\n{traceback.format_exc()}")
        return ExecutionResult(success=False, phase="syntax", errors=[f"Parser Internal Error: {str(e)}"])

    # 3. Semantic Analysis
    symbol_table_for_transpiler = None # Initialize
    analyzer = None # Initialize analyzer instance
    try:
        analyzer = SemanticAnalyzer()
        # Use the detailed tokens list for semantic analysis
        semantic_valid, semantic_errors = analyzer.analyze(detailed_tokens)
        if not semantic_valid:
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ExecutionResult(success=False, phase="semantic", errors=semantic_errors)

        # --- GET CORRECT SYMBOL TABLE SCOPE ---
        # Assuming 'mn' is the main function and variables are local to it
        mn_scope_table = analyzer.function_scopes.get("mn")
        if mn_scope_table is None:
             # Check global scope as a fallback if 'mn' isn't found or vars might be global
             # This depends on your language rules (can mn access globals?)
             print("Warning: 'mn' function scope not found, checking global scope for transpiler.")
             mn_scope_table = analyzer.global_scope # Fallback to global
             if mn_scope_table is None: # If even global is missing
                 print("Error: Neither 'mn' function scope nor global scope found after semantic analysis.")
                 response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                 return ExecutionResult(success=False, phase="semantic", errors=["Internal Server Error: Cannot find valid symbol table scope."])

        symbol_table_for_transpiler = mn_scope_table # Use the found scope
        # --- END SCOPE HANDLING ---

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        import traceback
        print(f"Semantic Analysis Internal Error: {str(e)}\n{traceback.format_exc()}")
        return ExecutionResult(success=False, phase="semantic", errors=[f"Semantic Analyzer Internal Error: {str(e)}"])

    # 4. Scan for 'npt' calls using the detailed token list
    required_prompts = scan_for_npt(detailed_tokens)

    # 5. Decide whether to request input or execute directly
    if required_prompts:
        # Input is required, return prompts to the frontend
        print(f"Input required: {required_prompts}") # Log prompts being sent
        return InputRequiredResponse(prompts=required_prompts)
    else:
        # No input needed, proceed directly to transpilation and execution
        print("No input required, proceeding to direct execution.")
        try:
            # Transpile using the detailed tokens and the determined symbol table scope
            transpiled_code = transpile_from_tokens(
                detailed_tokens,
                symbol_table_for_transpiler, # Pass the correct scope
                user_inputs={} # Empty dict as no input needed
            )
            # Check for transpiler errors indicated by comments
            if transpiled_code.startswith("// TRANSPILER ERROR") or transpiled_code.startswith("// UNEXPECTED"):
                 print(f"Transpilation failed: {transpiled_code}")
                 response.status_code = status.HTTP_400_BAD_REQUEST
                 # Extract error message if possible
                 error_msg = transpiled_code.split(":", 1)[-1].strip() if ":" in transpiled_code else transpiled_code
                 return ExecutionResult(success=False, phase="transpilation", errors=[error_msg])
        except Exception as e:
             response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
             import traceback
             print(f"Transpiler Internal Error: {str(e)}\n{traceback.format_exc()}")
             return ExecutionResult(success=False, phase="transpilation", errors=[f"Transpiler Internal Error: {str(e)}"])

        # 6. Compile and Run C code
        success, output, error_msg = compile_and_run_c(transpiled_code)

        if not success:
            print(f"C Compilation/Execution failed: {error_msg}")
            response.status_code = status.HTTP_400_BAD_REQUEST # Treat C errors as bad request for now
            return ExecutionResult(success=False, phase="compilation/execution", errors=[error_msg], transpiledCode=transpiled_code, output=output)
        else:
            print(f"Direct execution successful. Output:\n{output}\nWarnings:\n{error_msg}")
            return ExecutionResult(success=True, phase="execution", transpiledCode=transpiled_code, output=output, errors=[error_msg] if error_msg else [])


# --- Run Endpoint (Step 2: Execute with Provided Inputs) ---
@app.post("/api/run/execute", response_model=ExecutionResult)
async def execute_run_with_input(request: RunWithInputRequest, response: Response):
    """
    Performs final run after inputs are collected.
    Transpiles with inputs, compiles, and runs.
    """
    input_code = normalize_code(request.code)
    user_inputs = request.inputs
    print(f"Executing run with inputs: {user_inputs}")

    if not input_code.strip():
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ExecutionResult(success=False, phase="validation", errors=["No code provided."])

    # Re-run lexer to get tokens for transpiler
    lexer = Lexer(input_code)
    tokens_data, lexer_errors = lexer.make_tokens()
    if lexer_errors:
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ExecutionResult(success=False, phase="lexical", errors=[f"Error during re-lexing: {str(err)}" for err in lexer_errors])

    # Re-run semantic analysis to get the symbol table (necessary for type info in transpiler)
    detailed_tokens = [(tok.type, tok.value, tok.line, tok.column) for tok in tokens_data]
    symbol_table_for_transpiler = None
    analyzer = None
    try:
        analyzer = SemanticAnalyzer()
        semantic_valid, semantic_errors = analyzer.analyze(detailed_tokens)
        if not semantic_valid:
            # This really shouldn't happen if initiate_run passed
            response.status_code = status.HTTP_400_BAD_REQUEST
            return ExecutionResult(success=False, phase="semantic", errors=[f"Error during re-analysis: {err}" for err in semantic_errors])

        # --- GET CORRECT SYMBOL TABLE SCOPE ---
        mn_scope_table = analyzer.function_scopes.get("mn")
        if mn_scope_table is None:
             print("Warning: 'mn' function scope not found during re-analysis, checking global scope.")
             mn_scope_table = analyzer.global_scope
             if mn_scope_table is None:
                 print("Error: Neither 'mn' function scope nor global scope found during re-analysis.")
                 response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
                 return ExecutionResult(success=False, phase="semantic", errors=["Internal Server Error: Cannot find valid symbol table scope during re-analysis."])

        symbol_table_for_transpiler = mn_scope_table
        # --- END SCOPE HANDLING ---

    except Exception as e:
        response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
        import traceback
        print(f"Semantic Analyzer Internal Error during re-analysis: {str(e)}\n{traceback.format_exc()}")
        return ExecutionResult(success=False, phase="semantic", errors=[f"Semantic Analyzer Internal Error during re-analysis: {str(e)}"])

    # 1. Transpile with User Inputs
    try:
        # Pass the detailed tokens, correct scope, and user inputs
        transpiled_code = transpile_from_tokens(
            detailed_tokens,
            symbol_table_for_transpiler, # Pass the mn_scope_table
            user_inputs
        )
        # Check for transpiler errors
        if transpiled_code.startswith("// TRANSPILER ERROR") or transpiled_code.startswith("// UNEXPECTED"):
             print(f"Transpilation failed: {transpiled_code}")
             response.status_code = status.HTTP_400_BAD_REQUEST
             error_msg = transpiled_code.split(":", 1)[-1].strip() if ":" in transpiled_code else transpiled_code
             return ExecutionResult(success=False, phase="transpilation", errors=[error_msg])
    except Exception as e:
         response.status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
         import traceback
         print(f"Transpiler Internal Error: {str(e)}\n{traceback.format_exc()}")
         return ExecutionResult(success=False, phase="transpilation", errors=[f"Transpiler Internal Error: {str(e)}"])

    # 2. Compile and Run C code
    success, output, error_msg = compile_and_run_c(transpiled_code)

    if not success:
        print(f"C Compilation/Execution failed: {error_msg}")
        response.status_code = status.HTTP_400_BAD_REQUEST
        return ExecutionResult(success=False, phase="compilation/execution", errors=[error_msg], transpiledCode=transpiled_code, output=output)
    else:
        print(f"Execution with input successful. Output:\n{output}\nWarnings:\n{error_msg}")
        return ExecutionResult(success=True, phase="execution", transpiledCode=transpiled_code, output=output, errors=[error_msg] if error_msg else [])


# Health check endpoint (keep as is)
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Conso Language Server is running"}

# --- Run Server ---
if __name__ == "__main__":
    # Recommended: run via `uvicorn server:app --reload --host 0.0.0.0 --port 5000`
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)

