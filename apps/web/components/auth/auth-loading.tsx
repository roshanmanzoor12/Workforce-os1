interface AuthLoadingProps {
  title?: string;
  message?: string;
}

export function AuthLoading({
  title = "Loading",
  message = "Please wait while Workforce OS loads your account.",
}: AuthLoadingProps) {
  return (
    <section
      className="panel"
      style={{
        width: "min(100%, 460px)",
        padding: 32,
        textAlign: "center",
      }}
    >
      <div
        className="auth-submit-spinner"
        style={{
          margin:
            "0 auto 16px",
        }}
      />

      <h1
        style={{
          margin: 0,
          fontSize: 22,
          fontWeight: 600,
        }}
      >
        {title}
      </h1>

      <p
        className="text-label"
        style={{
          marginTop: 8,
          lineHeight: 1.65,
        }}
      >
        {message}
      </p>
    </section>
  );
}