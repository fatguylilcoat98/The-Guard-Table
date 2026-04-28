/*
 * The Guard Table — SSE streaming helpers
 */

export async function streamGuardResponse({ body, onEvent, onHttpError }) {
  const response = await fetch('/api/guard', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    let errBody = null;
    try { errBody = await response.json(); } catch (e) { /* non-JSON body */ }
    if (onHttpError) onHttpError(response.status, errBody);
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buf = '';

  while (true) {
    const { value, done } = await reader.read();
    if (done) break;
    buf += decoder.decode(value, { stream: true });

    let sep;
    while ((sep = buf.indexOf('\n\n')) !== -1) {
      const frame = buf.slice(0, sep);
      buf = buf.slice(sep + 2);
      const dataLine = frame.split('\n').find((l) => l.startsWith('data:'));
      if (!dataLine) continue;
      const payload = dataLine.slice(5).trim();
      if (!payload) continue;
      try {
        onEvent(JSON.parse(payload));
      } catch (e) {
        // ignore malformed frame
      }
    }
  }
}

export function parseGuardSections(text) {
  const sections = { wait: [], leverage: '', guard_steps: [] };
  const markers = [
    { tag: '===WAIT===', key: 'wait' },
    { tag: '===LEVERAGE===', key: 'leverage' },
    { tag: '===GUARD_STEPS===', key: 'guard_steps' },
  ];
  const found = [];
  for (const m of markers) {
    const idx = text.indexOf(m.tag);
    if (idx !== -1) found.push({ ...m, start: idx, contentStart: idx + m.tag.length });
  }
  found.sort((a, b) => a.start - b.start);
  for (let i = 0; i < found.length; i++) {
    const next = i + 1 < found.length ? found[i + 1].start : text.length;
    const block = text.slice(found[i].contentStart, next);
    if (found[i].key === 'leverage') {
      sections.leverage = block.replace(/^\n+|\n+$/g, '');
    } else {
      sections[found[i].key] = block.split('\n').map((l) => l.trim()).filter(Boolean);
    }
  }
  return sections;
}
