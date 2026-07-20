# ADR-0001: Base del sistema inmutable

- Estado: propuesto (decisión provisional de Fase 0)
- Fecha: 2026-07-18
- Decisores: equipo de Aureon OS

## Contexto

Aureon OS necesita una base x86-64 UEFI que permita construir imágenes reproducibles, actualizar el sistema de forma transaccional, conservar una ruta de rollback y ejecutar una sesión de escritorio Linux moderna. La base no debe obligar al proyecto a mantener un kernel, controladores gráficos ni un gestor de paquetes propios durante las primeras fases.

Los criterios de esta decisión son, por orden de prioridad:

1. Actualización de la imagen del sistema y recuperación verificable.
2. Postura de seguridad razonable por defecto, incluidos MAC y firmas cuando la cadena de distribución esté preparada.
3. Mantenimiento viable de Wayland, KWin, Qt 6/QML, PipeWire, Flatpak y la pila Mesa necesaria para el hardware objetivo.
4. Construcción y prueba aisladas en contenedor y QEMU, sin tocar discos del host.
5. Coste de operación, documentación y compatibilidad con un proyecto pequeño.

Esta comparación describe propiedades de diseño y riesgos a investigar. No es un benchmark ni demuestra que una alternativa rinda mejor que otra.

## Opciones consideradas

| Base | Actualizaciones y rollback | Seguridad y mantenimiento | Escritorio y gaming | Riesgos para Aureon |
| --- | --- | --- | --- | --- |
| Fedora con bootc | Orientada a imágenes de sistema gestionadas como artefactos OCI; encaja directamente con una entrega transaccional. | Fedora integra SELinux de forma habitual y dispone de un ecosistema cercano a las tecnologías previstas. Requiere fijar versiones, registrar procedencia de imágenes y validar el flujo exacto de firma. | Es una ruta razonable para Mesa, Wayland, KWin, Qt y Flatpak, pero la disponibilidad de cada paquete y variante de imagen debe comprobarse en la composición real. | El flujo bootc y la composición de imágenes añaden conceptos operativos que el proyecto debe automatizar y probar. |
| openSUSE Aeon / base MicroOS de escritorio | Su modelo transaccional basado en instantáneas ofrece una alternativa madura para actualización y reversión. | Su enfoque de sistema inmutable es afín al objetivo; los mecanismos, políticas MAC y herramientas difieren de Fedora y necesitan diseño específico. | Puede ofrecer una base de escritorio actual, pero se debe validar la integración concreta de la pila gráfica, Flatpak y las dependencias de gaming elegidas. | Cambiaría las herramientas de composición, actualización y diagnóstico; no debe asumirse equivalencia con bootc. |
| Debian | Prioriza estabilidad de paquetes; una imagen atómica y rollback no son el flujo predeterminado y exigirían integrar mecanismos adicionales. | Tiene un ecosistema conservador y ampliamente documentado. La política MAC y la cadena de actualización deberían diseñarse explícitamente para el producto. | Puede alojar la pila prevista, aunque su cadencia estable puede no coincidir con las necesidades de controladores y gráficos recientes. | Mayor trabajo propio para obtener actualizaciones de imagen, rollback y versiones gráficas deseadas. |
| Arch Linux | Entrega paquetes recientes, pero una actualización de sistema atómica con rollback no es el camino base de `pacman`. | La rapidez de cambio traslada más validación y mantenimiento continuo al proyecto. | Es atractiva para experimentar con componentes recientes; esa ventaja no sustituye pruebas de integración y recuperación. | Riesgo de regresiones y de construir una capa de inmutabilidad y soporte operativo demasiado pronto. |
| NixOS | Las generaciones declarativas proporcionan una ruta de rollback y reproducibilidad de configuración distinta al modelo OCI. | La declaratividad es valiosa, pero introduce un modelo de empaquetado y operación propio que el equipo debe dominar. | Es posible integrar los componentes previstos, con decisiones específicas para binarios, Flatpak, controladores y distribución de artefactos. | Cambia de forma material el modelo de composición, depuración y soporte respecto de la arquitectura propuesta. |

## Decisión

Se adopta **Fedora con bootc** como base provisional de Fase 0. La primera implementación deberá partir de una imagen mínima, mantener SELinux en modo enforcing cuando la imagen lo soporte y producir artefactos OCI y de máquina virtual dentro del espacio de trabajo. La sesión de escritorio no forma parte del criterio de salida de esta fase inicial: el primer objetivo es llegar de forma verificable a una consola y a un target de systemd esperado en QEMU.

La decisión no selecciona todavía:

- El registro de distribución ni la política final de firmas.
- El instalador, la disposición de particiones o el cifrado de instalaciones físicas.
- La variante exacta de KWin, greeter o componentes de escritorio.
- El soporte final de NVIDIA ni resultados de rendimiento en AMD Radeon RX 6600.

## Consecuencias

### Positivas

- El modelo de imagen OCI se alinea con el pipeline de build, distribución, prueba y promoción entre perfiles.
- El sistema base puede tratarse como inmutable durante las pruebas y conservar un despliegue anterior para rollback.
- La elección conserva una ruta directa hacia SELinux, systemd, Flatpak, PipeWire, NetworkManager, BlueZ y la pila gráfica prevista, sin crear sustitutos propios.

### Costes y límites

- El equipo debe aprender y documentar la composición, transporte, actualización y depuración de imágenes bootc antes de prometer recuperación de usuario.
- Una imagen arrancable en QEMU no valida hardware físico, aceleración gráfica, consumo, compatibilidad de juegos ni Secure Boot.
- Las extensiones sobre la base deben reducirse al mínimo y mantenerse como capas declaradas; modificar una instalación de prueba a mano no será evidencia de reproducibilidad.
- Cada dependencia grande o cambio del mecanismo de actualización requiere su propio ADR y una prueba de rollback.

## Criterios de reevaluación

Esta ADR se revisará antes de cerrar Fase 0 y de nuevo antes de Fase 4. Una alternativa podrá sustituir a Fedora bootc solo con evidencia reproducible guardada en el repositorio o en artefactos de CI que incluya, como mínimo:

1. Construcción desde un checkout limpio con versiones y hashes registrados.
2. Arranque repetible en la VM de referencia, logs seriales y un smoke test automatizado.
3. Actualización intencionalmente fallida seguida de rollback a un estado arrancable, sin escribir en discos físicos.
4. Una postura de seguridad documentada equivalente o superior para MAC, procedencia de artefactos, actualización y separación de privilegios.
5. Un plan de mantenimiento para la pila Wayland/Qt/Mesa/Flatpak y sus parches.
6. Medidas comparables de tiempo de build, tamaño de imagen, tiempo de arranque y recursos en la misma configuración; las diferencias deben incluir método, repeticiones y límites de incertidumbre.

No basta una preferencia, una captura aislada ni un único benchmark. El cambio de base requiere actualizar esta ADR, explicar la migración y conservar una ruta de rollback del proceso de desarrollo.

## Estado de validación

Al crear esta ADR no se ha construido ni arrancado una imagen de Aureon OS. La decisión se validará mediante el pipeline de Fase 0 descrito en [phase-0-pipeline.md](../architecture/phase-0-pipeline.md).
