import {interpolate, spring} from 'remotion';

export const FONT = '"Segoe UI", "Inter", system-ui, -apple-system, sans-serif';
export const MONO = '"Cascadia Code", "Cascadia Mono", Consolas, monospace';

export const ACCENT = '#4F8CFF';
export const CYAN = '#22D3EE';
export const RED = '#F87171';
export const GREEN = '#34D399';
export const TG = '#2AABEE';
export const WA = '#25D366';
export const INK = '#F2F6FF';
export const MUTED = '#93A3C0';

export const clamp = (v: number, min = 0, max = 1) =>
  Math.max(min, Math.min(max, v));

export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;

export const fadeIn = (frame: number, start: number, dur = 12) =>
  interpolate(frame, [start, start + dur], [0, 1], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

export const fadeOut = (frame: number, start: number, dur = 12) =>
  interpolate(frame, [start, start + dur], [1, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

export const rise = (frame: number, start: number, dist = 40, dur = 14) =>
  interpolate(frame, [start, start + dur], [dist, 0], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });

export const springIn = (
  frame: number,
  fps: number,
  start = 0,
  stiffness = 160,
  damping = 15,
) =>
  spring({
    frame: Math.max(0, frame - start),
    fps,
    config: {damping, stiffness, mass: 0.55},
  });
