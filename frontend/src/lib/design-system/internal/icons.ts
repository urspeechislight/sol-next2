// internal/icons.ts:SSOT for icon path geometry. Plain TS, ports verbatim.
// Single 24×24 viewBox. Consumed only by the Icon primitive.
//
// HOUSE STYLE — the identity set is drawn in the site's line-art language
// (the gold logo-mark graphics): fine 1.5 strokes, round caps, and four
// recurring motifs — the pointed dome, the ogee arch, the ray-crowned
// medallion, and the beaded chain. Utility glyphs (chevrons, arrows, close,
// check, search, copy…) stay clean geometry so controls read at 16px.
// Stroke width lives in the Icon primitive, not here.

export type IconName =
  | 'library'
  | 'reader'
  | 'graph'
  | 'daily'
  | 'search'
  | 'book-search'
  | 'sun'
  | 'moon'
  | 'chevron-left'
  | 'chevron-right'
  | 'chevron-down'
  | 'chevron-up'
  | 'close'
  | 'arrow-right'
  | 'external'
  | 'scroll'
  | 'star'
  | 'node'
  | 'layers'
  | 'grid'
  | 'info'
  | 'quote'
  | 'filter'
  | 'pin'
  | 'compass'
  | 'menu'
  | 'book'
  | 'calendar'
  | 'sparkle'
  | 'settings'
  | 'gear'
  | 'check'
  | 'link'
  | 'llm'
  | 'minus'
  | 'plus'
  | 'chevrons-left'
  | 'chevrons-right'
  | 'arrow-left'
  | 'arrow-back'
  | 'arrow-forward'
  | 'network'
  | 'share'
  | 'copy'
  | 'download'
  | 'qr'
  | 'x'
  | 'instagram'
  | 'facebook'
  | 'tiktok'
  | 'type'
  | 'text-size'
  | 'bookmark'
  | 'clock'
  | 'globe'
  | 'tag'
  | 'users'
  | 'eye'
  | 'sliders'
  | 'bell'
  | 'maximize'
  | 'highlighter'
  | 'note';

export const ICON_PATHS: Record<IconName, string> = {
  // Pointed-arch gateway framing three folio spines: the catalogue's front door.
  library:
    'M4 20v-7C4 8.5 7.2 5 12 3c4.8 2 8 5.5 8 10v7M3 20h18M9.2 20v-8.5M12 20V10M14.8 20v-8.5',
  // Open folio spread with curved page edges.
  reader: 'M12 6C10.5 4.6 8.5 4 6 4v14c2.5 0 4.5.6 6 2 1.5-1.4 3.5-2 6-2V4c-2.5 0-4.5.6-6 2zM12 6v14',
  // Isnād graph: ray-crowned medallion over two receivers, closed triangle link.
  graph:
    'M12 1.4v1.2M9.3 2.1l.6.8M14.7 2.1l-.6.8M14.3 5.6a2.3 2.3 0 11-4.6 0 2.3 2.3 0 014.6 0zM10.8 7.6C9.4 9.9 8 13 7.2 16.3M13.2 7.6c1.4 2.3 2.8 5.4 3.6 8.7M9.7 18.4a2.2 2.2 0 11-4.4 0 2.2 2.2 0 014.4 0zM18.7 18.4a2.2 2.2 0 11-4.4 0 2.2 2.2 0 014.4 0zM9.7 18.4h4.6',
  daily: 'M12 7v5l3 2M12 3a9 9 0 109 9 9 9 0 00-9-9z',
  search: 'M11 19a8 8 0 100-16 8 8 0 000 16zM21 21l-4.3-4.3',
  // A scroll (rolled parchment, top-left curl + two text lines) under a
  // magnifying glass: "search inside this book". Replaces the flat book+lens
  // glyph that read as a phone.
  'book-search':
    'M16 3H8a2 2 0 00-2 2v1a2 2 0 01-2 2M6 5v13M16 3a2 2 0 012 2v4M9 8h5M9 11h3M15 13.5a3 3 0 100 6 3 3 0 100-6M19 18.5l2.4 2.4',
  sun: 'M12 17a5 5 0 100-10 5 5 0 000 10zM12 1v3M12 20v3M4.2 4.2l2 2M17.8 17.8l2 2M1 12h3M20 12h3M4.2 19.8l2-2M17.8 6.2l2-2',
  moon: 'M21 12.8A9 9 0 1111.2 3a7 7 0 009.8 9.8z',
  'chevron-left': 'M15 18l-6-6 6-6',
  'chevron-right': 'M9 18l6-6-6-6',
  'chevron-down': 'M6 9l6 6 6-6',
  'chevron-up': 'M18 15l-6-6-6 6',
  close: 'M18 6L6 18M6 6l12 12',
  'arrow-right': 'M5 12h14M13 6l6 6-6 6',
  external: 'M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 012-2h6M15 3h6v6M10 14L21 3',
  // Vertical scroll: left curl, rolled right edge, text lines.
  scroll:
    'M15 3H9a2 2 0 00-2 2v1a2 2 0 01-2 2M7 5v14a2 2 0 002 2h6a2 2 0 002-2V5a2 2 0 00-2-2M10 9h4M10 12h4M10 15h2.5',
  star: 'M12 2l2.6 6.3 6.8.5-5.2 4.4 1.6 6.6L12 16.8 6.2 20.4l1.6-6.6L2.6 9.4l6.8-.5z',
  // Single ray-crowned medallion node.
  node: 'M12 5.6v1.2M7.6 6.8l.9.9M16.4 6.8l-.9.9M5.4 11.2l1.2.4M18.6 11.2l-1.2.4M16 14.5a4 4 0 11-8 0 4 4 0 018 0zM12 14.5h.01',
  // Strata under a dome: extraction as layered structure.
  layers: 'M4.5 10.5C4.5 6.8 8 4.4 12 3c4 1.4 7.5 3.8 7.5 7.5M4.5 10.5h15M4 15h16M4 19.5h16',
  grid: 'M3 3h7v7H3zM14 3h7v7h-7zM14 14h7v7h-7zM3 14h7v7H3z',
  info: 'M12 16v-4M12 8h.01M12 22a10 10 0 100-20 10 10 0 000 20z',
  quote: 'M7 11H4a1 1 0 01-1-1V7a3 3 0 013-3M17 11h-3a1 1 0 01-1-1V7a3 3 0 013-3',
  filter: 'M3 4h18l-7 8v7l-4-2v-5z',
  pin: 'M12 22s7-7.6 7-13A7 7 0 005 9c0 5.4 7 13 7 13zM12 11a2 2 0 100-4 2 2 0 000 4z',
  compass: 'M12 22a10 10 0 100-20 10 10 0 000 20zM16.2 7.8l-2.1 6.3-6.3 2.1 2.1-6.3z',
  // Manuscript text lines: the last line runs short, like a justified folio.
  menu: 'M4 6h16M4 12h16M4 18h10',
  // Closed mushaf: cover with a pointed-arch window and baseline.
  book: 'M7 2h12v20H7a2 2 0 01-2-2V4a2 2 0 012-2zM10 13.5V11c0-1.8 1-2.9 2-3.5 1 .6 2 1.7 2 3.5v2.5zM10 16.5h4',
  calendar: 'M3 9h18M7 3v3M17 3v3M5 5h14a2 2 0 012 2v12a2 2 0 01-2 2H5a2 2 0 01-2-2V7a2 2 0 012-2z',
  sparkle: 'M12 3v4M12 17v4M3 12h4M17 12h4M6 6l2.5 2.5M15.5 15.5L18 18M18 6l-2.5 2.5M8.5 15.5L6 18',
  settings:
    'M12 9a3 3 0 100 6 3 3 0 000-6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z',
  gear: 'M12 9a3 3 0 100 6 3 3 0 000-6zM19.4 15a1.65 1.65 0 00.33 1.82l.06.06a2 2 0 11-2.83 2.83l-.06-.06a1.65 1.65 0 00-1.82-.33 1.65 1.65 0 00-1 1.51V21a2 2 0 11-4 0v-.09A1.65 1.65 0 009 19.4a1.65 1.65 0 00-1.82.33l-.06.06a2 2 0 11-2.83-2.83l.06-.06a1.65 1.65 0 00.33-1.82 1.65 1.65 0 00-1.51-1H3a2 2 0 110-4h.09A1.65 1.65 0 004.6 9a1.65 1.65 0 00-.33-1.82l-.06-.06a2 2 0 112.83-2.83l.06.06a1.65 1.65 0 001.82.33H9a1.65 1.65 0 001-1.51V3a2 2 0 114 0v.09a1.65 1.65 0 001 1.51 1.65 1.65 0 001.82-.33l.06-.06a2 2 0 112.83 2.83l-.06.06a1.65 1.65 0 00-.33 1.82V9a1.65 1.65 0 001.51 1H21a2 2 0 110 4h-.09a1.65 1.65 0 00-1.51 1z',
  check: 'M20 6L9 17l-5-5',
  link: 'M10 13a5 5 0 007 0l3-3a5 5 0 00-7-7l-1 1M14 11a5 5 0 00-7 0l-3 3a5 5 0 007 7l1-1',
  // LLM: ray-crowned lamp over an open folio — the logo-mark's radiant lamp.
  llm: 'M12 1.2v1.3M8.6 2.2l.7.9M15.4 2.2l-.7.9M9.8 8.4c0-2 1-3.4 2.2-4.4 1.2 1 2.2 2.4 2.2 4.4 0 .8-.4 1.4-1 1.8h-2.4c-.6-.4-1-1-1-1.8zM11 10.2h2M12 10.2v1.4M12 13.4c-1.2-1-2.7-1.4-4.8-1.4v6c2.1 0 3.6.5 4.8 1.4 1.2-.9 2.7-1.4 4.8-1.4v-6c-2.1 0-3.6.4-4.8 1.4zM12 13.4v6',
  minus: 'M5 12h14',
  plus: 'M12 5v14M5 12h14',
  'chevrons-left': 'M11 17l-5-5 5-5M18 17l-5-5 5-5',
  'chevrons-right': 'M13 17l5-5-5-5M6 17l5-5-5-5',
  'arrow-left': 'M21 12H5M12 5l-7 7 7 7',
  'arrow-back': 'M9 14 4 9l5-5M4 9h10.5a5.5 5.5 0 0 1 5.5 5.5 5.5 5.5 0 0 1-5.5 5.5H11',
  'arrow-forward': 'M15 14l5-5-5-5M20 9H9.5A5.5 5.5 0 0 0 4 14.5 5.5 5.5 0 0 0 9.5 20H13',
  // Isnād chain: ray-crowned beaded medallions, the logo's finial mast.
  network:
    'M12 1.4v1.1M9.3 2.2l.7.7M14.7 2.2l-.7.7M13.6 4.6a1.6 1.6 0 11-3.2 0 1.6 1.6 0 013.2 0zM12 6.2v4.2M13.6 12.5a1.6 1.6 0 11-3.2 0 1.6 1.6 0 013.2 0zM12 14.1v4.2M13.6 20.4a1.6 1.6 0 11-3.2 0 1.6 1.6 0 013.2 0z',
  share: 'M4 12v7a2 2 0 002 2h12a2 2 0 002-2v-7M16 6l-4-4-4 4M12 2v13',
  copy: 'M9 9h10a2 2 0 012 2v10a2 2 0 01-2 2H9a2 2 0 01-2-2V11a2 2 0 012-2zM5 15H4a2 2 0 01-2-2V4a2 2 0 012-2h9a2 2 0 012 2v1',
  download: 'M12 3v12M7 10l5 5 5-5M4 21h16',
  qr: 'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM15 15h2v2h-2zM19 15h2M15 19h2M19 19h2v2',
  x: 'M4 4l7 8.6L4.3 20H7l5-5.6L16.5 20H20l-7.3-8.9L19.4 4H16.8l-4.5 5.2L8 4z',
  instagram:
    'M7 2h10a5 5 0 015 5v10a5 5 0 01-5 5H7a5 5 0 01-5-5V7a5 5 0 015-5zM12 8a4 4 0 100 8 4 4 0 000-8zM17.5 6.5h.01',
  facebook: 'M14 9V7a1 1 0 011-1h2V3h-3a4 4 0 00-4 4v2H7v3h3v9h3v-9h2.5l.5-3z',
  tiktok: 'M15 3v11.5a3.5 3.5 0 11-3-3.46M15 3a5 5 0 005 5',
  type: 'M4 7V4h16v3M9 20h6M12 4v16',
  'text-size': 'M3 18l4-11 4 11M4.3 14.5h5.4M14 18v-6.2a2.6 2.6 0 015.2 0V18M14 14.4h5.2',
  // Bookmark ribbon with an ogee (pointed-arch) notch mark.
  bookmark: 'M6 3h12v18l-6-4.2L6 21zM10.2 8.2c0-1 .8-1.8 1.8-2.4 1 .6 1.8 1.4 1.8 2.4',
  clock: 'M12 22a10 10 0 100-20 10 10 0 000 20zM12 7v5l3 2',
  globe: 'M12 22a10 10 0 100-20 10 10 0 000 20zM2 12h20M12 2a15 15 0 010 20 15 15 0 010-20z',
  tag: 'M20.6 13.4L13 21a1.7 1.7 0 01-2.4 0L3 13.4V4a1 1 0 011-1h9.4zM7.5 7.5h.01',
  users:
    'M16 21v-2a4 4 0 00-4-4H6a4 4 0 00-4 4v2M9 11a4 4 0 100-8 4 4 0 000 8zM22 21v-2a4 4 0 00-3-3.9M16 3.1a4 4 0 010 7.8',
  eye: 'M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7zM12 15a3 3 0 100-6 3 3 0 000 6z',
  sliders: 'M4 21v-7M4 10V3M12 21v-9M12 8V3M20 21v-5M20 12V3M1 14h6M9 8h6M17 16h6',
  bell: 'M18 8a6 6 0 10-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.7 21a2 2 0 01-3.4 0',
  maximize:
    'M8 3H5a2 2 0 00-2 2v3M21 8V5a2 2 0 00-2-2h-3M3 16v3a2 2 0 002 2h3M16 21h3a2 2 0 002-2v-3',
  highlighter: 'M9 11l-4 4v3h3l4-4M9 11l5-5 4 4-5 5M9 11l4 4',
  note: 'M14 3v4a1 1 0 001 1h4M5 3h9l5 5v11a2 2 0 01-2 2H5a2 2 0 01-2-2V5a2 2 0 012-2zM8 13h6M8 17h4',
};

// The full icon set as an array (derived from the path map, so it never drifts).
export const ICON_NAMES = Object.keys(ICON_PATHS) as IconName[];
