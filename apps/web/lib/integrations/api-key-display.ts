export function formatAPIKeyScope(
  value: string,
): string {
  return value
    .split(/[._:-]+/)
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1),
    )
    .join(" ");
}

export function parseAPIKeyScopes(
  value: string,
): string[] {
  return Array.from(
    new Set(
      value
        .split(/[\s,]+/)
        .map((scope) => scope.trim())
        .filter(Boolean),
    ),
  );
}