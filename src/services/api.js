// api.js
import axios from 'axios';

// Base API URL - ensure this matches your server configuration
const API_URL = 'http://localhost:5000/api'; // Adjust if your server runs elsewhere

/**
 * Initiates the code execution process.
 * Performs validation (lexical, syntax, semantic) on the server.
 * If input is required, returns prompts.
 * If no input is required, returns the full execution result.
 * If validation fails, returns error details.
 *
 * @param {string} code - The Conso code to run.
 * @returns {Promise<object>} - Promise resolving to either an InputRequiredResponse
 * or an ExecutionResult object from the server.
 */
export const initiateRun = async (code) => {
  console.log("Initiating run for code:", code.substring(0, 100) + "...");
  try {
    const response = await axios.post(`${API_URL}/run/initiate`, { code });
    console.log("Initiate run response:", response.data);
    // The response will have a 'status' field: 'input_required' or 'completed'/'error'
    return response.data;
  } catch (error) {
    console.error('Error initiating run:', error.response?.data || error.message);
    // Return the error response from the server if available
    if (error.response && error.response.data) {
      return {
        status: 'error', // Add a status field for consistency
        success: false,
        phase: error.response.data.phase || 'initiation',
        errors: error.response.data.errors || [error.message],
        transpiledCode: error.response.data.transpiledCode,
        output: error.response.data.output,
      };
    }
    // Generic error fallback
    throw new Error(error.response?.data?.detail || error.message || 'Failed to initiate run');
  }
};

/**
 * Executes the code after user inputs have been provided.
 * Sends the code and the collected inputs to the server for final transpilation and execution.
 *
 * @param {string} code - The original Conso code.
 * @param {object} inputs - An object mapping variable names to user-provided input strings.
 * @returns {Promise<object>} - Promise resolving to an ExecutionResult object.
 */
export const executeRunWithInput = async (code, inputs) => {
  console.log("Executing run with inputs:", inputs);
  try {
    const response = await axios.post(`${API_URL}/run/execute`, { code, inputs });
    console.log("Execute run response:", response.data);
    return response.data; // Should be an ExecutionResult
  } catch (error) {
    console.error('Error executing run with input:', error.response?.data || error.message);
     // Return the error response from the server if available
     if (error.response && error.response.data) {
      return {
        status: 'error', // Add a status field for consistency
        success: false,
        phase: error.response.data.phase || 'execution_with_input',
        errors: error.response.data.errors || [error.message],
        transpiledCode: error.response.data.transpiledCode,
        output: error.response.data.output,
      };
    }
    // Generic error fallback
    throw new Error(error.response?.data?.detail || error.message || 'Failed to execute run with input');
  }
};


// --- Keep other analysis functions as they are ---

export const analyzeLexical = async (code) => {
  try {
    const response = await axios.post(`${API_URL}/lexer`, { code });
    return response.data;
  } catch (error) {
    console.error('Lexical analysis error:', error);
    // Provide a more informative error structure
    return {
        success: false,
        errors: [error.response?.data?.detail || error.message || 'Failed to perform lexical analysis'],
        tokens: []
    };
    // throw new Error(error.response?.data?.detail || 'Failed to perform lexical analysis');
  }
};

export const analyzeSyntax = async (code) => {
  try {
    const response = await axios.post(`${API_URL}/parser`, { code });
    return response.data;
  } catch (error) {
    console.error('Syntax analysis error:', error);
     return {
        success: false,
        errors: [error.response?.data?.detail || error.message || 'Failed to perform syntax analysis'],
        syntaxValid: false
    };
    // throw new Error(error.response?.data?.detail || 'Failed to perform syntax analysis');
  }
};

export const analyzeSemantics = async (code) => {
  try {
    const response = await axios.post(`${API_URL}/semantic`, { code });
    return response.data;
  } catch (error) {
    console.error('Semantic analysis error:', error);
    return {
        success: false,
        errors: [error.response?.data?.detail || error.message || 'Failed to perform semantic analysis']
    };
    // throw new Error(error.response?.data?.detail || 'Failed to perform semantic analysis');
  }
};

// (Optional: Keep transpileToC if you still need a direct transpilation endpoint without execution)
// export const transpileToC = async (code) => { ... };

export const checkHealth = async () => {
  try {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    throw new Error('Failed to connect to Conso Language Server');
  }
};

// Export the functions
export default {
  analyzeLexical,
  analyzeSyntax,
  analyzeSemantics,
  initiateRun, // New function
  executeRunWithInput, // New function
  // transpileToC, // Optional
  checkHealth
};
