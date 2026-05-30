import time, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from datetime import datetime
from config   import INTERVALO_MIN, TELEGRAM_TOKEN, CHAT_ID
from scraper  import obtener_todos
from database import cargar_vistos, guardar_vistos, registrar_historial, stats
from notifier import construir_mensaje, enviar, enviar_stats

CICLOS_PARA_STATS = 144  # resumen cada ~24 hrs

def procesar(eventos, vistos):
    alertas = []
    for ev in eventos:
        eid, estado = ev["id"], ev["estado"]
        if eid not in vistos:
            alertas.append(("NUEVO", ev))
            vistos[eid] = {"estado": estado, "nombre": ev["nombre"]}
        elif vistos[eid].get("estado") == "offsale" and estado == "onsale":
            alertas.append(("DISPONIBLE", ev))
            vistos[eid]["estado"] = estado
    return alertas, vistos

def ciclo(contador):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Revisando...")
    vistos  = cargar_vistos()
    eventos = obtener_todos()
    alertas, vistos = procesar(eventos, vistos)
    guardar_vistos(vistos)

    for tipo, ev in alertas:
        registrar_historial(ev, tipo)
        if enviar(construir_mensaje(ev, tipo)):
            print(f"  ✅ {tipo}: {ev['nombre']} ({ev.get('plaza','?')})")
        time.sleep(1)

    if not alertas:
        print(f"  Sin cambios — {len(eventos)} eventos monitoreados.")

    if contador > 0 and contador % CICLOS_PARA_STATS == 0:
        enviar_stats(stats())

def main():
    if not TELEGRAM_TOKEN or not CHAT_ID:
        print("❌ Falta TELEGRAM_TOKEN o CHAT_ID"); return

    print(f"🤖 Bot PRO iniciado | Intervalo: {INTERVALO_MIN} min")
    enviar(
        "🤖 <b>Bot de boletos PRO activo</b>\n\n"
        "Monitoreando Ticketmaster MX y OCESA\n"
        "📍 Plazas: 🏙 CDMX y ⛰ MTY\n"
        "📊 Resumen diario automático\n\n"
        "Te aviso cuando haya novedades 🎫"
    )
    contador = 0
    while True:
        ciclo(contador)
        contador += 1
        time.sleep(INTERVALO_MIN * 60)

if __name__ == "__main__":
    main()
