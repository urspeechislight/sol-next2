/** The visual surface a control renders on: "app" (the parchment chrome) or
    "reader" (the reading surface, which re-points to the reader palette). One
    shared type so every primitive that takes a `surface` prop agrees on the
    values, instead of each importing it from a sibling primitive. */
export type Surface = 'app' | 'reader';
