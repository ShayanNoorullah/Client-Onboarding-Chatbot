import { useEffect, useRef, useState } from "react";
import { useWebSocket } from "../hooks/useWebSocket";
import type { UploadedAsset } from "../types/chat";
import ConsentCard from "./ConsentCard";
import FileUploadZone from "./FileUploadZone";
import MessageBubble from "./MessageBubble";
import ProgressStepper from "./ProgressStepper";
import QuickReplies from "./QuickReplies";
import TypingIndicator from "./TypingIndicator";

export default function ChatLayout() {
  const {
    sessionId,
    connected,
    waiting,
    messages,
    stage,
    suggestions,
    done,
    refId,
    consentGiven,
    clientName,
    error,
    sendMessage,
    sendAgree,
    addMessage,
  } = useWebSocket();

  const [input, setInput] = useState("");
  const [assets, setAssets] = useState<UploadedAsset[]>([]);
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, waiting]);

  const handleSend = () => {
    if (!input.trim()) return;
    sendMessage(input);
    setInput("");
  };

  const handleSuggestion = (text: string) => {
    if (text.toLowerCase() === "i agree") {
      sendAgree();
    } else {
      sendMessage(text);
    }
  };

  const handleUploaded = (asset: UploadedAsset, notify: string) => {
    setAssets((prev) => [...prev, asset]);
    sendMessage(notify);
  };

  const showConsentCard = !consentGiven && (stage === "consent" || stage === "greeting");
  const showFileUpload = consentGiven && !!clientName && !done;

  return (
    <div className="min-h-screen flex items-center justify-center p-4 bg-slate-100">
      <div className="w-full max-w-2xl bg-white rounded-2xl shadow-xl flex flex-col h-[90vh] overflow-hidden">
        <header className="bg-ati-navy text-white px-6 py-4">
          <h1 className="text-lg font-semibold">ATI Onboarding Assistant</h1>
          <p className="text-sm text-white/70">Awesome Technologies Inc.</p>
        </header>

        <ProgressStepper stage={stage} done={done} />

        {error && (
          <div className="mx-4 mt-3 px-4 py-2 bg-red-50 text-red-700 text-sm rounded-lg border border-red-200">
            {error}
          </div>
        )}

        <ConsentCard visible={showConsentCard} onAgree={sendAgree} disabled={waiting} />

        <div className="flex-1 overflow-y-auto px-4 py-4 space-y-3">
          {messages.map((m) => (
            <MessageBubble key={m.id} message={m} />
          ))}
          {waiting && <TypingIndicator />}
          {done && refId && (
            <div className="text-center text-sm text-green-700 bg-green-50 rounded-lg py-3 px-4">
              Brief complete! Reference ID: <strong>{refId}</strong>
            </div>
          )}
          <div ref={bottomRef} />
        </div>

        <FileUploadZone
          sessionId={sessionId}
          enabled={showFileUpload}
          assets={assets}
          onUploaded={handleUploaded}
          onNotify={(msg) => addMessage("system", msg)}
        />

        <QuickReplies
          suggestions={suggestions}
          disabled={waiting || done}
          onSelect={handleSuggestion}
        />

        <footer className="border-t border-slate-200 p-4">
          <div className="flex gap-2">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSend()}
              placeholder="Type your message..."
              disabled={waiting || done || !connected}
              className="flex-1 px-4 py-2.5 border border-slate-300 rounded-lg text-sm focus:outline-none focus:border-ati-navy disabled:opacity-50"
            />
            <button
              type="button"
              onClick={handleSend}
              disabled={waiting || done || !connected}
              className="px-5 py-2.5 bg-ati-navy text-white rounded-lg font-medium hover:bg-ati-navy/90 disabled:opacity-50 transition-colors"
            >
              Send
            </button>
          </div>
          <p className="text-xs text-slate-400 mt-2">
            {connected ? `Connected · Stage: ${stage}` : "Connecting..."}
          </p>
        </footer>
      </div>
    </div>
  );
}
