# Aureon Liquid Glass

Aureon Liquid Glass ya tiene una primera implementación vectorial para la
preview Plasma. No replica recursos ni medidas de otro sistema: usa una paleta
propia azul-violeta, un wallpaper SVG local, superficies translúcidas y las
capacidades existentes de contraste/blur de KWin.

## Aplicación inicial

El perfil predeterminado es **Balanced**:

- tema Plasma `AureonLiquidGlass`;
- esquema de color `AureonLiquidGlass`;
- panel inferior flotante y translúcido;
- blur y contraste habilitados por KWin cuando el hardware los admite;
- wallpaper SVG propio aplicado una sola vez al usuario desechable `aureon`.

El helper de inicio no descarga nada, no toca Windows y no vuelve a imponer el
wallpaper después de la primera aplicación. El usuario puede cambiar tema,
contraste, transparencia o wallpaper desde Plasma sin que Aureon lo restaure.

## Perfiles

| Perfil | Uso |
| --- | --- |
| Glass Off | Máxima legibilidad y menor coste visual. |
| Lite | Transparencia y blur discretos. |
| Balanced | Predeterminado con contraste protegido. |
| Ultra | No se activa automáticamente; necesita medición de fluidez en hardware real. |

`aureonctl appearance plan --profile balanced` describe un perfil sin aplicarlo.
La definición canónica está en
[`packaging/appearance-profiles.json`](../../packaging/appearance-profiles.json).

## Accesibilidad y degradación

La transparencia no es un requisito de legibilidad. Temas de alto contraste,
reducir movimiento y reducir transparencia siempre conservan la elección del
usuario. En hardware limitado se reduce blur, transparencia y decoración antes
de sacrificar interacción, input o audio.
