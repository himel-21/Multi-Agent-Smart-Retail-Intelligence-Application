import React, { useState } from 'react';
import './App.css';

// 1. Component for the Product Tiles
const ProductTile = ({ product }) => (
  <div className="product-card">
    <div className="badge">AI Recommended</div>
    <img src={product.image || 'https://via.placeholder.com/150'} alt={product.title} />
    <h3>{product.title}</h3>
    <p className="price">${product.price}</p>
    <p className="description">{product.description?. substring(0, 80)}...</p>
    <button className="view-btn">View Details</button>
  </div>
);

function App() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [chatHistory, setChatHistory] = useState([{ role: 'assistant', text: 'Hello! I can find high-readiness products for you. What category are you looking for?' }]);

  const handleSearch = async () => {
    if (!query) return;
    setLoading(true);
    
    // Add User message to chat
    setChatHistory(prev => [...prev, { role: 'user', text: query }]);

    try {
      // REPLACE THIS URL with your API Gateway Invoke URL
      const API_URL = "https://YOUR_API_ID.execute-api.ap-south-1.amazonaws.com/prod/query";
      
      const response = await fetch(API_URL, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          query: query, 
          user_type: 'customer' 
        }),
      });

      const data = await response.json();
      
      // We assume the Bedrock Agent returns a stringified JSON of products in "answer"
      // Your Bridge Lambda handles the raw string from Bedrock
      const aiResponse = data.answer;
      
      // Logic: Try to find JSON inside the AI string to show tiles
      try {
        const jsonMatch = aiResponse.match(/\[.*\]/s);
        if (jsonMatch) {
          const products = JSON.parse(jsonMatch[0]);
          setResults(products);
        }
      } catch (e) {
        console.log("No JSON array found in response, showing text only.");
      }

      setChatHistory(prev => [...prev, { role: 'assistant', text: aiResponse.replace(/\[.*\]/s, '') }]);
    } catch (error) {
      setChatHistory(prev => [...prev, { role: 'assistant', text: "Sorry, I'm having trouble connecting to the marketplace." }]);
    } finally {
      setLoading(false);
      setQuery("");
    }
  };

  return (
    <div className="dashboard-container">
      {/* Sidebar Chat */}
      <div className="sidebar">
        <h2>Retail AI Agent</h2>
        <div className="chat-box">
          {chatHistory.map((msg, i) => (
            <div key={i} className={`msg ${msg.role}`}>{msg.text}</div>
          ))}
        </div>
        <div className="input-area">
          <input 
            value={query} 
            onChange={(e) => setQuery(e.target.value)} 
            placeholder="Search category (e.g. electronics)..."
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button onClick={handleSearch} disabled={loading}>
            {loading ? '...' : 'Ask'}
          </button>
        </div>
      </div>

      {/* Main Content Tiles */}
      <div className="main-content">
        <header>
          <h1>Marketplace Discovery</h1>
          <p>Showing products with High AI-Readiness Scores</p>
        </header>
        <div className="tiles-grid">
          {results.length > 0 ? (
            results.map((p, i) => <ProductTile key={i} product={p} />)
          ) : (
            <div className="placeholder">Start a chat to see suggestions...</div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;   