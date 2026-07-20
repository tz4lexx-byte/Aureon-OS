# Manejo de secretos y material de firma

`.gitignore` reduce errores accidentales, pero no es un control de seguridad suficiente. Los secretos deben mantenerse fuera del checkout y nunca entregarse al guest de prueba ni a logs de CI.

## Reglas

- Claves privadas, tokens, contraseñas, almacenes PKCS y archivos `.env` locales no se versionan.
- Las firmas y certificados públicos no se ignoran globalmente: pueden versionarse solo después de revisar su procedencia, finalidad y licencia.
- Antes de abrir un remoto o aceptar contribuciones, CI debe ejecutar un escáner de secretos sobre cambios y sobre la historia según la política que se adopte.
- Un SBOM, manifiesto o log no debe incluir valores de entorno sensibles ni rutas personales sin necesidad.
- La generación, custodia y rotación de claves de firma requieren un ADR propio antes de Fase 4.

## Respuesta ante exposición

1. Detener la distribución del artefacto afectado.
2. Revocar o rotar la credencial fuera del repositorio.
3. Preservar evidencia mínima sin volver a publicar el secreto.
4. Registrar causa y prevención, sin convertir el incidente en un ejemplo que exponga datos.
