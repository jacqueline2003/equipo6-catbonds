# Sé el inversionista

App que hice para la dinámica de nuestro PIA de Productos Financieros Derivados (FCFM UANL), Equipo 6: *Bonos catastróficos: cuando un sismo es una inversión*.

Cada persona recibe $10,000 dólares (de mentira) y decide si los invierte en un bono normal o en un cat bond de México. Después ve qué le pasa a su dinero en 4 años: si tembló, dónde y si el sismo fue suficiente para disparar el bono. En la pantalla se van juntando los resultados de todos.

## Links

- Juego (es el link del QR): https://equipo6-catbonds.streamlit.app
- Guía rápida / tríptico digital: https://equipo6-catbonds.streamlit.app/?vista=info
- Pantalla para proyectar: `?vista=pantalla` (pide clave)

Tiene dos modos: **stand**, donde cada quien juega a su ritmo y la pantalla va sumando (es el que usamos en el pozo), y **salón**, donde todos votan y los años se avanzan al mismo tiempo.

## De dónde salen los números

Tomé como base el bono vigente de México, emitido en 2024 con el Banco Mundial (clase B, sismo).

| | Valor |
|---|---|
| Inversión | $10,000 dólares |
| Probabilidad anual de que se dispare (p) | 5.84% (pérdida esperada del bono, Artemis) |
| Severidad (s) | 100%, simplificación: si se dispara se pierde todo |
| Tasa libre de riesgo / bono normal (r_f) | 5.24% (T-bill de EE.UU. a 3 meses, abril 2024, FRED TB3MS) |
| Margen por riesgo | 11%, así que m = 0.11 / 0.0584 ≈ 1.88 |
| Cupón del cat bond | r_f + p × s × m = 16.2% |
| Pago del cupón | Trimestral, como el bono real (también se puede poner anual) |
| Magnitud mínima para dispararse | Costa del Pacífico 7.8 (Artemis, Oaxaca 2018); centro 7.4 (ilustrativo) |
| Sismos fuertes que no disparan | 30% por año, solo para mostrarlos en el mapa (ilustrativo) |

Los supuestos se pueden cambiar desde la pantalla, en "Supuestos".

## Cómo está hecha

- Python con Streamlit, publicada en Streamlit Community Cloud.
- Cada persona tiene su propio sorteo aleatorio con semilla, así que si recarga la página le sale lo mismo.
- Probabilidad de que se dispare en 4 años: 1 − (1 − p)⁴ ≈ 21%.
- El valor esperado de cada bono lo calculo recorriendo todos los casos posibles (sin sismo o con sismo en alguno de los 4 trimestres de cada año).
- El mapa de México es un SVG que dibujo a partir de un GeoJSON de dominio público.

## Correrla localmente

```
pip install -r requirements.txt
streamlit run app.py
```
