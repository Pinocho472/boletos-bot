import requests
from datetime import datetime
from config import TELEGRAM_TOKEN, CHAT_ID, CIUDADES

def _fmt_precio(mn, mx):
    if mn and mx: return f"💰 ${int(mn):,} - ${int(mx):,} MXN"
    if mn:        return f"💰 Desde ${int(mn):,} MXN"
    return ""

def _fmt_plaza(plaza):
    return CIUDADES.get(plaza, {}).get("label", "📍 México")

def construir_mensaje(evento, tipo):
    header = "🎫 <b>NUEVO EVENTO</b>" if tipo == "NUEVO" else "🔥 <b>¡BOLETOS DISPONIBLES!</b>"
    precio = _fmt_precio(evento.get('precio_min'), evento.get('precio_max'))
    precio_line = f"{precio}\n" if precio else ""
    return (
        f"{header} {_fmt_plaza(evento.get('plaza','otra'))}\n\n"
        f"🎤 <b>{evento['nombre']}</b>\n"
        f"📅 {evento['fecha']}\n"
        f"📍 {evento['ciudad']}\n"
        f"{precio_line}"
        f"🔗 {evento['url']}"
    )

def enviar(mensaje):
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage",
            json={"chat_id": CHAT_ID, "text": mensaje, "parse_mode": "HTML"},
            timeout=10
        )
        return r.status_code == 200
    except Exception as e:
        print(f"[Telegram] Error: {e}")
        return False

def enviar_stats(s):
    por_plaza = "\n".join(
        f"  {CIUDADES.get(p,{}).get('label', p)}: {n}"
        for p, n in s["por_plaza"].items()
    )
    enviar(
        f"📊 <b>Resumen diario del bot</b>\n\n"
        f"🎫 Total alertas: {s['total']}\n"
        f"✨ Eventos nuevos: {s['nuevos']}\n"
        f"🔥 Boletos liberados: {s['disponibles']}\n\n"
        f"<b>Por plaza:</b>\n{por_plaza or '  Sin datos aún'}"
    )

