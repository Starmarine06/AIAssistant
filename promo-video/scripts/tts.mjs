import {mkdir, writeFile, readdir} from 'node:fs/promises';
import path from 'node:path';

const VOICE_ID = 'onwK4e9ZLuTAKqWW03F9';
const MODEL = 'eleven_multilingual_v2';
const API_KEY = process.env.ELEVENLABS_API_KEY;
const OUT_DIR = path.resolve('audio/sections');

if (!API_KEY) {
  console.error('ELEVENLABS_API_KEY not set');
  process.exit(1);
}

const presets = {
  neutral: {stability: 0.68, similarity_boost: 0.85, style: 0.2},
  urgent: {stability: 0.2, similarity_boost: 0.9, style: 0.45},
  playful: {stability: 0.6, similarity_boost: 0.85, style: 0.3},
  whisper: {stability: 0.3, similarity_boost: 0.9, style: 0.3},
  dramatic: {stability: 0.45, similarity_boost: 0.88, style: 0.35},
  confident: {stability: 0.6, similarity_boost: 0.85, style: 0.25},
  warm: {stability: 0.65, similarity_boost: 0.83, style: 0.2},
};

const SECTIONS = [
  {id: 'hook', start: 0.2, text: "It's 9 PM. You just sat down.", preset: 'neutral'},
  {id: 'pain1', start: 3.25, text: 'You need a file. From your home PC.', preset: 'urgent'},
  {id: 'pain2', start: 5.7, text: 'Wait... did you lock it?', preset: 'urgent'},
  {id: 'pain3', start: 7.65, text: 'That build needed to run. An hour ago.', preset: 'urgent'},
  {id: 'pain4', start: 10.35, text: 'And the couch is... really comfortable.', preset: 'playful'},
  {id: 'turn', start: 12.8, text: 'What if... your PC lived in your pocket?', preset: 'whisper'},
  {id: 'reveal', start: 16.6, text: 'AI Assistant. Your Windows PC. Inside Telegram.', preset: 'dramatic'},
  {id: 'f1', start: 21.0, text: 'Text it like a friend. Run commands, open apps, lock the workstation.', preset: 'confident'},
  {id: 'f1b', start: 26.6, text: 'Real shell. Real output. Right in the chat.', preset: 'confident'},
  {id: 'f2', start: 30.4, text: 'It screenshots your screen with a grid. Tap D-six, and it clicks there.', preset: 'confident'},
  {id: 'f3', start: 36.2, text: 'Search your drives. And pull any file straight to your phone.', preset: 'confident'},
  {id: 'f4', start: 41.0, text: 'Calendar events, reminders. Scheduled from one message.', preset: 'confident'},
  {id: 'f5', start: 45.3, text: 'WhatsApp. Macros. Your own Python skills.', preset: 'confident'},
  {id: 'trust', start: 49.8, text: 'Private by default. Only you can command it.', preset: 'warm'},
  {id: 'cta', start: 53.4, text: 'AI Assistant. Free and open source. On GitHub. Link in bio.', preset: 'confident'},
];

async function synth(section) {
  const url = `https://api.elevenlabs.io/v1/text-to-speech/${VOICE_ID}`;
  const body = {
    text: section.text,
    model_id: MODEL,
    voice_settings: presets[section.preset],
  };
  const res = await fetch(url, {
    method: 'POST',
    headers: {
      'xi-api-key': API_KEY,
      'Content-Type': 'application/json',
      Accept: 'audio/mpeg',
    },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const errText = await res.text();
    throw new Error(`[${section.id}] HTTP ${res.status}: ${errText.slice(0, 300)}`);
  }
  const buf = Buffer.from(await res.arrayBuffer());
  const file = path.join(OUT_DIR, `${String(SECTIONS.indexOf(section) + 1).padStart(2, '0')}_${section.id}.mp3`);
  await writeFile(file, buf);
  return {file, bytes: buf.length};
}

await mkdir(OUT_DIR, {recursive: true});
const existing = await readdir(OUT_DIR);
for (const f of existing) {
  if (f.endsWith('.mp3')) await writeFile(path.join(OUT_DIR, f), Buffer.alloc(0));
}

for (const section of SECTIONS) {
  const {file, bytes} = await synth(section);
  console.log(`OK ${section.id.padEnd(6)} ${bytes} bytes -> ${file}`);
}