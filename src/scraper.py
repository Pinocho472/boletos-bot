import requests
from config import FUENTES, CIUDADES, CIUDADES_ACTIVAS

HEADERS = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}

def detectar_plaza(ciudad, venue=""):
    texto = (ciudad + " " + venue).lower()
    for clave, datos in CIUDADES.items():
        if clave not in CIUDADES_ACTIVAS:
            continue
        if any(k in texto for k in datos["keywords"] + datos["venues"]):
            return clave
    return "otra"

def _precio(ev):
    if "priceRanges" in ev:
        return ev["priceRanges"][0].get("min"), ev["priceRanges"][0].get("max")
    return None, None

def revisar_ticketmaster():
    eventos = []
    try:
        r = requests.get(FUENTES[0]["url"], headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        for ev in r.json().get("_embedded", {}).get("events", []):
            venue_obj = ev.get("_embedded", {}).get("venues", [{}])[0]
            ciudad    = venue_obj.get("city", {}).get("name", "")
            venue     = venue_obj.get("name", "")
            pmin, pmax = _precio(ev)
            plaza     = detectar_plaza(ciudad, venue)
            if plaza == "otra":
                continue
            eventos.append({
                "id":         ev.get("id", ""),
                "nombre":     ev.get("name", ""),
                "fecha":      ev.get("dates", {}).get("start", {}).get("localDate", ""),
                "ciudad":     ciudad,
                "venue":      venue,
                "plaza":      plaza,
                "estado":     ev.get("dates", {}).get("status", {}).get("code", ""),
                "precio_min": pmin,
                "precio_max": pmax,
                "fuente":     "Ticketmaster MX",
                "url":        ev.get("url", "https://ticketmaster.com.mx")
            })
    except Exception as e:
        print(f"[Ticketmaster] Error: {e}")
    return eventos

def revisar_ocesa():
    eventos = []
    try:
        r = requests.get(FUENTES[1]["url"], headers=HEADERS, timeout=15)
        if r.status_code != 200:
            return []
        for post in r.json():
            eventos.append({
                "id":         f"ocesa_{post.get('id','')}",
                "nombre":     post.get("title", {}).get("rendered", ""),
                "fecha":      post.get("date", "")[:10],
                "ciudad":     "Ciudad de México",
                "venue":      "",
                "plaza":      "cdmx",
                "estado":     "onsale",
                "precio_min": None,
                "precio_max": None,
                "fuente":     "OCESA",
                "url":        post.get("link", "")
            })
    except Exception as e:
        print(f"[OCESA] Error: {e}")
    return eventos

def obtener_todos():
    return revisar_ticketmaster() + revisar_ocesa()
