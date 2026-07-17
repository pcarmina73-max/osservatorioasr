# -*- coding: utf-8 -*-
"""
Applica a dati.json la decisione presa cliccando i pulsanti della notifica.

Uso: python scripts/applica_decisione.py "APPROVA: Campania"
     python scripts/applica_decisione.py "RIFIUTA: Campania"

APPROVA -> l'atto rilevato automaticamente diventa verificato: la nota
           viene ripulita e il changelog registra la conferma.
RIFIUTA -> la segnalazione automatica viene annullata: la regione torna
           allo stato "da_verificare" (nessun atto reperito).
"""

import json
import re
import sys
from datetime import date

FILE_DATI = "dati.json"


def main():
    if len(sys.argv) < 2:
        sys.exit("Uso: applica_decisione.py \"APPROVA: NomeRegione\" "
                 "oppure \"APPROVA-ITEM: id\"")

    m = re.match(r"\s*(APPROVA|RIFIUTA)(-ITEM)?\s*:\s*(.+?)\s*$",
                 sys.argv[1], re.I)
    if not m:
        sys.exit(f"Titolo non riconosciuto: {sys.argv[1]!r}")
    azione = m.group(1).upper()
    su_item = bool(m.group(2))
    oggetto = m.group(3)

    dati = json.load(open(FILE_DATI, encoding="utf-8"))
    oggi = date.today().strftime("%d/%m/%Y")

    if su_item:
        decidi_contenuto(dati, azione, oggetto, oggi)
    else:
        decidi_regione(dati, azione, oggetto, oggi)

    dati["meta"]["aggiornato"] = oggi
    json.dump(dati, open(FILE_DATI, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)


ETICHETTA = {"news": "news", "evento": "evento",
             "intervista": "intervista", "libro": "libro"}


def decidi_contenuto(dati, azione, item_id, oggi):
    contenuti = dati.get("contenuti", [])
    voce = next((c for c in contenuti if c.get("id") == item_id), None)
    if voce is None:
        sys.exit(f"Contenuto non trovato in dati.json: {item_id!r}")

    if azione == "APPROVA":
        if voce.get("approvato"):
            print(f"Contenuto {item_id}: già pubblicato.")
            return
        voce["approvato"] = True
        dati["changelog"].insert(0, {
            "d": oggi,
            "t": (f"Rassegna: pubblicat{'o' if voce.get('tipo') != 'news' else 'a'} "
                  f"{ETICHETTA.get(voce.get('tipo'), 'contenuto')} — "
                  f"\u201c{voce.get('titolo', '')[:90]}\u201d.")})
        print(f"Contenuto {item_id}: pubblicato nella rassegna.")
    else:
        voce["approvato"] = False
        voce["scartato"] = True     # resta in archivio: non verrà riproposto
        print(f"Contenuto {item_id}: scartato.")


def decidi_regione(dati, azione, regione, oggi):
    voce = next((r for r in dati["regioni"]
                 if r["nome"].lower() == regione.lower()), None)
    if voce is None:
        sys.exit(f"Regione non trovata in dati.json: {regione!r}")

    if azione == "APPROVA":
        if voce.get("verificato", True):
            print(f"{voce['nome']}: già verificata, nessuna modifica.")
            return
        voce["verificato"] = True
        # trasformo la nota provvisoria in una nota pulita
        voce["nota"] = re.sub(
            r"^Rilevato automaticamente.*?Titolo:\s*",
            "", voce.get("nota", "")).strip()
        if voce["nota"]:
            voce["nota"] += " (fonte: Olympus - Univ. Urbino)."
        dati["changelog"].insert(0, {
            "d": oggi,
            "t": (f"Confermato il recepimento: {voce['nome']}, "
                  f"{voce.get('atto', 'atto')} del "
                  f"{voce.get('data', 'data n.d.')}.")})
        esito = "approvazione applicata"
    else:  # RIFIUTA
        voce.update({"stato": "da_verificare", "atto": "", "data": "",
                     "nota": "", "link": "", "verificato": True})
        dati["changelog"].insert(0, {
            "d": oggi,
            "t": (f"Annullata dopo verifica la segnalazione automatica "
                  f"per {voce['nome']}.")})
        esito = "segnalazione annullata"

    print(f"{voce['nome']}: {esito}.")


if __name__ == "__main__":
    main()
