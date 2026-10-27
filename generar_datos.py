"""
Generador de datos ficticios: seguimiento de la carga docente de una universidad.
Todos los nombres, identificadores y cifras son inventados. Semilla fija para que sea reproducible.
"""
import random, os
from datetime import date, timedelta
import pandas as pd

random.seed(42)
BASE = "datos"
os.makedirs(f"{BASE}/extracciones_planificacion", exist_ok=True)
os.makedirs(f"{BASE}/maestros", exist_ok=True)
os.makedirs("soluciones", exist_ok=True)

LETRAS = "BCDFGHJKLMNPRSTVWXYZ"
def ip_ficticia(usados, rng=random):
    while True:
        d = f"{rng.randint(0, 9999):04d}{''.join(rng.choices(LETRAS, k=3))}"
        if d not in usados:
            usados.add(d); return d

NOMBRES = ["Ana","Luis","Marta","Carlos","Lucía","Javier","Elena","Pablo","Carmen","Sergio","Laura","Antonio",
           "Isabel","Miguel","Paula","José","Raquel","David","Cristina","Alberto","Nuria","Fernando","Beatriz",
           "Jorge","Silvia","Rubén","Teresa","Andrés","Irene","Manuel","Rosa","Diego","Pilar","Óscar","Sara"]
APELLIDOS = ["García","Martínez","López","Sánchez","Pérez","Gómez","Ruiz","Hernández","Jiménez","Díaz","Moreno",
             "Muñoz","Álvarez","Romero","Navarro","Torres","Domínguez","Gil","Vázquez","Serrano","Ramos","Blanco",
             "Molina","Castillo","Ortega","Rubio","Marín","Sanz","Iglesias","Medina","Garrido","Cortés","Castro"]

CENTROS = {
    "Facultad de Ciencias de la Salud": ["Grado en Enfermería","Grado en Fisioterapia","Máster en Nutrición Clínica"],
    "Facultad de Ciencias Jurídicas y de la Empresa": ["Grado en ADE","Grado en Derecho","Máster en Dirección de RRHH"],
    "Escuela Politécnica": ["Grado en Ingeniería Informática","Grado en Arquitectura","Máster en Ciencia de Datos"],
    "Facultad de Comunicación": ["Grado en Periodismo","Grado en Publicidad"],
    "Facultad de Deporte": ["Grado en Ciencias del Deporte"],
}
MODALIDAD_POR_TIT = lambda t: random.choices(["Presencial","Semipresencial","A distancia"],
                                             [0.75,0.15,0.10] if t.startswith("Grado") else [0.35,0.35,0.30])[0]

# ---------- Asignaturas ----------
asignaturas = []
cod = 1000
for centro, tits in CENTROS.items():
    for tit in tits:
        n = random.randint(18, 30)
        modalidad = MODALIDAD_POR_TIT(tit)
        for i in range(n):
            cod += 1
            curso = random.randint(1, 4) if tit.startswith("Grado") else 1
            asignaturas.append({
                "cod_asignatura": f"AS{cod}", "asignatura": f"{tit.split(' en ')[-1]} - Asignatura {i+1:02d}",
                "titulacion": tit, "tipo_estudio": "Grado" if tit.startswith("Grado") else "Máster",
                "centro": centro, "curso": curso, "semestre": random.choice([1, 2]),
                "creditos_ects": random.choice([3, 4.5, 6, 6, 6, 9]),
                "alumnos_matriculados": random.randint(12, 120) if tit.startswith("Grado") else random.randint(8, 40),
                "modalidad": modalidad,
            })
# Asignaturas sin alumnos (control 1)
sin_alumnos = random.sample(asignaturas, 12)
for a in sin_alumnos: a["alumnos_matriculados"] = 0
asig_df = pd.DataFrame(asignaturas)

# ---------- Docentes (maestro de personal, la fuente correcta) ----------
CONTRATOS = [("Docente a tiempo completo", 70), ("Docente a tiempo parcial", 40), ("Docente vinculado", 70),
             ("Ponente invitado", 25), ("Docente de apoyo", 15)]
usados, docentes, idn = set(), [], 0
for tipo, n in CONTRATOS:
    for _ in range(n):
        idn += 1
        centro = random.choice(list(CENTROS))
        docentes.append({
            "id_empleado": f"EMP{idn:04d}", "ip": ip_ficticia(usados),
            "nombre": random.choice(NOMBRES),
            "apellidos": f"{random.choice(APELLIDOS)} {random.choice(APELLIDOS)}",
            "tipo_contrato": tipo, "centro_adscripcion": centro,
            "fecha_alta": date(random.randint(2005, 2026), random.randint(1, 12), 1),
            "categoria": {"Docente a tiempo completo": "Plantilla fija", "Docente a tiempo parcial": "Plantilla temporal",
                          "Docente vinculado": "Plantilla vinculada", "Ponente invitado": "Personal externo",
                          "Docente de apoyo": "Plantilla de apoyo"}[tipo],
        })
for d in docentes:
    d["fecha_alta"] = min(d["fecha_alta"], date(2026, 8, 1))
doc_df = pd.DataFrame(docentes)

# Contrato tal como figura (mal) en la planificación para algunos docentes (control 2)
contrato_planif = {d["ip"]: d["tipo_contrato"] for d in docentes}
discrepantes = random.sample([d for d in docentes if d["tipo_contrato"] != "Ponente invitado"], 9)
for d in discrepantes:
    otros = [c for c, _ in CONTRATOS if c not in (d["tipo_contrato"], "Ponente invitado")]
    contrato_planif[d["ip"]] = random.choice(otros)

# ---------- Asignaciones docentes iniciales ----------
RANGOS = {"Docente a tiempo completo": ((4, 7), (30, 90)), "Docente a tiempo parcial": ((3, 5), (20, 60)),
          "Docente vinculado": ((2, 4), (15, 60)), "Ponente invitado": ((1, 2), (4, 12)),
          "Docente de apoyo": ((2, 4), (15, 45))}
asign = {}  # id_asignacion -> dict
aid = 0
def nueva_asignacion(doc, asig, horas):
    global aid
    aid += 1
    asign[aid] = {"id_asignacion": aid, "ip": doc["ip"], "cod_asignatura": asig["cod_asignatura"],
                  "grupo": random.choice(["A", "A", "B", "C"]), "horas": horas}
    return aid

for d in docentes:
    (nmin, nmax), (hmin, hmax) = RANGOS[d["tipo_contrato"]]
    pool = [a for a in asignaturas if a["centro"] == d["centro_adscripcion"]] if random.random() < 0.8 else asignaturas
    for a in random.sample(pool, random.randint(nmin, nmax)):
        nueva_asignacion(d, a, random.randint(hmin, hmax))
# Garantizar horas en asignaturas sin alumnos
for a in sin_alumnos:
    if not any(x["cod_asignatura"] == a["cod_asignatura"] for x in asign.values()):
        doc = random.choice([d for d in docentes if d["tipo_contrato"] != "Ponente invitado"])
        nueva_asignacion(doc, a, random.randint(20, 60))

# ---------- Simulación de extracciones diarias ----------
dias = [date(2026, 9, 1) + timedelta(days=i) for i in range(61)]
dias = [d for d in dias if d.weekday() < 5]
conf_exceso = random.sample([d for d in docentes if d["tipo_contrato"] == "Ponente invitado"], 6)
dia_conf = {d["ip"]: random.choice(dias[10:-5]) for d in conf_exceso}
dia_ausente = random.choice(dias[15:-10])
asig_ausente = random.choice([a for a in asignaturas if sum(x["cod_asignatura"] == a["cod_asignatura"]
                                                            for x in asign.values()) >= 2])
docmap = {d["ip"]: d for d in docentes}
asigmap = {a["cod_asignatura"]: a for a in asignaturas}

# ---------- Bajas de personal (control 5) ----------
rb = random.Random(2026)
excluidos = {d["ip"] for d in discrepantes}
candidatos = [d for d in docentes if d["tipo_contrato"] != "Ponente invitado" and d["ip"] not in excluidos]
bajas = rb.sample(candidatos, 9)
fecha_baja = {}
reasignados = {}  # ip que se va -> (fecha desde la que se sustituye, ip del sustituto)
nuevos = []
for i, d in enumerate(bajas):
    fb = rb.choice(dias[8:-8])
    fecha_baja[d["ip"]] = fb
    if i < 4:  # baja bien gestionada: sus horas pasan a un docente nuevo
        idn += 1
        nuevo = {"id_empleado": f"EMP{idn:04d}", "ip": ip_ficticia(usados, rb), "nombre": rb.choice(NOMBRES),
                 "apellidos": f"{rb.choice(APELLIDOS)} {rb.choice(APELLIDOS)}", "tipo_contrato": d["tipo_contrato"],
                 "centro_adscripcion": d["centro_adscripcion"], "fecha_alta": fb, "categoria": d["categoria"]}
        nuevos.append(nuevo)
        reasignados[d["ip"]] = (fb, nuevo["ip"])
        contrato_planif[nuevo["ip"]] = nuevo["tipo_contrato"]
        docmap[nuevo["ip"]] = nuevo
    # i >= 4: baja no comunicada a la planificación, sigue apareciendo con horas
historicos = []
for _ in range(3):  # antiguos empleados sin asignaciones en este curso
    idn += 1
    historicos.append({"id_empleado": f"EMP{idn:04d}", "ip": ip_ficticia(usados, rb), "nombre": rb.choice(NOMBRES),
                       "apellidos": f"{rb.choice(APELLIDOS)} {rb.choice(APELLIDOS)}",
                       "tipo_contrato": "Docente a tiempo parcial", "centro_adscripcion": rb.choice(list(CENTROS)),
                       "fecha_alta": date(rb.randint(2015, 2022), rb.randint(1, 12), 1), "categoria": "Plantilla temporal",
                       "fecha_baja": date(2025, rb.randint(1, 12), rb.randint(1, 28))})

def ensuciar_texto(s):
    r = random.random()
    if r < 0.04: return s.upper()
    if r < 0.08: return s + " "
    if r < 0.10: return s.lower()
    return s

registro_global = 0
for dia in dias:
    if dia != dias[0]:
        # cambios habituales de la propuesta: ajustes de horas, altas y bajas
        for x in random.sample(list(asign.values()), max(1, int(len(asign) * 0.01))):
            x["horas"] = max(2, x["horas"] + random.choice([-15, -10, -6, -4, 4, 6, 10, 15]))
        if random.random() < 0.5:
            d = random.choice([d for d in docentes if d["tipo_contrato"] != "Ponente invitado"])
            nueva_asignacion(d, random.choice(asignaturas), random.randint(10, 45))
        if random.random() < 0.3:
            del asign[random.choice(list(asign))]
        # ponentes invitados que superan el límite anual de 30 h (control 3)
        for ip, dc in dia_conf.items():
            if dia == dc:
                actual = sum(x["horas"] for x in asign.values() if x["ip"] == ip)
                nueva_asignacion(docmap[ip], random.choice(asignaturas), 30 - actual + random.randint(4, 20))

    filas = []
    for x in asign.values():
        if dia == dia_ausente and x["cod_asignatura"] == asig_ausente["cod_asignatura"]:
            continue  # la asignatura no aparece en el fichero de ese día (control 4)
        ip_ef = x["ip"]
        if ip_ef in reasignados and dia >= reasignados[ip_ef][0]:
            ip_ef = reasignados[ip_ef][1]
        d, a = docmap[ip_ef], asigmap[x["cod_asignatura"]]
        registro_global += 1
        filas.append({
            "ID_REGISTRO": registro_global, "CURSO_ACADEMICO": "2026-27", "FECHA_DESCARGA": dia,
            "IP": ip_ef, "NOMBRE": d["nombre"], "APELLIDOS": d["apellidos"],
            "TIPO_CONTRATO": contrato_planif[ip_ef], "CENTRO_ADSCRIPCION": d["centro_adscripcion"],
            "CENTRO_IMPARTICION": a["centro"], "TITULACION": a["titulacion"], "TIPO_ESTUDIO": a["tipo_estudio"],
            "COD_ASIGNATURA": a["cod_asignatura"], "ASIGNATURA": a["asignatura"], "GRUPO": x["grupo"],
            "SEMESTRE": a["semestre"], "MODALIDAD": ensuciar_texto(a["modalidad"]),
            "HORAS_ASIGNADAS": x["horas"], "ID_ASIGNACION": x["id_asignacion"],
            "USUARIO_MODIFICACION": random.choice(["admin_sec01", "admin_sec02", "admin_sec03", "sistema"]),
            "OBSERVACIONES": random.choice([None] * 30 + ["Pendiente de validar", "Revisar grupo"]),
        })
    # filas generadas por error en la aplicación (hay que limpiarlas en Power Query)
    for _ in range(random.randint(5, 15)):
        base = dict(random.choice(filas))
        tipo_err = random.choice(["sin_ip", "registro_erroneo", "horas_cero"])
        registro_global += 1
        base["ID_REGISTRO"] = registro_global
        if tipo_err == "sin_ip": base["IP"] = None; base["NOMBRE"] = None; base["APELLIDOS"] = None
        elif tipo_err == "registro_erroneo": base["COD_ASIGNATURA"] = "ERR000"; base["ASIGNATURA"] = "REGISTRO ERRÓNEO"
        else: base["HORAS_ASIGNADAS"] = 0
        filas.append(base)
    # duplicados exactos (mismo ID_REGISTRO)
    filas += [dict(f) for f in random.sample(filas, random.randint(2, 6))]
    random.shuffle(filas)
    pd.DataFrame(filas).to_excel(f"{BASE}/extracciones_planificacion/planificacion_docente_{dia:%Y-%m-%d}.xlsx", index=False)

# ---------- Maestros ----------
maestro = pd.DataFrame(docentes + nuevos + historicos)
maestro["fecha_baja"] = maestro.apply(lambda r: fecha_baja.get(r["ip"], r.get("fecha_baja")), axis=1)
maestro["fecha_baja"] = pd.to_datetime(maestro["fecha_baja"]).dt.date
maestro.to_excel(f"{BASE}/maestros/maestro_personal.xlsx", index=False)
asig_df.drop(columns=["modalidad"]).to_excel(f"{BASE}/maestros/asignaturas.xlsx", index=False)


# ---------- Soluciones (para comprobar tu dashboard, no para el portfolio) ----------
final = pd.DataFrame(asign.values())
with pd.ExcelWriter("soluciones/soluciones_controles.xlsx") as w:
    s1 = final.merge(asig_df[["cod_asignatura", "asignatura", "titulacion", "alumnos_matriculados"]], on="cod_asignatura")
    s1[s1.alumnos_matriculados == 0].groupby(["cod_asignatura", "asignatura", "titulacion"], as_index=False)["horas"] \
        .sum().rename(columns={"horas": "horas_asignadas_ultimo_dia"}).to_excel(w, sheet_name="horas_sin_alumnos", index=False)
    pd.DataFrame([{"ip": d["ip"], "nombre": d["nombre"], "apellidos": d["apellidos"],
                   "contrato_maestro": d["tipo_contrato"], "contrato_planificacion": contrato_planif[d["ip"]]}
                  for d in discrepantes]).to_excel(w, sheet_name="discrepancias_contrato", index=False)
    tot = final.groupby("ip", as_index=False)["horas"].sum()
    conf = doc_df[doc_df.tipo_contrato == "Ponente invitado"][["ip", "nombre", "apellidos"]].merge(tot, on="ip")
    conf[conf.horas > 30].rename(columns={"horas": "horas_ultimo_dia"}).to_excel(w, sheet_name="ponentes_exceso", index=False)
    pd.DataFrame([{"fecha_descarga": dia_ausente, "cod_asignatura": asig_ausente["cod_asignatura"],
                   "asignatura": asig_ausente["asignatura"]}]).to_excel(w, sheet_name="asignatura_ausente", index=False)
ultimo = pd.read_excel(f"{BASE}/extracciones_planificacion/planificacion_docente_{dias[-1]:%Y-%m-%d}.xlsx")
ultimo = ultimo[ultimo.IP.notna() & (ultimo.COD_ASIGNATURA != "ERR000") & (ultimo.HORAS_ASIGNADAS > 0)].drop_duplicates()
sol5 = maestro[maestro.fecha_baja.notna()][["ip", "nombre", "apellidos", "fecha_baja"]] \
    .merge(ultimo.groupby("IP", as_index=False)["HORAS_ASIGNADAS"].sum(), left_on="ip", right_on="IP")
sol5 = sol5[pd.to_datetime(sol5.fecha_baja) <= pd.Timestamp(dias[-1])].drop(columns="IP") \
    .rename(columns={"HORAS_ASIGNADAS": "horas_ultimo_dia"})
with pd.ExcelWriter("soluciones/soluciones_controles.xlsx", mode="a", engine="openpyxl") as w:
    sol5.to_excel(w, sheet_name="bajas_en_planificacion", index=False)
print("Días:", len(dias), "| asignaciones finales:", len(final), "| registro_global:", registro_global)
