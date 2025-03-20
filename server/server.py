from fastapi import FastAPI, HTTPException, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import uvicorn
import sys
import copy

# Import your existing modules
from lexer import Lexer, Token
from parser import parse
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

# Lexical analysis endpoint
@app.post("/api/lexer", response_model=LexerResponse)
async def lexical_analysis(request: CodeRequest):
    try:
        # Create a lexer instance with the provided code
        lexer = Lexer(request.code)
        tokens, errors = lexer.make_tokens()
        
        # Clear the global token list used by the parser
        definitions.token.clear()
        
        # Fill the global token list with the new tokens
        for token in tokens:
            definitions.token.append((token.type, token.line, token.column))
        
        # Convert tokens to response format
        token_responses = [
            TokenResponse(
                value=token.value if token.value is not None else "",
                type=token.type,
                line=token.line,
                column=token.column
            ) for token in tokens
        ]
        
        # Return the response
        return LexerResponse(
            tokens=token_responses,
            success=len(errors) == 0,
            errors=[str(err) for err in errors]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Lexer error: {str(e)}")

# Syntax analysis endpoint
@app.post("/api/parser", response_model=ParserResponse)
async def syntax_analysis(request: CodeRequest):
    try:
        # First run lexer to get tokens
        lexer = Lexer(request.code)
        tokens, lexer_errors = lexer.make_tokens()
        
        if lexer_errors:
            return ParserResponse(
                success=False,
                errors=[str(err) for err in lexer_errors],
                syntaxValid=False
            )
        
        # Clear the global token list
        definitions.token.clear()
        
        # Fill the global token list with the new tokens
        for token in tokens:
            definitions.token.append((token.type, token.line, token.column))
        
        # Run parser using your existing parse function
        result, error_messages, syntax_valid = parse()
        
        return ParserResponse(
            success=syntax_valid,
            errors=error_messages if error_messages else [],
            syntaxValid=syntax_valid
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Parser error: {str(e)}")

# Semantic analysis endpoint
@app.post("/api/semantic", response_model=SemanticResponse)
async def semantic_analysis(request: CodeRequest):
    try:
        # First run lexer to get tokens
        lexer = Lexer(request.code)
        tokens, lexer_errors = lexer.make_tokens()
        
        if lexer_errors:
            return SemanticResponse(
                success=False,
                errors=[str(err) for err in lexer_errors]
            )
        
        # Create semantic tokens in the format expected by your analyzer
        semantic_tokens = [(token.type, token.value, token.line, token.column) for token in tokens]
        
        # Save a copy of the current token list for parser
        original_tokens = copy.deepcopy(definitions.token)
        
        # Run semantic analysis
        analyzer = SemanticAnalyzer()
        success, errors = analyzer.analyze(semantic_tokens)
        
        # Restore the original tokens for other operations
        definitions.token.clear()
        definitions.token.extend(original_tokens)
        
        return SemanticResponse(
            success=success,
            errors=errors
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Semantic analysis error: {str(e)}")

# Health check endpoint
@app.get("/api/health")
async def health_check():
    return {"status": "healthy", "message": "Conso Language Server is running"}

# Run the server
if __name__ == "__main__":
    uvicorn.run("server:app", host="0.0.0.0", port=5000, reload=True)