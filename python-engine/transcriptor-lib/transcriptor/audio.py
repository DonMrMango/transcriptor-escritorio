"""
Módulo de procesamiento de audio y video
"""

import subprocess
import os
import tempfile
import math
from pathlib import Path

class AudioProcessor:
    """Procesador de archivos de audio y video"""

    VIDEO_EXTENSIONS = {
        '.mp4', '.mov', '.avi', '.mkv', '.webm',
        '.flv', '.wmv', '.m4v', '.mpg', '.mpeg'
    }

    AUDIO_EXTENSIONS = {
        '.mp3', '.wav', '.m4a', '.flac', '.ogg',
        '.aac', '.wma', '.opus'
    }

    def is_video(self, filepath):
        """
        Determina si un archivo es video

        Args:
            filepath: Path o string del archivo

        Returns:
            bool: True si es video
        """
        ext = Path(filepath).suffix.lower()
        return ext in self.VIDEO_EXTENSIONS

    def is_audio(self, filepath):
        """
        Determina si un archivo es audio

        Args:
            filepath: Path o string del archivo

        Returns:
            bool: True si es audio
        """
        ext = Path(filepath).suffix.lower()
        return ext in self.AUDIO_EXTENSIONS

    def get_duration(self, filepath):
        """
        Obtiene la duración de un archivo de audio/video

        Args:
            filepath: Ruta del archivo

        Returns:
            float: Duración en segundos, None si falla
        """
        try:
            cmd = [
                'ffprobe', '-v', 'error',
                '-show_entries', 'format=duration',
                '-of', 'default=noprint_wrappers=1:nokey=1',
                str(filepath)
            ]

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )

            return float(result.stdout.strip())

        except Exception as e:
            print(f"⚠️ No se pudo obtener duración: {e}")
            return None

    def extract_audio(self, video_path, output_path=None):
        """
        Extrae audio de un video

        Args:
            video_path: Ruta del video
            output_path: Ruta de salida (opcional)

        Returns:
            str: Ruta del archivo de audio extraído

        Raises:
            Exception: Si ffmpeg falla
        """
        if output_path is None:
            # Crear archivo temporal
            tmp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.wav'
            )
            output_path = tmp.name
            tmp.close()

        try:
            cmd = [
                'ffmpeg', '-i', str(video_path),
                '-vn',  # Sin video
                '-acodec', 'pcm_s16le',  # WAV codec
                '-ar', '16000',  # 16kHz (óptimo para Whisper)
                '-ac', '1',  # Mono
                '-y',  # Sobrescribir
                output_path
            ]

            subprocess.run(
                cmd,
                capture_output=True,
                check=True
            )

            return output_path

        except subprocess.CalledProcessError as e:
            # Limpiar archivo temporal si falló
            if os.path.exists(output_path):
                os.remove(output_path)

            raise Exception(f"Error extrayendo audio: {e.stderr.decode()}")

    def create_chunks(self, audio_path, chunk_duration=240, overlap=15):
        """
        Divide un archivo de audio en chunks

        Args:
            audio_path: Ruta del audio
            chunk_duration: Duración de cada chunk en segundos (default: 4min)
            overlap: Segundos de overlap entre chunks (default: 15s)

        Returns:
            list: Lista de rutas de los chunks creados
        """
        duration = self.get_duration(audio_path)
        if not duration:
            # Si no podemos obtener duración, retornar archivo original
            return [str(audio_path)]

        chunks = []
        num_chunks = math.ceil(duration / (chunk_duration - overlap))

        for i in range(num_chunks):
            start_time = i * (chunk_duration - overlap)
            end_time = min(start_time + chunk_duration, duration)

            # Crear chunk
            chunk_tmp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix=f'_chunk_{i}.wav'
            )
            chunk_path = chunk_tmp.name
            chunk_tmp.close()

            cmd = [
                'ffmpeg', '-i', str(audio_path),
                '-ss', str(start_time),
                '-t', str(end_time - start_time),
                '-acodec', 'copy',
                '-y',
                chunk_path
            ]

            try:
                subprocess.run(
                    cmd,
                    capture_output=True,
                    check=True
                )
                chunks.append(chunk_path)

            except subprocess.CalledProcessError as e:
                print(f"⚠️ Error creando chunk {i}: {e}")
                # Eliminar chunk fallido
                if os.path.exists(chunk_path):
                    os.remove(chunk_path)

        return chunks

    def convert_to_wav(self, input_path, output_path=None):
        """
        Convierte cualquier audio a WAV optimizado para transcripción

        Args:
            input_path: Ruta del archivo de entrada
            output_path: Ruta de salida (opcional)

        Returns:
            str: Ruta del archivo WAV
        """
        if output_path is None:
            tmp = tempfile.NamedTemporaryFile(
                delete=False,
                suffix='.wav'
            )
            output_path = tmp.name
            tmp.close()

        try:
            cmd = [
                'ffmpeg', '-i', str(input_path),
                '-acodec', 'pcm_s16le',
                '-ar', '16000',  # 16kHz
                '-ac', '1',  # Mono
                '-y',
                output_path
            ]

            subprocess.run(
                cmd,
                capture_output=True,
                check=True
            )

            return output_path

        except subprocess.CalledProcessError as e:
            if os.path.exists(output_path):
                os.remove(output_path)

            raise Exception(f"Error convirtiendo audio: {e.stderr.decode()}")

    @staticmethod
    def check_ffmpeg():
        """
        Verifica si ffmpeg está instalado

        Returns:
            bool: True si ffmpeg está disponible

        Raises:
            EnvironmentError: Si ffmpeg no está instalado
        """
        try:
            subprocess.run(
                ['ffmpeg', '-version'],
                capture_output=True,
                check=True
            )
            return True

        except (subprocess.CalledProcessError, FileNotFoundError):
            raise EnvironmentError(
                "ffmpeg no está instalado. "
                "Instálalo con: brew install ffmpeg (macOS) "
                "o apt-get install ffmpeg (Linux)"
            )
