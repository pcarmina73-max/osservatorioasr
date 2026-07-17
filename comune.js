/* OsservatorioASR.it — elementi condivisi tra le pagine */

const ETICHETTE = {
  recepito:"Recepito", in_corso:"In corso",
  non_recepito:"Non recepito", da_verificare:"Nessun atto reperito"
};

const SIGLE = {
  "Abruzzo":"ABR","Basilicata":"BAS","Calabria":"CAL","Campania":"CAM",
  "Emilia-Romagna":"EMR","Friuli-Venezia Giulia":"FVG","Lazio":"LAZ",
  "Liguria":"LIG","Lombardia":"LOM","Marche":"MAR","Molise":"MOL",
  "Piemonte":"PIE","Puglia":"PUG","Sardegna":"SAR","Sicilia":"SIC",
  "Toscana":"TOS","Umbria":"UMB","Valle d'Aosta":"VDA","Veneto":"VEN",
  "P.A. Trento":"TN","P.A. Bolzano":"BZ"
};

/* posizione [colonna, riga] nella mappa a tessere */
const POSIZIONI = {
  "P.A. Bolzano":[4,1], "Friuli-Venezia Giulia":[6,1],
  "Valle d'Aosta":[1,2], "Lombardia":[3,2], "P.A. Trento":[4,2], "Veneto":[5,2],
  "Piemonte":[1,3], "Emilia-Romagna":[4,3],
  "Liguria":[2,4], "Toscana":[3,4], "Umbria":[4,4], "Marche":[5,4],
  "Lazio":[3,5], "Abruzzo":[4,5], "Molise":[5,5],
  "Sardegna":[1,6], "Campania":[4,6], "Basilicata":[5,6], "Puglia":[6,6],
  "Calabria":[5,7],
  "Sicilia":[3,8]
};


function parseData(d){ const p=d.split("/"); return new Date(+p[2], +p[1]-1, +p[0]); }


function riempi(id, arr, eventi){
  const el = document.getElementById(id);
  if(!el) return;
  if(eventi){
    const adesso = new Date();
    const fut = arr.filter(a=>parseData(a.data)>=adesso)
                   .sort((a,b)=>parseData(a.data)-parseData(b.data));
    const pas = arr.filter(a=>parseData(a.data)<adesso);
    fut.forEach(a=>a._futuro=true);
    arr = [...fut, ...pas];
  }
  if(!arr.length){
    el.innerHTML = "<li class='vuoto'>Nessun contenuto pubblicato al momento.</li>";
    return;
  }
  el.innerHTML = arr.map(c=>`
    <li${c._futuro?' class="evento-futuro"':''}>
      <span class="cdata">${c.data||""}</span>
      <a href="${c.link}" target="_blank" rel="noopener">${c.titolo}</a>
      ${c.fonte?`<span class="cfonte"> — ${c.fonte}</span>`:""}
      ${c.descr?`<div class="cdescr">${c.descr}</div>`:""}
    </li>`).join("");
}


async function caricaDati(){
  const res = await fetch("dati.json?v=" + Date.now());
  if(!res.ok) throw new Error(res.status);
  return await res.json();
}

function erroreDati(){
  const el = document.querySelector("main");
  if(el) el.insertAdjacentHTML("afterbegin",
    "<p style='padding:20px;font-size:.9rem'>Impossibile caricare <code>dati.json</code>. " +
    "In locale avvia un piccolo server (<code>python -m http.server</code>); online funziona da sé.</p>");
}

const PAGINE = [
  ["index.html","Home"],["accordo.html","L'Accordo"],["news.html","News"],
  ["eventi.html","Eventi"],["interviste.html","Interviste"],
  ["libri.html","Libri"],["storia.html","Storico Accordi"]
];

function scheletro(attiva, titolo, sottotitolo){
  const nav = PAGINE.map(([url,nome]) =>
    `<a href="${url}"${url===attiva?' class="attiva"':''}>${nome}</a>`).join("");

  const testata = titolo ? `
    <div class="wrap">
      <div class="eyebrow">OsservatorioASR.it — osservatorio indipendente</div>
      <h1>${titolo}</h1>
      ${sottotitolo?`<p class="sub">${sottotitolo}</p>`:""}
    </div>` : `
    <div class="wrap">
      <div class="eyebrow">OsservatorioASR.it — osservatorio indipendente</div>
      <h1>Recepimento regionale dell'Accordo Stato-Regioni sulla formazione in salute e sicurezza</h1>
      <p class="sub">Monitoraggio degli atti con cui Regioni e Province autonome recepiscono l'Accordo unico del 17 aprile 2025 sui percorsi formativi previsti dal D.Lgs. 81/2008.</p>
      <div class="rif">
        <span>Rep. Atti n. 59/CSR</span>
        <span>GU Serie Generale n. 119 — 24/05/2025</span>
        <span>In vigore dal 24/05/2025</span>
      </div>
      <div>
        <a class="btn-doc" href="https://www.statoregioni.it/media/owuphvgy/p-9-csr-atto-rep-n-59-17apr2025.pdf" target="_blank" rel="noopener" download>
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12"/><path d="m7 11 5 5 5-5"/><path d="M5 21h14"/></svg>
          Scarica il testo dell'Accordo (PDF)
        </a>
      </div>`;

  document.body.insertAdjacentHTML("afterbegin", `
    <div class="demo">ℹ Ricognizione su fonti web e banca dati Olympus (Univ. Urbino). "Nessun atto reperito" non esclude atti non ancora indicizzati.</div>
    <header>${testata}</div></header>
    <nav class="menu" aria-label="Sezioni del sito"><div class="wrap">${nav}</div></nav>`);

  document.body.insertAdjacentHTML("beforeend", `
    <footer class="wrap">
      Fonti: Conferenza Stato-Regioni, Ministero del Lavoro e delle Politiche Sociali, Bollettini Ufficiali Regionali, <a href="https://olympus.uniurb.it/index.php?option=com_content&view=category&id=27&Itemid=137" target="_blank" rel="noopener">Olympus – Osservatorio Università di Urbino</a>.
      Testo dell'Accordo: <a href="https://www.statoregioni.it/media/owuphvgy/p-9-csr-atto-rep-n-59-17apr2025.pdf" target="_blank" rel="noopener">Rep. 59/CSR del 17/04/2025 (PDF)</a>.
      Ultimo aggiornamento dei dati: <span id="oggi"></span>.
      <div class="indip">Osservatorio indipendente: questo sito non è affiliato alla Conferenza Stato-Regioni né ad alcuna pubblica amministrazione.</div>
    </footer>`);
}

function segnaAggiornamento(META){
  const el = document.getElementById("oggi");
  if(el) el.textContent = (META && META.aggiornato) ||
    new Date().toLocaleDateString("it-IT");
}
