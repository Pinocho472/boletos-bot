import requests
import re
import json
from config import CIUDADES, CIUDADES_ACTIVAS

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "application/json, text/plain, */*",
    "Accept-Language": "es-MX,es;q=0.9",
    "Referer": "https://www.ticketmaster.com.mx/"
}

OCESA_URL = "https://ocesa.com.mx/wp-json/wp/v2/posts?per_page=20&categories=eventos"

TM_SEARCH_URL = "https://www.ticketmaster.com.mx/api/2.0/search?q=&lat=25.6866&long=-100.3161&radius=200&unit=km&size=50&page=0"

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
    urls = [
        "https://www.ticketmaster.com.mx/api/2.0/search?q=&city=Monterrey&size=50&page=0",
        "https://www.ticketmaster.com.mx/api/2.0/search?q=&city=Mexico&size=50&page=0",
    ]
    for url in urls:
        try:
            r = requests.get(url, headers=HEADERS, timeout=15)
            print(f"[Ticketmaster] Status: {r.status_code} | URL: {url[:60]}")
            if r.status_code != 200:
                continue
            data = r.json()
            evs = data.get("_embedded", {}).get("events", [])
            print(f"[Ticketmaster] Eventos encontrados: {len(evs)}")
            for ev in evs:
                venue_obj = ev.get("_embedded", {}).get("venues", [{}])[0]
                ciudad    = venue_obj.get("city", {}).get("name", "")
                venue     = venue_obj.get("name", "")
                pmin, pmax = _precio(ev)
                plaza     = detectar_plaza(ciudad, venue)
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
        r = requests.get(OCESA_URL, headers=HEADERS, timeout=15)
        print(f"[OCESA] Status: {r.status_code}")
        if r.status_code != 200:
            return []
        posts = r.json()
        print(f"[OCESA] Posts encontrados: {len(posts)}")
        for post in posts:
            titulo = post.get("title", {}).get("rendered", "")
            link   = post.get("link", "")
            fecha  = post.get("date", "")[:10]
            eventos.append({
                "id":         f"ocesa_{post.get('id','')}",
                "nombre":     titulo,
                "fecha":      fecha,
                "ciudad":     "Ciudad de México",
                "venue":      "",
                "plaza":      "cdmx",
                "estado":     "onsale",
                "precio_min": None,
                "precio_max": None,
                "fuente":     "OCESA",
                "url":        link
            })
    except Exception as e:
        print(f"[OCESA] Error: {e}")
    return eventos

def obtener_todos():
    tm  = revisar_ticketmaster()
    oc  = revisar_ocesa()
    print(f"[Total] TM: {len(tm)} | OCESA: {len(oc)}")
    return tm + oc
