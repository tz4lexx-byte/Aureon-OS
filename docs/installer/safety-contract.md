# Contrato de seguridad del instalador

No existe instalador ejecutable en esta preview. `aureonctl installer plan`
siempre devuelve `manual-only` y no acepta una unidad como argumento.

Un instalador futuro deberá mostrar la unidad de forma visual, simular el plan,
requerir confirmación del particionado y del bootloader, y permitir conservar
el cargador existente. Nunca podrá reducir una partición, formatear, cambiar el
orden de arranque o enrolar claves de firmware automáticamente.
