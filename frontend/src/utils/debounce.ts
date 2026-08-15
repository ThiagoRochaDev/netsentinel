// Coalesces bursty triggers (e.g. many WebSocket messages arriving within
// milliseconds of each other) into a single call — protects the UI from
// hammering the API / re-rendering on every individual message during a
// burst. Trailing-edge only: fires once, `waitMs` after the last call.
export function debounce<T extends (...args: never[]) => void>(fn: T, waitMs: number): T {
  let timer: ReturnType<typeof setTimeout> | undefined;
  return ((...args: Parameters<T>) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), waitMs);
  }) as T;
}
