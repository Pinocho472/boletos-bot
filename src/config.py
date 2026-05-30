import os

TELEGRAM_TOKEN   = os.environ.get("TELEGRAM_TOKEN", "")
CHAT_ID          = os.environ.get("CHAT_ID", "")
INTERVALO_MIN    = int(os.environ.get("INTERVALO_MIN", 10))
CIUDADES_ACTIVAS = ["cdmx", "mty"]

CIUDADES = {
    "cdmx": {
        "label": "🏙 CDMX",
        "keywords": ["ciudad de mexico","cdmx","mexico city","df","naucalpan","ecatepec","tlalnepantla"],
        "venues":   ["foro sol","auditorio nacional","palacio de los deportes","arena cdmx",
                     "forum buenavista","coca cola flow","pepsi center","teatro metropolitan",
                     "el plaza condesa","lunario"]
    },
    "mty": {
        "label": "⛰ MTY",
        "keywords": ["monterrey","san pedro garza garcia","san nicolas","guadalupe",
                     "apodaca","santa catarina","nuevo leon"],
        "venues":   ["arena monterrey","auditorio banamex","explanada cintermex",
                     "parque fundidora","cafe iguana","el barco","arena santa catarina"]
    }
}

FUENTES = [
    {
        "nombre": "Ticketmaster MX",
        "url":    "https://www.ticketmaster.com.mx/json/search/event/get?apikey=GkB8Z037ZfqbLCNtZViAgrpgfPAwMgD1&countryCode=MX&size=20&page=0",
        "tipo":   "ticketmaster"
    },
    {
        "nombre": "OCESA",
        "url":    "https://ocesa.com.mx/wp-json/wp/v2/posts?per_page=10&categories=eventos",
        "tipo":   "wordpress"
    },
]
