# Conso Web IDE

A web-based Integrated Development Environment (IDE) for the custom programming language "Conso". This IDE allows users to write, analyze (lexically, syntactically, semantically), transpile (to C), and run Conso code directly in the browser. It also features a RAG-powered chatbot to answer questions about the Conso language.

## ✨ Features

*   **Code Editor:** Feature-rich code editing experience powered by Monaco Editor.
*   **Lexical, Syntax, and Semantic Analysis:** Comprehensive code analysis to ensure correctness.
*   **Transpilation:** Convert valid Conso code into equivalent C code.
*   **Execution:** Compile and run the generated C code to see the output.
*   **Interactive Input:** Supports interactive input prompts defined within the Conso code.
*   **Real-time Feedback:** Provides immediate feedback on errors during different analysis phases.
*   **Conso Chatbot:** A RAG-powered chatbot using the Gemini API to answer questions about the Conso language.
*   **Containerized:** Fully containerized with Docker for easy setup and deployment.

## 🖼️ Screenshot

*Coming soon...*

## 💻 Tech Stack

**Frontend:**
![React](https://img.shields.io/badge/React-61DAFB?style=flat-square&logo=react&logoColor=black)
![JavaScript](https://img.shields.io/badge/JavaScript-F7DF1E?style=flat-square&logo=javascript&logoColor=black)
![HTML5](https://img.shields.io/badge/HTML5-E34F26?style=flat-square&logo=html5&logoColor=white)
![CSS3](https://img.shields.io/badge/CSS3-1572B6?style=flat-square&logo=css3&logoColor=white)
![Monaco Editor](https://img.shields.io/badge/Monaco_Editor-007ACC?style=flat-square&logo=visualstudiocode&logoColor=white)

**Backend:**
![Node.js](https://img.shields.io/badge/Node.js-339933?style=flat-square&logo=nodedotjs&logoColor=white)
![Express.js](https://img.shields.io/badge/Express.js-000000?style=flat-square&logo=express&logoColor=white)
![Python](https://img.shields.io/badge/Python-3776AB?style=flat-square&logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=flat-square&logo=fastapi&logoColor=white)
![WebSocket](https://img.shields.io/badge/WebSocket-000000?style=flat-square&logo=websocket&logoColor=white)

**Compilation/Execution & Containerization:**
![GCC](https://img.shields.io/badge/GCC-007396?style=flat-square&logo=gnu&logoColor=white)
![Docker](https://img.shields.io/badge/Docker-2496ED?style=flat-square&logo=docker&logoColor=white)

## 🚀 Getting Started

### Prerequisites

*   **Docker:** Required to build and run the application. Download from [docker.com](https://www.docker.com/products/docker-desktop).
*   **Git:** Required to clone the repository.

### Local Setup

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/conso-web-ide.git
    cd conso-web-ide
    ```

2.  **Create an environment file for the Gemini API Key:**
    Create a file named `.env` in the `backend` directory (`conso-web-ide/backend/.env`) and add your Gemini API key:
    ```
    GEMINI_API_KEY=your_api_key_here
    ```

3.  **Build and run the application using Docker Compose:**
    ```bash
    docker compose up --build
    ```

4.  **Access the application:**
    *   **Frontend:** `http://localhost:3000`
    *   **Python API:** `http://localhost:5000`
    *   **WebSocket:** `ws://localhost:5001`
    *   **Node.js RAG API:** `http://localhost:8000`

## ☁️ Deployment

This application is ready for deployment on platforms that support Docker containers, such as Render, AWS, or Google Cloud.

### Example: Deploying on Render

1.  **Push your code to a GitHub repository.**
2.  **On the Render dashboard, create a new "Web Service" for each of the following services:**
    *   **Frontend (`frontend`):**
        *   **Runtime:** Docker
        *   **Root Directory:** `.`
        *   **Dockerfile:** `./Dockerfile`
    *   **Backend (`backend`):**
        *   **Runtime:** Docker
        *   **Root Directory:** `backend`
        *   **Dockerfile:** `./Dockerfile`
        *   **Environment Variables:** Add `GEMINI_API_KEY` with your API key.
    *   **Python Server (`server`):**
        *   **Runtime:** Docker
        *   **Root Directory:** `server`
        *   **Dockerfile:** `./Dockerfile`
3.  **Configure the necessary environment variables in your frontend to point to the deployed backend URLs.**

## 🔧 How to Use

1.  Ensure the application is running (either locally or deployed).
2.  Open your web browser and navigate to the frontend URL (e.g., `http://localhost:3000`).
3.  Write your Conso code in the editor provided.
4.  Use the buttons (likely labeled "Lex", "Parse", "Semantic", "Run", etc.) to trigger the different analysis phases or to transpile and execute the code.
5.  Output and errors will be displayed in designated areas of the IDE.
6.  To use the Conso Chatbot, navigate to the chatbot interface (if separate) and ask questions about the Conso language.