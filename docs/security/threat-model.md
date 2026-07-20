# Modelo inicial de amenazas

## Activos a proteger

- Integridad de la imagen de sistema y de sus actualizaciones.
- Datos del usuario, configuraciones y diagnósticos.
- Claves de firma que se incorporarán en una fase posterior.
- Disponibilidad de la máquina tras actualización, fallo de energía o un componente defectuoso.

## Límites de confianza iniciales

1. El host Windows es externo al sistema invitado y no debe modificarse.
2. QEMU y el archivo `qcow2` son un entorno de prueba aislado, no un destino de instalación.
3. El registro de contenedores y dependencias remotas no se consideran confiables sin verificación de referencia, digest o firma.
4. Los logs pueden contener información sensible y se revisan antes de compartirlos.

## Amenazas prioritarias de Fase 0

| Amenaza | Riesgo | Control inicial |
| --- | --- | --- |
| Error de destino de escritura | Daño al host | Rutas de imagen permitidas, rechazo de dispositivos físicos y revisión antes de operaciones de escritura. |
| Imagen o dependencia manipulada | Compromiso de build | Pines de versión/digest antes de un build reproducible; verificación documentada. |
| Imagen que no arranca | Pérdida de tiempo o falsa evidencia | Consola serial, timeout, logs conservados y prueba automatizada. |
| Regresión no detectada | Degradación de calidad | Baselines y repetición estadística antes de bloquear CI. |
| Exposición de secretos | Compromiso de cuentas | Revisión, prohibición de claves/tokens, reglas de ignore específicas y escaneo de secretos obligatorio en CI antes de abrir contribuciones externas. |

## Decisiones aún pendientes

- Política de firma, rotación y custodia de claves.
- Registro OCI y controles de acceso.
- Política de vulnerabilidades y retención de diagnósticos.
- Alcance exacto de Secure Boot y TPM.
