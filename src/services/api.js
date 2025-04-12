import axios from 'axios';

// Base API URL - change this to your server address
const API_URL = 'http://localhost:5000/api';

// Function to analyze code with the lexer
export const analyzeLexical = async (code) => {
  try {
    const response = await axios.post(`${API_URL}/lexer`, { code });
    return response.data;
  } catch (error) {
    console.error('Lexical analysis error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to perform lexical analysis');
  }
};

// Function to analyze code with the parser
export const analyzeSyntax = async (code) => {
  try {
    const response = await axios.post(`${API_URL}/parser`, { code });
    return response.data;
  } catch (error) {
    console.error('Syntax analysis error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to perform syntax analysis');
  }
};

// Function to analyze code with the semantic analyzer
export const analyzeSemantics = async (code) => {
  try {
    const response = await axios.post(`${API_URL}/semantic`, { code });
    return response.data;
  } catch (error) {
    console.error('Semantic analysis error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to perform semantic analysis');
  }
};

// Function to transpile Conso code to C
export const transpileToC = async (code) => {
  try {
    const response = await axios.post(`${API_URL}/transpile`, { code });
    return response.data;
  } catch (error) {
    console.error('Transpilation error:', error);
    throw new Error(error.response?.data?.detail || 'Failed to transpile code to C');
  }
};

// Function to run Conso code (transpile, compile, and execute)
export const runConsoCode = async (code) => {
  try {
    console.log("Sending run request to server with code:", code.substring(0, 50) + "...");
    const response = await axios.post(`${API_URL}/run`, { code });
    console.log("Raw API response:", response);
    console.log("Response data:", response.data);
    console.log("Output field:", response.data.output); // Check if this exists and what it contains
    return response.data;
  } catch (error) {
    console.error('Code execution error:', error);
    throw error;
  }
};

// Check API health
export const checkHealth = async () => {
  try {
    const response = await axios.get(`${API_URL}/health`);
    return response.data;
  } catch (error) {
    console.error('Health check error:', error);
    throw new Error('Failed to connect to Conso Language Server');
  }
};

export default {
  analyzeLexical,
  analyzeSyntax,
  analyzeSemantics,
  transpileToC,
  runConsoCode,
  checkHealth
};