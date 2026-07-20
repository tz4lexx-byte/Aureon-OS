# Benchmarks

## Estado

No hay mediciones registradas todavía.

## Metodología mínima para Fase 0

- Registrar host, versión de QEMU, acelerador, firmware OVMF, vCPU, RAM y GPU virtual.
- Repetir arranque al menos cinco veces después de un calentamiento razonable.
- Conservar consola serial, `systemd-analyze`, hash de imagen y comandos exactos.
- Distinguir memoria PSS, RSS, caché de página y memoria compartida; no usar una cifra ambigua de «RAM usada».
- No comparar resultados de TCG, WHPX y KVM como si fueran equivalentes.

Los presupuestos objetivos se describen en [docs/performance/budgets.md](docs/performance/budgets.md). Ninguna meta se considera cumplida sin datos crudos y un procedimiento de repetición.
