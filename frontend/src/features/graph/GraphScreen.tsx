import { Badge, Heading, Icon, Text } from "../../lib/design-system";
import "./GraphScreen.css";

export function GraphScreen() {
  return (
    <section className="graph">
      <div className="graph__canvas" role="img" aria-label="Knowledge graph, coming soon">
        <svg className="graph__scaffold" viewBox="0 0 400 300" aria-hidden="true">
          <g fill="none" stroke="currentColor" strokeWidth="1.5">
            <line x1="80" y1="60" x2="200" y2="150" />
            <line x1="320" y1="60" x2="200" y2="150" />
            <line x1="200" y1="150" x2="120" y2="240" />
            <line x1="200" y1="150" x2="290" y2="240" />
            <circle cx="80" cy="60" r="10" />
            <circle cx="320" cy="60" r="10" />
            <circle cx="200" cy="150" r="13" />
            <circle cx="120" cy="240" r="10" />
            <circle cx="290" cy="240" r="10" />
          </g>
        </svg>
        <div className="graph__placeholder">
          <Icon name="network" size="lg" />
          <Heading level={3}>Transmission graph</Heading>
          <Text as="p" size="sm" tone="muted" className="graph__hint">
            Narrators, isnāds, citations and cross-transmissions, explored as a living network. Wiring in next.
          </Text>
          <Badge>Coming soon</Badge>
        </div>
      </div>
      <aside className="graph__panel">
        <Text size="xs" tone="faint" weight="semibold" className="graph__label">Inspector</Text>
        <Text as="p" size="sm" tone="muted">Select a narrator to trace their chain, their students, and the works that cite them.</Text>
      </aside>
    </section>
  );
}
