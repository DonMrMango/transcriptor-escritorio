import './MenuPanel.css';

interface MenuPanelProps {
  onStartRecording: () => void;
  onClose: () => void;
}

export default function MenuPanel({ onStartRecording, onClose }: MenuPanelProps) {
  const handleTranscribeFile = async () => {
    // TODO: Abrir file picker y transcribir archivo
    console.log('Transcribir archivo');
  };

  return (
    <div className="menu-panel">
      <div className="menu-header">
        <h3>Transcriptor</h3>
        <button className="close-btn" onClick={onClose}>×</button>
      </div>

      <div className="menu-options">
        <button className="menu-btn record-btn" onClick={onStartRecording}>
          <span className="btn-icon">🎙️</span>
          <span className="btn-label">Grabar Audio</span>
          <span className="btn-description">Graba y transcribe en tiempo real</span>
        </button>

        <button className="menu-btn file-btn" onClick={handleTranscribeFile}>
          <span className="btn-icon">📁</span>
          <span className="btn-label">Transcribir Archivo</span>
          <span className="btn-description">Audio o video existente</span>
        </button>
      </div>

      <div className="menu-footer">
        <span className="version">v0.1.0</span>
      </div>
    </div>
  );
}
