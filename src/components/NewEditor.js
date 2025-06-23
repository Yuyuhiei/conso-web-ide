import React, { useEffect, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { configureConsoLanguage } from '../utils/consoLanguageConfig';
import { registerMonacoThemes } from '../utils/themes';
import './NewEditor.css'; // Import the new CSS file

const NewEditor = ({ 
  value, 
  onChange, 
  onSave,
  theme = 'conso-dark'
}) => {
  const editorRef = useRef(null);
  const monacoRef = useRef(null);
  
  // Initialize Monaco editor and configure language
  const handleEditorDidMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    
    // Register custom themes
    registerMonacoThemes(monaco);

    // Configure the Conso language
    configureConsoLanguage(monaco);
    
    // Set the editor language to Conso
    monaco.editor.setModelLanguage(editor.getModel(), 'conso');
    
    // Add keyboard shortcuts for save
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.KeyS, () => {
      if (onSave) onSave();
    });
    
    // Set editor options
    editor.updateOptions({
      tabSize: 4,
      insertSpaces: true,
      autoIndent: 'full',
      contextmenu: true,
      fontFamily: 'Consolas, "Courier New", monospace',
      fontSize: 16,
      lineHeight: 24,
      padding: {
        top: 10,
        bottom: 10
      },
    });
  };
  
  // This effect runs when the value prop changes
  useEffect(() => {
    if (editorRef.current && value !== editorRef.current.getValue()) {
      editorRef.current.setValue(value);
    }
  }, [value]);
  
  // This effect updates the theme when it changes
  useEffect(() => {
    if (monacoRef.current) {
      monacoRef.current.editor.setTheme(theme);
    }
  }, [theme]);
  
  return (
    <div className="editor-container">
      <Editor
        height="100%"
        width="100%"
        defaultLanguage="conso"
        defaultValue={value}
        onChange={onChange}
        onMount={handleEditorDidMount}
        theme={theme} // Use the theme prop directly
        options={{
          selectOnLineNumbers: true,
          roundedSelection: false,
          readOnly: false,
          cursorStyle: 'line',
          automaticLayout: true,
          glyphMargin: false,
          folding: false,
          lineNumbersMinChars: 3,
          minimap: { enabled: true, side: 'right' },
          scrollBeyondLastLine: false,
          wordWrap: 'on',
          scrollbar: {
            verticalScrollbarSize: 8,
            horizontalScrollbarSize: 8,
            arrowSize: 12,
            useShadows: false,
          }
        }}
      />
    </div>
  );
};

export default NewEditor;