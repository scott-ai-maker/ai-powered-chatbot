import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Send, FileText, X, Download, Trash2, Settings } from 'lucide-react';
import './index.css';

// Configure axios base URL based on environment
const API_BASE_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000';
const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60 seconds for RAG processing
});

function App() {
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [conversationId, setConversationId] = useState(null);
  const [useRAG, setUseRAG] = useState(true);
  const [uploadedFiles, setUploadedFiles] = useState([]);
  const [dragOver, setDragOver] = useState(false);
  
  const messagesEndRef = useRef(null);
  const fileInputRef = useRef(null);

  // Sample questions for sidebar
  const sampleQuestions = [
    "What skills do I need to become an AI engineer?",
    "How do I transition from software development to AI?",
    "What are the key differences between ML Engineer and Data Scientist roles?",
    "Which programming languages are most important for AI careers?",
    "How can I build a portfolio for AI engineering roles?",
    "What are the current AI job market trends?",
    "How do I prepare for AI engineering interviews?",
    "What certifications are valuable for AI careers?"
  ];

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Generate conversation ID on first load
  useEffect(() => {
    setConversationId(generateConversationId());
  }, []);

  const generateConversationId = () => {
    return 'conv_' + Math.random().toString(36).substring(2, 15) + Math.random().toString(36).substring(2, 15);
  };

  // Handle file drag and drop
  const handleDragOver = (event) => {
    event.preventDefault();
    setDragOver(true);
  };

  const handleDragLeave = () => {
    setDragOver(false);
  };

  const handleDrop = (event) => {
    event.preventDefault();
    setDragOver(false);
    const files = Array.from(event.dataTransfer.files);
    handleFileUpload(files);
  };

  const handleFileInputChange = (event) => {
    const files = Array.from(event.target.files);
    handleFileUpload(files);
  };

  const handleFileUpload = (files) => {
    const validFiles = files.filter(file => 
      file.type === 'application/pdf' || 
      file.type === 'text/plain' || 
      file.name.endsWith('.txt') ||
      file.name.endsWith('.md')
    );
    
    if (validFiles.length !== files.length) {
      setError('Only PDF, TXT, and MD files are supported');
      setTimeout(() => setError(null), 5000);
    }
    
    setUploadedFiles(prev => [...prev, ...validFiles]);
  };

  const removeFile = (index) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  // Send message to chatbot
  const sendMessage = async () => {
    if (!inputMessage.trim()) return;

    const userMessage = {
      id: Date.now(),
      text: inputMessage,
      sender: 'user',
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setLoading(true);
    setError(null);

    try {
      const requestData = {
        message: inputMessage,
        conversation_id: conversationId,
        user_id: 'demo_user',
        temperature: 0.7,
        max_tokens: 1000,
        stream: false
      };

      // Add uploaded files if any
      if (uploadedFiles.length > 0) {
        const formData = new FormData();
        formData.append('data', JSON.stringify(requestData));
        uploadedFiles.forEach((file, index) => {
          formData.append(`file_${index}`, file);
        });
        
        // For now, we'll process files separately
        // In a full implementation, you'd send formData to a file processing endpoint
      }

      const endpoint = useRAG ? '/api/chat?use_rag=true' : '/api/chat';
      const response = await api.post(endpoint, requestData);

      const botMessage = {
        id: Date.now() + 1,
        text: response.data.message,
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString(),
        processingTime: response.data.processing_time_ms,
        sources: response.data.metadata?.knowledge_sources || []
      };

      setMessages(prev => [...prev, botMessage]);
      
      // Clear uploaded files after successful message
      setUploadedFiles([]);
      
    } catch (err) {
      console.error('Chat error:', err);
      setError(err.response?.data?.error || 'Failed to send message. Please try again.');
      
      const errorMessage = {
        id: Date.now() + 1,
        text: 'Sorry, I encountered an error processing your request. Please try again.',
        sender: 'assistant',
        timestamp: new Date().toLocaleTimeString(),
        isError: true
      };
      
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  const clearConversation = () => {
    setMessages([]);
    setConversationId(generateConversationId());
  };

  const exportConversation = () => {
    const conversation = messages.map(msg => ({
      sender: msg.sender,
      message: msg.text,
      timestamp: msg.timestamp
    }));
    
    const blob = new Blob([JSON.stringify(conversation, null, 2)], {
      type: 'application/json'
    });
    
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `conversation_${conversationId}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  const askSampleQuestion = (question) => {
    setInputMessage(question);
  };

  return (
    <div className="app">
      <div className="chat-container">
        <div className="header">
          <h1>🤖 AI Career Mentor</h1>
          <p>Your intelligent guide to AI engineering careers</p>
        </div>

        <div className="main-content">
          <div className="sidebar">
            <h3>💡 Try These Questions</h3>
            <ul className="sample-questions">
              {sampleQuestions.map((question, index) => (
                <li 
                  key={index}
                  className="sample-question"
                  onClick={() => askSampleQuestion(question)}
                >
                  {question}
                </li>
              ))}
            </ul>

            <div className="conversation-controls">
              <button className="control-button" onClick={clearConversation}>
                <Trash2 size={16} /> Clear
              </button>
              <button className="control-button" onClick={exportConversation}>
                <Download size={16} /> Export
              </button>
            </div>

            <div className="rag-toggle">
              <label>
                <input
                  type="checkbox"
                  checked={useRAG}
                  onChange={(e) => setUseRAG(e.target.checked)}
                />
                Use Knowledge Base (RAG)
              </label>
            </div>
          </div>

          <div className="chat-area">
            <div className="messages-container">
              {messages.length === 0 && (
                <div className="welcome-message">
                  <h3>Welcome to AI Career Mentor! 👋</h3>
                  <p>Ask me anything about AI engineering careers, skills, job market trends, or career transitions.</p>
                  {useRAG && <p><strong>Knowledge Base is enabled</strong> - I can provide detailed, research-backed answers.</p>}
                </div>
              )}

              {messages.map((message) => (
                <div key={message.id} className={`message ${message.sender}`}>
                  <div className={`message-bubble ${message.isError ? 'error' : ''}`}>
                    {message.text}
                    <div className="message-info">
                      {message.timestamp}
                      {message.processingTime && ` • ${message.processingTime}ms`}
                      {message.sources && message.sources.length > 0 && (
                        <div className="sources">
                          📚 Sources: {message.sources.length} references
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}

              {loading && (
                <div className="message assistant">
                  <div className="message-bubble">
                    <div className="loading-indicator">
                      <div className="spinner"></div>
                      {useRAG ? 'Searching knowledge base and generating response...' : 'Thinking...'}
                    </div>
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
              {error && (
                <div className="error-message">
                  {error}
                </div>
              )}

              <div 
                className={`file-upload-area ${dragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
              >
                <FileText size={24} />
                <div className="file-upload-text">
                  Drag & drop documents or click to upload (PDF, TXT, MD)
                </div>
                <input
                  ref={fileInputRef}
                  type="file"
                  multiple
                  accept=".pdf,.txt,.md"
                  onChange={handleFileInputChange}
                  style={{ display: 'none' }}
                />
              </div>

              {uploadedFiles.length > 0 && (
                <div className="uploaded-files">
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="uploaded-file">
                      <FileText size={14} />
                      {file.name}
                      <button
                        className="remove-file"
                        onClick={() => removeFile(index)}
                      >
                        <X size={14} />
                      </button>
                    </div>
                  ))}
                </div>
              )}

              <div className="input-container">
                <div className="input-group">
                  <textarea
                    className="textarea"
                    value={inputMessage}
                    onChange={(e) => setInputMessage(e.target.value)}
                    onKeyPress={handleKeyPress}
                    placeholder="Ask me about AI careers, skills, job market, or career transitions..."
                    disabled={loading}
                  />
                </div>
                <button
                  className="send-button"
                  onClick={sendMessage}
                  disabled={loading || !inputMessage.trim()}
                >
                  {loading ? (
                    <div className="spinner" />
                  ) : (
                    <Send size={20} />
                  )}
                  Send
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;