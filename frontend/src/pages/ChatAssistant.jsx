import { useState, useRef, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../api/client.js";

const SUGGESTIONS = [
  "Which machines need maintenance today?",
  "Summarize today's high-risk alerts.",
  "What machines have the lowest health score?",
];

export default function ChatAssistant() {
  const [messages, setMessages] = useState([
    {
      role: "assistant",
      text: "I'm your maintenance copilot. Ask me about machine health, failure risk, or what needs attention today.",
      refs: [],
    },
  ]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const scrollRef = useRef(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: "smooth" });
  }, [messages]);

  async function send(question) {
    if (!question.trim() || loading) return;
    setMessages((m) => [...m, { role: "user", text: question, refs: [] }]);
    setInput("");
    setLoading(true);
    try {
      const res = await api.askChat(question);
      setMessages((m) => [...m, { role: "assistant", text: res.answer, refs: res.referenced_machine_ids }]);
    } catch (e) {
      setMessages((m) => [...m, { role: "assistant", text: `Something went wrong: ${e.message}`, refs: [] }]);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="flex flex-col h-[calc(100vh-56px)] max-w-3xl">
      <header className="mb-4">
        <p className="text-xs uppercase tracking-wider text-signal-cyan mb-1">AI Assistant</p>
        <h2 className="font-display text-2xl font-semibold">Ask FactoryPulse</h2>
      </header>

      <div ref={scrollRef} className="flex-1 overflow-y-auto panel p-5 space-y-4 mb-4">
        {messages.map((m, i) => (
          <div key={i} className={`flex ${m.role === "user" ? "justify-end" : "justify-start"}`}>
            <div
              className={`max-w-[85%] rounded-xl px-4 py-3 text-sm leading-relaxed whitespace-pre-line ${
                m.role === "user" ? "bg-signal-cyan/15 text-ink-100" : "bg-base-800 text-ink-200"
              }`}
            >
              {m.text}
              {m.refs?.length > 0 && (
                <div className="flex flex-wrap gap-1.5 mt-2">
                  {m.refs.map((id) => (
                    <Link
                      key={id}
                      to={`/machines/${id}`}
                      className="text-[11px] px-2 py-0.5 rounded bg-base-700 text-signal-cyan hover:bg-base-600"
                    >
                      {id}
                    </Link>
                  ))}
                </div>
              )}
            </div>
          </div>
        ))}
        {loading && <p className="text-xs text-ink-500">FactoryPulse is thinking...</p>}
      </div>

      <div className="flex flex-wrap gap-2 mb-3">
        {SUGGESTIONS.map((s) => (
          <button
            key={s}
            onClick={() => send(s)}
            className="text-xs px-3 py-1.5 rounded-lg border border-base-700 text-ink-300 hover:border-signal-cyan/40 hover:text-signal-cyan transition-colors"
          >
            {s}
          </button>
        ))}
      </div>

      <form
        onSubmit={(e) => {
          e.preventDefault();
          send(input);
        }}
        className="flex gap-2"
      >
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Ask about a machine, e.g. Why is M-105 critical?"
          className="flex-1 bg-base-900 border border-base-700 rounded-lg px-4 py-3 text-sm outline-none focus:border-signal-cyan/50"
        />
        <button
          type="submit"
          disabled={loading}
          className="px-5 py-3 rounded-lg bg-signal-cyan/15 text-signal-cyan text-sm font-medium hover:bg-signal-cyan/25 transition-colors disabled:opacity-40"
        >
          Ask
        </button>
      </form>
    </div>
  );
}
