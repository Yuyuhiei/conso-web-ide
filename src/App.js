import React, { useState, useEffect } from 'react';
import { v4 as uuidv4 } from 'uuid'; // You'll need to install this: npm install uuid
import CodeEditor from './components/NewEditor';
import Terminal from './components/Terminal';
import TokenTable from './components/TokenTable';
import Sidebar from './components/Sidebar';
import { analyzeSemantics } from './services/api';
import websocketService from './services/websocketService';
import './App.css';

const App = () => {
  // File management state
  const [files, setFiles] = useState(() => {
    // Try to load files from local storage
    const savedFiles = localStorage.getItem('conso-files');
    if (savedFiles) {
      return JSON.parse(savedFiles);
    }
    // Default to a single untitled file
    return [
      {
        id: uuidv4(),
        name: 'Untitled.cns',
        content: ''
      }
    ];
  });
  
  const [currentFileId, setCurrentFileId] = useState(() => {
    // Use the first file as current file
    const savedFiles = localStorage.getItem('conso-files');
    if (savedFiles) {
      const parsedFiles = JSON.parse(savedFiles);
      return parsedFiles.length > 0 ? parsedFiles[0].id : null;
    }
    return files[0].id;
  });
  
  // Editor and analysis state
  const [output, setOutput] = useState('Welcome to Conso Web IDE');
  const [tokens, setTokens] = useState([]);
  const [semanticEnabled, setSemanticEnabled] = useState(false);
  const [analyzing, setAnalyzing] = useState(false);
  const [codeChanged, setCodeChanged] = useState(false);
  
  // Theme state
  const [currentTheme, setCurrentTheme] = useState(() => {
    const savedTheme = localStorage.getItem('conso-theme');
    return savedTheme || 'conso-dark';
  });
  
  // Current file accessor
  const currentFile = files.find(file => file.id === currentFileId) || files[0];
  
  // Save files to local storage when they change
  useEffect(() => {
    localStorage.setItem('conso-files', JSON.stringify(files));
  }, [files]);
  
  // Save theme to local storage when it changes
  useEffect(() => {
    localStorage.setItem('conso-theme', currentTheme);
  }, [currentTheme]);
  
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
    // Update the current file content
    setFiles(prevFiles => 
      prevFiles.map(file => 
        file.id === currentFileId 
          ? { ...file, content: newValue } 
          : file
      )
    );
    
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
      const response = await analyzeSemantics(currentFile.content);
      
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
    if (!currentFileId) return;
    
    const blob = new Blob([currentFile.content], { type: 'text/plain' });
    const link = document.createElement('a');
    link.download = currentFile.name;
    link.href = window.URL.createObjectURL(blob);
    link.click();
    setOutput(prev => `${prev}\nFile saved: ${currentFile.name}`);
  };

  // Handle file open from disk
  const handleOpenFromDisk = (event) => {
    const file = event.target.files[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target.result;
        
        // Check if we already have 10 files (maximum)
        if (files.length >= 10) {
          alert('You have reached the maximum of 10 files. Please delete a file before adding a new one.');
          return;
        }
        
        // Create a new file
        const newFile = {
          id: uuidv4(),
          name: file.name.endsWith('.cns') ? file.name : `${file.name}.cns`,
          content: content
        };
        
        setFiles(prevFiles => [...prevFiles, newFile]);
        setCurrentFileId(newFile.id);
        setOutput(prev => `${prev}\nFile loaded: ${newFile.name}`);
        
        // Trigger analysis after loading the file
        websocketService.sendCode(content);
      };
      reader.readAsText(file);
    }
  };

  // Clear the terminal
  const clearTerminal = () => {
    setOutput('Terminal cleared');
  };
  
  // File management functions
  const handleFileSelect = (fileId) => {
    setCurrentFileId(fileId);
    
    // Get the selected file
    const selectedFile = files.find(file => file.id === fileId);
    if (selectedFile) {
      // Send the file content for analysis
      websocketService.sendCode(selectedFile.content);
    }
  };
  
  const handleFileCreate = (name) => {
    // Check if we already have 10 files (maximum)
    if (files.length >= 10) {
      alert('You have reached the maximum of 10 files. Please delete a file before adding a new one.');
      return;
    }
    
    // Create a new file
    const newFile = {
      id: uuidv4(),
      name: name,
      content: ''
    };
    
    setFiles(prevFiles => [...prevFiles, newFile]);
    setCurrentFileId(newFile.id);
    
    // Clear analysis since we're starting with empty content
    setTokens([]);
    setSemanticEnabled(false);
    websocketService.sendCode('');
  };
  
  const handleFileRename = (fileId, newName) => {
    setFiles(prevFiles => 
      prevFiles.map(file => 
        file.id === fileId 
          ? { ...file, name: newName } 
          : file
      )
    );
  };
  
  const handleFileDelete = (fileId) => {
    // Make sure we don't delete the last file
    if (files.length <= 1) {
      alert('You cannot delete the last file.');
      return;
    }
    
    // Remove the file
    setFiles(prevFiles => prevFiles.filter(file => file.id !== fileId));
    
    // If the deleted file was the current file, select another file
    if (fileId === currentFileId) {
      const remainingFiles = files.filter(file => file.id !== fileId);
      setCurrentFileId(remainingFiles[0].id);
      
      // Send the new current file content for analysis
      websocketService.sendCode(remainingFiles[0].content);
    }
  };
  
  // Theme management
  const handleThemeChange = (themeId) => {
    setCurrentTheme(themeId);
  };

  return (
    <div className="app-container" style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <header className="app-header" style={{ display: 'flex', alignItems: 'center', backgroundColor: '#252526', padding: '0 10px', borderBottom: '1px solid #333' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <img 
            src="/assets/revamped_cnslogo.svg" 
            alt="Conso Logo" 
            style={{ height: '32px', width: 'auto' }}
          />
          <div className="app-title" style={{ 
            fontFamily: 'Segoe UI, Arial, sans-serif', 
            fontSize: '20px',
            fontWeight: 'bold', 
            padding: '10px 0', 
            marginRight: '20px' 
          }}>
            CNS Compiler
          </div>
        </div>
        
        <div className="file-name-container" style={{ flexGrow: 1 }}>
          <span style={{ marginRight: '8px' }}>{currentFile?.name || 'Untitled.cns'}</span>
        </div>
        
        <div className="app-controls" style={{ display: 'flex', gap: '8px' }}>
          <button onClick={handleSave} style={{ backgroundColor: '#0E639C', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}>Save</button>
          <input 
            type="file" 
            id="file-open" 
            accept=".cns,.txt" 
            style={{ display: 'none' }} 
            onChange={handleOpenFromDisk} 
          />
          <button 
            onClick={() => document.getElementById('file-open').click()}
            style={{ backgroundColor: '#0E639C', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}
          >
            Open from Disk
          </button>
          <button 
            onClick={runSemanticAnalysis} 
            disabled={!semanticEnabled}
            style={{ 
              backgroundColor: semanticEnabled ? '#0d47a1' : '#444',
              color: 'white', 
              border: 'none', 
              padding: '6px 12px', 
              borderRadius: '4px', 
              cursor: semanticEnabled ? 'pointer' : 'not-allowed',
              opacity: semanticEnabled ? 1 : 0.7
            }}
          >
            Semantic Analysis
          </button>
          <button 
            onClick={clearTerminal}
            style={{ backgroundColor: '#f44336', color: 'white', border: 'none', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer' }}
          >
            Clear Terminal
          </button>
        </div>
      </header>
      
      <div className="main-content" style={{ 
        position: 'relative', 
        flex: 1, 
        display: 'flex', 
        flexDirection: 'row',
        overflow: 'hidden'
      }}>
        {/* Sidebar */}
        <Sidebar 
          files={files}
          currentFile={currentFile}
          onFileSelect={handleFileSelect}
          onFileCreate={handleFileCreate}
          onFileRename={handleFileRename}
          onFileDelete={handleFileDelete}
          currentTheme={currentTheme}
          onThemeChange={handleThemeChange}
          resizable={true}
        />
        
        {/* Editor and Terminal container */}
        <div className="editor-terminal-container" style={{ 
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
              value={currentFile?.content || ''} 
              onChange={handleCodeChange} 
              onSave={handleSave}
              theme={currentTheme}
            />
            
            Token Table on the right side
            <TokenTable tokens={tokens} />
          </div>
          
          {/* Terminal at the bottom */}
          <Terminal 
            output={output} 
            codeChanged={codeChanged} 
          />
        </div>
      </div>
    </div>
  );
};

export default App;
