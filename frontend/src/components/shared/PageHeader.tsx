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
        background: "#172032",
        border: "1px solid rgba(55,75,105,0.5)",
      }}
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="max-w-2xl">
          <p className="label-caps" style={{ color: "#4a84d6" }}>
            {eyebrow}
          </p>
          <h2
            className="mt-2 text-[1.5rem] font-bold leading-tight tracking-tight text-white sm:text-[1.75rem]"
            style={{ fontFamily: "'Space Grotesk', sans-serif" }}
          >
            {title}
          </h2>
          <p className="mt-2 text-[13px] leading-relaxed" style={{ color: "#7a92a8" }}>
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