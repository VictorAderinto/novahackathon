import React, { useState, useRef, useEffect } from 'react';
import ReactMarkdown from 'react-markdown';
import { Send, Bot, User } from 'lucide-react';

function ChatInterface({ onSendMessage, isProcessing }) {
    const [messages, setMessages] = useState([
        { role: 'system', text: "Welcome to the **Power System Nova Helper**. Load a case to begin." }
    ]);
    const [input, setInput] = useState("");
    const messagesEndRef = useRef(null);

    const scrollToBottom = () => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    };

    useEffect(scrollToBottom, [messages]);

    const handleSend = async () => {
        if (!input.trim()) return;

        const userMsg = { role: 'user', text: input };
        setMessages(prev => [...prev, userMsg]);
        setInput("");

        try {
            const response = await onSendMessage(input);
            const botMsg = { role: 'assistant', text: response };
            setMessages(prev => [...prev, botMsg]);
        } catch (err) {
            const errorMsg = { role: 'error', text: "Failed to get response." };
            setMessages(prev => [...prev, errorMsg]);
        }
    };

    const handleKeyDown = (e) => {
        if (e.key === 'Enter') handleSend();
    };

    return (
        <div className="chat-panel">
            <div className="chat-header">
                <h2><Bot size={20} color="#8b5cf6" /> Nova Assistant</h2>
            </div>

            <div className="messages-container">
                {messages.map((msg, i) => (
                    <div key={i} className={`message ${msg.role}`}>
                        <div className="bubble">
                            <ReactMarkdown>{msg.text}</ReactMarkdown>
                        </div>
                    </div>
                ))}
                {isProcessing && (
                    <div className="message assistant">
                        <div className="bubble processing">
                            Thinking...
                        </div>
                    </div>
                )}
                <div ref={messagesEndRef} />
            </div>

            <div className="input-area">
                <input
                    type="text"
                    value={input}
                    onChange={(e) => setInput(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder="Ask about the grid (e.g., 'Simulate outage on Line 5')..."
                    disabled={isProcessing}
                />
                <button onClick={handleSend} disabled={isProcessing}>
                    <Send size={18} />
                </button>
            </div>
        </div>
    );
}

export default ChatInterface;
