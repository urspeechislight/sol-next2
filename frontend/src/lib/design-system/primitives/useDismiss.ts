import { useEffect } from 'react';
import type { RefObject } from 'react';

/** Close-on-Escape for any dismissible surface: the one document key listener
    shared by popovers and drawers alike, so no component re-implements it. */
export function useEscape(onClose: () => void, active = true): void {
  useEffect(() => {
    if (!active) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') onClose();
    };
    document.addEventListener('keydown', onKey);
    return () => {
      document.removeEventListener('keydown', onKey);
    };
  }, [onClose, active]);
}

/** Close-on-Escape and close-on-outside-click for an anchored popover: the
    dismissal behavior shared by every floating surface (Menu's listbox, the
    filter popover), so no component re-implements document listeners. */
export function useDismiss(
  root: RefObject<HTMLElement | null>,
  open: boolean,
  onClose: () => void,
): void {
  useEscape(onClose, open);
  useEffect(() => {
    if (!open) return;
    const onDoc = (e: MouseEvent) => {
      if (root.current && !root.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', onDoc);
    return () => {
      document.removeEventListener('mousedown', onDoc);
    };
  }, [root, open, onClose]);
}
