# Packaging

Esta carpeta fija la declaración de la imagen bootc de Fase 0, el almacenamiento Podman dedicado y la configuración sin red para el builder anidado. Las referencias de Fedora bootc e Image Builder están fijadas por digest y la cadena manual ya produjo un `qcow2` válido.

El runner `test-smoke --execute` verifica las mismas entradas antes de usarlas y monta únicamente el store dedicado y el directorio `images/<build-id>/` en el conversor. No usa el store global, dispositivos físicos ni red de guest.
