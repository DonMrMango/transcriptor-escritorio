# Integración con Laravel

Existen **3 opciones** para integrar el transcriptor con Laravel:

---

## Opción 1: Python Script + Subprocess (Recomendado)

Crea un script Python wrapper y llámalo desde Laravel.

### 1.1 Crear script wrapper

```python
# resources/python/transcribir.py
import sys
import json
from transcriptor import Transcriptor

def main():
    if len(sys.argv) < 3:
        print(json.dumps({'error': 'Uso: python transcribir.py API_KEY ARCHIVO'}))
        sys.exit(1)

    api_key = sys.argv[1]
    archivo = sys.argv[2]
    language = sys.argv[3] if len(sys.argv) > 3 else 'es'

    trans = Transcriptor(api_key=api_key)

    try:
        resultado = trans.transcribir(archivo, language=language)
        print(json.dumps(resultado))
    except Exception as e:
        print(json.dumps({'error': str(e)}))
        sys.exit(1)

if __name__ == '__main__':
    main()
```

### 1.2 Service en Laravel

```php
<?php
// app/Services/TranscriptorService.php

namespace App\Services;

use Illuminate\Support\Facades\Storage;
use Illuminate\Http\UploadedFile;

class TranscriptorService
{
    private $apiKey;
    private $pythonPath;
    private $scriptPath;

    public function __construct()
    {
        $this->apiKey = env('GROQ_API_KEY');
        $this->pythonPath = env('PYTHON_PATH', 'python3');
        $this->scriptPath = resource_path('python/transcribir.py');
    }

    public function transcribir(UploadedFile $audio, string $language = 'es')
    {
        // Guardar archivo temporalmente
        $path = $audio->store('temp');
        $fullPath = Storage::path($path);

        try {
            // Ejecutar script Python
            $command = sprintf(
                '%s %s %s %s %s',
                escapeshellcmd($this->pythonPath),
                escapeshellarg($this->scriptPath),
                escapeshellarg($this->apiKey),
                escapeshellarg($fullPath),
                escapeshellarg($language)
            );

            $output = shell_exec($command);
            $result = json_decode($output, true);

            // Eliminar temporal
            Storage::delete($path);

            if (isset($result['error'])) {
                throw new \Exception($result['error']);
            }

            return $result;

        } catch (\Exception $e) {
            Storage::delete($path);
            throw $e;
        }
    }
}
```

### 1.3 Controller

```php
<?php
// app/Http/Controllers/FormularioController.php

namespace App\Http\Controllers;

use App\Models\Formulario;
use App\Services\TranscriptorService;
use Illuminate\Http\Request;

class FormularioController extends Controller
{
    public function store(Request $request, TranscriptorService $transcriptor)
    {
        $request->validate([
            'grabacion' => 'required|file|mimes:mp3,wav,m4a,mp4,mov',
        ]);

        $audio = $request->file('grabacion');

        try {
            // Transcribir
            $resultado = $transcriptor->transcribir($audio);

            // Guardar archivo permanentemente
            $audioPath = $audio->store('audios');

            // Crear formulario
            $formulario = Formulario::create([
                'user_id' => auth()->id(),
                'audio_path' => $audioPath,
                'transcripcion' => $resultado['text'],
                'duracion' => $resultado['duration'] ?? null,
                'idioma' => $resultado['language'] ?? 'es',
                'modelo' => $resultado['model'] ?? null,
            ]);

            return redirect()
                ->route('formularios.show', $formulario)
                ->with('success', 'Formulario creado y transcrito');

        } catch (\Exception $e) {
            return back()
                ->withInput()
                ->withErrors(['error' => 'Error en transcripción: ' . $e->getMessage()]);
        }
    }
}
```

### 1.4 Modelo

```php
<?php
// app/Models/Formulario.php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;

class Formulario extends Model
{
    protected $fillable = [
        'user_id',
        'audio_path',
        'transcripcion',
        'duracion',
        'idioma',
        'modelo',
    ];

    protected $casts = [
        'duracion' => 'integer',
    ];

    public function user()
    {
        return $this->belongsTo(User::class);
    }
}
```

### 1.5 Migración

```php
<?php
// database/migrations/xxxx_create_formularios_table.php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    public function up()
    {
        Schema::create('formularios', function (Blueprint $table) {
            $table->id();
            $table->foreignId('user_id')->constrained()->onDelete('cascade');
            $table->string('audio_path');
            $table->text('transcripcion')->nullable();
            $table->integer('duracion')->nullable();
            $table->string('idioma', 10)->default('es');
            $table->string('modelo', 50)->nullable();
            $table->timestamps();
        });
    }

    public function down()
    {
        Schema::dropIfExists('formularios');
    }
};
```

### 1.6 .env

```env
GROQ_API_KEY=tu_api_key_de_groq
PYTHON_PATH=python3
```

---

## Opción 2: API Flask Interna

Ejecuta el transcriptor como API Flask interna.

### 2.1 Crear API Flask

```python
# resources/api/transcriptor_api.py
from flask import Flask, request, jsonify
from transcriptor import Transcriptor
import os

app = Flask(__name__)
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

@app.route('/transcribir', methods=['POST'])
def transcribir():
    if 'audio' not in request.files:
        return jsonify({'error': 'No file'}), 400

    audio = request.files['audio']
    language = request.form.get('language', 'es')

    trans = Transcriptor(api_key=GROQ_API_KEY)

    try:
        resultado = trans.transcribir(audio, language=language)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(port=5555)
```

### 2.2 Service Laravel

```php
<?php
// app/Services/TranscriptorApiService.php

namespace App\Services;

use Illuminate\Support\Facades\Http;
use Illuminate\Http\UploadedFile;

class TranscriptorApiService
{
    private $apiUrl;

    public function __construct()
    {
        $this->apiUrl = env('TRANSCRIPTOR_API_URL', 'http://localhost:5555');
    }

    public function transcribir(UploadedFile $audio, string $language = 'es')
    {
        $response = Http::attach(
            'audio', fopen($audio->getPathname(), 'r'), $audio->getClientOriginalName()
        )->post("{$this->apiUrl}/transcribir", [
            'language' => $language
        ]);

        if ($response->failed()) {
            throw new \Exception($response->json()['error'] ?? 'Error desconocido');
        }

        return $response->json();
    }
}
```

---

## Opción 3: Job Asíncrono con Queue

Para no bloquear la request HTTP.

### 3.1 Job

```php
<?php
// app/Jobs/TranscribirAudioJob.php

namespace App\Jobs;

use App\Models\Formulario;
use App\Services\TranscriptorService;
use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;

class TranscribirAudioJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $formulario;

    public function __construct(Formulario $formulario)
    {
        $this->formulario = $formulario;
    }

    public function handle(TranscriptorService $transcriptor)
    {
        try {
            $audioPath = storage_path('app/' . $this->formulario->audio_path);

            // Transcribir
            $resultado = $transcriptor->transcribir(
                new \Illuminate\Http\UploadedFile($audioPath, basename($audioPath))
            );

            // Actualizar formulario
            $this->formulario->update([
                'transcripcion' => $resultado['text'],
                'duracion' => $resultado['duration'] ?? null,
            ]);

        } catch (\Exception $e) {
            // Log error
            \Log::error('Error transcribiendo: ' . $e->getMessage());

            $this->formulario->update([
                'transcripcion' => 'Error: ' . $e->getMessage()
            ]);
        }
    }
}
```

### 3.2 Usar en Controller

```php
public function store(Request $request)
{
    $audio = $request->file('grabacion');
    $audioPath = $audio->store('audios');

    // Crear formulario SIN transcripción
    $formulario = Formulario::create([
        'user_id' => auth()->id(),
        'audio_path' => $audioPath,
        'transcripcion' => null, // Se llenará después
    ]);

    // Despachar job para transcribir en background
    TranscribirAudioJob::dispatch($formulario);

    return redirect()
        ->route('formularios.show', $formulario)
        ->with('info', 'Formulario creado. La transcripción se procesará en breve.');
}
```

---

## Comparación de Opciones

| Aspecto | Opción 1 (Script) | Opción 2 (API) | Opción 3 (Queue) |
|---------|-------------------|----------------|------------------|
| **Complejidad** | Baja | Media | Media |
| **Performance** | Bloquea request | Bloquea request | No bloquea |
| **Escalabilidad** | Baja | Media | Alta |
| **Deploy** | Simple | Requiere 2 procesos | Requiere worker |
| **Recomendado para** | Prototipos | Apps pequeñas | Producción |

---

## Instalación en Servidor

```bash
# En tu servidor Laravel
cd /var/www/laravel-app

# Instalar transcriptor
pip3 install -e /ruta/a/transcriptor-lib/

# Verificar
python3 -c "from transcriptor import Transcriptor; print('OK')"

# Si usas Opción 2, ejecutar API:
python3 resources/api/transcriptor_api.py &

# Si usas Opción 3, ejecutar queue worker:
php artisan queue:work
```

---

**Recomendación:** Usa **Opción 1** para proyectos simples, **Opción 3** para producción.
