# OsservatorioASR.it — istruzioni

Questo pacchetto contiene il sito e il sistema di aggiornamento automatico.

## Cosa c'è dentro

- `index.html` — la home: mappa, schede regionali, andamento, aggiornamenti
- `accordo.html`, `news.html`, `eventi.html`, `interviste.html`, `libri.html`, `storia.html` — le sottopagine (ognuna con proprio indirizzo, titolo e descrizione: meglio per Google)
- `style.css` e `comune.js` — grafica e struttura condivise: intestazione, menu e piè di pagina si modificano qui, una volta sola per tutte le pagine
- `dati.json` — i dati: stati regionali, atti, changelog. **È l'unico file da toccare per aggiornare i contenuti**
- `scripts/controlla_olympus.py` — il "robot" che ogni giorno controlla la banca dati Olympus dell'Università di Urbino (recepimenti regionali)
- `scripts/controlla_contenuti.py` — il robot della rassegna: ogni giorno cerca su Google News notizie, eventi e interviste sull'Accordo, e su Google Books i libri dedicati
- `scripts/applica_decisione.py` — applica ai dati la tua decisione (Approva / Non approvare)
- `.github/workflows/controllo-olympus.yml` — la pianificazione che esegue il robot ogni mattina
- `.github/workflows/gestione-approvazioni.yml` — l'automatismo che reagisce ai tuoi clic di approvazione

## Come funziona l'automazione

Ogni giorno alle 7:30 (ora italiana estiva) il robot:
1. legge la prima pagina della sezione regionale di Olympus;
2. cerca nei titoli gli atti riferiti all'Accordo (parole chiave: accordo + 59 / 17 aprile 2025 / recepimento);
3. se trova un atto nuovo per una regione non ancora censita, aggiorna `dati.json`: la regione diventa "Recepito" con l'etichetta gialla **"rilevamento automatico — da confermare"**, il changelog registra la novità e il sito si aggiorna da solo;
4. apre una **issue** nel repository per avvisarti (GitHub ti manda una mail se hai le notifiche attive).

**Il tuo compito quando arriva una notifica:** apri il link all'atto e verifica che sia davvero il recepimento del 59/CSR. Poi, nella notifica stessa, clicca uno dei due pulsanti:

- **✅ Approva** — si apre una pagina già compilata: premi il pulsante verde di conferma e l'automatismo fa il resto (l'etichetta "da confermare" sparisce, la nota viene ripulita, il changelog registra la conferma, il sito si aggiorna in un paio di minuti).
- **❌ Non approvare** — stessa procedura: la segnalazione viene annullata e la regione torna a "Nessun atto reperito".

Non serve toccare `dati.json` a mano (resta comunque possibile, per correzioni fini). **Sicurezza:** i pulsanti funzionano solo se a cliccarli è il proprietario del repository o un collaboratore autorizzato; chiunque altro riceve un rifiuto automatico senza che i dati vengano toccati.


## La rassegna automatica (news, eventi, interviste, libri)

Ogni giorno, insieme al controllo dei recepimenti, il robot della rassegna:
1. interroga **Google News** (notizie in italiano sull'Accordo Stato-Regioni e la formazione sicurezza) e **Google Books** (volumi dedicati);
2. scarta ciò che non è pertinente e classifica il resto: **news**, **evento** (convegni, seminari, webinar), **intervista**, **libro**;
3. aggiunge i contenuti a `dati.json` come **non approvati**: NON compaiono sul sito finché non li approvi tu;
4. apre una issue con l'elenco e, per ciascun contenuto, i pulsanti **✅ Approva / ❌ Non approvare** (stessa modalità dei recepimenti).

Approvato → il contenuto compare nella sezione giusta della rassegna (le news si dividono da sole tra "Ultimo anno" e "Archivio"; gli eventi futuri salgono in cima con il bordo verde). Non approvato → resta in archivio invisibile e non ti verrà mai riproposto.

Puoi anche aggiungere contenuti a mano in `dati.json`, nella lista `contenuti`, copiando la struttura di una voce esistente e mettendo `"approvato": true`.

## Le pagine del sito

**Home** (mappa, schede regionali, andamento, aggiornamenti) · **L'Accordo** (cosa prevede, tappe, FAQ) · **News** (ultimo anno + archivio) · **Eventi** · **Interviste** · **Libri** · **Storia** (gli Accordi 2011-2016 con i link ai testi in Gazzetta, segnalati come non più applicabili). Il menu in alto è presente su ogni pagina.

## Pubblicazione su GitHub Pages (una volta sola, ~15 minuti)

1. Crea un account su **github.com** (gratuito) se non lo hai.
2. Crea un nuovo repository **pubblico** (pulsante "New repository"), ad esempio `osservatorio-59csr`.
3. Carica tutti i file di questa cartella **rispettando la struttura** (la cartella `.github/workflows/` è essenziale). Il modo più semplice: "Add file → Upload files" e trascina tutto; se il caricamento della cartella nascosta `.github` non funziona dal browser, crea il file a mano con "Add file → Create new file" scrivendo come nome `.github/workflows/controllo-olympus.yml` e incollando il contenuto.
4. Vai su **Settings → Pages**, alla voce "Branch" scegli `main` e cartella `/ (root)`, salva. Dopo qualche minuto il sito sarà online all'indirizzo `https://TUONOME.github.io/osservatorio-59csr/`.
5. Vai su **Actions**: alla prima visita GitHub chiede di abilitare i workflow — conferma. Puoi anche lanciare subito un controllo manuale: "Controllo quotidiano Olympus → Run workflow".
6. Per ricevere le mail di notifica: icona campanella → Settings → assicurati che le notifiche "Issues" siano attive per il tuo repository.

### Dominio personalizzato

Quando avrai registrato il dominio (es. accordostatoregioni.it): Settings → Pages → "Custom domain", inserisci il dominio e segui le istruzioni per i record DNS presso il tuo registrar.

## Cose da personalizzare

- In `index.html` sostituisci `segnalazioni@tuodominio.it` con il tuo indirizzo email reale (sezione "Segnala un atto").
- In `dati.json` puoi aggiungere in ogni momento voci al `changelog` (le più recenti in alto).

## Avvertenze

- **Test in locale:** aprendo `index.html` con doppio clic i dati non si caricano (i browser bloccano la lettura di file locali). Per provarlo sul tuo computer apri un terminale nella cartella ed esegui `python -m http.server`, poi visita `http://localhost:8000`. Online su GitHub Pages funziona senza fare nulla.
- **Limiti dei robot:** quello dei recepimenti legge solo la prima pagina di Olympus (dove compaiono le novità); quello della rassegna dipende dai feed di Google News e Google Books. Se questi servizi cambiano struttura, gli script vanno ritoccati. La verifica umana resta indispensabile: è proprio il senso del meccanismo Approva/Non approvare.
- **Dominio:** quando registri osservatorioasr.it, collegalo in Settings → Pages → Custom domain.
- **Cortesia verso la fonte:** il sito cita Olympus nel footer; valuta una mail all'Osservatorio Olympus dell'Università di Urbino per informarli dell'uso e chiedere se dispongono di un feed RSS, che renderebbe il controllo più robusto.
