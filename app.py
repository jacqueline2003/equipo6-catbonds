"""
Sé el inversionista - dinámica del PIA, Equipo 6
Productos Financieros Derivados, FCFM UANL

Modos (se eligen en la pantalla):
  salón -> todos votan, se cierra la votación y el presentador avanza los años
  stand -> cada visitante juega sus 4 años en su celular; la pantalla acumula a todos

Vistas:
  celular  ->  https://TU-APP.streamlit.app
  pantalla ->  https://TU-APP.streamlit.app/?vista=pantalla&clave=CLAVE
"""
import io
import random
import threading
import uuid

import qrcode
import streamlit as st

CLAVE = "equipo6"  # cámbienla antes de la expo

# Valores por defecto (los mismos del Excel, pestaña 3)
DEFAULTS = {
    "inversion": 10_000,
    "tasa_normal": 0.04,   # supuesto del equipo
    "p": 0.0584,           # pérdida esperada anual, bono vigente 2024 clase B (se supone s = 100%)
    "severidad": 1.0,
    "m": 0.11 / 0.0584,    # margen 11% / pérdida esperada 5.84% ≈ 1.88 (bono 2024 clase B)
    "trimestral": True,    # cupón por trimestre (como el bono real) o una vez al año
}
ANIOS = 4

st.set_page_config(page_title="Sé el inversionista", page_icon="🌎", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap');
html, body, [class*="css"], .stMarkdown, p, li, label { font-family: 'Source Sans 3', sans-serif; }
h1, h2, h3, .big { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }
#MainMenu, footer { visibility: hidden; }
.block-container { padding-top: 1.6rem; }
.tag { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.8rem; font-weight:600; }
.tag-cat { background:#C8553D; color:#fff; }
.tag-normal { background:#2E5E8C; color:#fff; }
.card { background:#fff; border:1px solid #E2DACD; border-radius:14px; padding:14px 16px; margin-bottom:10px; }
.anio { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #EEE7DC; }
.anio:last-child { border-bottom:none; }
.ok { color:#2F7D4F; font-weight:600; }
table.flujo { width:100%; border-collapse:collapse; font-size:0.92rem; border:none !important; margin:0 !important; }
table.flujo tr, table.flujo td, table.flujo th { border-left:none !important; border-right:none !important; border-top:none !important; background:transparent !important; }
table.flujo th { text-align:left; font-weight:600; color:#5B6672; font-size:0.78rem; text-transform:uppercase; letter-spacing:0.03em; padding:6px 4px; border-bottom:1px solid #E2DACD; }
table.flujo td { padding:8px 4px; border-bottom:1px solid #EEE7DC; vertical-align:top; }
table.flujo td.n, table.flujo th.n { text-align:right; white-space:nowrap; }
.desglose div { display:flex; justify-content:space-between; padding:4px 0; }
.desglose .tot { border-top:1px solid #E2DACD; margin-top:4px; padding-top:8px; font-weight:700; }
.mal { color:#B23A2B; font-weight:700; }
.persona { border-radius:10px; padding:8px 10px; font-weight:600; font-size:0.95rem; color:#fff; text-align:center;
           overflow:hidden; white-space:nowrap; text-overflow:ellipsis; }
.rejilla { display:grid; grid-template-columns:repeat(auto-fill, minmax(150px, 1fr)); gap:8px; }
@media (max-width: 640px) { .rejilla { grid-template-columns:repeat(3, 1fr); gap:6px; } .persona { font-size:0.8rem; padding:6px 4px; } }
.p-jugando { background:#9AA3AC; } .p-cat { background:#3C8D5A; } .p-hit { background:#B23A2B; } .p-normal { background:#2E5E8C; } .p-normal-sismo { background:#2E5E8C; box-shadow: inset 0 0 0 3px #E8A33D; }
.metric { font-family:'Space Grotesk',sans-serif; font-size:2.6rem; margin:2px 0 8px; font-weight:700; line-height:1.1; }
.label { font-size:0.85rem; margin-bottom:2px; color:#5B6672; text-transform:uppercase; letter-spacing:0.04em; }
.grande { font-family:'Space Grotesk',sans-serif; font-size:3rem; font-weight:700; line-height:1.05; margin:4px 0 6px; }
.big { font-family:'Space Grotesk',sans-serif; font-weight:700; }
</style>
""", unsafe_allow_html=True)


# ---------- estado compartido entre todos los celulares y la pantalla ----------
@st.cache_resource
def estado():
    return {
        "lock": threading.Lock(),
        "votos": {},            # id -> {"nombre": str, "eleccion": "cat" | "normal"}
        "modo": "salon",        # salon (todos a la vez) | stand (llegan de a pocos)
        "fase": "votacion",     # votacion | sorteo (solo modo salón)
        "anio": 0,              # último año revelado (0 a 4)
        "semilla": random.randint(1, 10**9),
        "params": dict(DEFAULTS),
    }

E = estado()
# Si la app se actualiza sin reiniciarse, el estado viejo puede no tener los datos nuevos:
for _k, _v in DEFAULTS.items():
    E["params"].setdefault(_k, _v)
E.setdefault("modo", "salon")


def cupon_cat():
    """Cupón justo = r_f + p x s x m (igual que la pestaña 3 del Excel)."""
    pr = E["params"]
    return pr["tasa_normal"] + pr["p"] * pr["severidad"] * pr["m"]


def dinero(x):
    return f"${x:,.0f}"


def sismos_de(pid):
    """Sorteo fijo por persona: no cambia aunque entren más votos."""
    rng = random.Random(f"{E['semilla']}|{pid}")
    res = []
    for _ in range(ANIOS):
        hay = rng.random() < E["params"]["p"]
        trimestre = 1 + int(rng.random() * 4)
        res.append(trimestre if hay else 0)   # 0 = sin sismo; 1 a 4 = trimestre del sismo
    return res


def flujos(eleccion, sismos):
    """Año por año. sismos[a] = 0 si no tembló, o el trimestre (1 a 4) del sismo.
    Trimestral: el año del sismo se cobran los trimestres anteriores al sismo.
    Anual: el cupón se paga al final del año, así que el año del sismo ya no se cobra."""
    pr = E["params"]
    inv = pr["inversion"]
    principal = inv
    filas = []
    for a in range(ANIOS):
        if eleccion == "normal":
            cupon, perdido = inv * pr["tasa_normal"], 0.0
        else:
            vivo = principal > 0
            antes = principal
            perdido = min(principal, pr["severidad"] * inv) if sismos[a] else 0.0
            principal -= perdido
            frac = (sismos[a] - 1) / 4 if (sismos[a] and pr["trimestral"]) else 0.0
            cupon = cupon_cat() * (antes * frac + principal * (1 - frac))
        disparo = eleccion == "cat" and sismos[a] and vivo
        filas.append({"anio": a + 1, "sismo": disparo, "evento": bool(sismos[a]), "trimestre": sismos[a],
                      "cupon": cupon, "perdido": perdido, "principal": principal})
    return filas


def total_recibido(filas):
    return sum(f["cupon"] for f in filas) + filas[-1]["principal"]


def esperado(eleccion):
    """Lo que se recibe en promedio: recorre todos los caminos posibles de 4 años
    (cada año: sin sismo, o sismo en el trimestre 1, 2, 3 o 4)."""
    import itertools
    p = E["params"]["p"]
    tot = 0.0
    for sismos in itertools.product(range(5), repeat=ANIOS):
        prob = 1.0
        for x in sismos:
            prob *= (p / 4) if x else (1 - p)
        tot += prob * total_recibido(flujos(eleccion, list(sismos)))
    return tot


def comparar_html(hits, n, teoria, hits_cat=None, hits_normal=None):
    """Recuadro: cuántos tuvieron sismo en este grupo contra lo esperado, con dos barras."""
    real = hits / n if n else 0
    def barra(etiqueta, valor, color, texto):
        return (f"<div style='margin:6px 0'><div style='display:flex;justify-content:space-between;font-size:0.9rem'>"
                f"<span>{etiqueta}</span><b>{texto}</b></div>"
                f"<div style='background:#EEE7DC;border-radius:6px;height:12px;margin-top:3px'>"
                f"<div style='width:{min(valor, 1) * 100:.0f}%;background:{color};height:12px;border-radius:6px'></div></div></div>")
    return ("<div class='card'><b>¿A cuántos les tocó sismo en sus 4 años? (contando a todos)</b>"
            + barra(f"En este grupo ({hits} de {n})", real, "#B23A2B", f"{real:.0%}")
            + barra(f"Lo esperado (como {teoria * n:.0f} de {n})", teoria, "#9AA3AC", f"{teoria:.0%}")
            + (f"<div style='display:flex;gap:16px;flex-wrap:wrap;margin-top:8px;font-size:0.9rem'>"
               f"<span><span class='tag' style='background:#B23A2B;color:#fff'>{hits_cat}</span> "
               f"{'tenía cat bond: lo perdió' if hits_cat == 1 else 'tenían cat bond: lo perdieron'}</span>"
               f"<span><span class='tag tag-normal'>{hits_normal}</span> "
               f"{'tenía bono normal: no le afectó' if hits_normal == 1 else 'tenían bono normal: no les afectó'}</span></div>"
               if hits_cat is not None else "")
            + f"<p style='margin:8px 0 0;font-size:0.85rem;color:#5B6672'>{teoria:.0%} = probabilidad de que tiemble al menos una vez en {ANIOS} años. "
              f"Contamos a todos porque el sismo no depende del bono que elegiste. "
              f"Con más gente, el grupo se acerca al {teoria:.0%}.</p></div>")


def regla_cupon():
    if E["params"]["trimestral"]:
        return "El cupón se paga cada trimestre: el año del sismo solo cobras los trimestres antes del sismo."
    return "El cupón se paga al final de cada año, solo si el bono sigue vivo: el año del sismo ya no se cobra."


def prob_4_anios():
    return 1 - (1 - E["params"]["p"]) ** ANIOS


def qr_png(url):
    img = qrcode.make(url, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def url_base():
    try:
        u = st.context.url
        return u.split("?")[0].rstrip("/")
    except Exception:
        return "https://TU-APP.streamlit.app"


# ============================== VISTA CELULAR ==============================
def vista_celular():
    qp = st.query_params
    if "id" not in qp:
        qp["id"] = uuid.uuid4().hex[:10]
    pid = qp["id"]

    st.markdown("<div class='label'>PIA · Equipo 6 · Bonos catastróficos</div>", unsafe_allow_html=True)
    st.markdown("## Sé el inversionista")

    stand = E["modo"] == "stand"
    if pid not in E["votos"]:
        if not stand and E["fase"] != "votacion":
            st.info("La votación ya cerró. Sigue los resultados en la pantalla.")
            return
        pr = E["params"]
        st.write(f"Tienes **{dinero(pr['inversion'])}** para invertir durante {ANIOS} años. ¿Dónde los pones?")
        c1, c2 = st.columns(2)
        inv = pr["inversion"]
        c = cupon_cat()
        with c1:
            st.markdown(f"""<div class='card'><span class='tag tag-cat'>Cat bond</span>
            <div class='big' style='font-size:1.8rem;margin:8px 0 6px'>{c:.1%} anual</div>
            <div class='anio'><span>Si no tiembla en {ANIOS} años</span><b>recibes {dinero(inv * (1 + ANIOS * c))}</b></div>
            <div class='anio'><span>Probabilidad de que tiemble en {ANIOS} años</span><b>{prob_4_anios():.0%}</b></div>
            <div class='anio'><span>Si tiembla</span><b class='mal'>pierdes tus {dinero(inv)}</b></div>
            <p style='margin:6px 0 0;font-size:0.85rem;color:#5B6672'>Si tiembla te quedas con los cupones que ya cobraste, pero ya no te regresan tu dinero y dejas de cobrar.</p></div>""",
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='card'><span class='tag tag-normal'>Bono normal</span>
            <div class='big' style='font-size:1.8rem;margin:8px 0 6px'>{pr['tasa_normal']:.1%} anual</div>
            <div class='anio'><span>Pase lo que pase</span><b>recibes {dinero(inv * (1 + ANIOS * pr['tasa_normal']))}</b></div>
            <div class='anio'><span>Riesgo de perder tu dinero</span><b>ninguno</b></div>
            <p style='margin:6px 0 0;font-size:0.85rem;color:#5B6672'>Cobras tus intereses cada año y al final te regresan tus {dinero(inv)}.</p></div>""",
                        unsafe_allow_html=True)
        with st.expander("Ficha del bono: datos para decidir"):
            st.markdown(f"""
| Dato | Valor |
|---|---|
| Emisor | Gobierno federal de México, con el Banco Mundial |
| Bono | El vigente: emitido en 2024, vence en 2028 (clase B, sismo) |
| Qué lo dispara | Un sismo muy fuerte en las zonas del contrato, sobre todo el sur y la costa del Pacífico. Cada zona tiene su magnitud mínima |
| Probabilidad de sismo por año | {pr['p']:.2%} |
| Probabilidad de que se dispare en {ANIOS} años | {prob_4_anios():.1%} |
| Si se dispara | Pierdes el {pr['severidad']:.0%} de lo invertido y dejas de cobrar |
| Cupón | {c:.1%} anual = {pr['tasa_normal']:.0%} (tasa libre de riesgo) + {c - pr['tasa_normal']:.1%} (pago por el riesgo) |
| Cuándo se cobra el cupón | {regla_cupon()} |
| Lo que recibirías en promedio | Cat bond {dinero(esperado('cat')).replace('$', chr(92) + '$')} · Bono normal {dinero(esperado('normal')).replace('$', chr(92) + '$')} |
""")
            st.caption(("Como en el bono real, el cupón se paga cada 3 meses. " if pr["trimestral"] else
                        "Simplificación: aquí el cupón se paga una vez al año; en el bono real se paga cada 3 meses y cobras hasta el trimestre del sismo. ") +
                       "Suponemos que si se dispara se pierde todo; el bono real puede pagar por partes. "
                       "Así ya pasó en 2017: el sismo de Chiapas (8.1) activó el bono de entonces y México cobró 150 millones de dólares. "
                       "Fuentes: Banco Mundial y Artemis (abril 2024).")
        with st.form("voto"):
            nombre = st.text_input("Tu nombre", max_chars=18, placeholder="Ej. Ana")
            eleccion = st.radio("Mi elección", ["Cat bond", "Bono normal"], horizontal=True, index=None)
            if st.form_submit_button("Invertir", type="primary", use_container_width=True):
                if not nombre.strip() or eleccion is None:
                    st.warning("Escribe tu nombre y elige un bono.")
                elif not stand and E["fase"] != "votacion":
                    st.info("La votación ya cerró.")
                else:
                    with E["lock"]:
                        E["votos"][pid] = {"nombre": nombre.strip(),
                                           "eleccion": "cat" if eleccion == "Cat bond" else "normal",
                                           "anio": 0}
                    st.rerun()
        return

    if stand:
        seguimiento_stand(pid)
    else:
        seguimiento(pid)


def tabla_anios(v, filas, anio, eleccion=None):
    eleccion = eleccion or v["eleccion"]
    html = ("<div class='card'><table class='flujo'><tr><th>Año</th><th>Qué pasó</th>"
            "<th class='n'>Cobraste</th><th class='n'>Invertido</th></tr>")
    for f in filas[:anio]:
        if eleccion == "normal":
            txt = "<span class='ok'>Hubo sismo, no te afecta</span>" if f["evento"] else "<span class='ok'>Sin sismo</span>"
        elif f["sismo"]:
            cuando = f" en el trimestre {f['trimestre']}" if E["params"]["trimestral"] else ""
            txt = f"<span class='mal'>Sismo{cuando}: se disparó, pierdes {dinero(f['perdido'])}</span>"
            if E["params"]["trimestral"]:
                txt += f"<br><span style='color:#5B6672;font-size:0.82rem'>Cobraste {f['trimestre'] - 1} de 4 trimestres</span>"
        elif f["principal"] == 0:
            txt = "<span style='color:#8A939C'>Ya no cobras</span>"
        else:
            txt = "<span class='ok'>Sin sismo</span>"
        html += (f"<tr><td><b>{f['anio']}</b></td><td>{txt}</td>"
                 f"<td class='n'>+{dinero(f['cupon'])}</td><td class='n'>{dinero(f['principal'])}</td></tr>")
    html += "</table>"
    if eleccion == "cat":
        html += f"<p style='margin:8px 0 0;font-size:0.8rem;color:#5B6672'>{regla_cupon()}</p>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def desglose(filas, inv):
    cupones = sum(f["cupon"] for f in filas)
    regreso = filas[-1]["principal"]
    tot = cupones + regreso
    neto = tot - inv
    color = "#2F7D4F" if neto >= 0 else "#B23A2B"
    palabra = "Ganaste" if neto >= 0 else "Perdiste"
    return (f"<div class='card desglose'>"
            f"<div><span>Cupones que cobraste ({ANIOS} años)</span><span>{dinero(cupones)}</span></div>"
            f"<div><span>+ Lo que te regresan al final</span><span>{dinero(regreso)}</span></div>"
            f"<div class='tot'><span>= Total que recibiste</span><span>{dinero(tot)}</span></div>"
            f"<div><span>− Lo que invertiste</span><span>{dinero(inv)}</span></div>"
            f"<div class='tot' style='color:{color}'><span>= {palabra}</span><span>{dinero(abs(neto))}</span></div>"
            f"</div>")


def resultado_final(v, sismos, filas):
    inv = E["params"]["inversion"]
    tot = total_recibido(filas)
    st.markdown(f"<div class='label'>Tu resultado</div><div class='grande'>{dinero(tot)}</div>"
                f"<p style='margin:0 0 8px'>es lo que recibiste en total, ya sumando los {ANIOS} años.</p>",
                unsafe_allow_html=True)
    st.markdown(desglose(filas, inv), unsafe_allow_html=True)

    otro = "normal" if v["eleccion"] == "cat" else "cat"
    filas_otro = flujos(otro, sismos)
    nombre_otro = "bono normal" if otro == "normal" else "cat bond"
    tot_otro = total_recibido(filas_otro)
    with st.expander(f"¿Y si hubieras elegido el {nombre_otro}? Habrías recibido {dinero(tot_otro)}",
                     expanded=(otro == "cat")):
        st.caption("Mismos años y mismos sismos que te tocaron a ti.")
        tabla_anios(v, filas_otro, ANIOS, eleccion=otro)
        st.markdown(desglose(filas_otro, inv), unsafe_allow_html=True)


def seguimiento_stand(pid):
    """Modo stand: cada visitante avanza sus propios años."""
    v = E["votos"].get(pid)
    if v is None:
        st.info("Se reinició la dinámica. Recarga la página para volver a jugar.")
        return
    tag = "<span class='tag tag-cat'>Cat bond</span>" if v["eleccion"] == "cat" else "<span class='tag tag-normal'>Bono normal</span>"
    st.markdown(f"**{v['nombre']}**, invertiste en {tag}", unsafe_allow_html=True)
    sismos = sismos_de(pid)
    filas = flujos(v["eleccion"], sismos)
    anio = v.get("anio", 0)
    if anio == 0:
        st.markdown("<div class='card'>Vamos a ver qué pasa con tu dinero año por año.</div>", unsafe_allow_html=True)
    else:
        tabla_anios(v, filas, anio)
    if anio < ANIOS:
        etiqueta = "Empezar: año 1" if anio == 0 else f"Siguiente: año {anio + 1}"
        if st.button(etiqueta, type="primary", use_container_width=True):
            v["anio"] = anio + 1
            st.rerun()
    else:
        resultado_final(v, sismos, filas)
        if st.button("Jugar otra vez", use_container_width=True):
            st.query_params["id"] = uuid.uuid4().hex[:10]
            st.rerun()


@st.fragment(run_every=2)
def seguimiento(pid):
    v = E["votos"].get(pid)
    if v is None:
        st.info("Se reinició la dinámica. Recarga la página para volver a votar.")
        return
    tag = "<span class='tag tag-cat'>Cat bond</span>" if v["eleccion"] == "cat" else "<span class='tag tag-normal'>Bono normal</span>"
    st.markdown(f"**{v['nombre']}**, invertiste en {tag}", unsafe_allow_html=True)

    anio = E["anio"] if E["fase"] == "sorteo" else 0
    if anio == 0:
        st.markdown("<div class='card'>Listo. Ahora mira la pantalla: vamos a ver qué pasa año por año.</div>",
                    unsafe_allow_html=True)
        return

    sismos = sismos_de(pid)
    filas = flujos(v["eleccion"], sismos)
    tabla_anios(v, filas, anio)
    if anio == ANIOS:
        resultado_final(v, sismos, filas)


# ============================== VISTA PANTALLA ==============================
def controles():
    with st.sidebar:
        st.markdown("### Controles")
        opciones = {"salon": "Salón: todos a la vez", "stand": "Stand: llegan de a pocos"}
        nuevo = st.radio("Modo", list(opciones), format_func=opciones.get,
                         index=list(opciones).index(E["modo"]))
        if nuevo != E["modo"]:
            with E["lock"]:
                E.update(modo=nuevo, votos={}, fase="votacion", anio=0, semilla=random.randint(1, 10**9))
            st.rerun()
        if E["modo"] == "stand":
            st.caption("Cada visitante avanza sus años en su celular. La pantalla suma a todos los que pasan.")
        else:
            st.caption("Votación abierta" if E["fase"] == "votacion" else f"Sorteo · año {E['anio']} de {ANIOS}")
        if E["modo"] == "stand":
            pass
        elif E["fase"] == "votacion":
            if st.button("Cerrar votación y empezar", type="primary", use_container_width=True):
                with E["lock"]:
                    E["fase"], E["anio"] = "sorteo", 0
                st.rerun()
        else:
            c1, c2 = st.columns(2)
            if c1.button("◀ Año", use_container_width=True, disabled=E["anio"] == 0):
                E["anio"] -= 1; st.rerun()
            if c2.button("Año ▶", type="primary", use_container_width=True, disabled=E["anio"] == ANIOS):
                E["anio"] += 1; st.rerun()
            if st.button("Reabrir votación", use_container_width=True):
                E["fase"], E["anio"] = "votacion", 0; st.rerun()

        st.divider()
        with st.expander("Supuestos"):
            pr = E["params"]
            pr["p"] = st.number_input("Probabilidad anual de sismo", 0.0, 1.0, pr["p"], 0.005, format="%.4f",
                                      help="Bono vigente 2024, clase B: 5.84%.")
            pr["tasa_normal"] = st.number_input("Tasa del bono normal", 0.0, 1.0, pr["tasa_normal"], 0.001, format="%.4f")
            pr["severidad"] = st.number_input("% del principal que se pierde", 0.0, 1.0, pr["severidad"], 0.25)
            pr["m"] = st.number_input("Múltiplo de riesgo (m)", 0.5, 5.0, pr["m"], 0.05, format="%.2f")
            pagos = st.radio("Pagos del cupón", ["Trimestrales", "Anuales"], index=0 if pr["trimestral"] else 1,
                             horizontal=True, help="Trimestrales: como el bono real. Anuales: más simple.")
            pr["trimestral"] = pagos == "Trimestrales"
            st.caption(f"Cupón del cat bond = {pr['tasa_normal']:.2%} + {pr['p']:.2%} × {pr['severidad']:.0%} × {pr['m']:.2f} = **{cupon_cat():.2%}**")
        if st.button("Reiniciar todo (borra votos)", use_container_width=True):
            with E["lock"]:
                E.update(votos={}, fase="votacion", anio=0, semilla=random.randint(1, 10**9))
            st.rerun()


def chip(r):
    if r["eleccion"] == "normal":
        cls = "p-normal-sismo" if r.get("sismo_normal") else "p-normal"
    elif r["golpeado"]:
        cls = "p-hit"
    elif r["terminado"]:
        cls = "p-cat"
    else:
        cls = "p-jugando"
    return f"<div class='persona {cls}'>{r['nombre']}</div>"


def pantalla_stand():
    pr = E["params"]
    votos = list(E["votos"].items())
    res = []
    for pid, v in votos:
        s = sismos_de(pid)
        filas = flujos(v["eleccion"], s)
        a = v.get("anio", 0)
        res.append({**v, "sismos": s, "filas": filas, "terminado": a == ANIOS,
                    "golpeado": any(f["sismo"] for f in filas[:a]),
                    "sismo_normal": v["eleccion"] == "normal" and any(f["evento"] for f in filas[:a])})
    n = len(res)
    fin = [r for r in res if r["terminado"]]
    cat = [total_recibido(r["filas"]) for r in fin if r["eleccion"] == "cat"]
    nor = [total_recibido(r["filas"]) for r in fin if r["eleccion"] == "normal"]
    n_cat = sum(r["eleccion"] == "cat" for r in res)
    golpeados = sum(r["golpeado"] for r in res)

    izq, der = st.columns([1, 1.5], gap="large")
    with izq:
        st.markdown("<div class='label'>Escanea y juega</div>", unsafe_allow_html=True)
        st.image(qr_png(url_base()), use_container_width=True)
        st.caption(url_base())
    with der:
        st.markdown("# ¿Dónde pondrías tus $10,000?")
        st.markdown(f"<span class='tag tag-cat'>Cat bond · {cupon_cat():.1%}</span> &nbsp; "
                    f"<span class='tag tag-normal'>Bono normal · {pr['tasa_normal']:.1%}</span>",
                    unsafe_allow_html=True)
        st.write("")
        a, b, c = st.columns(3)
        a.markdown(f"<div class='label'>Han jugado</div><div class='metric'>{n}</div>", unsafe_allow_html=True)
        b.markdown(f"<div class='label'>Eligieron cat bond</div><div class='metric' style='color:#C8553D'>{n_cat}</div>", unsafe_allow_html=True)
        c.markdown(f"<div class='label'>Eligieron bono normal</div><div class='metric' style='color:#2E5E8C'>{n - n_cat}</div>", unsafe_allow_html=True)
        x, y = st.columns(2)
        if cat:
            x.markdown(f"<div class='label'>Promedio cat bond</div><div class='metric' style='color:#C8553D'>{dinero(sum(cat)/len(cat))}</div>", unsafe_allow_html=True)
        if nor:
            y.markdown(f"<div class='label'>Promedio bono normal</div><div class='metric' style='color:#2E5E8C'>{dinero(sum(nor)/len(nor))}</div>", unsafe_allow_html=True)
        if fin:
            hit_all = sum(any(r["sismos"]) for r in fin)
            hc = sum(any(r["sismos"]) for r in fin if r["eleccion"] == "cat")
            teoria = 1 - (1 - pr["p"]) ** ANIOS
            st.markdown(comparar_html(hit_all, len(fin), teoria, hc, hit_all - hc), unsafe_allow_html=True)

    if res:
        st.markdown("<div class='label' style='margin-top:10px'>Últimos en jugar</div>", unsafe_allow_html=True)
        st.markdown("<span class='tag' style='background:#9AA3AC;color:#fff'>Jugando</span> &nbsp; "
                    "<span class='tag' style='background:#3C8D5A;color:#fff'>Cat bond intacto</span> &nbsp; "
                    "<span class='tag' style='background:#B23A2B;color:#fff'>Cat bond disparado</span> &nbsp; "
                    "<span class='tag tag-normal'>Bono normal</span> &nbsp; "
                    "<span class='tag tag-normal' style='box-shadow: inset 0 0 0 2px #E8A33D'>Bono normal con sismo (no le afecta)</span>", unsafe_allow_html=True)
        st.write("")
        recientes = res[-18:][::-1]
        st.markdown(f"<div class='rejilla'>{''.join(chip(r) for r in recientes)}</div>", unsafe_allow_html=True)


@st.fragment(run_every=2)
def pantalla():
    if E["modo"] == "stand":
        pantalla_stand()
        return
    votos = dict(E["votos"])
    n = len(votos)
    n_cat = sum(v["eleccion"] == "cat" for v in votos.values())
    pr = E["params"]

    if E["fase"] == "votacion":
        izq, der = st.columns([1, 1.3], gap="large")
        with izq:
            st.markdown("<div class='label'>Escanea y vota</div>", unsafe_allow_html=True)
            st.image(qr_png(url_base()), use_container_width=True)
            st.caption(url_base())
        with der:
            st.markdown("# ¿Dónde pondrías tus $10,000?")
            st.markdown(f"<span class='tag tag-cat'>Cat bond · {cupon_cat():.1%}</span> &nbsp; "
                        f"<span class='tag tag-normal'>Bono normal · {pr['tasa_normal']:.1%}</span>",
                        unsafe_allow_html=True)
            st.write("")
            a, b, c = st.columns(3)
            a.markdown(f"<div class='label'>Votos</div><div class='metric'>{n}</div>", unsafe_allow_html=True)
            b.markdown(f"<div class='label'>Cat bond</div><div class='metric' style='color:#C8553D'>{n_cat}</div>", unsafe_allow_html=True)
            c.markdown(f"<div class='label'>Bono normal</div><div class='metric' style='color:#2E5E8C'>{n - n_cat}</div>", unsafe_allow_html=True)
            if n:
                st.progress(n_cat / n, text=f"{n_cat / n:.0%} eligió cat bond")
            nombres = " · ".join(v["nombre"] for v in list(votos.values())[-30:])
            st.caption(nombres)
        return

    anio = E["anio"]
    res = {}
    for pid, v in votos.items():
        s = sismos_de(pid)
        filas = flujos(v["eleccion"], s)
        golpeado = any(f["sismo"] for f in filas[:anio])
        sn = v["eleccion"] == "normal" and any(f["evento"] for f in filas[:anio])
        res[pid] = {**v, "filas": filas, "golpeado": golpeado, "sismos": s, "sismo_normal": sn}
    golpeados = sum(r["golpeado"] for r in res.values())

    titulo = "Antes del primer año" if anio == 0 else f"Año {anio} de {ANIOS}"
    st.markdown(f"# {titulo}")
    a, b, c = st.columns(3)
    a.markdown(f"<div class='label'>Han jugado</div><div class='metric'>{n}</div>", unsafe_allow_html=True)
    b.markdown(f"<div class='label'>Eligieron cat bond</div><div class='metric' style='color:#C8553D'>{n_cat}</div>", unsafe_allow_html=True)
    c.markdown(f"<div class='label'>Eligieron bono normal</div><div class='metric' style='color:#2E5E8C'>{n - n_cat}</div>", unsafe_allow_html=True)

    st.markdown("<span class='tag' style='background:#3C8D5A;color:#fff'>Cat bond intacto</span> &nbsp; "
                "<span class='tag' style='background:#B23A2B;color:#fff'>Cat bond disparado</span> &nbsp; "
                "<span class='tag tag-normal'>Bono normal</span> &nbsp; "
                    "<span class='tag tag-normal' style='box-shadow: inset 0 0 0 2px #E8A33D'>Bono normal con sismo (no le afecta)</span>", unsafe_allow_html=True)
    st.write("")
    orden = sorted(res.values(), key=lambda r: (r["eleccion"] != "cat", not r["golpeado"], r["nombre"].lower()))
    chips = "".join(
        f"<div class='persona {('p-normal-sismo' if r['sismo_normal'] else 'p-normal') if r['eleccion'] == 'normal' else ('p-hit' if r['golpeado'] else 'p-cat')}'>{r['nombre']}</div>"
        for r in orden)
    st.markdown(f"<div class='rejilla'>{chips}</div>", unsafe_allow_html=True)

    if anio == ANIOS and n:
        st.divider()
        inv = pr["inversion"]
        cat = [total_recibido(r["filas"]) for r in res.values() if r["eleccion"] == "cat"]
        nor = [total_recibido(r["filas"]) for r in res.values() if r["eleccion"] == "normal"]
        todos_cat = [total_recibido(flujos("cat", r["sismos"])) for r in res.values()]
        x, y, z = st.columns(3)
        if cat:
            x.markdown(f"<div class='label'>Promedio cat bond</div><div class='metric' style='color:#C8553D'>{dinero(sum(cat)/len(cat))}</div>"
                       f"<p>Rango: {dinero(min(cat))} a {dinero(max(cat))}</p>", unsafe_allow_html=True)
        if nor:
            y.markdown(f"<div class='label'>Promedio bono normal</div><div class='metric' style='color:#2E5E8C'>{dinero(sum(nor)/len(nor))}</div>"
                       f"<p>Todos recibieron lo mismo</p>", unsafe_allow_html=True)
        hit_all = sum(any(r["sismos"]) for r in res.values())
        hc = sum(any(r["sismos"]) for r in res.values() if r["eleccion"] == "cat")
        teoria = 1 - (1 - pr["p"]) ** ANIOS
        st.markdown(comparar_html(hit_all, n, teoria, hc, hit_all - hc), unsafe_allow_html=True)
        st.caption(f"Cada persona invirtió {dinero(inv)}. {regla_cupon()}")


def vista_pantalla():
    if st.query_params.get("clave") != CLAVE:
        st.error("Falta la clave en el link de la pantalla.")
        return
    controles()
    pantalla()


if st.query_params.get("vista") == "pantalla":
    vista_pantalla()
else:
    vista_celular()
