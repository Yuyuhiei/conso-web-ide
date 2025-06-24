require('dotenv').config();
const express = require('express');
const cors = require('cors'); // 1. Import cors
const { GoogleGenerativeAI } = require('@google/generative-ai');
const fs = require('fs').promises;
const path = require('path');

// --- Configuration ---
const PORT = 3001; // Use a fixed port
const VECTOR_STORE_PATH = path.join(__dirname, 'vector-store.json');

// --- Initialize Express & Gemini ---
const app = express();
app.use(cors());
app.use(express.json());
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const embeddingModel = genAI.getGenerativeModel({ model: "embedding-001" });
// FINAL FIX: Use the latest recommended model to ensure compatibility.
const generativeModel = genAI.getGenerativeModel({ model: "gemini-1.5-flash-latest" });

// --- In-memory Vector Store ---
let vectorStore = [];

// --- Helper Function: Cosine Similarity ---
function cosineSimilarity(vecA, vecB) {
    let dotProduct = 0.0;
    let normA = 0.0;
    let normB = 0.0;
    for (let i = 0; i < vecA.length; i++) {
        dotProduct += vecA[i] * vecB[i];
        normA += vecA[i] * vecA[i];
        normB += vecB[i] * vecB[i];
    }
    if (normA === 0 || normB === 0) {
        return 0;
    }
    return dotProduct / (Math.sqrt(normA) * Math.sqrt(normB));
}

// --- API Endpoint for Chat ---
app.post('/api/chat', async (req, res) => {
    const { query } = req.body;

    if (!query) {
        return res.status(400).json({ error: 'Query is required.' });
    }

    try {
        // 1. Embed the user's query
        const queryEmbeddingResult = await embeddingModel.embedContent(query);
        const queryEmbedding = queryEmbeddingResult.embedding.values;

        // 2. Find the most relevant context from the vector store
        const relevantChunks = vectorStore
            .map(item => {
                const similarity = cosineSimilarity(queryEmbedding, item.embedding);
                return { ...item, similarity };
            })
            .sort((a, b) => b.similarity - a.similarity)
            .slice(0, 3); // Get top 3 most relevant chunks

        const context = relevantChunks.map(item => item.content).join('\n\n');

        // 3. Generate a response using the context and new rules
        const prompt = `You are Conso-bot, an expert AI assistant for the Conso programming language.
        The language was created by Lauvigne G. Lumeda, a 3rd year PLM Computer Science Student, and his groupmates. If asked about the creator, you must state this.
        Your primary role is to explain the features of the Conso language using the provided context. You are not allowed to write or generate new Conso code for the user. If asked to create code, you must politely decline.
        You should also mention that the information is about 90% accurate as the model is still being trained and processed.
        
        Based on these rules and the following context, answer the user's question. If the context doesn't contain the answer, say you don't have enough information.
        
        Context:
        ${context}
        
        Question:
        ${query}
        
        Answer:`;

        const result = await generativeModel.generateContent(prompt);
        const response = await result.response;
        const text = response.text();

        res.json({ answer: text });

    } catch (error) {
        console.error("Error processing chat:", error); 
        res.status(500).json({ error: 'Failed to process your request.' });
    }
});

// Add a root route handler to confirm the server is running
app.get('/', (req, res) => {
    res.send('Conso-bot backend is running!');
});

// --- Start Server ---
async function startServer() {
    try {
        // Load the vector store into memory
        const data = await fs.readFile(VECTOR_STORE_PATH, 'utf-8');
        vectorStore = JSON.parse(data);
        console.log(`Vector store loaded with ${vectorStore.length} entries.`);

        app.listen(PORT, '0.0.0.0', () => {
            console.log(`Server is running on http://0.0.0.0:${PORT}`);
        });
    } catch (error) {
        console.error("Failed to start server:", error);
        console.error("Please run 'node setup-rag.js' first to create the vector store.");
        process.exit(1);
    }
}

startServer();