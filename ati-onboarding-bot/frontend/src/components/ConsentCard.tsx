interface Props {
  visible: boolean;
  onAgree: () => void;
  disabled: boolean;
}

export default function ConsentCard({ visible, onAgree, disabled }: Props) {
  if (!visible) return null;

  return (
    <div className="mx-4 mb-3 p-4 rounded-xl border-2 border-ati-gold/40 bg-amber-50/50">
      <p className="text-sm text-ati-navy mb-3">
        Before we begin, ATI collects your name, project details, and uploaded files to prepare your brief.
        Data is not sold to third parties.{" "}
        <a
          href="https://awesometechinc.com/privacy-policy/"
          target="_blank"
          rel="noreferrer"
          className="underline text-blue-600"
        >
          Privacy Policy
        </a>
      </p>
      <button
        type="button"
        onClick={onAgree}
        disabled={disabled}
        className="w-full sm:w-auto px-6 py-2.5 bg-green-600 hover:bg-green-700 text-white font-semibold rounded-lg disabled:opacity-50 transition-colors"
      >
        I Agree — Continue
      </button>
    </div>
  );
}
