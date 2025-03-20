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
  checkHealth
};