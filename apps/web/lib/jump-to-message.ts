export function jumpToMessage(elementId: string): boolean {
  const target = document.getElementById(elementId);

  if (!target) return false;

  const reducedMotion = window.matchMedia(
    "(prefers-reduced-motion: reduce)",
  ).matches;

  target.scrollIntoView({
    behavior: reducedMotion ? "auto" : "smooth",
    block: "center",
    inline: "nearest",
  });

  return true;
}
