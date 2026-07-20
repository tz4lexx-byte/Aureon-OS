# Pruebas de Fase 0

## Contrato de `aureon-dev test-smoke`

El comando ya tiene un modo de planificación seguro por defecto y un runner de
ejecución explícita (`--execute`). El runner solo se inicia desde Linux/WSL con
root; no intenta elevar Windows ni invocar WSL automáticamente. La primera
repetición real mediante este runner sigue pendiente de evidencia nueva.

El comando final deberá:

1. Validar que todas las rutas de salida se encuentran dentro del repositorio.
2. Construir una imagen OCI reproducible.
3. Convertirla a un `qcow2` bajo `images/`.
4. Crear un snapshot virtual de prueba, nunca un disco físico.
5. Arrancar QEMU con OVMF y una consola serial redirigida a archivo.
6. Esperar el target de systemd acordado o un agente de prueba.
7. Registrar ID de build, hash, acelerador, tiempo de arranque, resultado y rutas de logs.
8. Solicitar apagado limpio y comprobar que QEMU salió.

## Casos de fallo obligatorios

- Herramienta requerida ausente: fallo descriptivo y sin artefactos fuera de `build/` o `images/`.
- Ruta de imagen fuera del repositorio: rechazo antes de invocar herramientas externas.
- Timeout de arranque: guardar logs, finalizar solo el proceso hijo de QEMU y conservar el disco virtual.
- Smoke test fallido: marcar la ejecución fallida sin borrar evidencia.

## Estado de verificación

La cadena se ejecutó manualmente una vez con `phase0-f44-20260718`: produjo
una OCI derivada, un `qcow2`, un overlay, `AUREON_PHASE0_READY` y apagado
limpio. El nuevo runner y sus validaciones de rutas, logs, serial y apagado
tienen pruebas unitarias, pero aún no se ha ejecutado una segunda vez mediante
`test-smoke --execute` desde el WSL propietario. Esa repetición es necesaria
antes de declarar reproducibilidad.

La verificación del CLI y sus límites actuales se registra en [verification-2026-07-18.md](verification-2026-07-18.md).
