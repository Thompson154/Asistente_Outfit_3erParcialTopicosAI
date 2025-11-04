# Outfit Assistant AI - Guía de Inicio Rápido

## 📁 Estructura del Proyecto

```
3erParcial_Topicos_SelectosAI/
├── database.py          # Nueva base de datos para ropa y outfits
├── tools.py            # Herramientas para manejo de prendas e imágenes
├── agent.py            # Agente DSPy para recomendaciones de outfit
├── api.py              # API REST con FastAPI
├── static/             # Archivos estáticos (CSS, JS)
│   ├── css/styles.css
│   └── js/app.js
├── templates/          # Templates HTML
│   ├── index.html      # Página principal
│   ├── upload.html     # Subir prendas
│   ├── wardrobe.html   # Ver guardarropa
│   └── outfits.html    # Outfits guardados
├── uploads/            # Almacenamiento de imágenes
│   └── clothes/
├── .env                # Variables de entorno (OPENAI_API_KEY)
└── pyproject.toml      # Dependencias actualizadas
```

## 🚀 Cómo Ejecutar

### 1. Verifica las dependencias
```bash
uv sync
```

### 2. Configura tu API Key de OpenAI
Asegúrate de que `.env` contiene:
```
OPENAI_API_KEY=tu_api_key_aquí
```

### 3. Inicia el servidor
```bash
uv run fastapi dev api.py
```

O con uvicorn:
```bash
uv run uvicorn api:app --reload --host 0.0.0.0 --port 8000
```

### 4. Abre tu navegador
Visita: http://localhost:8000

## 📱 Funcionalidades

### 1. Subir Prendas
- Ve a `/upload`
- Arrastra o selecciona una imagen de ropa
- La IA (GPT-4o-mini) analizará automáticamente la imagen
- Revisa y confirma las etiquetas sugeridas
- Guarda la prenda en tu guardarropa

### 2. Ver Guardarropa
- Ve a `/wardrobe`
- Visualiza todas tus prendas organizadas
- Cada prenda muestra sus etiquetas (tipo, color, categoría, ocasión, estilo)
- Elimina prendas si lo deseas

### 3. Generar Outfits
- Desde la página principal (`/`)
- Describe la ocasión (ej: "fiesta de terror", "entrevista de trabajo")
- Agrega preferencias opcionales
- El agente (GPT-4o) analizará tu guardarropa y generará recomendaciones

### 4. Guardar Outfits
- Los outfits generados se guardan automáticamente
- Ve a `/outfits` para ver tus combinaciones guardadas

## 🤖 Modelos de IA Utilizados

1. **GPT-4o-mini** (análisis de imágenes)
   - Análisis visual de prendas
   - Generación automática de etiquetas
   - Rápido y económico

2. **GPT-4o** (recomendaciones)
   - Razonamiento complejo para combinaciones
   - Entendimiento de contexto y ocasiones
   - Recomendaciones personalizadas

## 🗄️ Base de Datos

SQLite con las siguientes tablas:

- `clothes`: Prendas con rutas de imágenes
- `tags`: Etiquetas de cada prenda
- `outfits`: Outfits guardados
- `outfit_items`: Relación entre outfits y prendas
- `user_requests`: Historial de consultas

## 🎨 Tecnologías

- **Backend**: FastAPI + Python 3.12
- **IA**: OpenAI API + DSPy (ReAct Agent)
- **Frontend**: HTML + Tailwind CSS + Vanilla JS
- **Base de Datos**: SQLite
- **Procesamiento de Imágenes**: Pillow (PIL)

## 📝 API Endpoints

### Prendas
- `POST /api/clothes/upload` - Subir y analizar imagen
- `POST /api/clothes` - Guardar prenda con tags
- `GET /api/clothes` - Listar todas las prendas
- `GET /api/clothes/{id}` - Detalle de prenda
- `DELETE /api/clothes/{id}` - Eliminar prenda

### Outfits
- `POST /api/outfits/generate` - Generar outfit con IA
- `POST /api/outfits` - Guardar outfit
- `GET /api/outfits` - Listar outfits guardados
- `GET /api/outfits/{id}` - Detalle de outfit

### HTML Pages
- `GET /` - Página principal
- `GET /upload` - Subir prendas
- `GET /wardrobe` - Ver guardarropa
- `GET /outfits` - Outfits guardados

## 🔧 Solución de Problemas

### Error: "Import PIL could not be resolved"
Ejecuta: `uv sync` para instalar Pillow

### Error: "OPENAI_API_KEY not found"
Verifica que `.env` contiene tu API key

### Error al subir imágenes
Verifica que la carpeta `uploads/clothes` existe y tiene permisos de escritura

### El servidor no inicia
Verifica que el puerto 8000 está disponible o usa otro: `--port 8080`

## 📱 Responsive Design

La interfaz es completamente responsive y funciona en:
- 💻 Desktop
- 📱 Móvil
- 🖥️ Tablet

## 🎯 Próximos Pasos Sugeridos

1. Sube algunas prendas de prueba
2. Experimenta con diferentes ocasiones
3. Guarda tus outfits favoritos
4. Personaliza los estilos en `static/css/styles.css`

## 📚 Recursos

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [DSPy Docs](https://dspy-docs.vercel.app/)
- [OpenAI API](https://platform.openai.com/docs/)

## ✅ Testing

Para probar que todo funciona:

```bash
# 1. Verificar sintaxis
uv run python -m py_compile database.py tools.py agent.py api.py

# 2. Iniciar servidor
uv run fastapi dev api.py

# 3. En otro terminal, probar endpoints
curl http://localhost:8000/api/clothes
```

---

**¡Disfruta tu nuevo Asistente de Outfit! 👔✨**
