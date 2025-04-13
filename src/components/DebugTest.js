// Create a file named DebugTest.js in your components directory

import React, { useState } from 'react';
import axios from 'axios';

const API_URL = 'http://localhost:5000/api';

const DebugTest = () => {
  const [code, setCode] = useState(`mn(){
    prnt("Hello World");
    prnt(5 + 5);
    end;
}`);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const runDebugTest = async () => {
    setLoading(true);
    try {
      const response = await axios.post(`${API_URL}/debug-run`, { code });
      console.log('Debug run response:', response.data);
      setResult(response.data);
    } catch (error) {
      console.error('Error during debug run:', error);
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '20px', maxWidth: '1000px', margin: '0 auto' }}>
      <h1>Conso Debug Test</h1>
      
      <div style={{ marginBottom: '20px' }}>
        <textarea
          value={code}
          onChange={(e) => setCode(e.target.value)}
          style={{
            width: '100%',
            height: '200px',
            fontFamily: 'monospace',
            padding: '10px',
            marginBottom: '10px'
          }}
        />
        
        <button
          onClick={runDebugTest}
          disabled={loading}
          style={{
            padding: '10px 15px',
            backgroundColor: '#0066cc',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: loading ? 'not-allowed' : 'pointer'
          }}
        >
          {loading ? 'Running Test...' : 'Run Debug Test'}
        </button>
      </div>
      
      {result && (
        <div>
          <h2>Result</h2>
          
          <div style={{ marginBottom: '20px' }}>
            <h3>Success: {result.success ? 'Yes' : 'No'}</h3>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h3>Transpiled Code</h3>
            <pre style={{
              backgroundColor: '#f5f5f5',
              padding: '10px',
              borderRadius: '4px',
              maxHeight: '300px',
              overflow: 'auto'
            }}>
              {result.transpiled_code || 'No transpiled code available'}
            </pre>
          </div>
          
          <div style={{ marginBottom: '20px' }}>
            <h3>Execution Output</h3>
            <pre style={{
              backgroundColor: '#f5f5f5',
              padding: '10px',
              borderRadius: '4px',
              maxHeight: '150px',
              overflow: 'auto'
            }}>
              {result.execution_output || 'No output available'}
            </pre>
            
            {result.execution_output && (
              <div>
                <h4>Output as byte values (for whitespace visibility):</h4>
                <pre style={{
                  backgroundColor: '#f5f5f5',
                  padding: '10px',
                  borderRadius: '4px'
                }}>
                  {Array.from(result.execution_output).map(c => `[${c.charCodeAt(0)}:${c}]`).join(' ')}
                </pre>
              </div>
            )}
          </div>
          
          {result.steps && (
            <div>
              <h3>Execution Steps</h3>
              {result.steps.map((step, index) => (
                <div key={index} style={{
                  marginBottom: '10px',
                  padding: '10px',
                  backgroundColor: step.status === 'success' ? '#e6ffe6' : '#ffe6e6',
                  borderRadius: '4px'
                }}>
                  <h4>Step {index + 1}: {step.step} - {step.status}</h4>
                  <pre style={{
                    backgroundColor: '#ffffff80',
                    padding: '5px',
                    borderRadius: '4px',
                    maxHeight: '150px',
                    overflow: 'auto'
                  }}>
                    {JSON.stringify(step, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default DebugTest;