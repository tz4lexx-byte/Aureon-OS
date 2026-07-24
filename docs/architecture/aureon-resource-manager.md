# Aureon Resource Manager

`aureon-resourced` se define primero como una política, no como un programa
que fuerce prioridades. La representación inicial es `aureonctl resource
plan`: muestra el plan local sin modificar cgroups.

## Clases

| Clase | Ejemplos | Regla |
| --- | --- | --- |
| Crítica | input, PipeWire, KWin | No se limita como trabajo de fondo. |
| Interactiva | aplicación visible, juego | Recibe prioridad proporcional, no máxima permanente. |
| Normal | aplicaciones secundarias | Comparte los recursos disponibles. |
| Diferible | índices, actualizaciones, limpieza, copias | Se pospone bajo presión o durante una sesión elegida. |

Cuando se habilite la aplicación real, requerirá cgroup v2, un ámbito de
sesión creado por systemd y un registro local de la política. No podrá cerrar
documentos, matar aplicaciones interactivas, alterar voltajes o conservar
límites al terminar la sesión.

## Memoria e I/O

La política futura observa PSI y disponibilidad de memoria antes de reaccionar.
Multi-Gen LRU, zram y límites suaves son decisiones por perfil y hardware; no
se activan ni se publican como resultados sin prueba física. La limpieza solo
puede actuar sobre categorías `REGENERABLE` y `TEMPORAL` definidas en
[`data-classes.json`](../../packaging/data-classes.json).
