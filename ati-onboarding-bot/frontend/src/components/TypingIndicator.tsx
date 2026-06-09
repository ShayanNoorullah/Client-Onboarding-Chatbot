export default function TypingIndicator() {
  return (
    <div className="flex items-start">
      <div className="bg-ati-light text-ati-navy rounded-2xl rounded-bl-sm px-4 py-3 flex gap-1.5">
        <span className="typing-dot w-2 h-2 bg-ati-navy/40 rounded-full" />
        <span className="typing-dot w-2 h-2 bg-ati-navy/40 rounded-full" />
        <span className="typing-dot w-2 h-2 bg-ati-navy/40 rounded-full" />
      </div>
    </div>
  );
}
