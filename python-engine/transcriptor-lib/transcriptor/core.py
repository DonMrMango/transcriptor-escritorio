"""
Módulo principal de transcripción
"""

import requests
import os
import tempfile
from pathlib import Path
from .audio import AudioProcessor

class Transcriptor:
    """
    Cliente para transcripción de audio/video usando Groq Whisper

    Ejemplo:
        trans = Transcriptor(api_key='tu_key')
        resultado = trans.transcribir('audio.mp3', language='es')
    """

    API_URL = "https://api.groq.com/openai/v1/audio/transcriptions"
    MAX_FILE_SIZE_MB = 25  # Groq limit

    def __init__(self, api_key, default_model='whisper-large-v3-turbo'):
        """
        Inicializa el transcriptor

        Args:
            api_key (str): API Key de Groq
            default_model (str): Modelo por defecto
        """
        if not api_key:
            raise ValueError("API Key es requerida")

        self.api_key = api_key
        self.default_model = default_model
        self.audio_processor = AudioProcessor()

    def transcribir(self, archivo, language='es', model=None, prompt='',
                   format='json', chunk_if_needed=True):
        """
        Transcribe un archivo de audio o video

        Args:
            archivo: Ruta del archivo (str) o file-like object
            language: Código de idioma ISO ('es', 'en', etc.)
            model: Modelo a usar (por defecto: self.default_model)
            prompt: Prompt opcional para contexto
            format: Formato de salida ('json', 'text', 'verbose_json')
            chunk_if_needed: Si es True, divide archivos grandes automáticamente

        Returns:
            dict: {
                'text': str,           # Texto transcrito
                'language': str,       # Idioma detectado
                'duration': float,     # Duración en segundos
                'success': bool,       # Si fue exitoso
                'model': str,          # Modelo usado
                'chunks': int          # Número de chunks procesados
            }

        Raises:
            FileNotFoundError: Si el archivo no existe
            ValueError: Si el archivo no es válido
            Exception: Si hay error en la API
        """
        model = model or self.default_model

        # Manejar diferentes tipos de entrada
        if isinstance(archivo, str):
            filepath = Path(archivo)
            if not filepath.exists():
                raise FileNotFoundError(f"Archivo no encontrado: {archivo}")

            # Procesar archivo
            return self._transcribir_archivo(
                filepath, language, model, prompt, format, chunk_if_needed
            )

        else:
            # File-like object (ej: Django/Flask UploadedFile)
            return self._transcribir_fileobject(
                archivo, language, model, prompt, format
            )

    def _transcribir_archivo(self, filepath, language, model, prompt, format, chunk_if_needed):
        """Transcribe un archivo del filesystem"""

        # Convertir video a audio si es necesario
        if self.audio_processor.is_video(filepath):
            print(f"🎬 Detectado video, extrayendo audio...")
            audio_path = self.audio_processor.extract_audio(filepath)
        else:
            audio_path = filepath

        # Obtener duración
        duration = self.audio_processor.get_duration(audio_path)

        # Verificar tamaño
        size_mb = os.path.getsize(audio_path) / (1024 * 1024)

        if size_mb > self.MAX_FILE_SIZE_MB and chunk_if_needed:
            print(f"📦 Archivo grande ({size_mb:.1f}MB), dividiendo en chunks...")
            return self._transcribir_chunks(
                audio_path, duration, language, model, prompt, format
            )

        # Transcribir archivo completo
        text = self._call_api(audio_path, language, model, prompt, format)

        return {
            'text': text,
            'language': language,
            'duration': duration,
            'success': True,
            'model': model,
            'chunks': 1
        }

    def _transcribir_fileobject(self, fileobj, language, model, prompt, format):
        """Transcribe un file-like object (ej: request.FILES['audio'])"""

        # Guardar temporalmente
        with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp:
            # Leer del file object
            if hasattr(fileobj, 'read'):
                tmp.write(fileobj.read())
            elif hasattr(fileobj, 'file'):
                # Django UploadedFile
                for chunk in fileobj.chunks():
                    tmp.write(chunk)
            else:
                raise ValueError("Tipo de archivo no soportado")

            tmp_path = tmp.name

        try:
            # Transcribir archivo temporal
            result = self._transcribir_archivo(
                Path(tmp_path), language, model, prompt, format, chunk_if_needed=True
            )
            return result

        finally:
            # Limpiar temporal
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def _transcribir_chunks(self, audio_path, duration, language, model, prompt, format):
        """Divide el audio en chunks y transcribe cada uno"""

        chunk_duration = 4 * 60  # 4 minutos por chunk
        chunks = self.audio_processor.create_chunks(
            audio_path,
            chunk_duration=chunk_duration
        )

        texts = []
        for i, chunk_path in enumerate(chunks, 1):
            print(f"   Procesando chunk {i}/{len(chunks)}...")
            text = self._call_api(chunk_path, language, model, prompt, format)
            texts.append(text)

            # Limpiar chunk temporal
            if os.path.exists(chunk_path):
                os.remove(chunk_path)

        # Unir textos
        full_text = '\n\n'.join(texts)

        return {
            'text': full_text,
            'language': language,
            'duration': duration,
            'success': True,
            'model': model,
            'chunks': len(chunks)
        }

    def _call_api(self, filepath, language, model, prompt, format):
        """
        Llama a la API de Groq para transcribir

        Returns:
            str: Texto transcrito

        Raises:
            Exception: Si hay error en la API
        """
        with open(filepath, 'rb') as audio_file:
            files = {
                'file': (os.path.basename(filepath), audio_file, 'audio/mpeg')
            }

            data = {
                'model': model,
                'response_format': format
            }

            if language and language != 'auto':
                data['language'] = language

            if prompt:
                data['prompt'] = prompt

            headers = {
                'Authorization': f'Bearer {self.api_key}'
            }

            response = requests.post(
                self.API_URL,
                files=files,
                data=data,
                headers=headers,
                timeout=600
            )

        if response.status_code == 200:
            result = response.json()

            if format == 'verbose_json':
                # Devolver formato estructurado
                return self._format_verbose(result)
            else:
                return result.get('text', '')

        else:
            raise Exception(
                f'Error de API Groq: {response.status_code} - {response.text}'
            )

    def _format_verbose(self, result):
        """Formatea respuesta verbose con timestamps"""
        output = []
        output.append("=== TRANSCRIPCIÓN COMPLETA ===\n")
        output.append(result.get('text', ''))
        output.append("\n\n=== SEGMENTOS CON TIMESTAMPS ===\n")

        segments = result.get('segments', [])
        for segment in segments:
            start = segment.get('start', 0)
            end = segment.get('end', 0)
            text = segment.get('text', '').strip()

            start_min = int(start // 60)
            start_sec = int(start % 60)
            end_min = int(end // 60)
            end_sec = int(end % 60)

            output.append(
                f"[{start_min:02d}:{start_sec:02d} - {end_min:02d}:{end_sec:02d}] {text}"
            )

        return "\n".join(output)

    def transcribir_url(self, url, language='es', model=None, prompt=''):
        """
        Transcribe audio desde una URL

        Args:
            url: URL del archivo de audio/video
            language: Código de idioma
            model: Modelo a usar
            prompt: Prompt opcional

        Returns:
            dict: Resultado de transcripción
        """
        # Descargar archivo temporalmente
        import urllib.request

        with tempfile.NamedTemporaryFile(delete=False, suffix='.tmp') as tmp:
            print(f"📥 Descargando desde {url}...")
            urllib.request.urlretrieve(url, tmp.name)
            tmp_path = tmp.name

        try:
            result = self.transcribir(tmp_path, language, model, prompt)
            return result
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
