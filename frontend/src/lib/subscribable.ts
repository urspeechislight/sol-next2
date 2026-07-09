// A minimal listener registry for useSyncExternalStore-backed stores, so each
// store (theme, search history, and any future one) shares one subscribe/notify
// pair instead of reimplementing the boilerplate.

export interface Subscribable {
  subscribe: (listener: () => void) => () => void;
  notify: () => void;
}

export function createSubscribable(): Subscribable {
  const listeners = new Set<() => void>();
  const subscribe = (listener: () => void): (() => void) => {
    listeners.add(listener);
    return () => {
      listeners.delete(listener);
    };
  };
  const notify = (): void => {
    for (const listener of listeners) listener();
  };
  return { subscribe, notify };
}
