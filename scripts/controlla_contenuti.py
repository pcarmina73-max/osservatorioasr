# -*- coding: utf-8 -*-
"""
Controllo quotidiano dei contenuti web sull'Accordo Stato-Regioni 59/CSR:
- notizie, eventi e interviste dal feed di Google News;
- libri da Google Books.

I contenuti trovati vengono aggiunti a dati.json con "approvato": false
(quindi NON compaiono sul sito) e segnalati in novita_contenuti.txt con i
pulsanti Approva / Non approvare. Solo dopo l'approvazione diventano
visibili nella rassegna.
"""

import hashlib
import json
import os
import re
import sys
import xml.etree.ElementTree as ET
from datetime import date
from email.utils import parsedate_to_datetime
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

FILE_DATI = "dati.json"
FILE_NOVITA = "novita_contenuti.txt"

RICERCHE_NEWS = [
    '"accordo stato-regioni" formazione sicurezza',
    '"accordo stato regioni" sicurezza lavoro recepimento',
    '"59/CSR"',
]
RICERCA_LIBRI = 'accordo stato regioni formazione sicurezza lavoro 81/2008'

PAROLE_EVENTO = ("convegno", "seminario", "webinar", "workshop", "incontro",
                 "giornata di studio", "tavola rotonda", "forum", "save the date")
PAROLE_OBBLIGATORIE = ("sicurezza", "formazione", "81", "59")


def _scarica(url):
    req = Request(url, headers={"User-Agent":
                  "OsservatorioASR/1.0 (rassegna quotidiana)"})
    with urlopen(req, timeout=60) as r:
        return r.read()


def _id_di(link, titolo):
    return hashlib.md5((link + "|" + titolo).encode("utf-8")).hexdigest()[:10]


def _pertinente(testo):
    t = testo.lower()
    if "accordo" not in t or ("stato-regioni" not in t and
                              "stato regioni" not in t and "csr" not in t):
        return False
    return any(p in t for p in PAROLE_OBBLIGATORIE)


def _classifica(titolo):
    t = titolo.lower()
    if "intervista" in t:
        return "intervista"
    # attenzione: "conferenza stato-regioni" è l'organo, non un evento
    t_senza = t.replace("conferenza stato-regioni", "").replace(
        "conferenza stato regioni", "")
    if any(p in t_senza for p in PAROLE_EVENTO) or "conferenza" in t_senza:
        return "evento"
    return "news"


def cerca_news():
    trovati = []
    for query in RICERCHE_NEWS:
        url = ("https://news.google.com/rss/search?q=" + quote_plus(query) +
               "&hl=it&gl=IT&ceid=IT:it")
        try:
            radice = ET.fromstring(_scarica(url))
        except Exception as e:
            print(f"Avviso: feed non raggiungibile per {query!r} ({e})",
                  file=sys.stderr)
            continue
        for item in radice.iter("item"):
            titolo = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            fonte = (item.findtext("source") or "").strip()
            pub = item.findtext("pubDate") or ""
            if not titolo or not link or not _pertinente(titolo):
                continue
            try:
                dt = parsedate_to_datetime(pub)
                data = dt.strftime("%d/%m/%Y")
            except Exception:
                data = ""
            trovati.append({
                "id": _id_di(link, titolo),
                "tipo": _classifica(titolo),
                "titolo": titolo,
                "fonte": fonte,
                "data": data,
                "link": link,
                "descr": "",
                "approvato": False,
            })
    return trovati


def cerca_libri():
    url = ("https://www.googleapis.com/books/v1/volumes?q=" +
           quote_plus(RICERCA_LIBRI) + "&langRestrict=it&maxResults=20"
           "&orderBy=newest")
    try:
        dati = json.loads(_scarica(url))
    except Exception as e:
        print(f"Avviso: Google Books non raggiungibile ({e})", file=sys.stderr)
        return []
    trovati = []
    for voce in dati.get("items", []):
        info = voce.get("volumeInfo", {})
        titolo = info.get("title", "")
        descr = info.get("description", "")
        if not _pertinente(titolo + " " + descr):
            continue
        link = info.get("infoLink") or info.get("canonicalVolumeLink") or ""
        if not link:
            continue
        pub = info.get("publishedDate", "")     # "2025" o "2025-06-01"
        m = re.match(r"(\d{4})(?:-(\d{2}))?(?:-(\d{2}))?", pub)
        data = (f"{m.group(3) or '01'}/{m.group(2) or '01'}/{m.group(1)}"
                if m else "")
        autori = ", ".join(info.get("authors", []))
        editore = info.get("publisher", "")
        dettagli = " · ".join(x for x in (autori, editore,
                                          m.group(1) if m else "") if x)
        trovati.append({
            "id": _id_di(link, titolo),
            "tipo": "libro",
            "titolo": titolo,
            "fonte": editore,
            "data": data,
            "link": link,
            "descr": dettagli,
            "approvato": False,
        })
    return trovati


def pulsanti(item):
    repo = os.environ.get("GITHUB_REPOSITORY", "")
    if not repo:
        return ""
    base = f"https://github.com/{repo}/issues/new"
    ap = (base + "?title=" + quote_plus(f"APPROVA-ITEM: {item['id']}") +
          "&body=" + quote_plus("Pubblica questo contenuto nella rassegna. "
                                "Premi il pulsante verde per applicare."))
    no = (base + "?title=" + quote_plus(f"RIFIUTA-ITEM: {item['id']}") +
          "&body=" + quote_plus("Scarta questo contenuto. Premi il "
                                "pulsante verde per applicare."))
    return f"  ➜ [✅ Approva]({ap}) · [❌ Non approvare]({no})"


ETICHETTA = {"news": "News", "evento": "Evento",
             "intervista": "Intervista", "libro": "Libro"}


def main():
    dati = json.load(open(FILE_DATI, encoding="utf-8"))
    contenuti = dati.setdefault("contenuti", [])
    esistenti = {c["id"] for c in contenuti}
    esistenti_link = {c["link"] for c in contenuti}

    candidati = cerca_news() + cerca_libri()

    nuovi = []
    for c in candidati:
        if c["id"] in esistenti or c["link"] in esistenti_link:
            continue
        esistenti.add(c["id"]); esistenti_link.add(c["link"])
        contenuti.append(c)
        nuovi.append(c)

    if not nuovi:
        print("Nessun nuovo contenuto rilevato.")
        return

    json.dump(dati, open(FILE_DATI, "w", encoding="utf-8"),
              ensure_ascii=False, indent=2)

    with open(FILE_NOVITA, "w", encoding="utf-8") as f:
        f.write("La rassegna automatica ha trovato nuovi contenuti "
                "in attesa di approvazione (non ancora visibili sul "
                "sito):\n\n")
        for c in nuovi:
            f.write(f"- **[{ETICHETTA[c['tipo']]}]** {c['titolo']}"
                    f"{' — ' + c['fonte'] if c['fonte'] else ''}"
                    f"{' (' + c['data'] + ')' if c['data'] else ''}\n"
                    f"  Link: {c['link']}\n{pulsanti(c)}\n\n")
        f.write("---\n**Come decidere:** apri il link, valuta il "
                "contenuto, poi clicca \u2705 Approva (comparir\u00e0 "
                "nella sezione giusta della rassegna) oppure \u274c Non "
                "approvare (verr\u00e0 scartato). Conferma col pulsante "
                "verde nella pagina che si apre.\n")

    print(f"Trovati {len(nuovi)} nuovi contenuti:")
    for c in nuovi:
        print(f"- [{c['tipo']}] {c['titolo']}")


if __name__ == "__main__":
    main()
