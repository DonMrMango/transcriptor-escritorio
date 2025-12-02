import { useState } from 'react';
import './App.css';
import FloatingOrb from './components/FloatingOrb';
import MenuPanel from './components/MenuPanel';
import RecordingPanel from './components/RecordingPanel';

export type AppState = 'idle' | 'menu' | 'recording' | 'transcribing';

function App() {
  const [state, setState] = useState<AppState>('idle');

  const handleOrbClick = () => {
    if (state === 'idle') {
      setState('menu');
    } else if (state === 'menu') {
      setState('idle');
    }
  };

  const handleStartRecording = () => {
    setState('recording');
  };

  const handleStopRecording = () => {
    setState('transcribing');
  };

  const handleTranscribeComplete = () => {
    setState('idle');
  };

  const handleBack = () => {
    setState('idle');
  };

  return (
    <div className="app-container">
      <FloatingOrb
        state={state}
        onClick={handleOrbClick}
      />

      {state === 'menu' && (
        <MenuPanel
          onStartRecording={handleStartRecording}
          onClose={() => setState('idle')}
        />
      )}

      {(state === 'recording' || state === 'transcribing') && (
        <RecordingPanel
          state={state}
          onStop={handleStopRecording}
          onComplete={handleTranscribeComplete}
          onBack={handleBack}
        />
      )}
    </div>
  );
}

export default App;
