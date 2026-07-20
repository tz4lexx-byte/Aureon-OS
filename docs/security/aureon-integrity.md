# Aureon Integrity

Integrity Basic es un diagnóstico local y sin transmisión. Sus resultados
permitidos son `PASS`, `FAIL`, `UNAVAILABLE` y `DEVELOPMENT_MODE`; una futura
implementación deberá explicar cada resultado y su evidencia mínima.

Integrity Competitive no se implementa en esta preview. Antes de hacerlo se
necesita una revisión que pruebe que LSM, eBPF, SELinux, TPM, servicio de
usuario y validación de servidor no son suficientes. Un módulo de kernel no se
creará por conveniencia.

Si llega a existir, será opt-in por juego, temporal, abierto, descargable al
cerrar la sesión y no podrá leer datos personales. La exportación de cualquier
resultado sigue siendo nivel D.
