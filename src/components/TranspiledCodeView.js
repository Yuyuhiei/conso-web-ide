import React, { useRef, useEffect } from 'react';
import Editor from '@monaco-editor/react';

const TranspiledCodeView = ({ code, visible, onClose, onSave }) => {
  const editorRef = useRef(null);
  
  useEffect(() => {
    // When code or visibility changes, update the editor
    if (editorRef.current && visible) {
      // If the editor already has a different value, setValue method
      // can be used to update the content without recreating the editor
      if (editorRef.current.getValue() !== code) {
        editorRef.current.setValue(code);
      }
    }
  }, [code, visible]);

  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    
    // Set some options for the transpiled code view (read-only, etc.)
    editor.updateOptions({
      readOnly: true,
      minimap: { enabled: true },
      scrollBeyondLastLine: false,
      wordWrap: 'on',
      autoIndent: 'full',
      contextmenu: true,
      fontSize: 14,
      lineHeight: 20,
    });
    
    // Set the theme to a C/C++ friendly dark theme
    monaco.editor.setTheme('vs-dark');
  };

  // If not visible, don't render
  if (!visible) {
    return null;
  }

  return (
    <div className="transpiled-code-container" style={{
      position: 'absolute',
      top: 0,
      right: 0,
      bottom: 0,
      left: 0,
      zIndex: 10,
      backgroundColor: '#1e1e1e',
      display: visible ? 'flex' : 'none',
      flexDirection: 'column'
    }}>
      <div className="transpiled-header" style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '8px 16px',
        backgroundColor: '#007acc',
        color: 'white',
        fontWeight: 'bold'
      }}>
        <span>Transpiled C Code</span>
        <div style={{ display: 'flex', gap: '8px' }}>
          <button 
            onClick={() => navigator.clipboard.writeText(code)}
            style={{
              backgroundColor: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Copy to Clipboard
          </button>
          <button 
            onClick={onSave}
            style={{
              backgroundColor: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Save as File
          </button>
          <button 
            onClick={onClose}
            style={{
              backgroundColor: 'rgba(255,255,255,0.2)',
              border: 'none',
              color: 'white',
              padding: '4px 8px',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Close
          </button>
        </div>
      </div>
      <div style={{ flex: 1, overflow: 'hidden' }}>
        <Editor
          height="100%"
          width="100%"
          language="c"
          value={code}
          onMount={handleEditorDidMount}
          options={{
            readOnly: true,
            minimap: { enabled: true },
            scrollBeyondLastLine: false
          }}
        />
      </div>
    </div>
  );
};

export default TranspiledCodeView;