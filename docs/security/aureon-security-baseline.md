# Base de seguridad

La preview mantiene una imagen bootc inmutable, SELinux cuando la plataforma lo
provee, QEMU sin red y sin carpetas compartidas. `aureonctl integrity doctor`
solo revisa estado local de Secure Boot, SELinux y `ntsync`; no enumera
documentos, conversaciones, pulsaciones, capturas, micrófono, cámara ni la
lista general de procesos.

Secure Boot, TPM, cifrado, enrolamiento de claves y módulos firmados requieren
hardware físico y confirmación de nivel C. Ninguna de esas operaciones forma
parte del launcher de la preview.
