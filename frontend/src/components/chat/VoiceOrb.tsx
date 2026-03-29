import { AudioLines, Mic, ShieldCheck, Sparkles } from "lucide-react";

export function VoiceOrb() {
  const readinessItems = [
    {
      label: "Voice space",
      value: "Calm visual guidance",
      icon: <Mic className="h-4 w-4" />,
    },
    {
      label: "Current mode",
      value: "Text chat available now",
      icon: <AudioLines className="h-4 w-4" />,
    },
    {
      label: "Safety layer",
      value: "Context-aware responses",
      icon: <ShieldCheck className="h-4 w-4" />,
    },
  ];

  return (
    <section className="surface-card animate-rise-in rounded-[30px] border border-white/10 p-8 shadow-halo">
      <div className="flex flex-col items-center text-center">
        <div className="relative flex h-56 w-56 items-center justify-center">
          <div className="animate-pulse-soft absolute inset-0 rounded-full border border-brand-300/14" />
          <div className="animate-drift absolute inset-5 rounded-full border border-brand-300/12" />
          <div className="absolute inset-10 rounded-full border border-white/10" />
          <div className="animate-float-slow flex h-28 w-28 items-center justify-center rounded-full bg-gradient-to-br from-brand-300 via-brand-400 to-[#ffe7b5] text-ink shadow-[0_0_45px_rgba(108,227,207,0.28)]">
            <Mic className="h-11 w-11" />
          </div>
        </div>
        <div className="rounded-full border border-brand-300/20 bg-brand-400/10 px-4 py-2 text-sm text-brand-300">
          Gentle voice workspace
        </div>
        <h3 className="mt-5 font-display text-2xl font-semibold text-white">
          A soft focal point for guided check-ins
        </h3>
        <p className="mt-4 max-w-lg text-sm leading-7 text-slate-300">
          Motion stays intentionally light so the interface feels alive without becoming
          distracting. Text conversation remains the primary path while voice support grows.
        </p>
        <div className="mt-8 grid w-full gap-3 text-left sm:grid-cols-3">
          {readinessItems.map((item) => (
            <div
              key={item.label}
              className="rounded-[24px] border border-white/8 bg-white/[0.03] p-4"
            >
              <div className="inline-flex rounded-2xl bg-brand-400/12 p-2 text-brand-300">
                {item.icon}
              </div>
              <p className="mt-3 text-xs uppercase tracking-[0.24em] text-slate-500">
                {item.label}
              </p>
              <p className="mt-2 text-sm font-medium text-slate-100">{item.value}</p>
            </div>
          ))}
        </div>
        <div className="mt-6 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/[0.03] px-4 py-2 text-sm text-slate-300">
          <Sparkles className="h-4 w-4 text-gold" />
          Designed to support attention, not steal it.
        </div>
      </div>
    </section>
  );
}
