import { useEffect } from 'react';
import type { RefObject } from 'react';

/** Selector for the elements a focus scope considers tabbable. */
export const FOCUSABLE =
  'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])';

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

/** Focus discipline for dialogs and drawers: on activation, move focus to the
    first tabbable element inside `root`; on deactivation (or unmount), return
    focus to whatever had it before. The one place this bookkeeping lives, so
    no dialog re-implements it. */
export function useFocusScope(root: RefObject<HTMLElement | null>, active: boolean): void {
  useEffect(() => {
    if (!active) return;
    const previous = document.activeElement instanceof HTMLElement ? document.activeElement : null;
    root.current?.querySelector<HTMLElement>(FOCUSABLE)?.focus();
    return () => previous?.focus();
  }, [root, active]);
}
