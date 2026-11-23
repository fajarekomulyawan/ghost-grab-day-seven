// Day one, day seven — entry program.
//
// The entry is a TikTok video: the same tiny agent-built game
// (Ghost Grab) on the day it was made and after a week of daily
// updates, cut between identical moments — same map, same start,
// visibly more going on the second time. It ends with make.fun's
// referral end card. VIDEO.json names the posted video.
//
// This program checks that VIDEO.json is present, that it carries
// the video's full TikTok address, and that the rendered video.mp4
// sits beside it — then prints the address so anyone can watch the
// entry. Standard library only, no network.
//
//   node main.ts

import { readFileSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { fileURLToPath } from 'node:url';

const here = fileURLToPath(new URL('.', import.meta.url));

const raw = readFileSync(join(here, 'VIDEO.json'), 'utf8');
const video = JSON.parse(raw);
if (typeof video.url !== 'string' || !video.url.startsWith('https://www.tiktok.com/')) {
  throw new Error('VIDEO.json must carry the full TikTok address in "url"');
}
const bytes = statSync(join(here, 'video.mp4')).size;
console.log(`Ghost Grab, day one vs day seven (${bytes} bytes of video)`);
console.log(`watch it here: ${video.url}`);
