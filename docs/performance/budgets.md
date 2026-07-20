# Presupuestos de rendimiento

## Entorno de referencia planificado

- VM x86-64 UEFI.
- 4 vCPU y 8 GB RAM.
- `virtio-gpu` cuando esté disponible; renderizado por software solo para pruebas funcionales.
- Cinco minutos de sesión estabilizada para métricas de reposo.

## Metas por fase

| Métrica | Fase funcional | Beta | Objetivo estable |
| --- | ---: | ---: | ---: |
| PSS total de escritorio | <= 1.2 GB | <= 900 MB | <= 700 MB |
| CPU idle promedio | < 1 % | < 1 % | < 1 % |
| Arranque a login (VM) | < 15 s | Medir | Medir |
| Arranque a escritorio (VM) | < 20 s | Medir | Medir |

Estas son metas, no resultados. Las mediciones deberán identificar método, muestras, dispersión y restricciones del acelerador de virtualización.

## Guardrails

No se aceptan reducciones de seguridad, accesibilidad o estabilidad para alcanzar una cifra aislada. Cualquier regresión superior al 3 % requiere una explicación y decisión documentada.
