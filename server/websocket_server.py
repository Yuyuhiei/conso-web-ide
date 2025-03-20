from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from typing import List, Dict, Any
import json
import asyncio
import copy

# Import your existing modules
from lexer import Lexer
from parser import parse
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

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        while True:
            data = await websocket.receive_text()
            
            # Parse the received data
            try:
                request_data = json.loads(data)
                code = request_data.get("code", "")
                
                # If there's code to analyze, perform lexical and syntax analysis
                if code:
                    # Run the lexer
                    lexer = Lexer(code)
                    tokens, lexer_errors = lexer.make_tokens()
                    
                    # Convert tokens to a format that can be JSON serialized
                    serialized_tokens = [
                        {
                            "value": token.value if token.value is not None else "",
                            "type": token.type,
                            "line": token.line,
                            "column": token.column
                        } for token in tokens
                    ]
                    
                    # Prepare lexer response
                    lexer_response = {
                        "type": "lexer_result",
                        "tokens": serialized_tokens,
                        "success": len(lexer_errors) == 0,
                        "errors": [str(err) for err in lexer_errors]
                    }
                    
                    # Send lexer results
                    await manager.send_personal_message(json.dumps(lexer_response), websocket)
                    
                    # If no lexer errors, run the parser
                    if not lexer_errors:
                        try:
                            # Clear the global token list
                            definitions.token.clear()
                            
                            # Fill the global token list with the new tokens
                            for token in tokens:
                                definitions.token.append((token.type, token.line, token.column))
                            
                            # Run parser using existing parse function
                            result, error_messages, syntax_valid = parse()
                            
                            # Prepare parser response
                            parser_response = {
                                "type": "parser_result",
                                "success": syntax_valid,
                                "errors": error_messages if error_messages else [],
                                "syntaxValid": syntax_valid
                            }
                            
                            # Send parser results
                            await manager.send_personal_message(json.dumps(parser_response), websocket)
                        except Exception as e:
                            parser_error = {
                                "type": "parser_result",
                                "success": False,
                                "errors": [f"Parser error: {str(e)}"],
                                "syntaxValid": False
                            }
                            await manager.send_personal_message(json.dumps(parser_error), websocket)
            except json.JSONDecodeError:
                error_response = {
                    "type": "error",
                    "message": "Invalid JSON data received"
                }
                await manager.send_personal_message(json.dumps(error_response), websocket)
            except Exception as e:
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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "Conso WebSocket Server is running"}

# Run the server
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("websocket_server:app", host="0.0.0.0", port=5001, reload=True)