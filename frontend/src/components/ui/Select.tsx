"use client";

import { type SelectHTMLAttributes } from "react";

interface Option {
  value: string;
  label: string;
}
interface Props extends SelectHTMLAttributes<HTMLSelectElement> {
  label: string;
  options: Option[];
  placeholder?: string;
}

export function Select({ label, options, placeholder, id, name, className = "", ...rest }: Props) {
  const selectId = id || name || label.toLowerCase().replace(/\s+/g, "-");
  return (
    <div className="space-y-1.5">
      <label htmlFor={selectId} className="block text-sm font-medium text-foreground">
        {label}
      </label>
      <select
        id={selectId}
        name={name}
        className={`w-full rounded-xl border border-border bg-surface px-3.5 py-2.5 text-sm text-foreground outline-none transition focus:border-teal focus:ring-2 focus:ring-teal/30 ${className}`}
        {...rest}
      >
        {placeholder && <option value="">{placeholder}</option>}
        {options.map((o) => (
          <option key={o.value} value={o.value}>
            {o.label}
          </option>
        ))}
      </select>
    </div>
  );
}
