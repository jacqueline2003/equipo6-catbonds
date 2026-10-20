# Sé el inversionista

Dinámica del PIA (Equipo 6, Bonos catastróficos). El público vota desde el celular y la pantalla muestra en vivo qué le pasó a cada quien en 4 años.

## Dos modos (se eligen en la pantalla, en Controles)

- **Salón: todos a la vez.** Todos votan, se cierra la votación y el presentador avanza los años con un botón.
- **Stand: llegan de a pocos.** Cada visitante juega sus 4 años en su propio celular. La pantalla va sumando a todos los que pasan en el día.

Cambiar de modo borra los votos.

## Links

- Celular: `https://TU-APP.streamlit.app` (es el link del QR)
- Pantalla (proyector): `https://TU-APP.streamlit.app/?vista=pantalla&clave=equipo6`

Antes de la expo cambien la `CLAVE` en `app.py`.

## Supuestos (los mismos de la pestaña 3 del Excel)

| | Valor |
|---|---|
| Inversión | $10,000 |
| Probabilidad anual de sismo (p) | 3.43% |
| Severidad (s) | 100% |
| Tasa del bono normal (r_f) | 4% |
| Múltiplo de riesgo (m) | 1.31 |
| Cupón del cat bond | r_f + p × s × m = 8.49% |

Se cambian en la pantalla, en "Supuestos". Muévanlos **antes** de abrir la votación, porque el cupón depende de p.

## Correrla en tu compu

```
pip install -r requirements.txt
streamlit run app.py
```

## Subirla (gratis)

1. Sube esta carpeta a un repo público de GitHub.
2. Entra a share.streamlit.io con tu cuenta de GitHub → Create app → elige el repo y `app.py`.
3. En "App URL" ponle un nombre, por ejemplo `equipo6-catbonds`.

La app se duerme si nadie la usa en varios días. Ábrela unos minutos antes de exponer.
