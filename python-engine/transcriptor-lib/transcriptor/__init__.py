"""
Transcriptor - Librería de transcripción de audio/video con Groq Whisper
Grupo Lada Technologies

Uso básico:
    from transcriptor import Transcriptor

    trans = Transcriptor(api_key='tu_groq_key')
    resultado = trans.transcribir('audio.mp3', language='es')
    print(resultado['text'])
"""

from .core import Transcriptor

__version__ = '1.0.0'
__author__ = 'Grupo Lada Technologies'
__all__ = ['Transcriptor']
