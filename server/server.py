from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any
import uvicorn
import copy
import re

# Import your existing modules
from lexer import Lexer
from parser import parse, ParserError
from semantic import SemanticAnalyzer
import definitions

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

# Run the server
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)