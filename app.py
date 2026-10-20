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
    "p": 0.0343,           # pérdida esperada anual del bono 2017 (s = 100%)
    "severidad": 1.0,
    "m": 1.31,             # margen 4.5% / pérdida esperada 3.43% (bono 2017)
}
ANIOS = 4

st.set_page_config(page_title="Sé el inversionista", page_icon="🌎", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;700&family=Source+Sans+3:wght@400;600&display=swap');
html, body, [class*="css"], .stMarkdown, p, li, label { font-family: 'Source Sans 3', sans-serif; }
h1, h2, h3, .big { font-family: 'Space Grotesk', sans-serif !important; letter-spacing: -0.01em; }
#MainMenu, footer, header [data-testid="stToolbar"] { visibility: hidden; }
.block-container { padding-top: 1.6rem; }
.tag { display:inline-block; padding:2px 10px; border-radius:999px; font-size:0.8rem; font-weight:600; }
.tag-cat { background:#C8553D; color:#fff; }
.tag-normal { background:#2E5E8C; color:#fff; }
.card { background:#fff; border:1px solid #E2DACD; border-radius:14px; padding:14px 16px; margin-bottom:10px; }
.anio { display:flex; justify-content:space-between; align-items:center; padding:10px 0; border-bottom:1px solid #EEE7DC; }
.anio:last-child { border-bottom:none; }
.ok { color:#2F7D4F; font-weight:600; }
.mal { color:#B23A2B; font-weight:700; }
.persona { border-radius:10px; padding:8px 10px; font-weight:600; font-size:0.95rem; color:#fff; text-align:center;
           overflow:hidden; white-space:nowrap; text-overflow:ellipsis; margin-bottom:8px; }
.p-jugando { background:#9AA3AC; } .p-cat { background:#3C8D5A; } .p-hit { background:#B23A2B; } .p-normal { background:#2E5E8C; }
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


def cupon_cat():
    """Cupón justo = r_f + p x s x m (igual que la pestaña 3 del Excel)."""
    pr = E["params"]
    return pr["tasa_normal"] + pr["p"] * pr["severidad"] * pr["m"]


def dinero(x):
    return f"${x:,.0f}"


def sismos_de(pid):
    """Sorteo fijo por persona: no cambia aunque entren más votos."""
    rng = random.Random(f"{E['semilla']}|{pid}")
    return [rng.random() < E["params"]["p"] for _ in range(ANIOS)]


def flujos(eleccion, sismos):
    """Año por año. El sismo cuenta al final del año: ese año sí se cobra el cupón."""
    pr = E["params"]
    inv = pr["inversion"]
    principal = inv
    filas = []
    for a in range(ANIOS):
        if eleccion == "normal":
            cupon, perdido = inv * pr["tasa_normal"], 0.0
        else:
            cupon = principal * cupon_cat()
            perdido = min(principal, pr["severidad"] * inv) if sismos[a] else 0.0
            principal -= perdido
        filas.append({"anio": a + 1, "sismo": sismos[a] and eleccion == "cat",
                      "cupon": cupon, "perdido": perdido, "principal": principal})
    return filas


def total_recibido(filas):
    return sum(f["cupon"] for f in filas) + filas[-1]["principal"]


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
        with c1:
            st.markdown(f"""<div class='card'><span class='tag tag-cat'>Cat bond</span>
            <div class='big' style='font-size:1.8rem;margin:8px 0 2px'>{cupon_cat():.1%} anual</div>
            <p style='margin:0'>Si no tiembla, ganas mucho. Si hay un sismo fuerte en la zona, pierdes tu dinero y se va a la reconstrucción.</p></div>""",
                        unsafe_allow_html=True)
        with c2:
            st.markdown(f"""<div class='card'><span class='tag tag-normal'>Bono normal</span>
            <div class='big' style='font-size:1.8rem;margin:8px 0 2px'>{pr['tasa_normal']:.1%} anual</div>
            <p style='margin:0'>Pase lo que pase, cobras tus intereses y al final te regresan tu dinero.</p></div>""",
                        unsafe_allow_html=True)
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


def tabla_anios(v, filas, anio):
    html = "<div class='card'>"
    for f in filas[:anio]:
        if f["sismo"]:
            txt = f"<span class='mal'>Sismo. Se disparó el bono: pierdes {dinero(f['perdido'])}</span>"
        elif v["eleccion"] == "cat" and f["principal"] == 0:
            txt = "<span style='color:#8A939C'>Ya no te queda principal</span>"
        else:
            txt = "<span class='ok'>Sin sismo</span>"
        html += f"<div class='anio'><span><b>Año {f['anio']}</b> · {txt}</span><span>+{dinero(f['cupon'])}</span></div>"
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)


def resultado_final(v, sismos, filas):
    inv = E["params"]["inversion"]
    tot = total_recibido(filas)
    otro = "normal" if v["eleccion"] == "cat" else "cat"
    tot_otro = total_recibido(flujos(otro, sismos))
    signo = "ganaste" if tot >= inv else "perdiste"
    st.markdown(f"<div class='label'>Recibiste en total</div><div class='grande'>{dinero(tot)}</div>"
                f"<p>O sea, {signo} {dinero(abs(tot - inv))} sobre tus {dinero(inv)}.</p>",
                unsafe_allow_html=True)
    nombre_otro = "bono normal" if otro == "normal" else "cat bond"
    st.caption(f"Con el {nombre_otro} habrías recibido {dinero(tot_otro)}.")


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
                                      help="Real 2017: 3.43%. Súbanla si son pocos en el salón y quieren que se vea algún sismo.")
            pr["tasa_normal"] = st.number_input("Tasa del bono normal", 0.0, 1.0, pr["tasa_normal"], 0.001, format="%.4f")
            pr["severidad"] = st.number_input("% del principal que se pierde", 0.0, 1.0, pr["severidad"], 0.25)
            pr["m"] = st.number_input("Múltiplo de riesgo (m)", 0.5, 5.0, pr["m"], 0.05, format="%.2f")
            st.caption(f"Cupón del cat bond = {pr['tasa_normal']:.2%} + {pr['p']:.2%} × {pr['severidad']:.0%} × {pr['m']:.2f} = **{cupon_cat():.2%}**")
        if st.button("Reiniciar todo (borra votos)", use_container_width=True):
            with E["lock"]:
                E.update(votos={}, fase="votacion", anio=0, semilla=random.randint(1, 10**9))
            st.rerun()


def chip(r):
    if r["eleccion"] == "normal":
        cls = "p-normal"
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
                    "golpeado": any(f["sismo"] for f in filas[:a])})
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
        c.markdown(f"<div class='label'>Les tocó el sismo</div><div class='metric' style='color:#B23A2B'>{golpeados}</div>", unsafe_allow_html=True)
        x, y = st.columns(2)
        if cat:
            x.markdown(f"<div class='label'>Promedio cat bond</div><div class='metric' style='color:#C8553D'>{dinero(sum(cat)/len(cat))}</div>", unsafe_allow_html=True)
        if nor:
            y.markdown(f"<div class='label'>Promedio bono normal</div><div class='metric' style='color:#2E5E8C'>{dinero(sum(nor)/len(nor))}</div>", unsafe_allow_html=True)
        if fin:
            hit_all = sum(any(r["sismos"]) for r in fin)
            teoria = 1 - (1 - pr["p"]) ** ANIOS
            st.markdown(f"<div class='card'>Si los {len(fin)} que ya terminaron hubieran elegido cat bond, "
                        f"<b>{hit_all / len(fin):.0%}</b> habría perdido su dinero. La teoría dice <b>{teoria:.0%}</b>. "
                        f"Entre más gente juega, más se acercan.</div>", unsafe_allow_html=True)

    if res:
        st.markdown("<div class='label' style='margin-top:10px'>Últimos en jugar</div>", unsafe_allow_html=True)
        st.markdown("<span class='tag' style='background:#9AA3AC;color:#fff'>Jugando</span> &nbsp; "
                    "<span class='tag' style='background:#3C8D5A;color:#fff'>Cat bond intacto</span> &nbsp; "
                    "<span class='tag' style='background:#B23A2B;color:#fff'>Cat bond disparado</span> &nbsp; "
                    "<span class='tag tag-normal'>Bono normal</span>", unsafe_allow_html=True)
        st.write("")
        recientes = res[-18:][::-1]
        for i in range(0, len(recientes), 6):
            cols = st.columns(6)
            for col, r in zip(cols, recientes[i:i + 6]):
                col.markdown(chip(r), unsafe_allow_html=True)


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
        res[pid] = {**v, "filas": filas, "golpeado": golpeado, "sismos": s}
    golpeados = sum(r["golpeado"] for r in res.values())

    titulo = "Antes del primer año" if anio == 0 else f"Año {anio} de {ANIOS}"
    st.markdown(f"# {titulo}")
    a, b, c = st.columns(3)
    a.markdown(f"<div class='label'>Inversionistas</div><div class='metric'>{n}</div>", unsafe_allow_html=True)
    b.markdown(f"<div class='label'>Con cat bond</div><div class='metric' style='color:#C8553D'>{n_cat}</div>", unsafe_allow_html=True)
    c.markdown(f"<div class='label'>Cat bonds disparados</div><div class='metric' style='color:#B23A2B'>{golpeados}</div>", unsafe_allow_html=True)

    st.markdown("<span class='tag' style='background:#3C8D5A;color:#fff'>Cat bond intacto</span> &nbsp; "
                "<span class='tag' style='background:#B23A2B;color:#fff'>Cat bond disparado</span> &nbsp; "
                "<span class='tag tag-normal'>Bono normal</span>", unsafe_allow_html=True)
    st.write("")
    orden = sorted(res.values(), key=lambda r: (r["eleccion"] != "cat", not r["golpeado"], r["nombre"].lower()))
    cols_por_fila = 6
    for i in range(0, len(orden), cols_por_fila):
        cols = st.columns(cols_por_fila)
        for col, r in zip(cols, orden[i:i + cols_por_fila]):
            cls = "p-normal" if r["eleccion"] == "normal" else ("p-hit" if r["golpeado"] else "p-cat")
            col.markdown(f"<div class='persona {cls}'>{r['nombre']}</div>", unsafe_allow_html=True)

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
        teoria = 1 - (1 - pr["p"]) ** ANIOS
        z.markdown(f"<div class='label'>Si todos eligieran cat bond</div><div class='metric'>{hit_all} de {n}</div>"
                   f"<p>habrían perdido su dinero. En teoría: {teoria:.0%}, o {teoria * n:.1f} de {n}.</p>",
                   unsafe_allow_html=True)
        st.caption(f"Cada persona invirtió {dinero(inv)}. El sismo se cuenta al final del año, así que ese año sí se cobra el cupón.")


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
