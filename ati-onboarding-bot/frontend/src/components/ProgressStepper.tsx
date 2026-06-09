import type { Stage } from "../types/chat";

const STEPS = [
  { id: "consent", label: "Consent" },
  { id: "identity", label: "Name" },
  { id: "requirements", label: "Project" },
  { id: "clarify", label: "Files" },
  { id: "summarise", label: "Brief" },
];

function stageIndex(stage: Stage): number {
  const map: Record<string, number> = {
    greeting: 0,
    consent: 0,
    identity: 1,
    requirements: 2,
    clarify: 3,
    summarise: 4,
    error: -1,
  };
  return map[stage] ?? 0;
}

export default function ProgressStepper({ stage, done }: { stage: Stage; done: boolean }) {
  const current = done ? STEPS.length : stageIndex(stage);

  return (
    <div className="px-4 py-3 bg-white border-b border-slate-200">
      <div className="flex items-center justify-between max-w-lg mx-auto">
        {STEPS.map((step, i) => {
          const active = i <= current;
          const isCurrent = i === current && !done;
          return (
            <div key={step.id} className="flex flex-col items-center flex-1">
              <div
                className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-semibold transition-colors ${
                  active
                    ? isCurrent
                      ? "bg-ati-gold text-white ring-2 ring-ati-gold/30"
                      : "bg-ati-navy text-white"
                    : "bg-slate-200 text-slate-500"
                }`}
              >
                {i + 1}
              </div>
              <span className={`text-[10px] mt-1 hidden sm:block ${active ? "text-ati-navy font-medium" : "text-slate-400"}`}>
                {step.label}
              </span>
              {i < STEPS.length - 1 && (
                <div className="hidden sm:block absolute" />
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
