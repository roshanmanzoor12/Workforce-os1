"use client";

import { Search, X } from "lucide-react";
import type {
  ChangeEvent,
  InputHTMLAttributes,
} from "react";

interface SearchInputProps
  extends Omit<
    InputHTMLAttributes<HTMLInputElement>,
    "type" | "onChange"
  > {
  value: string;
  onChange: (value: string) => void;
  onClear?: () => void;
}

export function SearchInput({
  value,
  onChange,
  onClear,
  placeholder = "Search",
  disabled,
  ...props
}: SearchInputProps) {
  function handleChange(
    event: ChangeEvent<HTMLInputElement>,
  ) {
    onChange(event.target.value);
  }

  function handleClear() {
    onChange("");
    onClear?.();
  }

  return (
    <div
      className="input-group"
      style={{
        width: "100%",
      }}
    >
      <Search
        aria-hidden="true"
        size={15}
        strokeWidth={1.8}
        className="input-group__icon"
      />

      <input
        {...props}
        type="search"
        className="input"
        value={value}
        disabled={disabled}
        placeholder={placeholder}
        onChange={handleChange}
        style={{
          paddingRight: value ? 38 : 12,
        }}
      />

      {value ? (
        <button
          type="button"
          aria-label="Clear search"
          onClick={handleClear}
          disabled={disabled}
          style={{
            position: "absolute",
            top: "50%",
            right: 8,
            display: "grid",
            width: 26,
            height: 26,
            placeItems: "center",
            border: 0,
            borderRadius: 6,
            background: "transparent",
            color: "var(--color-text-muted)",
            cursor: disabled
              ? "not-allowed"
              : "pointer",
            transform: "translateY(-50%)",
          }}
        >
          <X
            size={14}
            strokeWidth={1.8}
          />
        </button>
      ) : null}
    </div>
  );
}