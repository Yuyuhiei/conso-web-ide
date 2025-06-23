import React, { useState, useRef, useEffect } from 'react';
import { VscSend } from 'react-icons/vsc';
import './ConsoChatbot.css';

const ConsoChatbot = () => {
  const [messages, setMessages] = useState([
    { sender: 'bot', text: 'Hi! I am the Conso-bot. Ask me anything about the Conso programming language.' }
  ]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    const currentInput = input;
    setInput('');
    setIsLoading(true);

    try {
      const apiUrl = process.env.REACT_APP_RAG_API_URL || 'http://localhost:3001';
      const response = await fetch(`${apiUrl}/api/chat`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        // 1. FIX: Change 'message' to 'query' to match the backend
        body: JSON.stringify({ query: currentInput }),
      });

      if (!response.ok) {
        throw new Error('Network response was not ok');
      }

      const data = await response.json();
      // 2. FIX: Change 'data.reply' to 'data.answer' to match the backend
      const botResponse = { sender: 'bot', text: data.answer };
      setMessages(prev => [...prev, botResponse]);

    } catch (error) {
      console.error("Error fetching from backend:", error);
      const errorResponse = { 
        sender: 'bot', 
        text: "Sorry, I couldn't connect to the server. Please make sure it's running." 
      };
      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
    // --- End of API call ---
  };

  return (
    <div className="conso-chatbot">
      <div className="chat-messages">
        {messages.map((msg, index) => (
          <div key={index} className={`message ${msg.sender}`}>
            <div className="message-bubble">{msg.text}</div>
          </div>
        ))}
        {isLoading && (
          <div className="message bot">
            <div className="message-bubble typing-indicator">
              <span></span><span></span><span></span>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>
      <form className="chat-input-form" onSubmit={handleSendMessage}>
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about Conso..."
          disabled={isLoading}
        />
        <button type="submit" disabled={isLoading || !input.trim()}>
          <VscSend />
        </button>
      </form>
    </div>
  );
};

export default ConsoChatbot;