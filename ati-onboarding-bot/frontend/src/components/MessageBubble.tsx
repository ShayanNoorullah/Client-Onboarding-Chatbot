import type { ChatMessage } from "../types/chat";

function linkify(text: string) {
  const urlRegex = /(https?:\/\/[^\s]+)/g;
  const parts = text.split(urlRegex);
  return parts.map((part, i) =>
    urlRegex.test(part) ? (
      <a key={i} href={part} target="_blank" rel="noreferrer" className="underline text-blue-600">
        {part}
      </a>
    ) : (
      <span key={i}>{part}</span>
    )
  );
}

export default function MessageBubble({ message }: { message: ChatMessage }) {
  const isUser = message.role === "user";
  const isSystem = message.role === "system";

  if (isSystem) {
    return (
      <div className="flex justify-center">
        <div className="bg-amber-50 text-amber-800 text-sm px-4 py-2 rounded-lg max-w-md text-center">
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"}`}>
      <div
        className={`max-w-[85%] px-4 py-3 rounded-2xl text-sm leading-relaxed whitespace-pre-wrap ${
          isUser
            ? "bg-ati-navy text-white rounded-br-sm"
            : "bg-ati-light text-ati-navy rounded-bl-sm"
        }`}
      >
        {linkify(message.content)}
      </div>
    </div>
  );
}
