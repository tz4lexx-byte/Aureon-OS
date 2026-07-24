# Construcción reproducible

La definición de la preview fija la base bootc por digest y enumera sus
paquetes en [`desktop-profile.json`](../packaging/desktop-profile.json). El
lanzador registra digest OCI, manifiesto de conversión, hash SHA-256 del
`qcow2`, logs e inventario RPM por build ID. El contexto y el digest excluyen
con las mismas reglas los cachés locales `__pycache__`, `.pyc` y `.pyo`.

Una release no se declarará reproducible hasta repetir la compilación desde un
checkout limpio y comparar inventarios y manifiestos de dos ejecuciones
independientes. `python3 tools/aureonctl validate` comprueba los contratos
fuente y `python3 tools/aureonctl reproducibility` muestra los gates
pendientes. Ninguno descarga ni escribe artefactos.
