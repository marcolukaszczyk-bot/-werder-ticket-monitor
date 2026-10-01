import os

import json

import requests

from bs4 import BeautifulSoup

WERDER_URL = "https://www.werder.de/tickets/maenner/heimspiele"

STATE_FILE = "state.json"

TELEGRAM_TOKEN = os.environ["TELEGRAM_BOT_TOKEN"]

TELEGRAM_CHAT_ID = os.environ["TELEGRAM_CHAT_ID"]

def get_page():

    response = requests.get(

        WERDER_URL,

        headers={

            "User-Agent": "Mozilla/5.0 WerderTicketMonitor/1.0"

        },

        timeout=30

    )

    response.raise_for_status()

    return response.text

def send_telegram(message):

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"

    requests.post(

        url,

        data={

            "chat_id": TELEGRAM_CHAT_ID,

            "text": message,

            "disable_web_page_preview": False

        },

        timeout=30

    ).raise_for_status()

def load_state():

    if not os.path.exists(STATE_FILE):

        return {}

    with open(STATE_FILE, "r", encoding="utf-8") as f:

        return json.load(f)

def save_state(state):

    with open(STATE_FILE, "w", encoding="utf-8") as f:

        json.dump(state, f, ensure_ascii=False, indent=2)

def main():

    html = get_page()

    soup = BeautifulSoup(html, "html.parser")

    text = soup.get_text(" ", strip=True)

    previous = load_state()

    # Wir überwachen die aktuellen Bearbeitungsstände.

    interesting_games = [

        "RB Leipzig",

        "FC Augsburg",

        "SC Paderborn 07",

        "TSG Hoffenheim",

        "Hamburger SV",

        "Borussia M'gladbach",

        "Bayer 04 Leverkusen",

        "1. FC Union Berlin",

        "SV Elversberg",

    ]

    current = {}

    for game in interesting_games:

        position = text.find(game)

        if position == -1:

            continue

        section = text[position:position + 500]

        statuses = [

            "Bestellphase läuft",

            "in Bearbeitung",

            "Bestellphase abgeschlossen",

            "Bestellphase beendet",

            "Bearbeitung abgeschlossen",

        ]

        status = "unbekannt"

        for possible_status in statuses:

            if possible_status in section:

                status = possible_status

                break

        current[game] = status

    # Beim ersten Lauf nur Zustand speichern.

    # Dadurch bekommst du nicht sofort eine Menge alter Meldungen.

    if not previous:

        save_state(current)

        print("Erster Lauf abgeschlossen. Ausgangszustand gespeichert.")

        return

    # Änderungen erkennen.

    for game, status in current.items():

        old_status = previous.get(game)

        if status != old_status:

            # Besonders interessant für dich:

            # Bestellphase läuft / Bearbeitung beginnt.

            if status in ["Bestellphase läuft", "in Bearbeitung"]:

                message = (

                    "🎟️ WERDER TICKET-ALARM\n\n"

                    f"SV Werder Bremen – {game}\n\n"

                    f"Status: {status}\n\n"

                    "Die Mitglieder-Bestellphase könnte geöffnet "

                    "bzw. bearbeitet werden.\n\n"

                    "👉 Jetzt prüfen:\n"

                    f"{WERDER_URL}"

                )

                send_telegram(message)

    save_state(current)

if __name__ == "__main__":

    main()