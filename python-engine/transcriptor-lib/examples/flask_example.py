"""
Ejemplo de integración con Flask
Grupo Lada Technologies
"""

from flask import Flask, request, jsonify, render_template
from transcriptor import Transcriptor
import os

app = Flask(__name__)

# Configuración
GROQ_API_KEY = os.getenv('GROQ_API_KEY', 'tu_api_key_aqui')
UPLOAD_FOLDER = 'uploads/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ========================================
# 1. RUTA SIMPLE DE TRANSCRIPCIÓN
# ========================================

@app.route('/transcribir', methods=['POST'])
def transcribir():
    """Endpoint simple para transcribir audio"""

    if 'audio' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400

    audio_file = request.files['audio']

    # Crear transcriptor
    trans = Transcriptor(api_key=GROQ_API_KEY)

    try:
        # Transcribir directamente del file object
        resultado = trans.transcribir(
            audio_file,
            language=request.form.get('language', 'es'),
            model=request.form.get('model', 'whisper-large-v3-turbo')
        )

        return jsonify({
            'success': True,
            'text': resultado['text'],
            'duration': resultado['duration'],
            'model': resultado['model'],
            'chunks': resultado['chunks']
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ========================================
# 2. RUTA CON GUARDADO EN DISCO
# ========================================

@app.route('/transcribir/guardar', methods=['POST'])
def transcribir_y_guardar():
    """Transcribe y guarda el archivo en disco"""

    if 'audio' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400

    audio_file = request.files['audio']
    filename = audio_file.filename

    # Guardar archivo
    filepath = os.path.join(UPLOAD_FOLDER, filename)
    audio_file.save(filepath)

    # Transcribir
    trans = Transcriptor(api_key=GROQ_API_KEY)

    try:
        resultado = trans.transcribir(filepath, language='es')

        return jsonify({
            'success': True,
            'text': resultado['text'],
            'file': filename,
            'duration': resultado['duration']
        })

    except Exception as e:
        # Eliminar archivo si falló
        if os.path.exists(filepath):
            os.remove(filepath)

        return jsonify({'error': str(e)}), 500


# ========================================
# 3. RUTA PARA TRANSCRIBIR DESDE URL
# ========================================

@app.route('/transcribir/url', methods=['POST'])
def transcribir_url():
    """Transcribe audio desde una URL"""

    data = request.get_json()
    url = data.get('url')

    if not url:
        return jsonify({'error': 'URL no proporcionada'}), 400

    trans = Transcriptor(api_key=GROQ_API_KEY)

    try:
        resultado = trans.transcribir_url(
            url,
            language=data.get('language', 'es')
        )

        return jsonify({
            'success': True,
            'text': resultado['text'],
            'duration': resultado['duration']
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# ========================================
# 4. INTERFAZ WEB SIMPLE
# ========================================

@app.route('/')
def index():
    """Página principal con formulario"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Transcriptor Flask</title>
        <style>
            body { font-family: Arial; max-width: 600px; margin: 50px auto; }
            .form-group { margin: 20px 0; }
            button { padding: 10px 20px; cursor: pointer; }
            #result { margin-top: 20px; padding: 15px; background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>🎙️ Transcriptor con Flask</h1>

        <form id="uploadForm">
            <div class="form-group">
                <label>Selecciona audio:</label><br>
                <input type="file" id="audioFile" accept="audio/*,video/*" required>
            </div>

            <div class="form-group">
                <label>Idioma:</label><br>
                <select id="language">
                    <option value="es">Español</option>
                    <option value="en">English</option>
                    <option value="fr">Français</option>
                </select>
            </div>

            <button type="submit">Transcribir</button>
        </form>

        <div id="result" style="display:none;">
            <h3>Resultado:</h3>
            <p id="transcription"></p>
            <small>Duración: <span id="duration"></span>s | Chunks: <span id="chunks"></span></small>
        </div>

        <script>
        document.getElementById('uploadForm').addEventListener('submit', async (e) => {
            e.preventDefault();

            const formData = new FormData();
            formData.append('audio', document.getElementById('audioFile').files[0]);
            formData.append('language', document.getElementById('language').value);

            // Mostrar loading
            document.getElementById('result').style.display = 'block';
            document.getElementById('transcription').innerText = 'Transcribiendo...';

            try {
                const response = await fetch('/transcribir', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();

                if (data.success) {
                    document.getElementById('transcription').innerText = data.text;
                    document.getElementById('duration').innerText = data.duration.toFixed(2);
                    document.getElementById('chunks').innerText = data.chunks;
                } else {
                    document.getElementById('transcription').innerText = 'Error: ' + data.error;
                }
            } catch (error) {
                document.getElementById('transcription').innerText = 'Error: ' + error.message;
            }
        });
        </script>
    </body>
    </html>
    '''


# ========================================
# 5. EJEMPLO CON BASE DE DATOS (SQLAlchemy)
# ========================================

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///transcripciones.db'
db = SQLAlchemy(app)

class Transcripcion(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    fecha = db.Column(db.DateTime, default=datetime.utcnow)
    nombre_archivo = db.Column(db.String(200))
    texto = db.Column(db.Text)
    duracion = db.Column(db.Float)
    idioma = db.Column(db.String(10))
    modelo = db.Column(db.String(50))

@app.route('/transcribir/db', methods=['POST'])
def transcribir_a_db():
    """Transcribe y guarda en base de datos"""

    if 'audio' not in request.files:
        return jsonify({'error': 'No se recibió archivo'}), 400

    audio_file = request.files['audio']

    trans = Transcriptor(api_key=GROQ_API_KEY)

    try:
        resultado = trans.transcribir(audio_file, language='es')

        # Guardar en DB
        transcripcion = Transcripcion(
            nombre_archivo=audio_file.filename,
            texto=resultado['text'],
            duracion=resultado['duration'],
            idioma=resultado['language'],
            modelo=resultado['model']
        )

        db.session.add(transcripcion)
        db.session.commit()

        return jsonify({
            'success': True,
            'id': transcripcion.id,
            'text': resultado['text']
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/transcripciones', methods=['GET'])
def listar_transcripciones():
    """Lista todas las transcripciones"""

    transcripciones = Transcripcion.query.order_by(
        Transcripcion.fecha.desc()
    ).all()

    return jsonify([{
        'id': t.id,
        'fecha': t.fecha.isoformat(),
        'archivo': t.nombre_archivo,
        'texto': t.texto[:200] + '...',  # Preview
        'duracion': t.duracion
    } for t in transcripciones])


# ========================================
# EJECUTAR
# ========================================

if __name__ == '__main__':
    # Crear tablas
    with app.app_context():
        db.create_all()

    print("🚀 Flask app corriendo en http://localhost:5000")
    app.run(debug=True, port=5000)
