import { useEffect, useRef } from 'react';
import './LightGooeyBackground.css';

/**
 * LightGooeyBackground — Premium warm ambient glow for LIGHT MODE ONLY.
 *
 * ISOLATION:
 *   - Uses .ambient-bg-light (never .ambient-bg — that belongs to dark mode)
 *   - Layer classes: .amb-l--light-* (unique, no overlap with dark .amb-l--)
 *   - Visibility: display:none by default; toggled via light-theme.css
 *     (html[data-theme="light"] .ambient-bg-light { display: block })
 *
 * MOUSE TRACKING:
 *   - Same RAF pattern as dark mode for consistency and performance
 *   - 900×900 warm glow blob, offset to center on cursor
 */
export default function LightGooeyBackground() {
  const mouseRef = useRef(null);

  useEffect(() => {
    let animationFrameId;

    const handleMouseMove = (e) => {
      if (!mouseRef.current) return;

      // Center the 900×900 blob on the cursor
      const x = e.clientX - 450;
      const y = e.clientY - 450;

      cancelAnimationFrame(animationFrameId);
      animationFrameId = requestAnimationFrame(() => {
        if (mouseRef.current) {
          mouseRef.current.style.transform = `translate(${x}px, ${y}px)`;
        }
      });
    };

    window.addEventListener('mousemove', handleMouseMove, { passive: true });

    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      cancelAnimationFrame(animationFrameId);
    };
  }, []);

  return (
    <div className="ambient-bg-light" aria-hidden="true">
      {/* Interactive warm mouse glow */}
      <div ref={mouseRef} className="amb-l--light amb-l--light-mouse" />
      {/* Central peach haze */}
      <div className="amb-l--light amb-l--light-center" />
      {/* Terracotta diagonal trace */}
      <div className="amb-l--light amb-l--light-trace" />
    </div>
  );
}
