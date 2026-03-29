import type { ReactNode } from "react";

type PageHeaderProps = {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
};

export function PageHeader({ eyebrow, title, description, actions }: PageHeaderProps) {
  return (
    <section
      className="rounded-[20px] p-5 sm:p-6"
      style={{
        background: "rgba(255,255,255,0.028)",
        border: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-2xl">
          <p className="text-[10px] font-semibold uppercase tracking-[0.22em] text-[#6ce3cf]/80">
            {eyebrow}
          </p>
          <h2
            className="mt-2 text-[1.5rem] font-bold leading-tight tracking-[-0.02em] text-white sm:text-[1.75rem]"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            {title}
          </h2>
          <p className="mt-2 text-[13px] leading-relaxed text-slate-500">
            {description}
          </p>
        </div>
        {actions && (
          <div className="shrink-0">{actions}</div>
        )}
      </div>
    </section>
  );
}