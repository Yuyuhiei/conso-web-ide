require('dotenv').config();
const { GoogleGenerativeAI } = require('@google/generative-ai');
const fs = require('fs').promises;
const path = require('path');

// --- Configuration ---
// 1. Pointing to the original ConsoRAG.md file.
const DOC_PATH = path.join(__dirname, '..', 'public', 'ConsoRAG.md'); 
const VECTOR_STORE_PATH = path.join(__dirname, 'vector-store.json');
const BATCH_SIZE = 100;

// --- Initialize Gemini ---
const genAI = new GoogleGenerativeAI(process.env.GEMINI_API_KEY);
const embeddingModel = genAI.getGenerativeModel({ model: "embedding-001" });

async function main() {
  console.log("Starting document processing for RAG setup...");

  // 1. Load and normalize the document.
  console.log(`Loading text from: ${DOC_PATH}`);
  let text = await fs.readFile(DOC_PATH, 'utf-8');
  text = text.replace(/\r\n/g, '\n'); // Normalize line endings
  console.log("Normalized line endings.");

  // 2. Parse the text into chunks by splitting it into paragraphs.
  // This is a more robust way to handle a general document.
  const originalChunks = text
    .split('\n\n') // Split by double newline (paragraphs)
    .map(chunk => chunk.trim()) // Trim whitespace
    .filter(chunk => chunk.length > 0); // Remove empty chunks

  console.log(`Parsed document into ${originalChunks.length} chunks.`);
  if (originalChunks.length === 0) {
      console.error("No chunks were created. Check the source file format.");
      return;
  }

  // 3. Create a "clean" version of chunks for the API by removing backticks and markdown.
  const cleanChunks = originalChunks.map(chunk => chunk.replace(/`/g, '').replace(/#/g, '').replace(/\*/g, ''));
  console.log("Created clean version of chunks for API.");

  // 4. Create embeddings for each CLEAN chunk.
  console.log("Generating embeddings...");
  const allEmbeddings = [];
  for (let i = 0; i < cleanChunks.length; i += BATCH_SIZE) {
    const batchChunks = cleanChunks.slice(i, i + BATCH_SIZE);
    const batchNumber = Math.floor(i / BATCH_SIZE) + 1;
    console.log(`Processing batch ${batchNumber} of ${Math.ceil(cleanChunks.length / BATCH_SIZE)}...`);
    
    const result = await embeddingModel.batchEmbedContents({
      requests: batchChunks.map(chunk => ({
        content: {
          parts: [{ text: chunk }],
          role: 'user'
        }
      })),
    });

    allEmbeddings.push(...result.embeddings);
  }
  console.log("All embeddings generated successfully.");

  // 5. Create and save the vector store.
  const vectorStore = originalChunks.map((chunk, index) => ({
    content: chunk,
    embedding: allEmbeddings[index].values,
  }));

  await fs.writeFile(VECTOR_STORE_PATH, JSON.stringify(vectorStore, null, 2));
  console.log(`Vector store created with ${vectorStore.length} entries and saved to: ${VECTOR_STORE_PATH}`);
  console.log("\nSetup complete! You can now start your main server.");
}

main().catch(e => {
    console.error("The script failed to complete.", e);
});