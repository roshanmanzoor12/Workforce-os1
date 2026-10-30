import type {
  ButtonHTMLAttributes,
  ReactNode,
} from "react";

type ButtonVariant =
  | "primary"
  | "brand"
  | "outline"
  | "ghost"
  | "danger";

type ButtonSize =
  | "sm"
  | "md"
  | "lg";

interface ButtonProps
  extends ButtonHTMLAttributes<HTMLButtonElement> {
  children: ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  loading?: boolean;
}

const variantClassNames: Record<
  ButtonVariant,
  string
> = {
  primary: "button--primary",
  brand: "button--brand",
  outline: "button--outline",
  ghost: "button--ghost",
  danger: "button--danger",
};

const sizeClassNames: Record<
  ButtonSize,
  string
> = {
  sm: "button--sm",
  md: "",
  lg: "button--lg",
};

export function Button({
  children,
  variant = "primary",
  size = "md",
  loading = false,
  disabled,
  className = "",
  type = "button",
  ...props
}: ButtonProps) {
  const classes = [
    "button",
    variantClassNames[variant],
    sizeClassNames[size],
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button
      {...props}
      type={type}
      className={classes}
      disabled={disabled || loading}
      aria-busy={loading || undefined}
    >
      {loading ? (
        <span
          aria-hidden="true"
          style={{
            width: 13,
            height: 13,
            border: "2px solid currentColor",
            borderRightColor: "transparent",
            borderRadius: "50%",
            animation:
              "workforce-button-spin 700ms linear infinite",
          }}
        />
      ) : null}

      {children}
    </button>
  );
}