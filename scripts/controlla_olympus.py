# -*- coding: utf-8 -*-
"""
Controllo quotidiano della banca dati Olympus (Università di Urbino):
cerca nuovi atti regionali di recepimento dell'Accordo Stato-Regioni
17/04/2025 (Rep. 59/CSR) e aggiorna dati.json.

Gli atti trovati vengono inseriti con "verificato": false e segnalati
nel file novita.txt, che il workflow usa per aprire una issue su GitHub.
La conferma finale resta umana: dopo il controllo, modifica dati.json
mettendo "verificato": true e ripulendo la nota.
"""

import json
import os
import re
import sys
import html
from datetime import date
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

URL_OLYMPUS = ("https://olympus.uniurb.it/index.php"
               "?option=com_content&view=category&id=27&Itemid=137")
BASE = "https://olympus.uniurb.it"
FILE_DATI = "dati.json"
FILE_NOVITA = "novita.txt"

MESI = {"gennaio": 1, "febbraio": 2, "marzo": 3, "aprile": 4,
        "maggio": 5, "giugno": 6, "luglio": 7, "agosto": 8,
        "settembre": 9, "ottobre": 10, "novembre": 11, "dicembre": 12}

# nome come appare su Olympus -> nome usato in dati.json
NOMI = {
    "abruzzo": "Abruzzo", "basilicata": "Basilicata", "calabria": "Calabria",
    "campania": "Campania", "emilia-romagna": "Emilia-Romagna",
    "emilia romagna": "Emilia-Romagna",
    "friuli-venezia giulia": "Friuli-Venezia Giulia",
    "friuli venezia giulia": "Friuli-Venezia Giulia",
    "lazio": "Lazio", "liguria": "Liguria", "lombardia": "Lombardia",
    "marche": "Marche", "molise": "Molise", "piemonte": "Piemonte",
    "puglia": "Puglia", "sardegna": "Sardegna", "sicilia": "Sicilia",
    "siciliana": "Sicilia", "toscana": "Toscana", "umbria": "Umbria",
    "valle d'aosta": "Valle d'Aosta", "valle d’aosta": "Valle d'Aosta",
    "veneto": "Veneto", "trento": "P.A. Trento", "bolzano": "P.A. Bolzano",
}


def scarica_pagina(url):
    req = Request(url, headers={"User-Agent":
                  "OsservatorioRecepimenti/1.0 (controllo quotidiano)"})
    with urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8", errors="replace")


def estrai_articoli(pagina):
    """Restituisce [(titolo, url_assoluto), ...] degli articoli in elenco."""
    articoli = []
    for href, testo in re.findall(
            r'<a[^>]+href="([^"]*view=article[^"]*)"[^>]*>(.*?)</a>',
            pagina, re.S):
        titolo = html.unescape(re.sub(r"<[^>]+>", " ", testo))
        titolo = re.sub(r"\s+", " ", titolo).strip()
        if len(titolo) < 25:          # scarta link di servizio
            continue
        url = html.unescape(href)
        if url.startswith("/"):
            url = BASE + url
        articoli.append((titolo, url))
    return articoli


def riguarda_accordo(titolo):
    t = titolo.lower()
    if "accordo" not in t:
        return False
    return any(chiave in t for chiave in
               ("59", "17 aprile 2025", "17.04.2025", "recepimento"))


def estrai_dettagli(titolo):
    """Da un titolo Olympus ricava (regione, atto, data gg/mm/aaaa)."""
    regione = None
    m = re.match(r"\s*(?:regione|provincia autonoma di)\s+([^,]+),", titolo,
                 re.I)
    if m:
        chiave = m.group(1).strip().lower()
        regione = NOMI.get(chiave)
        if not regione:                       # match parziale (es. "siciliana")
            for k, v in NOMI.items():
                if k in chiave:
                    regione = v
                    break
    atto, data = "", ""
    m = re.search(r"(DGR|D\.G\.R\.|D\.A\.|Decreto|Deliberazione|"
                  r"L\.R\.|Legge regionale)[^0-9]{0,20}"
                  r"(\d{1,2})\s+(gennaio|febbraio|marzo|aprile|maggio|giugno|"
                  r"luglio|agosto|settembre|ottobre|novembre|dicembre)\s+"
                  r"(\d{4})\s*,?\s*n\.?\s*([0-9][\w./-]*)",
                  titolo, re.I)
    if m:
        tipo, g, mese, anno, num = m.groups()
        atto = f"{tipo} n. {num}"
        data = f"{int(g):02d}/{MESI[mese.lower()]:02d}/{anno}"
    return regione, atto, data


def link_decisione(regione):
    """Link 'Approva' / 'Non approvare' da mostrare nella notifica."""
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        return ""
    base = f"https://github.com/{repo}/issues/new"
    ap = (base + "?title=" + quote_plus(f"APPROVA: {regione}") +
          "&body=" + quote_plus(
              "Confermo: l'atto è il recepimento dell'Accordo 59/CSR. "
              "Premi il pulsante verde per applicare la decisione."))
    no = (base + "?title=" + quote_plus(f"RIFIUTA: {regione}") +
          "&body=" + quote_plus(
              "L'atto NON è il recepimento dell'Accordo 59/CSR: annullare "
              "la segnalazione. Premi il pulsante verde per applicare."))
    return f"  ➜ [✅ Approva]({ap}) · [❌ Non approvare]({no})"


def main():
    dati = json.load(open(FILE_DATI, encoding="utf-8"))
    per_nome = {r["nome"]: r for r in dati["regioni"]}
    oggi = date.today().strftime("%d/%m/%Y")

    try:
        pagina = scarica_pagina(URL_OLYMPUS)
    except Exception as e:
        print(f"ERRORE: impossibile scaricare Olympus ({e})", file=sys.stderr)
        sys.exit(0)   # non far fallire il workflow per un problema di rete

    novita = []
    for titolo, url in estrai_articoli(pagina):
        if not riguarda_accordo(titolo):
            continue
        regione, atto, data = estrai_dettagli(titolo)
        if not regione or regione not in per_nome:
            continue
        voce = per_nome[regione]

        # già censito? (stesso numero di atto, o già recepito e verificato)
        if atto and atto in voce.get("atto", ""):
            continue
        if voce["stato"] == "recepito" and voce.get("verificato", True):
            continue
        # già rilevato in un giro precedente con lo stesso link
        if url and url == voce.get("link", ""):
            continue

        voce["stato"] = "recepito"
        if atto:
            voce["atto"] = atto
        if data:
            voce["data"] = data
        voce["link"] = url
        voce["verificato"] = False
        voce["nota"] = (f"Rilevato automaticamente da Olympus il {oggi} — "
                        f"in attesa di verifica. Titolo: {titolo}")

        descr = f"{regione}: {atto or 'atto da identificare'}" + \
                (f" del {data}" if data else "")
        dati["changelog"].insert(0, {
            "d": oggi,
            "t": f"[automatico] Possibile recepimento rilevato — {descr}. "
                 f"In attesa di verifica."})
        novita.append(f"- **{descr}**\n  Titolo: {titolo}\n  Link: {url}\n"
                      + link_decisione(regione))

    if novita:
        dati["meta"]["aggiornato"] = oggi
        dati["meta"]["ultimo_controllo"] = oggi
        json.dump(dati, open(FILE_DATI, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        with open(FILE_NOVITA, "w", encoding="utf-8") as f:
            f.write("Il controllo quotidiano su Olympus ha rilevato "
                    "possibili nuovi recepimenti:\n\n")
            f.write("\n\n".join(novita))
            f.write("\n\n---\n**Come decidere:** apri il link all'atto e "
                    "verifica che sia davvero il recepimento del 59/CSR, "
                    "poi clicca \u2705 Approva oppure \u274c Non approvare: "
                    "si apre una pagina gi\u00e0 compilata, conferma col "
                    "pulsante verde e il sito si aggiorna da solo in un "
                    "paio di minuti.\n")
        print(f"Trovate {len(novita)} novità:")
        print("\n".join(novita))
    else:
        print("Nessuna novità rilevata.")


if __name__ == "__main__":
    main()
