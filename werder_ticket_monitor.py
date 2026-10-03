import json
import os
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo


# ============================================================
# Werder Bremen - Mitglieder-Ticketmonitor
# Keine Werder-Anmeldedaten erforderlich.
# ============================================================

TELEGRAM_BOT_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]
TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

GERMANY = ZoneInfo("Europe/Berlin")
STATE_FILE = "state.json"


# Offizielle, aktuell veröffentlichte Bestellfristen
# Quelle: werder.de/tickets/maenner/heimspiele
SALES = [
    {
        "opponent": "RB Leipzig",
        "start": "2026-07-20T10:30:00+02:00",
    },
    {
        "opponent": "FC Augsburg",
        "start": "2026-07-20T10:30:00+02:00",
    },
    {
        "opponent": "SC Paderborn 07",
        "start": "2026-07-20T10:30:00+02:00",
    },
    {
        "opponent": "TSG Hoffenheim",
        "start": "2026-07-20T10:30:00+02:00",
    },
    {
        "opponent": "Hamburger SV",
        "start": "2026-09-07T10:30:00+02:00",
    },
    {
        "opponent": "Borussia M'gladbach",
        "start": "2026-09-21T10:30:00+02:00",
    },
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
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def send_telegram(message):
    url = (
        f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
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

    print("Aktuelle Zeit:", now.isoformat())
    print("Prüfe Werder-Mitglieder-Bestellfristen...")

    for sale in SALES:
        start = datetime.fromisoformat(sale["start"]).astimezone(GERMANY)
        opponent = sale["opponent"]

        # Sekunden bis zum Verkaufsstart
        seconds_until = (start - now).total_seconds()

        print(
            f"{opponent}: Start {start.strftime('%d.%m.%Y %H:%M')}, "
            f"{seconds_until:.0f} Sekunden entfernt"
        )

        # ----------------------------------------------------
        # 15 Minuten vorher
        # ----------------------------------------------------
        reminder_key = f"{opponent}_{sale['start']}_15min"

        if 0 <= seconds_until <= 5 * 60:
            # Falls wir den 15-Minuten-Zeitpunkt verpasst haben,
            # lösen wir trotzdem beim nächsten Lauf aus.
            pass

        if 10 * 60 <= seconds_until <= 20 * 60:
            if reminder_key not in state:
                message = (
                    "🟢 WERDER TICKET-ALARM\n\n"
                    f"🏟️ Heimspiel: Werder – {opponent}\n\n"
                    "⏰ Die Mitglieder-Bestellphase startet "
                    f"in etwa 15 Minuten:\n"
                    f"{start.strftime('%d.%m.%Y um %H:%M Uhr')}\n\n"
                    "👤 Fördermitglieder können bestellen.\n"
                    "👉 Jetzt schon bei werder.de einloggen "
                    "und um 10:30 Uhr bereit sein."
                )

                send_telegram(message)
                state[reminder_key] = now.isoformat()
                save_state(state)

                print("15-Minuten-Warnung gesendet.")

        # ----------------------------------------------------
        # Zum Verkaufsstart
        # ----------------------------------------------------
        start_key = f"{opponent}_{sale['start']}_start"

        if 0 <= seconds_until <= 5 * 60:
            if start_key not in state:
                message = (
                    "🚨 WERDER TICKET-ALARM 🚨\n\n"
                    f"🏟️ Werder – {opponent}\n\n"
                    "🎟️ Die Mitglieder-Bestellphase "
                    "sollte jetzt gestartet sein!\n\n"
                    "👤 Fördermitglieder sind zugelassen.\n"
                    "👉 Jetzt direkt zu werder.de und bestellen."
                )

                send_telegram(message)
                state[start_key] = now.isoformat()
                save_state(state)

                print("Startmeldung gesendet.")

    # Alte Termine müssen nicht gespeichert werden.
    save_state(state)

    print("Fertig.")


if __name__ == "__main__":
    main()