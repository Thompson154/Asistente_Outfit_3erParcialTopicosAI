Asistente de Outfit con OpenAI
Contexto del Proyecto

Este proyecto implementa un asistente personal de moda impulsado por la API de OpenAI, capaz de recomendar combinaciones de ropa (outfits) a partir del guardarropa del usuario.

Descripción General

El asistente permite al usuario subir fotos de las prendas de su clóset, las cuales pueden ser etiquetadas automáticamente por el sistema o manualmente por el usuario.

Luego, mediante instrucciones en lenguaje natural, el usuario puede solicitar outfits personalizados.
Por ejemplo:

"Quiero un outfit para una fiesta de terror."

El asistente analizará las prendas disponibles y devolverá una combinación ordenada de ropa adecuada para ese evento o situación.

Flujo del Sistema

El usuario carga imágenes de su ropa desde su clóset.

El agente etiqueta automáticamente las prendas (por tipo, color, estilo, etc.) si el usuario no lo hace.

El usuario realiza una solicitud en lenguaje natural (por ejemplo, “necesito un outfit para una entrevista de trabajo”).

El agente genera una combinación óptima de prendas existentes, en orden lógico (por ejemplo: camisa → pantalón → zapatos).

El usuario puede agregar nueva ropa o guardar outfits para futuras consultas.

Almacenamiento de Datos

Las imágenes se guardan localmente en la computadora del usuario para pruebas.

El sistema también permite almacenar y consultar nuevas prendas u outfits registrados.

Objetivo

Crear un asistente que combine visión por computadora, procesamiento de lenguaje natural (NLP) y razonamiento contextual, para ofrecer una experiencia de recomendación de ropa personalizada, simple y natural.