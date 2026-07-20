# Mapa de fases Aureon

El plan maestro se implementa en dos capas: fundamentos verificables en código
y validación de hardware/decisiones del usuario. `aureonctl status` expone el
estado de las fases 0–32 sin cambiar nada.

| Bloque | Fundamento entregado | Pendiente real |
| --- | --- | --- |
| 0–3 | Autoridad, recuperación, manifiestos, validación y baseline local. | Repetir builds limpios y medir en hardware. |
| 4–6 | Perfil KDE mínimo, tema, clases de servicios. | Ajustar tamaño/RAM tras medir una sesión real. |
| 7–10 | Política de recursos y clasificación de datos. | Aplicación cgroup/zram tras pruebas por hardware. |
| 11–14 | Diagnósticos locales y política de drivers. | Matriz AMD/Intel/NVIDIA, periféricos y pantallas. |
| 15–16 | Política de kernel y detección de `ntsync`. | Kernel/Proton medido en hardware. |
| 17–20 | Contratos de Gaming/Streaming y esquema de perfiles. | Runtimes, juegos, OBS y consentimientos reales. |
| 21–24 | Diagnóstico Integrity Basic y límites de seguridad. | Revisión formal antes de Competitive o módulo de kernel. |
| 25–28 | Planes de actualización, recuperación e instalador. | Cualquier escritura de disco, firmware o bootloader. |
| 29–32 | Protocolos de laboratorio, benchmark, UX y release. | Evidencia física y gates de lanzamiento. |

Los estados detallados y el enlace a la evidencia de cada fase viven en
[`packaging/aureon-control-plane.json`](../packaging/aureon-control-plane.json).
