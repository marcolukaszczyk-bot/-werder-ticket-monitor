import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GERMANY = ZoneInfo("Europe/Berlin")
STATE_FILE = "state.json"


# Offizielle Mitglieder-Bestellstarts von Werder Bremen
# Quelle:
# https://www.werder.de/tickets/maenner/heimspiele

SALES = [
    {
        "opponent": "Bayer 04 Leverkusen",
        "start": "2026-10-19T10:30:00+02:00",
    },
    {
        "opponent": "1. FC Union Berlin",
        "start": "2026-11-02T10:30:00+01:00",
    },
    {
        "opponent": "SV Elversberg",
        "start": "2026-11-23T10:30:00+01:00",
    },
]


def load_state():
    if not os.path.exists(STATE_FILE):
        return {}

    try:
        with open(STATE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as file:
        json.dump(state, file, ensure_ascii=False, indent=2)


def send_telegram(message):
    url = (
        f"https://api.telegram.org/"
        f"bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    )

    data = urllib.parse.urlencode({
        "chat_id": TELEGRAM_CHAT_ID,
        "text": message,
    }).encode("utf-8")

    request = urllib.request.Request(
        url,
        data=data,
        method="POST",
    )

    with urllib.request.urlopen(request, timeout=20) as response:
        if response.status != 200:
            raise RuntimeError(
                f"Telegram Fehler: HTTP {response.status}"
            )


def main():
    now = datetime.now(timezone.utc).astimezone(GERMANY)
    state = load_state()

    print("Aktuelle Zeit:", now.strftime("%d.%m.%Y %H:%M:%S"))
    print("Prüfe Mitglieder-Bestellstarts...")

    for sale in SALES:
        opponent = sale["opponent"]
        start = datetime.fromisoformat(sale["start"]).astimezone(GERMANY)

        seconds_until = (start - now).total_seconds()

        print(
            f"{opponent}: "
            f"{start.strftime('%d.%m.%Y %H:%M Uhr')} | "
            f"{seconds_until:.0f} Sekunden"
        )

        # -------------------------------------------------
        # 15-Minuten-Vorabwarnung
        # -------------------------------------------------
        reminder_key = f"{opponent}_{sale['start']}_15min"

        if 10 * 60 <= seconds_until <= 20 * 60:
            if reminder_key not in state:

                message = (
                    "🟢 WERDER TICKET-ALARM\n\n"
                    f"🏟️ Werder – {opponent}\n\n"
                    "⏰ Die Mitglieder-Bestellphase startet "
                    "in etwa 15 Minuten.\n\n"
                    f"📅 {start.strftime('%d.%m.%Y')}\n"
                    f"🕥 {start.strftime('%H:%M Uhr')}\n\n"
                    "👤 Fördermitglieder können bestellen.\n\n"
                    "👉 Bereite dich jetzt vor und "
                    "halte dich auf werder.de bereit."
                )

                send_telegram(message)

                state[reminder_key] = now.isoformat()
                save_state(state)

                print("15-Minuten-Alarm gesendet.")

        # -------------------------------------------------
        # Alarm zum Verkaufsstart
        # -------------------------------------------------
        start_key = f"{opponent}_{sale['start']}_start"

        if 0 <= seconds_until <= 5 * 60:
            if start_key not in state:

                message = (
                    "🚨 WERDER TICKET-ALARM 🚨\n\n"
                    f"🏟️ Werder – {opponent}\n\n"
                    "🎟️ Die Mitglieder-Bestellphase "
                    "startet jetzt!\n\n"
                    "👤 Fördermitglieder können bestellen.\n\n"
                    "👉 Jetzt direkt zu werder.de "
                    "und Bestellung aufgeben."
                )

                send_telegram(message)

                state[start_key] = now.isoformat()
                save_state(state)

                print("Start-Alarm gesendet.")

    save_state(state)
    print("Monitor erfolgreich beendet.")


if __name__ == "__main__":
    main()