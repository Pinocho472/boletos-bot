import json, os
from datetime import datetime

EVENTOS_FILE   = "data/eventos.json"
HISTORIAL_FILE = "data/historial.json"

def _cargar(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

def _guardar(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def cargar_vistos():       return _cargar(EVENTOS_FILE)
def guardar_vistos(data):  _guardar(EVENTOS_FILE, data)

def registrar_historial(evento, tipo_alerta):
    historial = _cargar(HISTORIAL_FILE)
    entrada = {
        "fecha_deteccion": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "tipo":            tipo_alerta,
        "nombre":          evento["nombre"],
        "ciudad":          evento["ciudad"],
        "plaza":           evento.get("plaza", "otra"),
        "venue":           evento.get("venue", ""),
        "fecha_evento":    evento["fecha"],
        "estado":          evento["estado"],
        "precio_min":      evento.get("precio_min"),
        "precio_max":      evento.get("precio_max"),
        "fuente":          evento["fuente"],
        "url":             evento["url"]
    }
    eid = evento["id"]
    if eid not in historial:
        historial[eid] = []
    historial[eid].append(entrada)
    _guardar(HISTORIAL_FILE, historial)

def stats():
    historial   = _cargar(HISTORIAL_FILE)
    total       = sum(len(v) for v in historial.values())
    nuevos      = sum(1 for v in historial.values() for e in v if e["tipo"] == "NUEVO")
    disponibles = sum(1 for v in historial.values() for e in v if e["tipo"] == "DISPONIBLE")
    por_plaza   = {}
    for v in historial.values():
        for e in v:
            p = e.get("plaza", "otra")
            por_plaza[p] = por_plaza.get(p, 0) + 1
    return {"total": total, "nuevos": nuevos, "disponibles": disponibles, "por_plaza": por_plaza}
