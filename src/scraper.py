import requests
import re
import json
from config import CIUDADES, CIUDADES_ACTIVAS

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "es-MX,es;q=0.9",
}

OCESA_URL = "https://ocesa.com.mx/wp-json/wp/v2/posts?per_page=20&categories=eventos"

TM_URLS = {
    "mty": "https://www.ticketmaster.com.mx/browse/mas-conciertos-catid-52/conciertos-rid-10001/monterrey-dma-803",
    "cdmx": "https://www.ticketmaster.com.mx/browse/mas-conciertos-catid-52/conciertos-rid-10001/todo-mexico-dma-801",
}

def detectar_plaza(ciudad, venue=""):
    texto = (ciudad + " " + venue).lower()
    for clave, datos in CIUDADES.items():
        if clave not in CIUDADES_ACTIVAS:
            continue
        if any(k in texto for k in datos["keywords"] + datos["venues"]):
            return clave
    return "otra"

def revisar_ticketmaster():
    eventos = []
    for plaza, url in TM_URLS.items():
        try:
            r = requests.get(url, headers=HEADERS, timeout=20)
            print(f"[TM-{plaza.upper()}] Status: {r.status_code}")
            if r.status_code != 200:
                continue

            # Buscar JSON embebido en el HTML
            match = re.search(r'__NEXT_DATA__\s*=\s*({.+?})\s*</script>', r.text, re.DOTALL)
            if not match:
                # Intentar parsear eventos desde el HTML directamente
                # Buscar patrones de eventos en el HTML
                nombres = re.findall(r'"name"\s*:\s*"([^"]{5,80})"', r.text)
                fechas  = re.findall(r'"localDate"\s*:\s*"(\d{4}-\d{2}-\d{2})"', r.text)
                ids     = re.findall(r'"id"\s*:\s*"([A-Z0-9]{16,})"', r.text)
                
                print(f"[TM-{plaza.upper()}] Encontrados {len(ids)} eventos via HTML")
                for i, eid in enumerate(ids[:30]):
                    eventos.append({
                        "id":         f"tm_{plaza}_{eid}",
                        "nombre":     nombres[i] if i < len(nombres) else f"Evento {eid}",
                        "fecha":      fechas[i] if i < len(fechas) else "",
                        "ciudad":     "Monterrey" if plaza == "mty" else "Ciudad de México",
                        "venue":      "",
                        "plaza":      plaza,
                        "estado":     "onsale",
                        "precio_min": None,
                        "precio_max": None,
                        "fuente":     "Ticketmaster MX",
                        "url":        url
                    })
                continue

            data = json.loads(match.group(1))
            evs  = (data.get("props", {})
                       .get("pageProps", {})
                       .get("events", []))
            print(f"[TM-{plaza.upper()}] Eventos en JSON: {len(evs)}")

            for ev in evs:
                venue   = ev.get("venue", {}).get("name", "")
                ciudad  = ev.get("venue", {}).get("city", "")
                eventos.append({
                    "id":         ev.get("id", f"tm_{plaza}_{len(eventos)}"),
                    "nombre":     ev.get("name", ""),
                    "fecha":      ev.get("startDate", "")[:10],
                    "ciudad":     ciudad,
                    "venue":      venue,
                    "plaza":      plaza,
                    "estado":     "onsale" if not ev.get("soldOut") else "offsale",
                    "precio_min": ev.get("minPrice"),
                    "precio_max": ev.get("maxPrice"),
                    "fuente":     "Ticketmaster MX",
                    "url":        ev.get("url", url)
                })
        except Exception as e:
            print(f"[TM-{plaza.upper()}] Error: {e}")
    return eventos

def revisar_ocesa():
    eventos = []
    try:
        r = requests.get(OCESA_URL, headers=HEADERS, timeout=15)
        print(f"[OCESA] Status: {r.status_code}")
        if r.status_code != 200:
            return []
        posts = r.json()
        print(f"[OCESA] Posts: {len(posts)}")
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
    tm = revisar_ticketmaster()
    oc = revisar_ocesa()
    print(f"[Total] TM:{len(tm)} OCESA:{len(oc)}")
    return tm + oc
