# Compatibilidad con aplicaciones Windows

Aureon utiliza componentes existentes —Wine, Proton, DXVK, VKD3D-Proton y las
interfaces del kernel disponibles— en lugar de reimplementar Windows.

`aureonctl driver doctor` detecta de forma local si existe `/dev/ntsync`, pero
no carga módulos, instala kernels ni afirma compatibilidad de un juego. Cada
perfil de juego se describe con el esquema
[`game-profile.schema.json`](../../packaging/game-profile.schema.json), debe
ser reversible y no puede introducir DLL externas o mods sin confirmación.

Los modos Standard, Competitive y Development son políticas diferentes. La
preview solo ofrece el contrato y el diagnóstico; las pruebas de Proton y
anticheat requieren hardware, drivers y juegos reales.
