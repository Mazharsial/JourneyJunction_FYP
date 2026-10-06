interface Props {
  tone?: "error" | "success" | "info";
  children: React.ReactNode;
}

const tones = {
  error: "border-error/30 bg-error/10 text-error",
  success: "border-success/30 bg-success/10 text-success",
  info: "border-teal/30 bg-teal/10 text-teal",
};

export function Alert({ tone = "info", children }: Props) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`rounded-xl border px-3.5 py-2.5 text-sm ${tones[tone]}`}
    >
      {children}
    </div>
  );
}
