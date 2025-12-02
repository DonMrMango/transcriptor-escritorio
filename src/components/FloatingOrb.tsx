import { AppState } from '../App';
import './FloatingOrb.css';

interface FloatingOrbProps {
  state: AppState;
  onClick: () => void;
}

export default function FloatingOrb({ state, onClick }: FloatingOrbProps) {
  const getOrbClass = () => {
    const baseClass = 'floating-orb';
    switch (state) {
      case 'idle':
        return `${baseClass} idle`;
      case 'menu':
        return `${baseClass} menu-open`;
      case 'recording':
        return `${baseClass} recording`;
      case 'transcribing':
        return `${baseClass} transcribing`;
      default:
        return baseClass;
    }
  };

  const getIcon = () => {
    switch (state) {
      case 'recording':
        return '🎙️';
      case 'transcribing':
        return '⚙️';
      default:
        return '✨';
    }
  };

  return (
    <div
      className={getOrbClass()}
      onClick={onClick}
      role="button"
      tabIndex={0}
    >
      <div className="orb-inner">
        <span className="orb-icon">{getIcon()}</span>
      </div>
      <div className="orb-glow"></div>
    </div>
  );
}
