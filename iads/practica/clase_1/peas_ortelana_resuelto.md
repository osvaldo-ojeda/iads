Anclaje al Caso: El Desafío Operativo de Ortelana Textil

Como objeto de estudio práctico, la materia utiliza a Ortelana Textil, una firma tradicional de fabricación y distribución de indumentaria al por mayor que se encuentra en un complejo proceso de digitalización postpandemia. El aumento explosivo de canales como e-commerce y WhatsApp ha generado severas fricciones operativas.

El problema central de esta semana radica en el subsistema de Onboarding y Validación de Clientes Mayoristas. Los nuevos distribuidores envían documentación fiscal, capturas de pantalla, datos de inscripción y consultas en texto libre totalmente desestructuradas. El equipo de administración gasta la mayor parte de su jornada transcribiendo datos manualmente hacia un sistema de gestión antiguo (backend rígido e inflexible) y validando si califican para compras a gran escala según las complejas normativas internas vigentes de la empresa.


Ejercicio de Taller: Modelado PEAS para Ortelana Textil

Los alumnos, organizados en equipos de arquitectura, deben estructurar el PEAS del agente de Onboarding automatizado para Ortelana Textil.


Resolución Esperada del Modelado

Entorno

Sistema de gestión/ERP legado (REST API rígida), servidores de correo corporativo IMAP, normativas internas de calidad de hilados y políticas comerciales en formato PDF dispersas en Drive.

Sensores

Correos entrantes de distribuidores, archivos adjuntos de inscripción (PDF/PNG), mensajes entrantes de la API de WhatsApp, peticiones HTTP del formulario web.

Base de Conocimiento

Historial de cuentas corrientes en base de datos SQL corporativa, base vectorial local (FAISS/Chroma a futuro) con el compendio completo de reglamentos comerciales y fiscales de la empresa.

Actuadores

Peticiones HTTP mutables al ERP legado para dar de alta registros, despacho automático de alertas de aprobación/rechazo vía mail, generación de JSON estructurado estrictamente validado para interoperabilidad.

Objetivo

Reducir el tiempo de procesamiento y alta de cuentas mayoristas de días a minutos, manteniendo una tasa de falsos positivos en validación normativa menor al 2% y mitigando el riesgo financiero.


