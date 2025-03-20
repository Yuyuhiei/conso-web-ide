# Conso Web IDE

A web-based IDE for the Conso programming language with real-time lexical, syntax, and semantic analysis.

## Project Overview

This project provides a modern web-based development environment for the Conso programming language, featuring:

- Monaco Editor with custom syntax highlighting for Conso
- Real-time lexical analysis with token visualization
- Syntax validation with immediate feedback
- Semantic analysis capabilities
- File saving and loading functionality

## Setup Instructions

### Prerequisites

- Node.js 14+ and npm
- Python 3.7+
- Your existing Conso language implementation files

### Backend Setup

1. Create a Python virtual environment:

```bash
# Navigate to server directory
cd server

# Create virtual environment
python -m venv venv

# Activate the virtual environment
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

2. Install the required Python packages:

```bash
pip install fastapi uvicorn websockets python-multipart
```

3. Make sure you have the following Conso language files in your server directory:
   - lexer.py
   - parser.py
   - definitions.py
   - semantic.py
   - server.py (the new FastAPI server)
   - websocket_server.py (the new WebSocket server)

4. Start the REST API server:

```bash
# From the server directory
uvicorn server:app --reload --port 5000
```

5. Start the WebSocket server (in a new terminal window):

```bash
# From the server directory with venv activated
uvicorn websocket_server:app --reload --port 5001
```

### Frontend Setup

Make sure your React project is set up with the required services and components:

1. Place the API and WebSocket service files in your `src/services` directory:
   - api.js
   - websocketService.js

2. Place the Conso language configuration file in your `src/utils` directory:
   - consoLanguageConfig.js

3. Start your React development server:

```bash
# From the project root
npm start
```

## Usage

1. The IDE will automatically connect to the backend services on startup
2. Type or load Conso code in the editor
3. Real-time lexical and syntax analysis will appear in the token table and terminal
4. Click "Semantic Analysis" to perform a semantic analysis when syntax is valid
5. Use the Save/Load buttons to manage your Conso files

## Project Structure

```
conso-web-ide/               # Root project folder
├── src/                     # React frontend
│   ├── components/          # React components
│   │   ├── Editor.js        # Monaco editor component
│   │   ├── Terminal.js      # Output/error display
│   │   └── TokenTable.js    # Lexical analysis display
│   ├── services/            # Backend communication
│   │   ├── api.js           # REST API client
│   │   └── websocketService.js # WebSocket client
│   ├── utils/               # Utilities
│   │   └── consoLanguageConfig.js # Monaco editor language config
│   └── App.js               # Main application component
├── server/                  # Python backend
│   ├── lexer.py             # Conso lexer
│   ├── parser.py            # Conso parser
│   ├── definitions.py       # Shared definitions
│   ├── semantic.py          # Semantic analyzer 
│   ├── server.py            # FastAPI REST server
│   └── websocket_server.py  # WebSocket server
└── README.md                # This file
```

## Troubleshooting

- **WebSocket Connection Issues**: Ensure both the API server (port 5000) and WebSocket server (port 5001) are running
- **CORS Errors**: If you encounter CORS issues, verify the CORS middleware in the server.py file is properly configured
- **Module Import Errors**: Make sure all Python files are in the correct server directory and the virtual environment is activated
- **Token Parsing Issues**: If you encounter issues with the parser not receiving the correct tokens, check that the global token list in definitions.py is being properly updated
- **Monaco Editor Not Loading**: Ensure the Monaco Editor is properly installed with `npm install @monaco-editor/react`

## Working with the Conso Language

### Basic Syntax

The Conso language has the following basic elements:

```
# Variable declarations
nt myNumber = 5;
dbl myDecimal = 3.14;
strng myString = "Hello Conso";
bln myBoolean = tr;
chr myChar = 'A';

# Control structures
f (myBoolean) {
    prnt("Condition is true");
}

fr (nt i = 0; i < 10; i++) {
    prnt(i);
}

# Functions
fnctn vd greet() {
    prnt("Hello World");
}

# Main function
mn() {
    greet();
}
```

### Code Examples

The IDE allows you to write and test Conso code with real-time feedback. Here are some examples to try:

1. **Hello World**:
```
mn() {
    prnt("Hello, Conso!");
}
```

2. **Fibonacci Sequence**:
```
fnctn nt fibonacci(nt n) {
    f (n <= 1) {
        rtrn n;
    }
    rtrn fibonacci(n-1) + fibonacci(n-2);
}

mn() {
    fr (nt i = 0; i < 10; i++) {
        prnt(fibonacci(i));
    }
}
```

## Extending the IDE

You can extend this web IDE with additional features:

1. **Debugging Tools**: Add breakpoints, step execution, and variable inspection
2. **Project Management**: Implement multi-file projects and directory structure
3. **Code Formatting**: Add automatic code formatting for Conso
4. **Theming**: Implement light/dark themes and customizable editor options
5. **Code Export**: Add options to export code to different formats

## Contributing

Contributions to the Conso Web IDE are welcome! Please feel free to submit issues or pull requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.