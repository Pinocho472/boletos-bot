import requests
import os
from datetime import datetime, timedelta

NEWS_API_KEY = os.environ.get("NEWS_API_KEY", "")
NEWS_URL     = "https://newsapi.org/v2/everything"

HEADERS = {"User-Agent": "Mozilla/5.0"}

QUERIES_MTY = [
    "concierto Monterrey",
    "boletos Monterrey concierto",
    "preventa Monterrey",
]

QUERIES_CDMX = [
    "concierto CDMX",
    "concierto Ciudad de Mexico",
    "preventa CDMX boletos",
]

def buscar_noticias(query, plaza):
    eventos = []
    try:
        desde = (datetime.now() - timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%S")
        params = {
            "q":          query,
            "language":   "es",
            "sortBy":     "publishedAt",
            "from":       desde,
            "pageSize":   10,
            "apiKey":     NEWS_API_KEY
        }
        r = requests.get(NEWS_URL, params=params, headers=HEADERS, timeout=15)
        print(f"[NewsAPI] '{query}' → Status: {r.status_code}")
        if r.status_code != 200:
            return []
        
        articulos = r.json().get("articles", [])
        print(f"[NewsAPI] '{query}' → {len(articulos)} noticias")
        
        for art in articulos:
            titulo = art.get("title", "")
            if not titulo or titulo == "[Removed]":
                continue
            eventos.append({
                "id":         f"news_{plaza}_{abs(hash(titulo))}",
                "nombre":     titulo,
                "fecha":      art.get("publishedAt", "")[:10],
                "ciudad":     "Monterrey" if plaza == "mty" else "Ciudad de México",
                "venue":      art.get("source", {}).get("name", ""),
                "plaza":      plaza,
                "estado":     "onsale",
                "precio_min": None,
                "precio_max": None,
                "fuente":     f"📰 {art.get('source', {}).get('name', 'Noticia')}",
                "url":        art.get("url", "")
            })
    except Exception as e:
        print(f"[NewsAPI] Error: {e}")
    return eventos

def obtener_todos():
    eventos = []
    
    for q in QUERIES_MTY:
        eventos += buscar_noticias(q, "mty")
    
    for q in QUERIES_CDMX:
        eventos += buscar_noticias(q, "cdmx")
    
    # Deduplicar por ID
    vistos = set()
    unicos = []
    for ev in eventos:
        if ev["id"] not in vistos:
            vistos.add(ev["id"])
            unicos.append(ev)
    
    print(f"[Total] {len(unicos)} noticias únicas de conciertos")
    return unicos
