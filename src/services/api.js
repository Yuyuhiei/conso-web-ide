// api.js
import axios from 'axios';

const API_URL = 'http://localhost:5000/api'; // Adjust if needed

// --- REMOVED Single Run Function ---
// export const runCode = async (code) => { /* ... */ };

// --- NEW Prepare Run Function ---
/**
 * Sends code to the backend to be compiled and prepared for an interactive run.
 * The backend should compile the code, generate a unique run ID, and return
 * the ID and the WebSocket URL for the interactive session.
 *
 * @param {string} code - The Conso code to prepare for running.
 * @returns {Promise<object>} - Promise resolving to an object like
 * { success: boolean, runId?: string, websocketUrl?: string, errors?: string[], phase?: string }.
 */
export const prepareRun = async (code) => {
  console.log("Sending prepare run request for code:", code.substring(0, 100) + "...");
  try {
    // Calls a new /api/run/prepare endpoint (or modified /api/run)
    // This endpoint should NOT execute the code, just compile and set up.
    const response = await axios.post(`${API_URL}/run/prepare`, { code }); // <-- NOTE: New endpoint name suggestion
    console.log("Prepare Run response:", response.data);
    // Expects { success: true, runId: '...', websocketUrl: '...' } on success
    // Or { success: false, phase: '...', errors: [...] } on failure
    return response.data;
  } catch (error) {
    console.error('Error preparing run:', error.response?.data || error.message);
    // Return a consistent error structure
    if (error.response && error.response.data) {
      return {
        success: false,
        phase: error.response.data.phase || 'prepare',
        errors: error.response.data.errors || [error.message || 'Unknown server error during preparation'],
        // Add other fields if the server might return them on error
      };
    }
    // Generic network/request error
    return {
        success: false,
        phase: 'network/request',
        errors: [error.message || 'Failed to prepare run due to network or server error.'],
    };
  }
};


// --- Keep other analysis functions ---
export const analyzeLexical = async (code) => {
    try {
        const response = await axios.post(`${API_URL}/lexer`, { code });
        return response.data;
    } catch (error) {
        console.error('Lexical analysis error:', error);
        return { success: false, errors: [error.response?.data?.detail || error.message || 'Failed to perform lexical analysis'], tokens: [] };
    }
};
export const analyzeSyntax = async (code) => {
    try {
        const response = await axios.post(`${API_URL}/parser`, { code });
        return response.data;
    } catch (error) {
        console.error('Syntax analysis error:', error);
        return { success: false, errors: [error.response?.data?.detail || error.message || 'Failed to perform syntax analysis'], syntaxValid: false };
    }
 };
export const analyzeSemantics = async (code) => {
    try {
        const response = await axios.post(`${API_URL}/semantic`, { code });
        return response.data;
    } catch (error) {
        console.error('Semantic analysis error:', error);
        return { success: false, errors: [error.response?.data?.detail || error.message || 'Failed to perform semantic analysis'] };
    }
};
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
  prepareRun, // Use the new function
  checkHealth
};
