/*
 * Mappamondo in proiezione ortografica, disegnato su canvas.
 *
 * Nessuna libreria: la proiezione ortografica sono sei righe di trigonometria
 * e le rotte sono interpolazioni su grande cerchio. Il totale sta sotto i
 * dieci kilobyte, contro le centinaia di una libreria di mappe, e non c'e'
 * niente che possa invecchiare o smettere di essere manutenuto.
 *
 * La pagina resta leggibile senza JavaScript: il canvas e' un rinforzo del
 * testo, non il testo.
 */
(function () {
  "use strict";

  var tela = document.getElementById("globo");
  if (!tela || !tela.getContext) return;

  var ctx = tela.getContext("2d");
  var RAD = Math.PI / 180;
  var terre = null;
  var chokepoint = null;

  var fermo = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  // --------------------------------------------------------------- geografia

  // I nodi della catena dell'olio motore. Le coordinate sono approssimate al
  // sito industriale o allo stretto; servono a orientare il lettore, non a
  // localizzare un impianto.
  var NODI = {
    rasLaffan:  { lon:  51.53, lat: 25.90, nome: "Ras Laffan, Qatar" },
    hormuz:     { lon:  56.60, lat: 26.57, nome: "Stretto di Hormuz" },
    onsan:      { lon: 129.35, lat: 35.43, nome: "Onsan, Corea del Sud" },
    suez:       { lon:  32.35, lat: 30.00, nome: "Canale di Suez" },
    goodHope:   { lon:  18.47, lat: -34.36, nome: "Capo di Buona Speranza" },
    genova:     { lon:   8.93, lat: 44.41, nome: "Genova" }
  };

  var ROTTE = [
    { da: "rasLaffan", a: "hormuz",   classe: "critica" },
    { da: "hormuz",    a: "suez",     classe: "critica" },
    { da: "suez",      a: "genova",   classe: "critica" },
    { da: "onsan",     a: "goodHope", classe: "alternativa" },
    { da: "goodHope",  a: "genova",   classe: "alternativa" }
  ];

  // ------------------------------------------------------------- proiezione

  var rotLon = -20, rotLat = 18;      // posizione corrente della camera
  var mira = { lon: -20, lat: 18 };   // dove sta andando

  function proietta(lon, lat, R, cx, cy) {
    var l = (lon - rotLon) * RAD;
    var f = lat * RAD;
    var f0 = rotLat * RAD;
    var cosc = Math.sin(f0) * Math.sin(f) + Math.cos(f0) * Math.cos(f) * Math.cos(l);
    if (cosc < 0) return null;        // faccia nascosta del globo
    return {
      x: cx + R * Math.cos(f) * Math.sin(l),
      y: cy - R * (Math.cos(f0) * Math.sin(f) - Math.sin(f0) * Math.cos(f) * Math.cos(l))
    };
  }

  // Interpolazione su grande cerchio: la rotta piu' breve fra due punti sulla
  // sfera, che e' anche quella che le navi seguono davvero.
  function grandeCerchio(a, b, passi) {
    var f1 = a.lat * RAD, l1 = a.lon * RAD;
    var f2 = b.lat * RAD, l2 = b.lon * RAD;
    var d = 2 * Math.asin(Math.sqrt(
      Math.pow(Math.sin((f2 - f1) / 2), 2) +
      Math.cos(f1) * Math.cos(f2) * Math.pow(Math.sin((l2 - l1) / 2), 2)));
    var punti = [];
    if (!d) return [{ lon: a.lon, lat: a.lat }];
    for (var i = 0; i <= passi; i++) {
      var t = i / passi;
      var A = Math.sin((1 - t) * d) / Math.sin(d);
      var B = Math.sin(t * d) / Math.sin(d);
      var x = A * Math.cos(f1) * Math.cos(l1) + B * Math.cos(f2) * Math.cos(l2);
      var y = A * Math.cos(f1) * Math.sin(l1) + B * Math.cos(f2) * Math.sin(l2);
      var z = A * Math.sin(f1) + B * Math.sin(f2);
      punti.push({
        lat: Math.atan2(z, Math.sqrt(x * x + y * y)) / RAD,
        lon: Math.atan2(y, x) / RAD
      });
    }
    return punti;
  }

  // ------------------------------------------------------------------ passi

  // -1 e non 0: vaiA() esce subito se il passo richiesto e' gia' quello
  // corrente, quindi partendo da 0 la prima chiamata non avrebbe evidenziato
  // nulla e tutte le tappe sarebbero rimaste smorzate fino al primo
  // scorrimento.
  var passo = -1;
  var avanzamento = 0;                 // 0..1 dentro il passo corrente
  var PASSI = [
    { mira: { lon:  40, lat: 20 }, etichetta:
      "Il globo mostra la rotta di una base lubrificante dal Qatar all'Italia." },
    { mira: { lon:  56, lat: 26 }, etichetta:
      "Il globo si centra sullo stretto di Hormuz, largo trentanove chilometri." },
    { mira: { lon:  90, lat: 15 }, etichetta:
      "Il globo mostra la rotta alternativa dalla Corea del Sud, che evita Hormuz." },
    { mira: { lon:  10, lat: 20 }, etichetta:
      "Il globo mostra i ventotto stretti marittimi monitorati nel mondo." },
    { mira: { lon:  40, lat: 20 }, etichetta:
      "Il globo colora gli stretti in base al calo dei transiti nel 2026: solo Hormuz e' fuori scala." }
  ];

  function vaiA(n) {
    n = Math.max(0, Math.min(PASSI.length - 1, n));
    if (n === passo) return;
    passo = n;
    mira = PASSI[n].mira;
    avanzamento = 0;
    tela.setAttribute("aria-label", PASSI[n].etichetta);
    var vivi = document.querySelectorAll("[data-passo]");
    for (var i = 0; i < vivi.length; i++) {
      vivi[i].classList.toggle("attivo", Number(vivi[i].dataset.passo) === n);
    }
  }

  // --------------------------------------------------------------- disegno

  function stile(nome) {
    return getComputedStyle(document.documentElement)
      .getPropertyValue(nome).trim() || "#888";
  }

  function disegna() {
    var dpr = Math.min(window.devicePixelRatio || 1, 2);
    var lato = tela.clientWidth;
    var altezza = tela.clientHeight;
    if (tela.width !== lato * dpr) {
      tela.width = lato * dpr;
      tela.height = altezza * dpr;
    }
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, lato, altezza);

    var cx = lato / 2, cy = altezza / 2;
    var R = Math.min(lato, altezza) / 2 - 8;

    // oceano
    ctx.beginPath();
    ctx.arc(cx, cy, R, 0, 2 * Math.PI);
    ctx.fillStyle = stile("--globo-mare");
    ctx.fill();

    // paralleli e meridiani, per dare il senso della rotazione
    ctx.strokeStyle = stile("--globo-griglia");
    ctx.lineWidth = 0.5;
    var g, k;
    for (g = -60; g <= 60; g += 30) {
      ctx.beginPath();
      var iniziato = false;
      for (k = -180; k <= 180; k += 3) {
        var p = proietta(k, g, R, cx, cy);
        if (!p) { iniziato = false; continue; }
        if (!iniziato) { ctx.moveTo(p.x, p.y); iniziato = true; }
        else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
    }
    for (g = -180; g < 180; g += 30) {
      ctx.beginPath();
      iniziato = false;
      for (k = -85; k <= 85; k += 3) {
        p = proietta(g, k, R, cx, cy);
        if (!p) { iniziato = false; continue; }
        if (!iniziato) { ctx.moveTo(p.x, p.y); iniziato = true; }
        else ctx.lineTo(p.x, p.y);
      }
      ctx.stroke();
    }

    // terre emerse
    if (terre) {
      ctx.fillStyle = stile("--globo-terra");
      for (var i = 0; i < terre.length; i++) {
        var anello = terre[i];
        ctx.beginPath();
        var aperto = false;
        for (var j = 0; j < anello.length; j++) {
          var q = proietta(anello[j][0], anello[j][1], R, cx, cy);
          if (!q) { aperto = false; continue; }
          if (!aperto) { ctx.moveTo(q.x, q.y); aperto = true; }
          else ctx.lineTo(q.x, q.y);
        }
        ctx.closePath();
        ctx.fill();
      }
    }

    if (passo <= 2) disegnaCatena(R, cx, cy);
    else disegnaChokepoint(R, cx, cy);
  }

  function disegnaRotta(rotta, R, cx, cy, quota, colore) {
    var punti = grandeCerchio(NODI[rotta.da], NODI[rotta.a], 48);
    var fino = Math.max(2, Math.floor(punti.length * quota));
    ctx.beginPath();
    var aperto = false;
    for (var i = 0; i < fino; i++) {
      var p = proietta(punti[i].lon, punti[i].lat, R, cx, cy);
      if (!p) { aperto = false; continue; }
      if (!aperto) { ctx.moveTo(p.x, p.y); aperto = true; }
      else ctx.lineTo(p.x, p.y);
    }
    ctx.strokeStyle = colore;
    ctx.lineWidth = 2.2;
    ctx.lineCap = "round";
    ctx.stroke();
  }

  function segna(nodo, R, cx, cy, colore, etichetta) {
    var p = proietta(nodo.lon, nodo.lat, R, cx, cy);
    if (!p) return;
    ctx.beginPath();
    ctx.arc(p.x, p.y, 4, 0, 2 * Math.PI);
    ctx.fillStyle = colore;
    ctx.fill();
    if (etichetta && tela.clientWidth > 420) {
      ctx.font = "12px system-ui, sans-serif";
      ctx.fillStyle = stile("--globo-testo");
      ctx.textAlign = "left";
      ctx.fillText(nodo.nome, p.x + 8, p.y + 4);
    }
  }

  function disegnaCatena(R, cx, cy) {
    var critica = stile("--accento");
    var alternativa = stile("--globo-alternativa");
    for (var i = 0; i < ROTTE.length; i++) {
      var r = ROTTE[i];
      if (r.classe === "alternativa" && passo < 2) continue;
      var quota = passo >= 2 ? 1 : Math.min(1, Math.max(0, avanzamento * 3 - i));
      if (quota <= 0) continue;
      disegnaRotta(r, R, cx, cy, quota,
                   r.classe === "critica" ? critica : alternativa);
    }
    var mostra = ["rasLaffan", "hormuz", "genova"];
    if (passo >= 2) mostra.push("onsan");
    for (var k = 0; k < mostra.length; k++) {
      segna(NODI[mostra[k]], R, cx, cy,
            mostra[k] === "onsan" ? alternativa : critica, true);
    }
  }

  function disegnaChokepoint(R, cx, cy) {
    if (!chokepoint) return;
    var neutro = stile("--globo-punto");
    var allarme = stile("--accento");
    for (var i = 0; i < chokepoint.length; i++) {
      var c = chokepoint[i];
      var p = proietta(c.lon, c.lat, R, cx, cy);
      if (!p) continue;
      var raggio = 2.5 + Math.sqrt(Math.max(c.navi, 0)) / 55;
      var grave = passo >= 4 && c.calo !== null && c.calo < -50;
      ctx.beginPath();
      ctx.arc(p.x, p.y, raggio, 0, 2 * Math.PI);
      ctx.fillStyle = grave ? allarme : neutro;
      ctx.globalAlpha = grave ? 1 : 0.75;
      ctx.fill();
      ctx.globalAlpha = 1;
      if (grave && tela.clientWidth > 420) {
        ctx.font = "600 12px system-ui, sans-serif";
        ctx.fillStyle = allarme;
        ctx.textAlign = "left";
        ctx.fillText(c.nome + " " + c.calo + "%", p.x + raggio + 5, p.y + 4);
      }
    }
  }

  // ------------------------------------------------------------------- ciclo

  function ciclo() {
    rotLon += (mira.lon - rotLon) * 0.05;
    rotLat += (mira.lat - rotLat) * 0.05;
    if (!fermo && Math.abs(mira.lon - rotLon) < 0.5) {
      mira.lon += 0.06;                // deriva lenta, cosi' il globo respira
    }
    if (avanzamento < 1) avanzamento += 0.012;
    disegna();
    requestAnimationFrame(ciclo);
  }

  // ------------------------------------------------------------ collegamenti

  function collega() {
    var tappe = document.querySelectorAll("[data-passo]");
    if ("IntersectionObserver" in window) {
      var oss = new IntersectionObserver(function (voci) {
        voci.forEach(function (v) {
          if (v.isIntersecting) vaiA(Number(v.target.dataset.passo));
        });
      }, { rootMargin: "-45% 0px -45% 0px" });
      for (var i = 0; i < tappe.length; i++) oss.observe(tappe[i]);
    }
    // comandi espliciti, per chi naviga da tastiera o non usa lo scorrimento
    var barra = document.getElementById("globo-comandi");
    if (barra) {
      barra.addEventListener("click", function (e) {
        var b = e.target.closest("button[data-vai]");
        if (b) {
          vaiA(Number(b.dataset.vai));
          tappe[Number(b.dataset.vai)].scrollIntoView({
            behavior: fermo ? "auto" : "smooth", block: "center" });
        }
      });
    }
  }

  Promise.all([
    fetch("assets/terre.json").then(function (r) { return r.json(); }),
    fetch("assets/chokepoint.json").then(function (r) { return r.json(); })
  ]).then(function (out) {
    terre = out[0];
    chokepoint = out[1];
    collega();
    vaiA(0);
    ciclo();
  }).catch(function () {
    // se i dati non arrivano il canvas resta vuoto e il testo basta da solo
    tela.style.display = "none";
  });
})();
