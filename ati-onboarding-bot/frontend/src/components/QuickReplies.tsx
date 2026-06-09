interface Props {
  suggestions: string[];
  disabled: boolean;
  onSelect: (text: string) => void;
}

export default function QuickReplies({ suggestions, disabled, onSelect }: Props) {
  if (!suggestions.length) return null;

  return (
    <div className="flex flex-wrap gap-2 px-4 py-2">
      {suggestions.map((s) => (
        <button
          key={s}
          type="button"
          disabled={disabled}
          onClick={() => onSelect(s)}
          className="px-3 py-1.5 text-sm rounded-full border border-ati-navy/20 text-ati-navy bg-white hover:bg-ati-light disabled:opacity-40 transition-colors"
        >
          {s}
        </button>
      ))}
    </div>
  );
}
