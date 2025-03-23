from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List
import json
import re

# Import your existing modules
from lexer import Lexer
from parser import parse, ParserError
import definitions

# Class to manage WebSocket connections
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        try:
            await websocket.send_text(message)
        except Exception as e:
            print(f"Error sending message: {str(e)}")
            self.disconnect(websocket)

# Create FastAPI app and WebSocket manager
app = FastAPI()
manager = ConnectionManager()

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

# WebSocket connection handler
@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            
            # Process received data
            try:
                request_data = json.loads(data)
                code = request_data.get("code", "")
                
                # Skip empty code
                if not code:
                    continue
                
                # Normalize code and process
                normalized_code = normalize_code(code)
                print(f"WebSocket normalized code:\n{normalized_code}")
                
                await process_code(normalized_code, websocket)
                
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON data received"
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)
            except Exception as e:
                print(f"Error processing request: {str(e)}")
                error_response = {
                    "type": "error",
                    "message": f"Error processing request: {str(e)}"
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {str(e)}")
        manager.disconnect(websocket)

# Process code - just like the run_lexer and run_parser functions in your GUI
async def process_code(code: str, websocket: WebSocket):
    try:
        # Clear previous tokens
        definitions.token.clear()
        
        # Create a lexer instance with the provided code
        lexer = Lexer(code)
        tokens, errors = lexer.make_tokens()
        
        # Store tokens for parser use
        for tok in tokens:
            definitions.token.append((tok.type, tok.line, tok.column))
        
        # Convert tokens for frontend display
        serialized_tokens = [
            {
                "value": tok.value if tok.value is not None else "",
                "type": tok.type,
                "line": tok.line,
                "column": tok.column
            } for tok in tokens
        ]
        
        # Send lexer results
        lexer_success = len(errors) == 0
        lexer_response = {
            "type": "lexer_result",
            "tokens": serialized_tokens,
            "success": lexer_success,
            "errors": [str(err) for err in errors]
        }
        await manager.send_personal_message(json.dumps(lexer_response), websocket)
        
        # If lexer succeeded, run parser
        if lexer_success:
            result, error_messages, syntax_valid = parse()
            
            # Send parser results
            parser_response = {
                "type": "parser_result",
                "success": syntax_valid,
                "errors": error_messages if error_messages else [],
                "syntaxValid": syntax_valid
            }
            await manager.send_personal_message(json.dumps(parser_response), websocket)
            
    except Exception as e:
        print(f"Processing error: {str(e)}")
        error_response = {
            "type": "error",
            "message": f"Processing error: {str(e)}"
        }
        await manager.send_personal_message(json.dumps(error_response), websocket)

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Conso WebSocket Server is running"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("websocket_server:app", host="0.0.0.0", port=5001, reload=True)