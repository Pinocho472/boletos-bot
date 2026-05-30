import time, sys, os, threading
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from datetime import datetime
from config   import INTERVALO_MIN, TELEGRAM_TOKEN, CHAT_ID, CIUDADES
from scraper  import obtener_todos
from database import cargar_vistos, guardar_vistos, registrar_historial, stats
from notifier import construir_mensaje, enviar, enviar_stats

CICLOS_PARA_STATS = 144
ultima_revision   = None
estado_fuentes    = {"Ticketmaster MX": "🟢 OK", "OCESA": "🟢 OK"}

def procesar(eventos, vistos):
    alertas = []
    for ev in eventos:
        eid, estado = ev["id"], ev["estado"]
        if eid not in vistos:
            alertas.append(("NUEVO", ev))
            vistos[eid] = {"estado": estado, "nombre": ev["nombre"],
                           "fecha": ev.get("fecha",""), "venue": ev.get("venue",""),
                           "plaza": ev.get("plaza","otra"), "precio_min": ev.get("precio_min"),
                           "precio_max": ev.get("precio_max")}
        elif vistos[eid].get("estado") == "offsale" and estado == "onsale":
            alertas.append(("DISPONIBLE", ev))
            vistos[eid]["estado"] = estado
    return alertas, vistos

def construir_status(vistos, eventos_actuales):
    ahora     = datetime.now().strftime("%d/%m/%Y %H:%M")
    s         = stats()
    total_ev  = len(vistos)

    # Precios de eventos activos
    precios = [v["precio_min"] for v in vistos.values() if v.get("precio_min")]
    if precios:
        precio_min = min(precios)
        precio_max = max(p for v in vistos.values() for p in [v.get("precio_max") or 0] if p)
        rango = f"💰 ${int(precio_min):,} - ${int(precio_max):,} MXN"
    else:
        rango = "💰 Sin precios disponibles"

    # Próximo evento
    fechas = [(v.get("fecha",""), v.get("nombre",""), v.get("venue",""), v.get("plaza",""))
              for v in vistos.values() if v.get("fecha","") >= datetime.now().strftime("%Y-%m-%d")]
    fechas.sort()
    if fechas:
        proximo = f"📅 {fechas[0][0]} — {fechas[0][1][:30]}\n   🏟 {fechas[0][2] or 'Sin venue'} {CIUDADES.get(fechas[0][3],{}).get('label','')}"
    else:
        proximo = "📅 Sin eventos próximos detectados"

    # Venues activos
    venues = list(set(v.get("venue","") for v in vistos.values() if v.get("venue","")))[:5]
    venues_txt = "\n".join(f"   • {v}" for v in venues) if venues else "   Sin venues detectados"

    # Por plaza
    cdmx_count = sum(1 for v in vistos.values() if v.get("plaza") == "cdmx")
    mty_count  = sum(1 for v in vistos.values() if v.get("plaza") == "mty")

    msg = (
        f"📡 <b>Status del Bot</b>\n"
        f"{'─'*25}\n\n"
        f"✅ <b>Estado:</b> Activo y corriendo\n"
        f"⏱ <b>Intervalo:</b> Cada {INTERVALO_MIN} minutos\n"
        f"🕐 <b>Última revisión:</b> {ultima_revision or ahora}\n\n"
        f"{'─'*25}\n"
        f"📊 <b>Eventos en seguimiento</b>\n"
        f"🎫 Total: {total_ev} eventos\n"
        f"🏙 CDMX: {cdmx_count} eventos\n"
        f"⛰ MTY: {mty_count} eventos\n\n"
        f"{'─'*25}\n"
        f"📈 <b>Alertas enviadas</b>\n"
        f"✨ Nuevos detectados: {s['nuevos']}\n"
        f"🔥 Boletos liberados: {s['disponibles']}\n\n"
        f"{'─'*25}\n"
        f"💵 <b>Rango de precios activos</b>\n"
        f"{rango}\n\n"
        f"{'─'*25}\n"
        f"📅 <b>Próximo evento</b>\n"
        f"{proximo}\n\n"
        f"{'─'*25}\n"
        f"🏟 <b>Venues con eventos</b>\n"
        f"{venues_txt}\n\n"
        f"{'─'*25}\n"
        f"🌐 <b>Fuentes</b>\n"
        f"  Ticketmaster MX: {estado_fuentes['Ticketmaster MX']}\n"
        f"  OCESA: {estado_fuentes['OCESA']}\n\n"
        f"⏰ {ahora}"
    )
    return msg

def revisar_comandos(vistos_ref):
    offset = 0
    while True:
        try:
            r = __import__("requests").get(
                f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getUpdates",
                params={"offset": offset, "timeout": 30},
                timeout=35
            )
            if r.status_code == 200:
                updates = r.json().get("result", [])
                for u in updates:
                    offset = u["update_id"] + 1
                    msg = u.get("message", {})
                    texto = msg.get("text", "").strip().lower()
                    if texto == "/status":
                        vistos = cargar_vistos()
                        enviar(construir_status(vistos, []))
                    elif texto == "/ayuda" or texto == "/help":
                        enviar(
                            "🤖 <b>Comandos disponibles</b>\n\n"
                            "/status — Ver estado completo del bot\n"
                            "/ayuda — Ver esta lista\n\n"
                            "El bot te avisa automáticamente cuando detecta eventos nuevos o boletos liberados en CDMX y MTY 🎫"
                        )
        except Exception as e:
            print(f"[Comandos] Error: {e}")
        time.sleep(2)

def ciclo(contador, vistos_ref):
    global ultima_revision, estado_fuentes
    ultima_revision = datetime.now().strftime("%d/%m/%Y %H:%M")
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Revisando...")

    vistos  = cargar_vistos()
    eventos = obtener_todos()
    alertas, vistos = procesar(eventos, vistos)
    guardar_vistos(vistos)
    vistos_ref.clear()
    vistos_ref.update(vistos)

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
        "Escribe /status para ver el estado completo\n"
        "Escribe /ayuda para ver comandos\n\n"
        "Te aviso cuando haya novedades 🎫"
    )

    vistos_ref = {}
    t = threading.Thread(target=revisar_comandos, args=(vistos_ref,), daemon=True)
    t.start()

    contador = 0
    while True:
        ciclo(contador, vistos_ref)
        contador += 1
        time.sleep(INTERVALO_MIN * 60)

if __name__ == "__main__":
    main()
