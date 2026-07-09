// Frontend SSOT guard: the TypeScript counterpart of the backend's
// constant_sprawl.repo_wide_collisions. Fails when a string-literal union type or
// a literal constant value (array or object) is enumerated in two or more files,
// so a vocabulary or shape that should live in one module cannot silently fork.
// Runs in CI via `pnpm fe:ssot`. Below jscpd's copy-paste floor, which is why it
// exists separately.
import { readdirSync, readFileSync } from 'node:fs';
import { join, relative } from 'node:path';
import { fileURLToPath } from 'node:url';
import ts from 'typescript';

const SRC = join(fileURLToPath(new URL('.', import.meta.url)), '..', 'src');
const REPO = join(SRC, '..', '..');
const EXCLUDE = /\.(test|spec)\.tsx?$|\.d\.ts$/;
const MIN_UNION_MEMBERS = 3;
const MIN_LITERAL_ELEMENTS = 3;

function walk(dir, out = []) {
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const p = join(dir, entry.name);
    if (entry.isDirectory()) walk(p, out);
    else if (/\.tsx?$/.test(entry.name) && !EXCLUDE.test(entry.name)) out.push(p);
  }
  return out;
}

function normalize(text) {
  return text.replace(/\s+/g, '').replace(/,([\]}])/g, '$1');
}

function collect(file) {
  const text = readFileSync(file, 'utf8');
  const sf = ts.createSourceFile(file, text, ts.ScriptTarget.Latest, true);
  const rel = relative(REPO, file);
  const items = [];
  const visit = (node) => {
    if (ts.isTypeAliasDeclaration(node) && ts.isUnionTypeNode(node.type)) {
      const lits = node.type.types.filter(
        (t) => ts.isLiteralTypeNode(t) && ts.isStringLiteral(t.literal),
      );
      if (lits.length >= MIN_UNION_MEMBERS && lits.length === node.type.types.length) {
        const members = lits.map((t) => t.literal.text).sort();
        items.push({
          key: `union|${members.join('|')}`,
          name: node.name.text,
          rel,
          kind: 'string-literal union type',
        });
      }
    }
    if (ts.isVariableStatement(node)) {
      for (const decl of node.declarationList.declarations) {
        if (!decl.initializer || !ts.isIdentifier(decl.name)) continue;
        const init = decl.initializer;
        if (ts.isArrayLiteralExpression(init) && init.elements.length >= MIN_LITERAL_ELEMENTS) {
          items.push({
            key: `array|${normalize(init.getText(sf))}`,
            name: decl.name.text,
            rel,
            kind: 'array constant value',
          });
        } else if (
          ts.isObjectLiteralExpression(init) &&
          init.properties.length >= MIN_LITERAL_ELEMENTS
        ) {
          items.push({
            key: `object|${normalize(init.getText(sf))}`,
            name: decl.name.text,
            rel,
            kind: 'object constant value',
          });
        }
      }
    }
    ts.forEachChild(node, visit);
  };
  visit(sf);
  return items;
}

const byKey = new Map();
for (const file of walk(SRC)) {
  for (const item of collect(file)) {
    if (!byKey.has(item.key)) byKey.set(item.key, []);
    byKey.get(item.key).push(item);
  }
}

const violations = [];
for (const group of byKey.values()) {
  const files = [...new Set(group.map((g) => g.rel))].sort();
  if (files.length >= 2) {
    const names = [...new Set(group.map((g) => g.name))].join(', ');
    violations.push(`${group[0].kind} duplicated as {${names}} across ${files.join(', ')}`);
  }
}

if (violations.length) {
  console.error('frontend SSOT: the same vocabulary or value is declared in more than one file:');
  for (const v of violations.sort()) console.error('  - ' + v);
  console.error(`\n${violations.length} violation(s). Hoist each to one module and import it.`);
  process.exit(1);
}
console.log('frontend SSOT: no cross-file duplicated vocabularies or constant values.');
