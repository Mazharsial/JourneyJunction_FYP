"use client";

import { forwardRef, type InputHTMLAttributes } from "react";

interface Props extends InputHTMLAttributes<HTMLInputElement> {
  label: string;
  error?: string;
}

export const Input = forwardRef<HTMLInputElement, Props>(function Input(
  { label, error, id, className = "", ...rest },
  ref,
) {
  const inputId = id || rest.name || label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="space-y-1.5">
      <label htmlFor={inputId} className="block text-sm font-medium text-foreground">
        {label}
      </label>
      <input
        id={inputId}
        ref={ref}
        aria-invalid={!!error}
        aria-describedby={error ? `${inputId}-error` : undefined}
        className={`w-full rounded-xl border bg-surface px-3.5 py-2.5 text-sm text-foreground outline-none transition placeholder:text-muted focus:border-teal focus:ring-2 focus:ring-teal/30 ${
          error ? "border-error" : "border-border"
        } ${className}`}
        {...rest}
      />
      {error && (
        <p id={`${inputId}-error`} className="text-xs text-error">
          {error}
        </p>
      )}
    </div>
  );
});
