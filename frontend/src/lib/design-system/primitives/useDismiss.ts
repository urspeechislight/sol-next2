import { useEffect } from 'react';
import type { RefObject } from 'react';

/** Close-on-Escape and close-on-outside-click for an anchored popover: the
    one dismissal behavior shared by every floating surface (Menu's listbox,
    the filter popover), so no component re-implements document listeners. */
export function useDismiss(
  root: RefObject<HTMLElement | null>,
  open: boolean,
  onClose: () => void,
): void {
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) onClose();
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('mousedown', onDoc);
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('mousedown', onDoc);
      document.removeEventListener('keydown', onKey);
    };
  }, [root, open, onClose]);
}
