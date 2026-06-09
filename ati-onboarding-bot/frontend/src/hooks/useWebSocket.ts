import { useCallback, useEffect, useRef, useState } from "react";
import type { ChatMessage, ServerMessage, Stage } from "../types/chat";

function uid() {
  return Math.random().toString(36).slice(2, 10);
}

export function useWebSocket() {
  const sessionId = useRef(crypto.randomUUID());
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [waiting, setWaiting] = useState(false);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [stage, setStage] = useState<Stage>("consent");
  const [suggestions, setSuggestions] = useState<string[]>(["I agree"]);
  const [done, setDone] = useState(false);
  const [refId, setRefId] = useState<string | null>(null);
  const [consentGiven, setConsentGiven] = useState(false);
  const [clientName, setClientName] = useState<string | null>(null);
  const [assetsCount, setAssetsCount] = useState(0);
  const [error, setError] = useState<string | null>(null);

  const addMessage = useCallback((role: ChatMessage["role"], content: string) => {
    setMessages((prev) => [...prev, { id: uid(), role, content }]);
  }, []);

  const handleServerMessage = useCallback((data: ServerMessage) => {
    setWaiting(false);
    setError(null);
    if (data.content?.trim()) {
      addMessage("assistant", data.content);
    }
    if (data.stage) setStage(data.stage);
    if (data.suggestions) setSuggestions(data.suggestions);
    if (data.consent_given !== undefined) setConsentGiven(data.consent_given);
    if (data.client_name !== undefined) setClientName(data.client_name);
    if (data.assets_count !== undefined) setAssetsCount(data.assets_count);
    if (data.done) {
      setDone(true);
      if (data.ref_id) setRefId(data.ref_id);
    }
  }, [addMessage]);

  useEffect(() => {
    let disposed = false;
    const protocol = location.protocol === "https:" ? "wss:" : "ws:";
    const ws = new WebSocket(`${protocol}//${location.host}/ws/chat/${sessionId.current}`);
    wsRef.current = ws;

    ws.onopen = () => {
      if (disposed) return;
      setConnected(true);
      setError(null);
    };
    ws.onclose = () => {
      if (disposed) return;
      setConnected(false);
      setWaiting(false);
    };
    ws.onerror = () => {
      if (disposed) return;
      setError("Connection error. Is the server running on port 8001?");
      setWaiting(false);
    };
    ws.onmessage = (ev) => {
      if (disposed) return;
      try {
        handleServerMessage(JSON.parse(ev.data));
      } catch {
        setError("Could not parse server response.");
        setWaiting(false);
      }
    };

    return () => {
      disposed = true;
      ws.onopen = null;
      ws.onclose = null;
      ws.onerror = null;
      ws.onmessage = null;
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  }, [handleServerMessage]);

  const sendPayload = useCallback((payload: object) => {
    const ws = wsRef.current;
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      setError("Not connected yet. Wait a moment, then try again.");
      return false;
    }
    if (waiting) return false;
    setWaiting(true);
    setError(null);
    ws.send(JSON.stringify(payload));
    return true;
  }, [waiting]);

  const sendMessage = useCallback((text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    addMessage("user", trimmed);
    sendPayload({ message: trimmed });
  }, [addMessage, sendPayload]);

  const sendAgree = useCallback(() => {
    addMessage("user", "I agree");
    sendPayload({ action: "agree", message: "I agree" });
  }, [addMessage, sendPayload]);

  return {
    sessionId: sessionId.current,
    connected,
    waiting,
    messages,
    stage,
    suggestions,
    done,
    refId,
    consentGiven,
    clientName,
    assetsCount,
    error,
    sendMessage,
    sendAgree,
    addMessage,
    setWaiting,
    setError,
  };
}
