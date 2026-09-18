import React from 'react';
import {AbsoluteFill, useCurrentFrame, useVideoConfig, interpolate} from 'remotion';
import {Check, Download, FileText, Search} from 'lucide-react';
import {Backdrop} from '../components/Backdrop';
import {Kicker, Words} from '../components/Type';
import {Phone, Bubble} from '../components/Phone';
import {useLayout} from '../LayoutContext';
import {
  FONT,
  MONO,
  MUTED,
  ACCENT,
  clamp,
  fadeIn,
  springIn,
} from '../lib';

const FILES = [
  {name: 'invoice_march.pdf', size: '2.4 MB'},
  {name: 'invoice_april.pdf', size: '1.1 MB'},
  {name: 'invoices.zip', size: '18 MB'},
];

export const Feature3: React.FC = () => {
  const frame = useCurrentFrame();
  const {fps} = useVideoConfig();
  const {scale, pad, isPortrait} = useLayout();
  const typed = 'invoice'.slice(
    0,
    Math.max(0, Math.min(7, Math.floor((frame - 10) / 2))),
  );
  const progress = interpolate(frame, [96, 130], [0, 100], {
    extrapolateLeft: 'clamp',
    extrapolateRight: 'clamp',
  });
  const cardW = (isPortrait ? 860 : 480) * scale;
  const arrowP = clamp(springIn(frame, fps, 76));
  return (
    <AbsoluteFill style={{fontFamily: FONT}}>
      <Backdrop />
      <div
        style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 44 * scale,
          padding: pad,
        }}
      >
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            gap: 24 * scale,
          }}
        >
          <Kicker start={0} center>
            Files
          </Kicker>
          <Words text="Any file. To your phone." start={8} size={76} center />
        </div>
        <div
          style={{
            display: 'flex',
            flexDirection: isPortrait ? 'column' : 'row',
            alignItems: 'center',
            gap: 40 * scale,
          }}
        >
          <div
            style={{
              width: cardW,
              borderRadius: 22 * scale,
              background: '#0C1322',
              border: '1px solid #FFFFFF14',
              boxShadow: '0 40px 90px rgba(0,0,0,0.5)',
              padding: 26 * scale,
              display: 'flex',
              flexDirection: 'column',
              gap: 18 * scale,
              opacity: clamp(springIn(frame, fps, 4)),
            }}
          >
            <div
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: 12 * scale,
                background: '#070C16',
                border: '1px solid #FFFFFF16',
                borderRadius: 12 * scale,
                padding: `${14 * scale}px ${18 * scale}px`,
                fontFamily: MONO,
                fontSize: 24 * scale,
                color: '#E8EFFA',
              }}
            >
              <Search size={22 * scale} color={MUTED} />
              {typed}
              <span style={{color: ACCENT}}>▍</span>
            </div>
            {FILES.map((f, i) => {
              const t = 26 + i * 10;
              const hot = i === 0;
              const hi = hot ? fadeIn(frame, 70, 8) : 0;
              return (
                <div
                  key={f.name}
                  style={{
                    opacity: fadeIn(frame, t, 10),
                    display: 'flex',
                    alignItems: 'center',
                    gap: 14 * scale,
                    padding: `${14 * scale}px ${16 * scale}px`,
                    borderRadius: 12 * scale,
                    border: `1.5px solid ${
                      hot ? `${ACCENT}${hi > 0 ? 'AA' : '00'}` : '#FFFFFF0D'
                    }`,
                    background: hot
                      ? `rgba(79,140,255,${0.14 * hi + 0.03})`
                      : '#FFFFFF04',
                  }}
                >
                  <FileText size={24 * scale} color={hot ? ACCENT : MUTED} />
                  <div style={{flex: 1}}>
                    <div
                      style={{
                        fontFamily: MONO,
                        fontSize: 22 * scale,
                        color: '#E8EFFA',
                      }}
                    >
                      {f.name}
                    </div>
                    <div style={{fontSize: 18 * scale, color: MUTED}}>
                      {f.size}
                    </div>
                  </div>
                  {hot ? (
                    <Download
                      size={22 * scale}
                      color={ACCENT}
                      style={{opacity: fadeIn(frame, 72, 8)}}
                    />
                  ) : null}
                </div>
              );
            })}
          </div>
          <div
            style={{
              width: 74 * scale,
              height: 74 * scale,
              borderRadius: '50%',
              background: ACCENT,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              boxShadow: '0 0 50px rgba(79,140,255,0.55)',
              opacity: arrowP,
              transform: `scale(${0.5 + 0.5 * arrowP}) rotate(${
                isPortrait ? 90 : 0
              }deg)`,
            }}
          >
            <Download size={34 * scale} color="#fff" strokeWidth={2.4} />
          </div>
          <Phone start={10} tilt={!isPortrait}>
            <Bubble in start={86}>
              <div
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 8 * scale,
                  minWidth: 220 * scale,
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 10 * scale,
                  }}
                >
                  <FileText size={24 * scale} color={ACCENT} />
                  <div>
                    <div style={{fontFamily: MONO, fontSize: 21 * scale}}>
                      invoice_march.pdf
                    </div>
                    <div style={{fontSize: 16 * scale, color: '#8FA3BF'}}>
                      2.4 MB
                    </div>
                  </div>
                </div>
                <div
                  style={{
                    height: 8 * scale,
                    borderRadius: 4,
                    background: '#FFFFFF14',
                    overflow: 'hidden',
                  }}
                >
                  <div
                    style={{
                      width: `${progress}%`,
                      height: '100%',
                      background: ACCENT,
                      borderRadius: 4,
                    }}
                  />
                </div>
              </div>
            </Bubble>
            <Bubble in start={134}>
              <Check size={20 * scale} color="#34D399" strokeWidth={3} />
              Saved to your phone
            </Bubble>
          </Phone>
        </div>
      </div>
    </AbsoluteFill>
  );
};
