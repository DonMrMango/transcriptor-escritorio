"""
Ejemplo de integración con Django
Grupo Lada Technologies
"""

# ========================================
# 1. INSTALACIÓN
# ========================================
"""
# Opción A: Desde carpeta local
pip install -e /ruta/a/transcriptor-lib/

# Opción B: Copiar carpeta transcriptor/ a tu proyecto Django
cp -r transcriptor-lib/transcriptor/ mi_proyecto/transcriptor/
"""

# ========================================
# 2. CONFIGURACIÓN EN settings.py
# ========================================
"""
# settings.py
GROQ_API_KEY = 'tu_api_key_de_groq'
TRANSCRIPTOR_DEFAULT_LANGUAGE = 'es'
TRANSCRIPTOR_MODEL = 'whisper-large-v3-turbo'
"""

# ========================================
# 3. MODELO (models.py)
# ========================================
"""
from django.db import models
from django.contrib.auth.models import User

class Formulario(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    # Audio
    archivo_audio = models.FileField(upload_to='audios/', null=True, blank=True)

    # Transcripción
    transcripcion = models.TextField(blank=True)
    duracion_segundos = models.IntegerField(null=True, blank=True)
    idioma = models.CharField(max_length=10, default='es')

    # Metadata
    modelo_usado = models.CharField(max_length=50, blank=True)
    fecha_transcripcion = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'formularios'
        ordering = ['-fecha_creacion']
"""

# ========================================
# 4. VISTA (views.py)
# ========================================

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.conf import settings
from django.utils import timezone
from .models import Formulario
from transcriptor import Transcriptor

@login_required
def crear_formulario(request):
    """Vista para crear formulario con grabación"""

    if request.method == 'POST':
        # Obtener archivo de audio
        audio_file = request.FILES.get('grabacion')

        if not audio_file:
            return render(request, 'formulario.html', {
                'error': 'No se recibió archivo de audio'
            })

        # Crear instancia del transcriptor
        trans = Transcriptor(
            api_key=settings.GROQ_API_KEY,
            default_model=settings.TRANSCRIPTOR_MODEL
        )

        try:
            # Transcribir
            resultado = trans.transcribir(
                audio_file,
                language=settings.TRANSCRIPTOR_DEFAULT_LANGUAGE
            )

            # Guardar en base de datos
            formulario = Formulario.objects.create(
                usuario=request.user,
                archivo_audio=audio_file,
                transcripcion=resultado['text'],
                duracion_segundos=int(resultado.get('duration', 0)),
                idioma=resultado['language'],
                modelo_usado=resultado['model'],
                fecha_transcripcion=timezone.now()
            )

            return redirect('formulario_detalle', pk=formulario.pk)

        except Exception as e:
            return render(request, 'formulario.html', {
                'error': f'Error en transcripción: {str(e)}'
            })

    return render(request, 'formulario.html')


@login_required
def retranscribir(request, pk):
    """Re-transcribir un formulario existente"""

    formulario = Formulario.objects.get(pk=pk, usuario=request.user)

    if not formulario.archivo_audio:
        return redirect('formulario_detalle', pk=pk)

    trans = Transcriptor(api_key=settings.GROQ_API_KEY)

    try:
        # Re-transcribir desde el archivo guardado
        resultado = trans.transcribir(
            formulario.archivo_audio.path,  # Ruta del archivo en MEDIA
            language='es'
        )

        # Actualizar
        formulario.transcripcion = resultado['text']
        formulario.fecha_transcripcion = timezone.now()
        formulario.save()

        return redirect('formulario_detalle', pk=pk)

    except Exception as e:
        # Manejar error
        pass


# ========================================
# 5. FORMULARIO HTML
# ========================================
"""
<!-- templates/formulario.html -->
{% extends 'base.html' %}

{% block content %}
<h2>Crear Formulario con Grabación</h2>

{% if error %}
    <div class="alert alert-danger">{{ error }}</div>
{% endif %}

<form method="post" enctype="multipart/form-data">
    {% csrf_token %}

    <div class="form-group">
        <label>Grabar Audio:</label>
        <button type="button" id="btnGrabar">🎤 Grabar</button>
        <button type="button" id="btnDetener" style="display:none;">⏹️ Detener</button>
        <span id="timer"></span>
    </div>

    <div class="form-group">
        <label>O subir archivo:</label>
        <input type="file" name="grabacion" accept="audio/*,video/*">
    </div>

    <button type="submit" class="btn btn-primary">
        Enviar y Transcribir
    </button>
</form>

<script>
let mediaRecorder;
let chunks = [];

document.getElementById('btnGrabar').onclick = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    mediaRecorder = new MediaRecorder(stream);

    mediaRecorder.ondataavailable = e => chunks.push(e.data);

    mediaRecorder.onstop = () => {
        const blob = new Blob(chunks, { type: 'audio/webm' });
        const file = new File([blob], 'grabacion.webm');

        // Asignar al input
        const dt = new DataTransfer();
        dt.items.add(file);
        document.querySelector('input[type="file"]').files = dt.files;
    };

    mediaRecorder.start();
    document.getElementById('btnGrabar').style.display = 'none';
    document.getElementById('btnDetener').style.display = 'inline';
};

document.getElementById('btnDetener').onclick = () => {
    mediaRecorder.stop();
    document.getElementById('btnGrabar').style.display = 'inline';
    document.getElementById('btnDetener').style.display = 'none';
};
</script>
{% endblock %}
"""

# ========================================
# 6. URLS (urls.py)
# ========================================
"""
from django.urls import path
from . import views

urlpatterns = [
    path('formulario/crear/', views.crear_formulario, name='crear_formulario'),
    path('formulario/<int:pk>/', views.formulario_detalle, name='formulario_detalle'),
    path('formulario/<int:pk>/retranscribir/', views.retranscribir, name='retranscribir'),
]
"""

# ========================================
# 7. TASK ASÍNCRONO CON CELERY (OPCIONAL)
# ========================================
"""
# tasks.py
from celery import shared_task
from transcriptor import Transcriptor
from .models import Formulario
from django.conf import settings

@shared_task
def transcribir_async(formulario_id):
    formulario = Formulario.objects.get(id=formulario_id)

    trans = Transcriptor(api_key=settings.GROQ_API_KEY)
    resultado = trans.transcribir(
        formulario.archivo_audio.path,
        language='es'
    )

    formulario.transcripcion = resultado['text']
    formulario.save()

    return formulario_id


# En views.py:
from .tasks import transcribir_async

def crear_formulario(request):
    # ... guardar formulario ...

    # Transcribir en background
    transcribir_async.delay(formulario.id)

    return redirect('formulario_detalle', pk=formulario.pk)
"""
