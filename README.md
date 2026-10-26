# Sé el inversionista

Dinámica del PIA (Equipo 6, Bonos catastróficos). El público vota desde el celular y la pantalla muestra en vivo qué le pasó a cada quien en 4 años.

## Dos modos (se eligen en la pantalla, en Controles)

- **Stand (por defecto): cada quien a su ritmo.** Cada visitante juega sus 4 años en su propio celular. La pantalla va sumando a todos.
- **Salón: todos a la vez.** Todos votan, se cierra la votación y el presentador avanza los años con un botón.

Cambiar de modo borra los votos.

## Links

- Celular: `https://equipo6-catbonds.streamlit.app` (es el link del QR)
- Pantalla (proyector): `https://equipo6-catbonds.streamlit.app/?vista=pantalla&clave=CLAVE`

Antes de la expo cambien la `CLAVE` en `app.py`.

## Supuestos (los mismos del Excel; bono vigente de México 2024, clase B de sismo)

| | Valor |
|---|---|
| Inversión | $10,000 dólares |
| Probabilidad anual de sismo (p) | 5.84% |
| Severidad (s) | 100% |
| Tasa libre de riesgo / bono normal (r_f) | 5.24% (T-bill de EE.UU. a 3 meses, abril 2024; FRED TB3MS) |
| Múltiplo de riesgo (m) | 1.88 (margen 11% / 5.84%) |
| Cupón del cat bond | r_f + p × s × m = 16.2% |
| Pagos del cupón | Trimestrales (opción: anuales) |
| Sismo fuerte que no dispara (solo para el mapa) | 30% por año, ilustrativo |
| Magnitud mínima para dispararse | Costa del Pacífico 7.8 (Artemis, Oaxaca 2018); centro 7.4 (ilustrativo) |

Se cambian en la pantalla, en "Supuestos". Muévanlos **antes** de empezar, porque el cupón depende de p. Si se cambia el código, den **Reboot app** para que tome los valores nuevos.

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
