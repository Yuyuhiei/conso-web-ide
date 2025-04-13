import React, { useState, useEffect, useRef } from 'react';
import { v4 as uuidv4 } from 'uuid'; // You'll need to install this: npm install uuid
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'; // Make sure you have react-router-dom installed
import CodeEditor from './components/NewEditor';
import Terminal from './components/Terminal';
import TokenTable from './components/TokenTable';
import Sidebar from './components/Sidebar';
import TranspiledCodeView from './components/TranspiledCodeView';
import DebugTest from './components/DebugTest'; // Import the DebugTest component
import { analyzeSemantics, runConsoCode } from './services/api';
import websocketService from './services/websocketService';
import './App.css';

// Main application component
const MainApp = () => {
  // File management state
  const [files, setFiles] = useState(() => {
    const savedFiles = localStorage.getItem('conso-files');
    if (savedFiles) {
      return JSON.parse(savedFiles);
    }
    return [
      {
        id: uuidv4(),
        name: 'Untitled.cns',
        content: ''
      }
    ];
  });

  const [currentFileId, setCurrentFileId] = useState(() => {
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
  const [isRunning, setIsRunning] = useState(false);

  // Ref for Terminal
  const terminalRef = useRef(null);

  // Theme state
  const [currentTheme, setCurrentTheme] = useState(() => {
    const savedTheme = localStorage.getItem('conso-theme');
    return savedTheme || 'conso-dark';
  });

  // Transpiler and execution state
  const [transpiledCode, setTranspiledCode] = useState('');
  const [programOutput, setProgramOutput] = useState('');
  const [showTranspiledCode, setShowTranspiledCode] = useState(false);

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
      .on('parserResult', async (data) => {
        if (data.syntaxValid) {
          try {
            const semanticResponse = await analyzeSemantics(currentFile.content);
            if (semanticResponse.success) {
              setSemanticEnabled(true);
              setOutput(prev => `${prev}\nParser run successfully!\nSemantic analysis passed! ✅`);
            } else {
              setSemanticEnabled(false);
              const errorMessages = semanticResponse.errors.join('\n');
              setOutput(prev => `${prev}\nParser run successfully!\nSemantic Error: ${errorMessages}`);
            }
          } catch (err) {
            setSemanticEnabled(false);
            setOutput(prev => `${prev}\nParser run successfully!\nSemantic analysis failed: ${err.message}`);
          }
        } else {
          setSemanticEnabled(false);
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

    websocketService.connect();

    return () => {
      websocketService.disconnect();
    };
  }, []);

  // Function for real-time analysis
  const handleCodeChange = (newValue) => {
    setFiles(prevFiles =>
      prevFiles.map(file =>
        file.id === currentFileId
          ? { ...file, content: newValue }
          : file
      )
    );

    setCodeChanged(true);
    setProgramOutput('');

    if (!analyzing) {
      setAnalyzing(true);
      const debounceTimer = setTimeout(() => {
        websocketService.sendCode(newValue);
        setAnalyzing(false);
      }, 500);

      return () => clearTimeout(debounceTimer);
    }
  };

  // Close the transpiled code view
  const handleCloseTranspiledView = () => {
    setShowTranspiledCode(false);
  };

  // Save transpiled C code to file
  const saveTranspiledCode = () => {
    if (!transpiledCode) return;

    const blob = new Blob([transpiledCode], { type: 'text/plain' });
    const link = document.createElement('a');
    const baseName = currentFile.name.replace('.cns', '');
    link.download = `${baseName}.c`;

    link.href = window.URL.createObjectURL(blob);
    link.click();
    setOutput(prev => `${prev}\nTranspiled C code saved: ${baseName}.c`);
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

        if (files.length >= 10) {
          alert('You have reached the maximum of 10 files. Please delete a file before adding a new one.');
          return;
        }

        const newFile = {
          id: uuidv4(),
          name: file.name.endsWith('.cns') ? file.name : `${file.name}.cns`,
          content: content
        };

        setFiles(prevFiles => [...prevFiles, newFile]);
        setCurrentFileId(newFile.id);
        setOutput(prev => `${prev}\nFile loaded: ${newFile.name}`);

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

    const selectedFile = files.find(file => file.id === fileId);
    if (selectedFile) {
      websocketService.sendCode(selectedFile.content);
    }
  };

  const handleFileCreate = (name) => {
    if (files.length >= 10) {
      alert('You have reached the maximum of 10 files. Please delete a file before adding a new one.');
      return;
    }

    const newFile = {
      id: uuidv4(),
      name: name,
      content: ''
    };

    setFiles(prevFiles => [...prevFiles, newFile]);
    setCurrentFileId(newFile.id);

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
    if (files.length <= 1) {
      alert('You cannot delete the last file.');
      return;
    }

    setFiles(prevFiles => prevFiles.filter(file => file.id !== fileId));

    if (fileId === currentFileId) {
      const remainingFiles = files.filter(file => file.id !== fileId);
      setCurrentFileId(remainingFiles[0].id);

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

        {/* Add debug mode link */}
        <div style={{ marginRight: '20px' }}>
          <Link to="/debug" style={{ color: '#0E639C', textDecoration: 'none' }}>Debug Mode</Link>
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
            onClick={() => terminalRef.current && terminalRef.current.run()}
            disabled={!semanticEnabled || isRunning}
            style={{
              backgroundColor: semanticEnabled && !isRunning ? '#2e7d32' : '#444',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              cursor: semanticEnabled && !isRunning ? 'pointer' : 'not-allowed',
              opacity: semanticEnabled && !isRunning ? 1 : 0.7
            }}
          >
            {isRunning ? 'Running...' : 'Run'}
          </button>
          <button
            onClick={() => setShowTranspiledCode(true)}
            disabled={!transpiledCode}
            style={{
              backgroundColor: transpiledCode ? '#4a148c' : '#444',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              cursor: transpiledCode ? 'pointer' : 'not-allowed',
              opacity: transpiledCode ? 1 : 0.7
            }}
          >
            View C Code
          </button>
          <button
            onClick={saveTranspiledCode}
            disabled={!transpiledCode}
            style={{
              backgroundColor: transpiledCode ? '#ef6c00' : '#444',
              color: 'white',
              border: 'none',
              padding: '6px 12px',
              borderRadius: '4px',
              cursor: transpiledCode ? 'pointer' : 'not-allowed',
              opacity: transpiledCode ? 1 : 0.7
            }}
          >
            Save C Code
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

            {/* Token Table on the right side */}
            <TokenTable tokens={tokens} />

            {/* Transpiled Code View */}
            {showTranspiledCode && (
              <div style={{ position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, zIndex: 100 }}>
                <TranspiledCodeView
                  code={transpiledCode}
                  visible={showTranspiledCode}
                  onClose={handleCloseTranspiledView}
                  onSave={saveTranspiledCode}
                />
              </div>
            )}
          </div>

          {/* Terminal at the bottom */}
          <Terminal
            ref={terminalRef}
            output={output}
            codeChanged={codeChanged}
            transpiledCode={transpiledCode}
            programOutput={programOutput}
            code={currentFile?.content || ""}
            onRunComplete={({ output: runOutput, error: runError, transpiledCode: runTranspiled }) => {
              if (runError) {
                setProgramOutput('');
                setOutput(prev => `${prev}\n${runError}`);
  } else if (runOutput !== undefined && runOutput !== null) {
    const outputValue = runOutput || '(Program executed but produced no output)';
    setProgramOutput(outputValue);
    setOutput(prev => `${prev}\nProgram Output:\n${outputValue}`);
  }
              if (runTranspiled !== undefined && runTranspiled !== null) {
                setTranspiledCode(runTranspiled);
              }
              setIsRunning(false);
            }}
            setIsRunning={setIsRunning}
          />
        </div>
      </div>
    </div>
  );
};

// Header navigation to go back to the main app from the debug page
const DebugHeader = () => {
  return (
    <header style={{
      backgroundColor: '#252526',
      padding: '10px 20px',
      borderBottom: '1px solid #333',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'space-between'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
        <img
          src="/assets/revamped_cnslogo.svg"
          alt="Conso Logo"
          style={{ height: '32px', width: 'auto' }}
        />
        <div style={{ fontFamily: 'Segoe UI, Arial, sans-serif', fontSize: '20px', fontWeight: 'bold' }}>
          CNS Compiler - Debug Mode
        </div>
      </div>
      <div>
        <Link to="/" style={{ color: '#0E639C', textDecoration: 'none' }}>Back to Editor</Link>
      </div>
    </header>
  );
};

// Wrapped DebugTest component with header
const DebugTestWithHeader = () => {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <DebugHeader />
      <DebugTest />
    </div>
  );
};

// Main App component with routing
const App = () => {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<MainApp />} />
        <Route path="/debug" element={<DebugTestWithHeader />} />
      </Routes>
    </Router>
  );
};

export default App;
