import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
const source = new URL('../docs/index.html', import.meta.url);
const output = new URL('../dist/index.html', import.meta.url);
const html = await readFile(source, 'utf8');
if (!html.includes('현장 안전보건 점검관리') || !html.includes('demoRows')) {
  throw new Error('The public demo entrypoint is missing or invalid.');
}
await mkdir(new URL('../dist/', import.meta.url), { recursive: true });
await writeFile(output, html);
console.log(`Public demo built: ${fileURLToPath(output)} (${Buffer.byteLength(html)} bytes)`);
