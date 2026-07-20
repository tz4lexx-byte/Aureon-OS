# Construcción reproducible

La definición de la preview fija la base bootc por digest y enumera sus
paquetes en [`desktop-profile.json`](../packaging/desktop-profile.json). El
lanzador registra digest OCI, manifiesto de conversión, hash SHA-256 del qcow2
y logs por build ID.

Una release no se declarará reproducible hasta fijar también la resolución de
RPM usada, repetir la compilación desde checkout limpio y comparar manifiestos.
`python3 tools/aureonctl validate` comprueba que los contratos fuente y la base
por digest sigan presentes; no descarga ni escribe artefactos.
