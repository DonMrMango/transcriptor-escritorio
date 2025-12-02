# 🎙️ Transcriptor - Librería Python para Groq Whisper

Librería minimalista y portable para transcribir audio/video usando Groq Whisper API.

**Desarrollado por Grupo Lada Technologies**

---

## ✨ Características

- ✅ **Simple y portable** - Solo necesita `requests` y `ffmpeg`
- ✅ **Multi-formato** - MP3, WAV, M4A, FLAC, MP4, MOV, AVI, etc.
- ✅ **Chunking automático** - Divide archivos grandes sin intervención
- ✅ **Conversión de video** - Extrae audio automáticamente
- ✅ **Framework-agnostic** - Funciona con Django, Flask, Laravel, etc.
- ✅ **File objects** - Acepta uploads directos de Django/Flask
- ✅ **Transcripción de URLs** - Descarga y transcribe automáticamente
- ✅ **Thread-safe** - Uso seguro en aplicaciones multi-thread

---

## 📦 Instalación

### Opción 1: Desde carpeta local
```bash
cd transcriptor-lib/
pip install -e .
```

### Opción 2: Copiar módulo directamente
```bash
cp -r transcriptor-lib/transcriptor/ tu_proyecto/
```

### Opción 3: Desde GitHub (cuando subas el repo)
```bash
pip install git+https://github.com/tuusuario/transcriptor-lib
```

---

## 🚀 Uso Básico

```python
from transcriptor import Transcriptor

# 1. Crear instancia
trans = Transcriptor(api_key='tu_groq_key')

# 2. Transcribir archivo
resultado = trans.transcribir('audio.mp3', language='es')

# 3. Obtener texto
print(resultado['text'])
print(f"Duración: {resultado['duration']} segundos")
print(f"Chunks procesados: {resultado['chunks']}")
```

---

## 📖 Ejemplos de Uso

### 1. Transcribir archivo del filesystem

```python
from transcriptor import Transcriptor

trans = Transcriptor(api_key='gsk_...')

# Archivo de audio
resultado = trans.transcribir('grabacion.mp3', language='es')

# Archivo de video (extrae audio automáticamente)
resultado = trans.transcribir('video.mp4', language='en')

# Con configuración avanzada
resultado = trans.transcribir(
    'audio.wav',
    language='es',
    model='whisper-large-v3',
    prompt='Contexto: reunión de negocios',
    format='verbose_json'  # Incluye timestamps
)
```

### 2. Transcribir file object (Django/Flask upload)

```python
# En Django
from django.core.files.uploadedfile import UploadedFile

def mi_vista(request):
    audio = request.FILES['grabacion']  # UploadedFile object

    trans = Transcriptor(api_key=settings.GROQ_API_KEY)
    resultado = trans.transcribir(audio, language='es')

    # Guardar en DB
    MiModelo.objects.create(transcripcion=resultado['text'])
```

```python
# En Flask
from flask import request

@app.route('/upload', methods=['POST'])
def upload():
    audio = request.files['audio']  # FileStorage object

    trans = Transcriptor(api_key=GROQ_API_KEY)
    resultado = trans.transcribir(audio)

    return jsonify(resultado)
```

### 3. Transcribir desde URL

```python
trans = Transcriptor(api_key='gsk_...')

resultado = trans.transcribir_url(
    'https://ejemplo.com/audio.mp3',
    language='es'
)
```

### 4. Archivos grandes (chunking automático)

```python
# Archivo de 100MB se divide automáticamente
resultado = trans.transcribir(
    'archivo_grande.mp3',
    language='es',
    chunk_if_needed=True  # Default: True
)

print(f"Se procesó en {resultado['chunks']} partes")
```

### 5. Personalizar modelo

```python
# Usar modelo específico
trans = Transcriptor(
    api_key='gsk_...',
    default_model='whisper-large-v3-turbo'  # Más rápido
)

# O especificar por llamada
resultado = trans.transcribir(
    'audio.mp3',
    model='whisper-large-v3'  # Más preciso pero lento
)
```

---

## 🔧 API Reference

### `Transcriptor(api_key, default_model='whisper-large-v3-turbo')`

Constructor de la clase principal.

**Parámetros:**
- `api_key` (str): API Key de Groq (obligatorio)
- `default_model` (str): Modelo por defecto

**Ejemplo:**
```python
trans = Transcriptor(api_key='gsk_...')
```

---

### `transcribir(archivo, language='es', model=None, prompt='', format='json', chunk_if_needed=True)`

Transcribe un archivo de audio o video.

**Parámetros:**
- `archivo` (str | Path | file-like): Ruta o file object
- `language` (str): Código ISO del idioma ('es', 'en', 'fr', etc.)
- `model` (str): Modelo a usar (None = usar default)
- `prompt` (str): Contexto opcional para mejor precisión
- `format` (str): 'json', 'text', 'verbose_json'
- `chunk_if_needed` (bool): Dividir archivos grandes automáticamente

**Retorna:**
```python
{
    'text': str,           # Texto transcrito
    'language': str,       # Idioma usado
    'duration': float,     # Duración en segundos
    'success': bool,       # Si fue exitoso
    'model': str,          # Modelo usado
    'chunks': int          # Número de chunks procesados
}
```

**Excepciones:**
- `FileNotFoundError`: Archivo no existe
- `ValueError`: Archivo no válido
- `Exception`: Error de API

---

### `transcribir_url(url, language='es', model=None, prompt='')`

Transcribe audio desde una URL.

**Parámetros:**
- `url` (str): URL del archivo
- Otros igual que `transcribir()`

**Retorna:** Mismo dict que `transcribir()`

---

## 🌐 Integración con Frameworks

### Django

Ver: [`examples/django_example.py`](examples/django_example.py)

```python
from transcriptor import Transcriptor
from django.conf import settings

trans = Transcriptor(api_key=settings.GROQ_API_KEY)
resultado = trans.transcribir(request.FILES['audio'])
```

### Flask

Ver: [`examples/flask_example.py`](examples/flask_example.py)

```python
from transcriptor import Transcriptor

trans = Transcriptor(api_key=GROQ_API_KEY)
resultado = trans.transcribir(request.files['audio'])
```

### Laravel

Ver: [`examples/laravel_integration.md`](examples/laravel_integration.md)

```php
// Opción 1: Via Python script
$output = shell_exec("python3 transcribir.py $apiKey $audioPath");
$resultado = json_decode($output, true);

// Opción 2: Via API Flask interna
$response = Http::attach('audio', ...)->post('http://localhost:5555/transcribir');
```

---

## 🛠️ Requisitos del Sistema

### Python
- Python 3.7 o superior
- `requests` (se instala automáticamente)

### Software Externo
- **ffmpeg** (obligatorio para video y chunking)

#### Instalar ffmpeg:

**macOS:**
```bash
brew install ffmpeg
```

**Ubuntu/Debian:**
```bash
sudo apt-get install ffmpeg
```

**Windows:**
Descargar de: https://ffmpeg.org/download.html

---

## ⚙️ Configuración

### API Key de Groq

Obtén tu API key gratis en: https://console.groq.com

```python
trans = Transcriptor(api_key='gsk_TuAPIKeyAqui')
```

### Modelos Disponibles

- `whisper-large-v3-turbo` (recomendado) - Rápido y preciso
- `whisper-large-v3` - Más preciso pero más lento

### Idiomas Soportados

Códigos ISO 639-1: `es`, `en`, `fr`, `de`, `it`, `pt`, `ru`, `ja`, `zh`, etc.

---

## 📊 Limitaciones

### Groq API
- **Tamaño máximo por archivo:** 25MB
- **Solución:** La librería divide archivos grandes automáticamente

### Rendimiento
- **Archivos grandes:** Se procesan en chunks de ~4 minutos
- **Videos:** Primero se extrae el audio (añade ~10-30% de tiempo)

---

## 🐛 Solución de Problemas

### Error: "ffmpeg not found"

**Solución:** Instala ffmpeg (ver sección Requisitos)

```bash
# Verificar instalación
ffmpeg -version
```

### Error: "API Key inválida"

**Solución:** Verifica tu API key en https://console.groq.com

### Error: "File too large"

**Solución:** Asegúrate de tener `chunk_if_needed=True` (es el default)

### Transcripción incorrecta

**Solución:** Usa el parámetro `prompt` para dar contexto:

```python
resultado = trans.transcribir(
    'audio.mp3',
    prompt='Reunión sobre desarrollo de software. Términos técnicos: Python, Django, API.'
)
```

---

## 🔒 Seguridad

- ✅ **No almacena audios:** Los archivos temporales se eliminan automáticamente
- ✅ **API Key segura:** Nunca incluyas la key en código versionado
- ✅ **Validación de archivos:** Verifica extensiones antes de procesar

**Buenas prácticas:**

```python
# ❌ NUNCA hagas esto
trans = Transcriptor(api_key='gsk_hardcoded_key')

# ✅ Usa variables de entorno
import os
trans = Transcriptor(api_key=os.getenv('GROQ_API_KEY'))

# ✅ O configuración de framework
trans = Transcriptor(api_key=settings.GROQ_API_KEY)  # Django
trans = Transcriptor(api_key=app.config['GROQ_KEY'])  # Flask
```

---

## 📈 Rendimiento

### Tiempos Aproximados

| Duración Audio | Modelo Turbo | Modelo Large |
|----------------|--------------|--------------|
| 1 minuto | ~2-3 seg | ~5-8 seg |
| 5 minutos | ~8-12 seg | ~20-30 seg |
| 30 minutos | ~45-60 seg | ~2-3 min |
| 1 hora | ~2-3 min | ~5-7 min |

*Tiempos reales dependen de la red y carga de la API*

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama: `git checkout -b feature/nueva-funcionalidad`
3. Commit: `git commit -m 'Agrega X funcionalidad'`
4. Push: `git push origin feature/nueva-funcionalidad`
5. Abre un Pull Request

---

## 📄 Licencia

[Especificar licencia]

---

## 👨‍💻 Desarrollado por

**Grupo Lada Technologies**

Para soporte: [tu email]

---

## 🎯 Roadmap

- [ ] Soporte para streaming en tiempo real
- [ ] Cache de transcripciones duplicadas
- [ ] Detección automática de idioma
- [ ] Soporte para múltiples archivos en batch
- [ ] Webhooks para notificaciones
- [ ] SDK para PHP nativo

---

**¡Disfruta transcribiendo con IA!** 🚀
