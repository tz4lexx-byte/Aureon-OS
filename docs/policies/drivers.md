# Política de controladores

Aureon elige automáticamente únicamente entre controladores ya instalados,
firmados y cuya coincidencia de hardware sea inequívoca. Instalar software
propietario, cambiar canal, degradar una versión o reiniciar requiere
confirmación.

Cada controlador futuro debe tener manifiesto de hardware, rango de kernel,
firmware, componentes 64/32 bits, Secure Boot, problemas conocidos, pruebas,
rollback y canal. La estructura se define en
[`driver-policy.json`](../../packaging/driver-policy.json).
