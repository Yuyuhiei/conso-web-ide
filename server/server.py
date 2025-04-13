from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import copy
import re

from lexer import Lexer
from parser import parse, ParserError
from semantic import SemanticAnalyzer
import definitions

import os
import tempfile
import subprocess
from transpiler import transpile, TranspilerError

app = FastAPI(title="Conso Language Server")

# Add CORS middleware to allow cross-origin requests from your React app
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Define request and response models
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

def normalize_code(code: str) -> str:
    """
    Normalize code to handle newlines and indentation in a way that
    satisfies the lexer's delimiter requirements
    """
    # Handle specific case where opening brace is followed by newline and indentation
    # Replace "{\n    " with "{ "
    code = re.sub(r'{\s*\n\s+', '{ ', code)
    
    # Remove spaces between mn and (
    code = re.sub(r'mn\s+\(', 'mn(', code)
    
    # Remove extra whitespace at end of lines
    code = re.sub(r'\s+\n', '\n', code)
    
    # Ensure consistent line endings
    code = code.replace('\r\n', '\n')
    
    return code

# Lexical analysis endpoint
@app.post("/api/lexer", response_model=LexerResponse)
async def lexical_analysis(request: CodeRequest):
    try:
        # Clear the existing tokens
        definitions.token.clear()
        
        # Get the input code and normalize it
        input_code = normalize_code(request.code)
        
        print(f"Normalized code:\n{input_code}")
        
        if not input_code:
            return LexerResponse(
                tokens=[],
                success=False,
                errors=["Empty input"]
            )
            
        # Create a lexer instance with the provided code
        lexer = Lexer(input_code)
        tokens, errors = lexer.make_tokens()
        
        # Store tokens in global token list
        for tok in tokens:
            definitions.token.append((tok.type, tok.line, tok.column))
        
        # Convert tokens to response format
        token_responses = [
            TokenResponse(
                value=tok.value if tok.value is not None else "",
                type=tok.type,
                line=tok.line,
                column=tok.column
            ) for tok in tokens
        ]
        
        # Return response
        return LexerResponse(
            tokens=token_responses,
            success=len(errors) == 0,
            errors=[str(err) for err in errors]
        )
    except Exception as e:
        print(f"Lexical Analysis Error: {str(e)}")
        return LexerResponse(
            tokens=[],
            success=False,
            errors=[f"Lexical Analysis Error: {str(e)}"]
        )

# Syntax analysis endpoint
@app.post("/api/parser", response_model=ParserResponse)
async def syntax_analysis(request: CodeRequest):
    try:
        # Get normalized code
        input_code = normalize_code(request.code)
        
        # First run lexer to get tokens
        lexer = Lexer(input_code)
        tokens, errors = lexer.make_tokens()
        
        if errors:
            return ParserResponse(
                success=False,
                errors=[str(err) for err in errors],
                syntaxValid=False
            )
        
        # Clear and populate the global token list
        definitions.token.clear()
        for tok in tokens:
            definitions.token.append((tok.type, tok.line, tok.column))
        
        # Run parser using your existing parse function
        result, error_messages, syntax_valid = parse()
        
        return ParserResponse(
            success=syntax_valid,
            errors=error_messages if error_messages else [],
            syntaxValid=syntax_valid
        )
    except ParserError as e:
        print(f"Parser Error: {str(e)}")
        return ParserResponse(
            success=False,
            errors=[str(e)],
            syntaxValid=False
        )
    except Exception as e:
        print(f"Unexpected error: {str(e)}")
        return ParserResponse(
            success=False,
            errors=[f"Syntax Analysis Error: {str(e)}"],
            syntaxValid=False
        )

# Semantic analysis endpoint
@app.post("/api/semantic", response_model=SemanticResponse)
async def semantic_analysis(request: CodeRequest):
    try:
        # Get normalized code
        input_code = normalize_code(request.code)
        
        # Save the original tokens for later restoration
        original_tokens = copy.deepcopy(definitions.token)
        
        # Run the lexer to get tokens
        lexer = Lexer(input_code)
        tokens, lexer_errors = lexer.make_tokens()
        
        if lexer_errors:
            return SemanticResponse(
                success=False,
                errors=[f"Lexical Error: {str(err)}" for err in lexer_errors]
            )
        
        # Create semantic tokens in the expected format
        semantic_tokens = [(tok.type, tok.value, tok.line, tok.column) for tok in tokens]
        
        # Create analyzer instance and run analysis
        analyzer = SemanticAnalyzer()
        success, errors = analyzer.analyze(semantic_tokens)
        
        # Restore the original tokens
        definitions.token.clear()
        definitions.token.extend(original_tokens)
        
        return SemanticResponse(
            success=success,
            errors=errors
        )
    except Exception as e:
        print(f"Semantic Analysis Error: {str(e)}")
        return SemanticResponse(
            success=False,
            errors=[f"Semantic Analysis Error: {str(e)}"]
        )

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Conso Language Server is running"}

# Run Conso code endpoint with improved error handling
@app.post("/api/run")
async def run_code(request: CodeRequest):
    """Run Conso code through transpilation, compilation, and execution."""
    import tempfile
    import os
    import sys
    import subprocess
    
    try:
        # Get normalized code
        input_code = normalize_code(request.code)
        
        # First run lexical analysis to get tokens
        lexer = Lexer(input_code)
        tokens, lexer_errors = lexer.make_tokens()
        
        if lexer_errors:
            return {
                "success": False,
                "phase": "lexical",
                "errors": [str(err) for err in lexer_errors],
                "transpiledCode": None,
                "output": None
            }
        
        # Clear and populate the global token list
        definitions.token.clear()
        for tok in tokens:
            definitions.token.append((tok.type, tok.line, tok.column))
        
        # Run parser
        result, parser_errors, syntax_valid = parse()
        
        if not syntax_valid:
            return {
                "success": False,
                "phase": "syntax",
                "errors": parser_errors,
                "transpiledCode": None,
                "output": None
            }
        
        # Create semantic tokens in the expected format
        semantic_tokens = [(tok.type, tok.value, tok.line, tok.column) for tok in tokens]
        
        # Create analyzer instance and run analysis
        analyzer = SemanticAnalyzer()
        semantic_valid, semantic_errors = analyzer.analyze(semantic_tokens)
        
        if not semantic_valid:
            return {
                "success": False,
                "phase": "semantic",
                "errors": semantic_errors,
                "transpiledCode": None,
                "output": None
            }
        
        # If all validations pass, transpile the code to C
        try:
            # Import the transpiler here to avoid circular imports
            from transpiler import transpile
            transpiled_code = transpile(input_code)
        except Exception as e:
            import traceback
            print(f"Transpilation error: {str(e)}")
            print(traceback.format_exc())
            return {
                "success": False,
                "phase": "transpilation",
                "errors": [f"Transpilation error: {str(e)}"],
                "transpiledCode": None,
                "output": None
            }
        
        # Compile and run the C code
        temp_dir = None
        
        try:
            # Create a temporary directory for our files
            temp_dir = tempfile.mkdtemp(prefix="conso_")
            c_file = os.path.join(temp_dir, "program.c")
            
            # Write C code to file
            with open(c_file, 'w') as f:
                f.write(transpiled_code)
            
            # Determine executable name based on platform
            if sys.platform == 'win32':
                executable = os.path.join(temp_dir, "program.exe")
            else:
                executable = os.path.join(temp_dir, "program")
                
            # Compile the C code
            compile_cmd = ['gcc', c_file, '-o', executable]
            compile_result = subprocess.run(
                compile_cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if compile_result.returncode != 0:
                return {
                    "success": False,
                    "phase": "compilation",
                    "errors": [compile_result.stderr],
                    "transpiledCode": transpiled_code,
                    "output": None
                }
            
            # Run the compiled executable
            run_result = subprocess.run(
                [executable],
                capture_output=True,
                text=True,
                timeout=5  # 5-second timeout to prevent infinite loops
            )
            
            # Log the output for debugging
            print(f"Program stdout: '{run_result.stdout}'")
            print(f"Program stderr: '{run_result.stderr}'")
            
            # Check for errors during execution
            if run_result.returncode != 0:
                return {
                    "success": False,
                    "phase": "execution",
                    "errors": [run_result.stderr if run_result.stderr else "Program exited with non-zero status"],
                    "transpiledCode": transpiled_code,
                    "output": None
                }
            
            # Success case
            return {
                "success": True,
                "phase": "execution",
                "errors": [],
                "transpiledCode": transpiled_code,
                "output": run_result.stdout
            }
        
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "phase": "execution",
                "errors": ["Execution timed out. Your program may have an infinite loop."],
                "transpiledCode": transpiled_code,
                "output": None
            }
        except Exception as e:
            import traceback
            print(f"Execution error: {str(e)}")
            print(traceback.format_exc())
            return {
                "success": False,
                "phase": "execution",
                "errors": [f"Execution error: {str(e)}"],
                "transpiledCode": transpiled_code,
                "output": None
            }
        finally:
            # Clean up temporary files
            try:
                if temp_dir and os.path.exists(temp_dir):
                    import shutil
                    shutil.rmtree(temp_dir)
            except Exception as e:
                print(f"Cleanup error: {str(e)}")
            
    except Exception as e:
        import traceback
        print(f"Run error: {str(e)}")
        print(traceback.format_exc())
        print(f"API Response: success=True, output={repr(run_result.stdout)}")
        return {
            "success": False,
            "phase": "unknown",
            "errors": [f"Unexpected error: {str(e)}"],
            "transpiledCode": None,
            "output": None
        }
    
@app.post("/api/debug-run")
async def debug_run(request: CodeRequest):
    """Debug run endpoint that captures detailed information about the execution process."""
    import tempfile
    import os
    import sys
    import subprocess
    
    result = {
        "success": False,
        "transpiled_code": None,
        "executable_path": None,
        "compilation_output": None,
        "execution_output": None,
        "execution_error": None,
        "steps": []
    }
    
    # Step 1: Transpile the code
    result["steps"].append({"step": "transpile", "status": "starting"})
    try:
        from transpiler import transpile
        input_code = normalize_code(request.code)
        transpiled_code = transpile(input_code)
        result["transpiled_code"] = transpiled_code
        result["steps"].append({"step": "transpile", "status": "success"})
    except Exception as e:
        import traceback
        result["steps"].append({
            "step": "transpile", 
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return result
    
    # Step 2: Create a C file
    temp_dir = None
    c_file = None
    
    try:
        # Create a temp directory
        temp_dir = tempfile.mkdtemp(prefix="conso_debug_")
        c_file = os.path.join(temp_dir, "debug_program.c")
        
        # Write the C code to file
        with open(c_file, "w") as f:
            f.write(transpiled_code)
        
        result["steps"].append({
            "step": "create_c_file", 
            "status": "success", 
            "file": c_file,
            "exists": os.path.exists(c_file),
            "size": os.path.getsize(c_file) if os.path.exists(c_file) else None
        })
    except Exception as e:
        import traceback
        result["steps"].append({
            "step": "create_c_file", 
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return result
    
    # Step 3: Compile the C code
    executable = None
    
    try:
        # Determine the executable name based on platform
        if sys.platform == "win32":
            executable = os.path.join(temp_dir, "debug_program.exe")
        else:
            executable = os.path.join(temp_dir, "debug_program")
            
        result["executable_path"] = executable
        
        # Compile command
        compile_cmd = ["gcc", c_file, "-o", executable]
        
        # Run the compilation
        compile_process = subprocess.run(
            compile_cmd,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        result["compilation_output"] = {
            "command": " ".join(compile_cmd),
            "returncode": compile_process.returncode,
            "stdout": compile_process.stdout,
            "stderr": compile_process.stderr
        }
        
        if compile_process.returncode != 0:
            result["steps"].append({
                "step": "compile", 
                "status": "error", 
                "returncode": compile_process.returncode,
                "stderr": compile_process.stderr
            })
            return result
            
        result["steps"].append({
            "step": "compile", 
            "status": "success", 
            "executable": {
                "path": executable,
                "exists": os.path.exists(executable),
                "size": os.path.getsize(executable) if os.path.exists(executable) else None
            }
        })
    except Exception as e:
        import traceback
        result["steps"].append({
            "step": "compile", 
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        })
        return result
    
    # Step 4: Run the program
    try:
        # Run the executable
        run_cmd = [executable]
        
        run_process = subprocess.run(
            run_cmd,
            capture_output=True,
            text=True,
            timeout=5
        )
        
        result["execution_output"] = run_process.stdout
        result["execution_error"] = run_process.stderr
        
        result["steps"].append({
            "step": "execute", 
            "status": "success" if run_process.returncode == 0 else "error", 
            "returncode": run_process.returncode,
            "stdout": run_process.stdout,
            "stderr": run_process.stderr,
            "stdout_bytes": [ord(c) for c in run_process.stdout[:20]] if run_process.stdout else None,
            "stderr_bytes": [ord(c) for c in run_process.stderr[:20]] if run_process.stderr else None
        })
        
        # Mark success if execution completed without errors
        if run_process.returncode == 0:
            result["success"] = True
    except Exception as e:
        import traceback
        result["steps"].append({
            "step": "execute", 
            "status": "error", 
            "error": str(e),
            "traceback": traceback.format_exc()
        })
    finally:
        # Clean up temporary files
        try:
            if temp_dir and os.path.exists(temp_dir):
                import shutil
                shutil.rmtree(temp_dir)
                result["steps"].append({"step": "cleanup", "status": "success"})
        except Exception as e:
            result["steps"].append({
                "step": "cleanup", 
                "status": "error", 
                "error": str(e)
            })
    
    return result

# Run the server
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)
