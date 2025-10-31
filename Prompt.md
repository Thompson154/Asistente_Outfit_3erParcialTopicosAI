Eres un experto en desarrollo de agentes inteligentes utilizando la API de OpenAI, con amplio conocimiento en FastAPI, Python asíncrono (uvicorn, asyncio), SQLite y desarrollo frontend responsivo (HTML, CSS, Tailwind o React).

Tu tarea es construir un asistente de outfit inteligente, basado en el contexto descrito en el archivo README.md del proyecto.

Objetivos del proyecto

El asistente debe permitir que el usuario:

Suba imágenes de las prendas de su clóset.

Etiquete manualmente o automáticamente las prendas (tipo, color, categoría).

Consulte outfits personalizados mediante lenguaje natural, usando los modelos de OpenAI adecuados.

Guarde y consulte prendas u outfits almacenados localmente (SQLite).

Instrucciones Generales

Analiza primero los archivos Python existentes en el repositorio para:

Comprender el estilo, estructura y nivel de código actual.

Mantener coherencia con el formato, estilo y convenciones ya usadas (nomenclatura, dependencias, estructura de carpetas).

Implementa lo siguiente:

Agente principal: que reciba instrucciones del usuario, procese las solicitudes y orqueste las llamadas a herramientas internas.

Herramientas (Tools): para manejar:

Subida y almacenamiento de imágenes.

Generación o lectura de etiquetas.

Consultas a la base de datos SQLite.

Generación de combinaciones de outfit con contexto.

API REST (FastAPI):

Endpoints para subir imágenes, consultar prendas y generar outfits.

Endpoint para interactuar con el agente.

Base de datos SQLite:

Tablas: clothes, tags, outfits, user_requests.

Relaciones simples (por ejemplo: una prenda puede tener múltiples etiquetas).

Interfaz de usuario responsiva:

Crea una interfaz web y móvil sencilla (puede ser en HTML + Tailwind o React).

Permite al usuario subir imágenes de ropa.

Tras subir una imagen, muestra una lista corta de botones con etiquetas sugeridas (tipo, color, categoría, ocasión).

El usuario puede seleccionar o editar esas etiquetas antes de guardar.

Debe ser totalmente funcional desde navegador móvil y de escritorio.

Modelos de OpenAI:

Utiliza el modelo más adecuado para cada tarea:

gpt-4.1 o superior para razonamiento y generación de outfits.

gpt-4o-mini o gpt-4o para análisis rápido de imágenes y etiquetado visual.

Si es necesario, crea un flujo que combine visión (imagen) + texto en una sola consulta.

Buenas prácticas:

Usa tipado estático (typing) en Python.

Mantén un manejo adecuado de excepciones.

Implementa endpoints asincrónicos (async def).

Organiza el proyecto siguiendo una estructura limpia:

app/
  ├── main.py
  ├── api/
  │   ├── endpoints/
  │   └── models/
  ├── core/
  ├── db/
  ├── agents/
  └── ui/


Entrega esperada:

Código funcional (backend + interfaz).

Explicación breve del flujo de datos entre usuario → API → agente → respuesta.

Archivo requirements.txt actualizado.

Criterios de calidad

Código modular, legible y escalable.

Interfaz fluida y responsiva.

Uso eficiente de los modelos de OpenAI.

Persistencia confiable en SQLite.

Capacidad de extensión futura (por ejemplo, integración con almacenamiento en la nube o APIs de moda).