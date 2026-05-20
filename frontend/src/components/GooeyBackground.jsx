import { useEffect, useRef } from 'react';
import './GooeyBackground.css';

/**
 * Four independent gradient layers animated via CSS keyframes.
 * Plus one interactive layer that follows the mouse.
 * ::before and ::after on the container handle two extra layers.
 * Single parent filter:blur() = one GPU pass, not per-element.
 */
export default function GooeyBackground() {
  const mouseRef = useRef(null);

  useEffect(() => {
    let animationFrameId;

    const handleMouseMove = (e) => {
      if (!mouseRef.current) return;
      
      // Calculate coordinates (center of the 800x800 element)
      const x = e.clientX - 400;
      const y = e.clientY - 400;

      // Use requestAnimationFrame to throttle CSS updates
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
    <div className="ambient-bg" aria-hidden="true">
      {/* Interactive mouse layer */}
      <div ref={mouseRef} className="amb-l amb-l--mouse" />
      {/* Center haze layer */}
      <div className="amb-l amb-l--center" />
      {/* Diagonal trace layer */}
      <div className="amb-l amb-l--trace" />
    </div>
  );
}
