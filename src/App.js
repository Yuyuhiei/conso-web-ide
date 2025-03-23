import React, { useState, useEffect } from 'react';
import CodeEditor from './components/NewEditor';
import Terminal from './components/Terminal';
import TokenTable from './components/TokenTable';
import { analyzeSemantics } from './services/api';
import websocketService from './services/websocketService';
import './App.css';

const App = () => {
  const [code, setCode] = useState('');
  const [fileName, setFileName] = useState('Untitled.cns');
  const [output, setOutput] = useState('Welcome to Conso Web IDE');
  const [tokens, setTokens] = useState([]);
  const [semanticEnabled, setSemanticEnabled] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [codeChanged, setCodeChanged] = useState(false);
  
  // Connect to WebSocket when the component mounts
  useEffect(() => {
    // Setup WebSocket event listeners
    websocketService
      .on('open', () => {
        setOutput(prev => `${prev}\nConnected to real-time analysis server`);
      })
      .on('lexerResult', (data) => {
        setTokens(data.tokens);
        
        if (data.success) {
          setOutput(prev => `${prev}\nLexer run successfully!`);
        } else {
          setSemanticEnabled(false);
          const errorMessages = data.errors.map(err => `Lexical Error: ${err}`).join('\n');
          setOutput(prev => `${prev}\n${errorMessages}`);
        }
      })
      .on('parserResult', (data) => {
        setSemanticEnabled(data.syntaxValid);
        
        if (data.success) {
          setOutput(prev => `${prev}\nParser run successfully!`);
        } else {
          const errorMessages = data.errors.join('\n');
          setOutput(prev => `${prev}\nSyntax errors:\n${errorMessages}`);
        }
      })
      .on('error', (data) => {
        setOutput(prev => `${prev}\nError: ${data.message}`);
      })
      .on('close', () => {
        setOutput(prev => `${prev}\nDisconnected from real-time analysis server`);
      });
    
    // Connect to WebSocket server
    websocketService.connect();
    
    // Cleanup on component unmount
    return () => {
      websocketService.disconnect();
    };
  }, []);

  // Function for real-time analysis
  const handleCodeChange = (newValue) => {
    setCode(newValue);
    setCodeChanged(true); // Mark that code has changed to clear semantic analysis messages
    
    // Only run the analyzer if we're not already analyzing
    // This prevents too many requests
    if (!analyzing) {
      setAnalyzing(true);
      const debounceTimer = setTimeout(() => {
        // Send code to WebSocket server for real-time analysis
        websocketService.sendCode(newValue);
        setAnalyzing(false);
      }, 500); // 500ms debounce
      
      return () => clearTimeout(debounceTimer);
    }
  };

  // Run semantic analysis
  const runSemanticAnalysis = async () => {
    try {
      setCodeChanged(false); // Reset the code changed flag when running semantic analysis
      setOutput(prev => `${prev}\nRunning semantic analysis...`);
      const response = await analyzeSemantics(code);
      
      if (response.success) {
        setOutput(prev => `${prev}\nSemantic analysis completed successfully!`);
      } else {
        setOutput(prev => `${prev}\nSemantic errors found:\n${response.errors.map(err => `  - ${err}`).join('\n')}`);
      }
    } catch (error) {
      setOutput(prev => `${prev}\nSemantic Analysis Error: ${error.message}`);
    }
  };

  // Handle file save
  const handleSave = () => {
    const blob = new Blob([code], { type: 'text/plain' });
    const link = document.createElement('a');
    link.download = fileName;
    link.href = window.URL.createObjectURL(blob);
    link.click();
    setOutput(prev => `${prev}\nFile saved: ${fileName}`);
  };

  // Handle file open
  const handleOpen = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        setCode(e.target.result);
        setFileName(file.name);
        setOutput(prev => `${prev}\nFile loaded: ${file.name}`);
        
        // Trigger analysis after loading the file
        websocketService.sendCode(e.target.result);
      };
      reader.readAsText(file);
    }
  };

  // Clear the terminal
  const clearTerminal = () => {
    setOutput('Terminal cleared');
  };

  // Handle file name change
  const handleFileNameChange = (e) => {
    setFileName(e.target.value);
  };

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header className="app-header">
        <div className="app-title">Conso Web IDE</div>
        <div className="file-name-container">
          <input 
            type="text" 
            value={fileName} 
            onChange={handleFileNameChange} 
            className="file-name-input"
          />
        </div>
        <div className="app-controls">
          <button onClick={handleSave}>Save</button>
          <input 
            type="file" 
            id="file-open" 
            accept=".cns" 
            style={{ display: 'none' }} 
            onChange={handleOpen} 
          />
          <button onClick={() => document.getElementById('file-open').click()}>
            Open
          </button>
          <button 
            onClick={runSemanticAnalysis} 
            disabled={!semanticEnabled}
            className={!semanticEnabled ? "disabled-button" : ""}
          >
            Semantic Analysis
          </button>
          <button onClick={clearTerminal}>Clear Terminal</button>
        </div>
      </header>
      
      <div className="main-content" style={{ 
        position: 'relative', 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Editor container */}
        <div className="editor-container" style={{ 
          position: 'relative', 
          flex: 1, 
          overflow: 'hidden' 
        }}>
          <CodeEditor 
            value={code} 
            onChange={handleCodeChange} 
            onSave={handleSave} 
          />
          
          {/* Token Table on the right side - this component positions itself */}
          <TokenTable tokens={tokens} />
        </div>
        
        {/* Terminal at the bottom */}
        <Terminal 
          output={output} 
          codeChanged={codeChanged} 
        />
      </div>
    </div>
  );
};

export default App;