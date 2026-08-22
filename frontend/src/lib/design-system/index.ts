// design-system/index.ts — PUBLIC barrel. Feature code imports ONLY from here.

export { Icon } from './primitives/Icon';
export type { IconProps, IconSize } from './primitives/Icon';
export type { IconName } from './internal/icons';
export { ICON_NAMES } from './internal/icons';

export { Text } from './primitives/Text';
export type { TextProps, TextSize, TextTone, TextWeight, TextFont } from './primitives/Text';

export { Heading } from './primitives/Heading';
export type { HeadingProps, HeadingLevel, HeadingFont } from './primitives/Heading';

export { Stack } from './primitives/Stack';
export type { StackProps, Gap, Align, Justify } from './primitives/Stack';

export { Inline } from './primitives/Inline';
export type { InlineProps } from './primitives/Inline';

export { Button } from './primitives/Button';
export type { ButtonProps, ButtonVariant, ButtonSize } from './primitives/Button';

export { Eyebrow } from './primitives/Eyebrow';
export type { EyebrowProps, EyebrowTracking } from './primitives/Eyebrow';

export { Dots } from './primitives/Dots';
export type { DotsProps } from './primitives/Dots';

export { PageGlow } from './components/PageGlow';

export { UnstyledButton } from './primitives/UnstyledButton';
export type { UnstyledButtonProps } from './primitives/UnstyledButton';

export { IconButton } from './primitives/IconButton';
export type { IconButtonProps, IconButtonSize } from './primitives/IconButton';
export type { Surface } from './surfaces';

export { Pill } from './primitives/Pill';
export type { PillProps } from './primitives/Pill';

export { NavArrow } from './primitives/NavArrow';
export type { NavArrowProps, NavArrowDirection, NavArrowSize } from './primitives/NavArrow';

export { Card } from './primitives/Card';
export type { CardProps, CardVariant, CardPad } from './primitives/Card';

export { Badge, BADGE_VARIANTS } from './primitives/Badge';
export type { BadgeProps, BadgeVariant } from './primitives/Badge';

export { Chip } from './primitives/Chip';
export type { ChipProps } from './primitives/Chip';

export { Link } from './primitives/Link';
export type { LinkProps, LinkVariant } from './primitives/Link';

export { NewTabLink } from './primitives/NewTabLink';
export type { NewTabLinkProps } from './primitives/NewTabLink';

export { Divider } from './primitives/Divider';
export type { DividerProps } from './primitives/Divider';

export { Spinner } from './primitives/Spinner';
export type { SpinnerProps, SpinnerSize } from './primitives/Spinner';

export { Pager } from './primitives/Pager';
export type { PagerProps } from './primitives/Pager';

export { Segmented } from './primitives/Segmented';
export type { SegmentedProps, SegmentedOption } from './primitives/Segmented';

export { Input } from './primitives/Input';
export type { InputProps } from './primitives/Input';

export { Menu } from './primitives/Menu';
export type { MenuProps, MenuOption, MenuVariant } from './primitives/Menu';

export { Logo } from './primitives/Logo';
export type { LogoProps, LogoSize } from './primitives/Logo';

export { ShareButton } from './primitives/ShareButton';
export type { ShareButtonProps } from './primitives/ShareButton';

export { Highlight } from './primitives/Highlight';
export type { HighlightProps } from './primitives/Highlight';

// Reader-domain components — composed from primitives + reader-surface tokens.
export { TocItem } from './components/TocItem';
export type { TocItemProps } from './components/TocItem';

export { MatchRow } from './components/MatchRow';
export type { MatchRowProps } from './components/MatchRow';

export { CiteLink } from './components/CiteLink';
export type { CiteLinkProps } from './components/CiteLink';
export { FootnoteRef } from './components/FootnoteRef';
export type { FootnoteRefProps } from './components/FootnoteRef';
export { NarratorLink } from './components/NarratorLink';
export type { NarratorLinkProps } from './components/NarratorLink';

export { IsnadNode } from './components/IsnadNode';
export type { IsnadNodeProps } from './components/IsnadNode';

export { TitleLockup } from './components/TitleLockup';
export type { TitleLockupProps, LockupMode, LockupVariant } from './components/TitleLockup';

export { SourceRecord } from './components/SourceRecord';
export type { SourceRecordProps } from './components/SourceRecord';

export { IndexRow } from './components/IndexRow';
export type { IndexRowProps } from './components/IndexRow';

export { RefPill } from './components/RefPill';
export type { RefPillProps } from './components/RefPill';

export { FacetChip } from './primitives/FacetChip';
export type { FacetChipProps } from './primitives/FacetChip';

export { Checkbox } from './primitives/Checkbox';
export type { CheckboxProps } from './primitives/Checkbox';
export { Apparatus } from './components/Apparatus';
export type { ApparatusProps } from './components/Apparatus';

export { useDismiss, useEscape } from './primitives/useDismiss';
