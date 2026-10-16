#!/usr/bin/env node
// Inlines the public data into the dashboard template -> web/dist/index.html (single file, no server needed).
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { join } from 'node:path';

const here = import.meta.dirname;
const parts = JSON.parse(readFileSync(join(here, '../data/parts.json'), 'utf8'));
const entities = JSON.parse(readFileSync(join(here, '../data/entities.json'), 'utf8'));
const data = { as_of: parts.as_of, parts: parts.parts, entities: entities.entities };
// Escape "<" so data can never close the script tag.
const json = JSON.stringify(data).replace(/</g, '\\u003c');
const html = readFileSync(join(here, 'template.html'), 'utf8').replace('__TPM_DATA__', () => json);
mkdirSync(join(here, 'dist'), { recursive: true });
writeFileSync(join(here, 'dist/index.html'), html);
console.log(`Built web/dist/index.html (${(html.length / 1024).toFixed(0)} KB)`);
