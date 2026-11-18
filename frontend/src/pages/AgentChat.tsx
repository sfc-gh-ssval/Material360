import { useState, useRef, useEffect } from "react";
import Markdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { agentChat } from "../services/api";

interface Message {
  role: "user" | "agent";
  content: string;
}

const INITIAL_MSG: Message = {
  role: "agent",
  content: "How can I help you with the engineering drawings? I can search across all parsed drawings for parts, materials, dimensions, and more.",
};

// Persist messages across navigation within the session
let sessionMessages: Message[] = [INITIAL_MSG];

export default function AgentChat() {
  const [messages, setMessages] = useState<Message[]>(sessionMessages);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const topRef = useRef<HTMLDivElement>(null);

  // Sync module-level cache whenever messages change
  useEffect(() => {
    sessionMessages = messages;
  }, [messages]);

  useEffect(() => {
    topRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const send = async () => {
    if (!input.trim() || loading) return;
    const question = input.trim();
    setInput("");
    setMessages((prev) => [...prev, { role: "user", content: question }]);
    setLoading(true);

    try {
      const res = await agentChat(question);
      setMessages((prev) => [...prev, { role: "agent", content: res.answer }]);
    } catch {
      setMessages((prev) => [...prev, { role: "agent", content: "Sorry, something went wrong. Please try again." }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChat = () => {
    setMessages([INITIAL_MSG]);
  };

  // Display messages in reverse order (latest on top)
  const reversed = [...messages].reverse();

  return (
    <div className="chat-page">
      <div className="chat-header">
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "flex-start" }}>
          <div>
            <h2>Drawing Analysis Agent</h2>
            <p>Ask questions about your engineering drawings, materials, dimensions, and BOM data.</p>
          </div>
          <button className="chat-clear" onClick={clearChat} disabled={messages.length <= 1}>
            Clear
          </button>
        </div>
      </div>

      <div className="chat-input-area" style={{ borderTop: "none", borderBottom: "1px solid var(--border)" }}>
        <input
          className="chat-input"
          placeholder="Ask about drawings, parts, materials, dimensions..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && send()}
          disabled={loading}
        />
        <button className="chat-send" onClick={send} disabled={loading || !input.trim()}>
          {loading ? "..." : "Send"}
        </button>
      </div>

      <div className="chat-messages">
        <div ref={topRef} />
        {loading && (
          <div className="chat-msg">
            <div className="chat-avatar agent">AI</div>
            <div className="chat-bubble" style={{ color: "var(--text-muted)" }}>
              Searching drawings and analyzing...
            </div>
          </div>
        )}
        {reversed.map((m, i) => (
          <div key={messages.length - 1 - i} className="chat-msg">
            <div className={`chat-avatar ${m.role}`}>{m.role === "agent" ? "AI" : "You"}</div>
            <div className="chat-bubble"><Markdown remarkPlugins={[remarkGfm]}>{m.content}</Markdown></div>
          </div>
        ))}
      </div>
    </div>
  );
}
