'use strict';
/* Escollera Norte — lee datos.json (lo arma GitHub cada hora) y dibuja el día. */

const TZ = 'America/Argentina/Buenos_Aires';
const CLAVE = 'fishbotweb:datos:v1';
const DIA_CORTO = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb'];
const DIA_LARGO = ['Domingo', 'Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado'];
const ACTIVIDAD = ['Pique bajo', 'Pique medio', 'Pique alto', 'Pique muy alto'];
const C = {
  ok: '#3DDC97', okBar: '#2FBF85', no: '#FF7A6B', noDim: '#5A2F3A', nada: '#2A3646',
  blue: '#4DA3FF', blueLight: '#8CC4FF', yellow: '#F5C451', muted: '#8C9BB0', text: '#E6EDF5',
  panel: '#121C2B', mayor: '#24507F', menor: '#1B3350', pez: '#B9DCFF',
};
const COLOR_OLA = { verde: C.ok, amarilla: C.yellow, roja: C.no };
const GRADOS = { N: 0, NE: 45, E: 90, SE: 135, S: 180, SO: 225, O: 270, NO: 315 };
const PEZ = 'M1 6C3 2.6 7.5 1.6 10.5 4.2L14 1.5V10.5L10.5 7.8C7.5 10.4 3 9.4 1 6Z';
const P = {
  check: 'M5 12.5l4.5 4.5L19 7.5',
  cross: 'M7 7l10 10M17 7L7 17',
  guion: 'M7 12h10',
  flecha: 'M12 19V5M6 11l6-6 6 6',
  atras: 'M15 6l-6 6 6 6',
  adelante: 'M9 6l6 6-6 6',
};
const NUBE = 'M7 18.5h10a4 4 0 0 0 .6-7.95A5.5 5.5 0 0 0 7.1 11.6 3.5 3.5 0 0 0 7 18.5z';
const NUBE_ALTA = 'M7 15h10a4 4 0 0 0 .6-7.95A5.5 5.5 0 0 0 7.1 8.1 3.5 3.5 0 0 0 7 15z';
const CIELO = {
  sol: 'M12 8.5a3.5 3.5 0 1 0 0 7a3.5 3.5 0 1 0 0-7z M12 2.5v2 M12 19.5v2 M2.5 12h2 M19.5 12h2 M5.3 5.3l1.4 1.4 M17.3 17.3l1.4 1.4 M5.3 18.7l1.4-1.4 M17.3 6.7l1.4-1.4',
  luna: 'M20 14.2A8 8 0 1 1 9.8 4a6.4 6.4 0 0 0 10.2 10.2z',
  algo_dia: 'M9 3.5v1.5 M3.5 9h1.5 M5.1 5.1l1 1 M12.9 5.1l-1 1 M6.3 11.2A3.5 3.5 0 1 1 12.4 7.8 M9.5 20h8a3.5 3.5 0 0 0 .5-6.96A4.8 4.8 0 0 0 9.3 14.1 3 3 0 0 0 9.5 20z',
  algo_noche: 'M15.5 3.5a4.2 4.2 0 1 0 5 5.2 3.4 3.4 0 0 1-5-5.2z M5 20h8.5a3.5 3.5 0 0 0 .5-6.96A4.8 4.8 0 0 0 4.8 14.1 3 3 0 0 0 5 20z',
  nublado: NUBE,
  niebla: 'M4 9h16 M3 13h18 M5 17h14',
  llovizna: NUBE_ALTA + ' M9 18.5v1 M13 18.5v1 M17 18.5v1',
  lluvia: NUBE_ALTA + ' M8.5 18l-1 2.5 M12.5 18l-1 2.5 M16.5 18l-1 2.5',
  tormenta: NUBE_ALTA + ' M12.5 16l-2 3.5h3l-2 3.5',
  nieve: NUBE_ALTA + ' M9 18.5h.01 M13 18.5h.01 M17 18.5h.01 M11 21h.01 M15 21h.01',
};
const CIELO_TXT = {
  despejado: 'Despejado', algo_nublado: 'Algo nublado', nublado: 'Nublado', niebla: 'Niebla',
  llovizna: 'Llovizna', lluvia: 'Lluvia', tormenta: 'Tormenta', nieve: 'Nieve',
};

let datos = null;
let diaSel = 0;
let sinRed = false;

/* ─── utilidades ─── */
const $ = (s) => document.querySelector(s);
const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const coma = (x, d = 1) => (x == null ? '–' : Number(x).toFixed(d).replace('.', ','));
// Todas las horas se manejan como minutos en un mismo marco, sin depender de la zona del celu.
const aMin = (s) => Date.UTC(+s.slice(0, 4), +s.slice(5, 7) - 1, +s.slice(8, 10), +s.slice(11, 13) || 0, +s.slice(14, 16) || 0) / 60000;
const hhmm = (s) => s.slice(11, 16);
const diaSemana = (fecha) => new Date(Date.UTC(+fecha.slice(0, 4), +fecha.slice(5, 7) - 1, +fecha.slice(8, 10))).getUTCDay();

function ahora() {
  const p = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
    timeZone: TZ, year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date()).map((x) => [x.type, x.value]));
  return `${p.year}-${p.month}-${p.day}T${p.hour}:${p.minute}`;
}

const svg = (path, { size = 16, stroke = 'currentColor', width = 2, rot = 0, label = '' } = {}) =>
  `<svg width="${size}" height="${size}" viewBox="0 0 24 24" fill="none" stroke="${stroke}" stroke-width="${width}" stroke-linecap="round" stroke-linejoin="round"${rot ? ` style="transform:rotate(${rot}deg)"` : ''}${label ? ` role="img" aria-label="${esc(label)}"` : ' aria-hidden="true"'}><path d="${path}"/></svg>`;
const pez = (w = 13, fill = C.pez, ojo = null) =>
  `<svg width="${w}" height="${Math.round(w * 0.75)}" viewBox="0 0 16 12" aria-hidden="true"><path d="${PEZ}" fill="${fill}"/>${ojo ? `<circle cx="4.3" cy="5.3" r="0.9" fill="${ojo}"/>` : ''}</svg>`;

function iconoCielo(h) {
  if (!h.cielo) return '';
  if (h.cielo === 'despejado') return h.dia === false ? CIELO.luna : CIELO.sol;
  if (h.cielo === 'algo_nublado') return h.dia === false ? CIELO.algo_noche : CIELO.algo_dia;
  return CIELO[h.cielo] || CIELO.nublado;
}

const flechaViento = (grados) => (grados == null ? 0 : (grados + 180) % 360);

function estadoHora(h) {
  if (h.ok === true) return { path: P.check, color: C.ok, txt: 'Conviene' };
  if (h.ok === false) return { path: P.cross, color: C.no, txt: 'No conviene' };
  return { path: P.guion, color: C.muted, txt: 'Sin datos' };
}

function textoMotivo(m) {
  const R = datos.reglas;
  if (m.regla === 'lluvia') return `Lluvia de ${coma(m.valor)} mm. El límite es ${R.lluvia_mm_max} mm.`;
  if (m.regla === 'prob') return `Probabilidad de lluvia de ${m.valor} %. El límite es menos de ${R.prob_lluvia_max} %.`;
  if (m.regla === 'ola') return `Olas de ${coma(m.valor)} m. El límite es menos de ${coma(R.ola_max)} m.`;
  if (m.regla === 'viento') return `Viento ${m.rumbo} de ${Math.round(m.valor)} km/h. Con ese viento el límite es ${m.limite} km/h.`;
  return '';
}

/* ─── carga ─── */
function edadMin(d) {
  if (!d || !d.generado) return Infinity;
  return aMin(ahora()) - aMin(d.generado);
}

function elegirDia(fechaPreferida) {
  const hoy = ahora().slice(0, 10);
  const i = datos.dias.findIndex((d) => d.fecha === (fechaPreferida || hoy));
  const j = datos.dias.findIndex((d) => d.fecha === hoy);
  diaSel = i >= 0 ? i : (j >= 0 ? j : 0);
}

async function cargar() {
  if (!datos) {
    try {
      const guardado = JSON.parse(localStorage.getItem(CLAVE) || 'null');
      if (guardado && guardado.dias) { datos = guardado; elegirDia(); render(); }
    } catch (e) { /* sin copia guardada */ }
  }
  try {
    const r = await fetch('datos.json', { cache: 'no-cache' });
    if (!r.ok) throw new Error(`HTTP ${r.status}`);
    const nuevo = await r.json();
    if (!nuevo || !Array.isArray(nuevo.dias) || !nuevo.dias.length) throw new Error('archivo incompleto');
    const fechaActual = datos && datos.dias[diaSel] ? datos.dias[diaSel].fecha : null;
    datos = nuevo;
    sinRed = false;
    try { localStorage.setItem(CLAVE, JSON.stringify(nuevo)); } catch (e) { /* lleno o bloqueado */ }
    elegirDia(fechaActual);
    render();
  } catch (e) {
    sinRed = true;
    if (datos) render(); else renderError();
  }
}

/* ─── dibujo ─── */
function render() {
  const d = datos.dias[diaSel];
  renderEstado();
  renderDias();
  renderVistazo(d);
  renderMarea(d);
  renderResumen(d);
  renderTabla(d);
  renderPie();
}

function renderError() {
  $('#estado').className = 'estado sin-red';
  $('#estado').innerHTML = '<span class="punto"></span>Sin conexión';
  $('#vistazo').innerHTML = `<p class="error">No pude cargar el pronóstico. Revisá la conexión y probá de nuevo.</p>
    <button type="button" class="btn" id="reintentar">Probar de nuevo</button>`;
  $('#reintentar').addEventListener('click', cargar);
}

function renderEstado() {
  const el = $('#estado');
  const hora = datos.generado ? datos.generado.slice(11, 16) : '–';
  const edad = edadMin(datos);
  let clase = 'ok';
  let txt = `Actualizado ${hora}`;
  if (sinRed || navigator.onLine === false) {
    clase = 'sin-red';
    txt = `Sin conexión · datos de las ${hora}`;
  } else if (edad > 150) {
    clase = 'viejo';
    txt = edad > 60 * 36 ? `Datos del ${datos.generado.slice(8, 10)}/${datos.generado.slice(5, 7)}` : `Datos de hace ${Math.round(edad / 60)} h`;
  }
  el.className = `estado ${clase}`;
  el.innerHTML = `<span class="punto"></span>${esc(txt)}`;
}

function colorBarra(h) {
  return h.ok === true ? C.okBar : h.ok === false ? C.noDim : C.nada;
}

function resumenDia(d) {
  const wd = diaSemana(d.fecha);
  const m = d.mejor ? `conviene de ${d.mejor.desde} a ${d.mejor.hasta} h` : 'no conviene';
  return `${DIA_LARGO[wd]} ${+d.fecha.slice(8, 10)}: ${m}`;
}

function renderDias() {
  $('#dias').innerHTML = datos.dias.map((d, i) => {
    const sel = i === diaSel;
    const ticks = d.horas.map((h) => `<span style="background:${colorBarra(h)}"></span>`).join('');
    return `<button type="button" class="dia${sel ? ' sel' : ''}" data-i="${i}" aria-pressed="${sel}">
      <span class="dia-ab" aria-hidden="true">${DIA_CORTO[diaSemana(d.fecha)]}</span>
      <span class="dia-num" aria-hidden="true">${+d.fecha.slice(8, 10)}</span>
      <span class="ticks" aria-hidden="true">${ticks}</span>
      <span class="sr">${esc(resumenDia(d))}</span>
    </button>`;
  }).join('');
}

function esHoy(d) { return d.fecha === ahora().slice(0, 10); }

function posAhora(d) {
  if (!esHoy(d)) return null;
  const t = aMin(ahora()) - aMin(`${d.fecha}T06:00`);
  return t >= 0 && t <= 19 * 60 ? t / (19 * 60) : null;
}

function ejePct() {
  return ['06', '09', '12', '15', '18', '21', '00'].map((t, i) => `<span style="left:${((i * 3 + 0.5) / 19 * 100).toFixed(2)}%">${t}</span>`).join('');
}

function renderVistazo(d) {
  const wd = diaSemana(d.fecha);
  const pos = posAhora(d);
  const cols = d.horas.map((h) => `<span class="v-col"><span class="v-bar" style="background:${colorBarra(h)}"></span><span class="v-baj" style="background:${h.bajante ? C.blue : 'transparent'}"></span></span>`).join('');
  $('#vistazo').innerHTML = `
    <div class="panel-cab">
      <h2>El día de un vistazo</h2>
      <span class="nota">${DIA_CORTO[wd]} ${+d.fecha.slice(8, 10)}${esHoy(d) ? ' · hoy' : ''} · 06 a 00 h</span>
    </div>
    <div class="v-wrap">
      <div class="v-grid">${cols}</div>
      ${pos != null ? `<span class="v-ahora" style="left:${(pos * 100).toFixed(2)}%"></span>` : ''}
    </div>
    <div class="eje" aria-hidden="true">${ejePct()}</div>
    <div class="leyenda">
      <span><i class="cuadro" style="background:${C.okBar}"></i>Conviene</span>
      <span><i class="cuadro" style="background:${C.noDim}"></i>No conviene</span>
      <span><i class="raya"></i>Bajante</span>
    </div>`;
}

/* Marea: curva entre pleamares y bajamares, como en una tabla de mareas */
function eventosMarea() {
  return (datos.mareas || []).map((e) => ({ t: aMin(e.ts), h: e.altura ?? (e.tipo === 'alta' ? 1.4 : 0.6), tipo: e.tipo, ts: e.ts }));
}

function nivel(ev, t) {
  if (ev.length < 2 || t < ev[0].t || t > ev[ev.length - 1].t) return null;
  let i = 0;
  while (i < ev.length - 2 && t > ev[i + 1].t) i++;
  const a = ev[i];
  const b = ev[i + 1];
  const f = (t - a.t) / (b.t - a.t);
  return a.h + (b.h - a.h) * (1 - Math.cos(Math.PI * f)) / 2;
}

function periodosDelDia(t0, t1) {
  return (datos.pique || [])
    .map((p) => ({ ...p, a: aMin(p.desde), b: aMin(p.hasta) }))
    .filter((p) => p.b > t0 && p.a < t1);
}

function renderMarea(d) {
  const cont = $('#marea');
  const W = Math.max(260, Math.round(cont.clientWidth - 28));
  const H = 162;
  const top = 26, bot = 96, base = 104, laneY = 112, laneH = 24;
  const hMin = 0.2, hMax = 2.1;
  const t0 = aMin(`${d.fecha}T06:00`);
  const t1 = t0 + 19 * 60;
  const X = (t) => (t - t0) / (t1 - t0) * W;
  const Y = (h) => top + (hMax - h) / (hMax - hMin) * (bot - top);
  const ev = eventosMarea();

  const pts = [];
  for (let t = t0; t <= t1; t += 10) {
    const h = nivel(ev, t);
    if (h != null) pts.push(`${X(t).toFixed(1)} ${Y(h).toFixed(1)}`);
  }

  const act = d.actividad;
  const chip = act == null ? '' : `<span class="chip-pique"><span class="peces">${[0, 1, 2].map((i) => pez(14, i < act ? C.blueLight : '#2A3B52')).join('')}</span>${ACTIVIDAD[act]}</span>`;
  const cab = `<div class="panel-cab"><h2>Marea y pique</h2>${chip}</div>`;

  if (pts.length < 2) {
    cont.innerHTML = `${cab}<p class="vacio">No hay datos de marea para este día.</p>`;
    return;
  }

  let g = '';
  // Bajantes: de cada pleamar a la bajamar siguiente
  for (let i = 0; i < ev.length - 1; i++) {
    if (ev[i].tipo !== 'alta' || ev[i + 1].tipo !== 'baja') continue;
    const a = Math.max(t0, ev[i].t);
    const b = Math.min(t1, ev[i + 1].t);
    if (b <= a) continue;
    const x = X(a);
    const w = X(b) - x;
    g += `<rect x="${x.toFixed(1)}" y="12" width="${w.toFixed(1)}" height="${base - 12}" rx="10" fill="rgba(77,163,255,0.07)"/>`;
    if (w > 54) g += `<text x="${(x + 7).toFixed(1)}" y="${base - 6}" font-size="10" fill="#6F8FB8">bajante</text>`;
  }

  const linea = `M ${pts.join(' L ')}`;
  g += `<path d="${linea} L ${W} ${base} L 0 ${base} Z" fill="rgba(77,163,255,0.16)"/>`;
  g += `<path d="${linea}" fill="none" stroke="${C.blue}" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"/>`;

  const pos = posAhora(d);
  if (pos != null) {
    const xn = pos * W;
    g += `<line x1="${xn.toFixed(1)}" x2="${xn.toFixed(1)}" y1="13" y2="${base}" stroke="${C.text}" stroke-width="1.5" stroke-linecap="round" stroke-dasharray="1 4"/>`;
    g += `<text x="${xn.toFixed(1)}" y="9" font-size="10" fill="${C.text}" text-anchor="middle">ahora</text>`;
  }

  // Pleamares y bajamares del día
  ev.filter((e) => e.t >= t0 && e.t <= t1).forEach((e) => {
    const x = X(e.t);
    const y = Y(e.h);
    const alta = e.tipo === 'alta';
    const anchor = x < 56 ? 'start' : x > W - 56 ? 'end' : 'middle';
    g += `<circle cx="${x.toFixed(1)}" cy="${y.toFixed(1)}" r="3.4" fill="${C.panel}" stroke="${C.blue}" stroke-width="2.5"/>`;
    g += `<text x="${x.toFixed(1)}" y="${(alta ? y - 10 : y + 17).toFixed(1)}" font-size="11" font-weight="500" fill="${C.blueLight}" text-anchor="${anchor}">${alta ? 'alta' : 'baja'} ${hhmm(e.ts)} · ${coma(e.h)} m</text>`;
  });

  // Pique: pastillas con pececitos
  const per = periodosDelDia(t0, t1);
  let primerX = W;
  per.forEach((p) => {
    let x = X(Math.max(p.a, t0));
    const w = Math.max(22, X(Math.min(p.b, t1)) - x);
    if (x + w > W) x = W - w;
    primerX = Math.min(primerX, x);
    const fondo = p.tipo === 'mayor' ? C.mayor : C.menor;
    const n = p.tipo === 'mayor' ? 2 : 1;
    const total = n * 13 + (n - 1) * 2;
    let fx = x + (w - total) / 2;
    g += `<rect x="${x.toFixed(1)}" y="${laneY}" width="${w.toFixed(1)}" height="${laneH}" rx="12" fill="${fondo}"/>`;
    for (let k = 0; k < n; k++) {
      g += `<g transform="translate(${fx.toFixed(1)} ${laneY + 7}) scale(0.8125)"><path d="${PEZ}" fill="${C.pez}"/><circle cx="4.3" cy="5.3" r="0.9" fill="${fondo}"/></g>`;
      fx += 15;
    }
  });
  if (primerX > 40) g += `<text x="0" y="${laneY + 16}" font-size="10" fill="${C.muted}">pique</text>`;

  // Eje de horas
  ['06', '09', '12', '15', '18', '21', '00'].forEach((lab, i) => {
    const x = X(t0 + i * 180);
    const anchor = i === 0 ? 'start' : i === 6 ? 'end' : 'middle';
    g += `<text x="${x.toFixed(1)}" y="${H - 4}" font-size="11" fill="${C.muted}" text-anchor="${anchor}">${lab}</text>`;
  });

  const desc = ev.filter((e) => e.t >= t0 && e.t <= t1).map((e) => `${e.tipo === 'alta' ? 'pleamar' : 'bajamar'} ${hhmm(e.ts)}`).join(', ');
  const fmt = (p) => `${hhmm(p.desde)} a ${hhmm(p.hasta)}`;
  const mayores = per.filter((p) => p.tipo === 'mayor').map(fmt);
  const menores = per.filter((p) => p.tipo === 'menor').map(fmt);
  const unir = (xs) => (xs.length > 1 ? `${xs.slice(0, -1).join(', ')} y ${xs[xs.length - 1]}` : xs[0]);
  let lista = '';
  if (mayores.length) lista += `<span><span class="pill" style="background:${C.mayor}">${pez(12)}${pez(12)}</span>Pique fuerte · ${unir(mayores)}</span>`;
  if (menores.length) lista += `<span><span class="pill" style="background:${C.menor}">${pez(12)}</span>Pique · ${unir(menores)}</span>`;

  cont.innerHTML = `${cab}
    <svg class="marea-svg" viewBox="0 0 ${W} ${H}" width="${W}" height="${H}" role="img" aria-label="Curva de marea de 06 a 00 h: ${esc(desc)}">${g}</svg>
    ${lista ? `<div class="pique-lista">${lista}</div>` : ''}`;
}

function renderResumen(d) {
  const mj = d.mejor ? `<span class="va" style="color:${C.ok}">${d.mejor.desde}–${d.mejor.hasta} h</span>` : `<span class="va" style="color:${C.no}">No conviene</span>`;
  const v = d.viento_max ? `${d.viento_max.rumbo} ${d.viento_max.kmh}` : '–';
  $('#resumen').innerHTML = `
    <div class="celda"><span class="et">Mejor franja</span>${mj}</div>
    <div class="celda"><span class="et">Ola máx</span><span class="va">${d.ola_max == null ? '–' : `${coma(d.ola_max)} m`}</span></div>
    <div class="celda"><span class="et">Viento máx</span><span class="va">${esc(v)}</span></div>`;
}

function horaActualIdx(d) {
  if (!esHoy(d)) return -1;
  const h = ahora().slice(11, 13);
  return d.horas.findIndex((x) => x.h === h && x.ts.slice(0, 10) === d.fecha);
}

function renderTabla(d) {
  const actual = horaActualIdx(d);
  const filas = d.horas.map((h, i) => {
    const st = estadoHora(h);
    const reglas = new Set((h.no || []).map((m) => m.regla));
    const lluviaHit = reglas.has('lluvia');
    const lluvia = lluviaHit ? `${coma(h.lluvia)} mm` : (h.prob == null ? '–' : `${h.prob}%`);
    const v = h.viento;
    const o = h.ola;
    const motivo = (h.no || []).map(textoMotivo).join(' ');
    return `<button type="button" class="fila${i === actual ? ' actual' : ''}" data-k="${i}" aria-label="${esc(`${h.h} h: ${st.txt}. ${motivo}`)}">
      <span class="hora">${h.h}</span>
      ${svg(st.path, { size: 15, stroke: st.color, width: 3 })}
      <span class="cel">${h.cielo ? svg(iconoCielo(h), { size: 17, stroke: C.muted, width: 1.8 }) : ''}<span class="prob${lluviaHit || reglas.has('prob') ? ' hit' : ''}">${lluvia}</span></span>
      <span class="chip${reglas.has('viento') ? ' hit' : ''}">${v ? `${svg(P.flecha, { size: 12, width: 2.8, rot: flechaViento(v.grados) })}<span style="width:20px">${v.rumbo || ''}</span><span>${v.kmh}</span>` : '–'}</span>
      <span class="raf">${v && v.raf != null ? v.raf : ''}</span>
      <span class="chip${reglas.has('ola') ? ' hit' : ''}">${o ? `<span class="punto-ola" style="background:${COLOR_OLA[o.color] || C.muted}"></span>${coma(o.m)}` : '–'}</span>
      <span class="baj">${h.bajante ? '▼' : ''}</span>
      <span class="cel">${h.pique ? pez(15, C.blueLight) : ''}</span>
    </button>`;
  }).join('');
  $('#tabla').innerHTML = `
    <div class="t-cab" aria-hidden="true"><span>Hora</span><span></span><span>Cielo</span><span>Viento</span><span>Ráf</span><span>Ola</span><span></span><span></span></div>
    ${filas}`;
}

function renderPie() {
  const R = datos.reglas;
  const f = datos.fuentes || {};
  const avisos = [];
  if (f.clima && f.clima.ok === false) avisos.push(`Open-Meteo no respondió en la última actualización: el clima es de ${f.clima.actualizado ? `las ${f.clima.actualizado.slice(11, 16)} del ${f.clima.actualizado.slice(8, 10)}/${f.clima.actualizado.slice(5, 7)}` : 'antes'}.`);
  if (f.olas && f.olas.ok === false) avisos.push('Las olas no se pudieron actualizar: se muestra el último dato guardado.');
  if (f.mareas && f.mareas.ok === false) avisos.push('tablademareas no respondió: las mareas son las últimas guardadas (no cambian de un día para otro).');
  $('#pie').innerHTML = `
    ${avisos.map((a) => `<p class="aviso">${esc(a)}</p>`).join('')}
    <div class="fila-ley">
      <span><span style="color:${C.ok}">✓</span> se puede</span>
      <span><span style="color:${C.no}">✕</span> no conviene</span>
      <span><span style="color:${C.no}">en rojo</span> = el motivo</span>
      <span><span style="color:${C.blue}">▼</span> bajante</span>
      <span>${pez(13, C.blueLight)} pique</span>
    </div>
    <div class="fila-ley">Ola
      <span><span class="punto-ola" style="background:${C.ok}"></span>hasta ${coma(R.ola_verde_max)}</span>
      <span><span class="punto-ola" style="background:${C.yellow}"></span>hasta ${coma(R.ola_amarilla_max)}</span>
      <span><span class="punto-ola" style="background:${C.no}"></span>${coma(R.ola_max)} o más</span>
    </div>
    <details>
      <summary>Cómo se decide si conviene</summary>
      <ul>
        <li>Más de ${R.lluvia_mm_max} mm de lluvia: no conviene.</li>
        <li>${R.prob_lluvia_max} % o más de probabilidad de lluvia: no conviene.</li>
        <li>Olas de ${coma(R.ola_max)} m o más: no conviene.</li>
        <li>Viento del sur (S, SE, SO): la escollera cubre, no cuenta en contra.</li>
        <li>Viento del norte (N, NE, NO) de más de ${R.viento_norte_max} km/h: no conviene.</li>
        <li>Viento del este u oeste de más de ${R.viento_lateral_max} km/h: no conviene.</li>
        <li>El pique es informativo: no cambia el ✓ ni el ✕.</li>
      </ul>
    </details>
    <span>Clima y olas: Open-Meteo · Mareas y actividad: tablademareas.com · Se actualiza cada hora.</span>`;
}

/* ─── detalle de una hora ─── */
function abrirDetalle(k) {
  const dlg = $('#detalle');
  renderDetalle(k);
  if (!dlg.open) dlg.showModal();
}

function renderDetalle(k) {
  const d = datos.dias[diaSel];
  const h = d.horas[k];
  const R = datos.reglas;
  const fin = h.h === '23' ? '00' : h.h === '00' ? '01' : String(+h.h + 1).padStart(2, '0');
  const reglas = new Set((h.no || []).map((m) => m.regla));
  const st = estadoHora(h);
  const clase = h.ok === true ? 'si' : h.ok === false ? 'no' : 'nada';
  const texto = h.ok === true ? 'Se puede: ninguna regla lo impide.' : h.ok === false ? (h.no || []).map(textoMotivo).join(' ') : 'Todavía no hay pronóstico para esta hora.';
  const v = h.viento;
  const o = h.ola;

  const icoRegla = (ok) => (ok
    ? `<span class="r-ico" style="background:rgba(61,220,151,0.16)">${svg(P.check, { size: 13, stroke: C.ok, width: 3.2, label: 'Cumple' })}</span>`
    : `<span class="r-ico" style="background:rgba(255,122,107,0.2)">${svg(P.cross, { size: 13, stroke: C.no, width: 3.2, label: 'No cumple' })}</span>`);
  let limViento = '–';
  if (v && v.rumbo) {
    if (['S', 'SE', 'SO'].includes(v.rumbo)) limViento = 'viene del sur: la escollera cubre';
    else if (['N', 'NE', 'NO'].includes(v.rumbo)) limViento = `límite con viento del norte: ${R.viento_norte_max} km/h`;
    else limViento = `límite con viento del este u oeste: ${R.viento_lateral_max} km/h`;
  }
  const filasReglas = h.ok == null ? '' : [
    { nom: 'Lluvia acumulada', val: `${coma(h.lluvia)} mm`, lim: `límite: ${R.lluvia_mm_max} mm`, ok: !reglas.has('lluvia') },
    { nom: 'Probabilidad de lluvia', val: `${h.prob ?? '–'} %`, lim: `límite: menos de ${R.prob_lluvia_max} %`, ok: !reglas.has('prob') },
    { nom: 'Altura de ola', val: o ? `<span class="punto-ola" style="background:${COLOR_OLA[o.color]}"></span>${coma(o.m)} m` : '–', lim: `límite: menos de ${coma(R.ola_max)} m`, ok: !reglas.has('ola') },
    { nom: 'Viento', val: v ? `${svg(P.flecha, { size: 13, width: 2.8, rot: flechaViento(v.grados) })}${v.rumbo} ${v.kmh} km/h` : '–', lim: limViento, ok: !reglas.has('viento') },
  ].map((r) => `<div class="regla${r.ok ? '' : ' falla'}">${icoRegla(r.ok)}<span class="r-nom">${r.nom}</span><span class="r-val">${r.val}</span><span class="r-lim">${esc(r.lim)}</span></div>`).join('');

  // Marea en esta hora
  const ev = eventosMarea();
  const t = aMin(h.ts);
  const sig = ev.find((e) => e.t > t);
  const marea = sig
    ? `<span class="va">${h.bajante ? 'Bajante' : 'Creciente'} · ${sig.tipo === 'alta' ? 'alta' : 'baja'} a las ${hhmm(sig.ts)} · ${coma(sig.h)} m</span>`
    : '<span class="va">–</span>';
  const prox = ev.find((e) => e.t > t && e.tipo === 'alta');
  const extraMarea = !h.bajante && prox ? `<span class="extra">La bajante arranca a las ${hhmm(prox.ts)}</span>` : '';

  // Pique en esta hora
  const enHora = periodosDelDia(t, t + 60);
  let pique;
  if (enHora.length) {
    const p = enHora[0];
    pique = `<div class="dato ancho pique"><span class="pez-circ">${pez(22, C.pez, '#1B3350')}</span><span style="display:flex;flex-direction:column;gap:2px">
      <span class="va" style="color:${C.blueLight}">${p.tipo === 'mayor' ? 'Pique fuerte' : 'Pique'} de ${hhmm(p.desde)} a ${hhmm(p.hasta)}</span>
      <span class="et">${esc(p.motivo)}</span></span></div>`;
  } else {
    const sigP = (datos.pique || []).find((p) => aMin(p.desde) >= t + 60);
    pique = `<div class="dato ancho"><span class="et">Pique</span><span class="va">Sin período en esta hora</span>${sigP ? `<span class="extra">El próximo arranca a las ${hhmm(sigP.desde)}${sigP.desde.slice(0, 10) !== h.ts.slice(0, 10) ? ` del ${sigP.desde.slice(8, 10)}/${sigP.desde.slice(5, 7)}` : ''}</span>` : ''}</div>`;
  }

  const sol = d.sol && d.sol.sale ? `sale ${d.sol.sale} · se pone ${d.sol.pone}` : '–';
  const ant = d.horas[k - 1];
  const sig2 = d.horas[k + 1];
  const pasoTxt = (x) => (x ? `${x.h}:00 <span style="color:${estadoHora(x).color}">${x.ok === true ? '✓' : x.ok === false ? '✕' : '–'}</span>` : '');

  $('#detalle').innerHTML = `<div class="d-in">
    <div class="d-nav">
      <button type="button" class="d-cerrar" data-cerrar>${svg(P.atras, { size: 18, width: 2.4 })}${DIA_LARGO[diaSemana(d.fecha)]} ${+d.fecha.slice(8, 10)}</button>
      <span class="nota" style="font-size:12px;color:${C.muted}">Detalle de la hora</span>
    </div>
    <section class="d-hero">
      <div class="d-hora"><strong id="detalle-titulo">${h.h}:00</strong><span>a ${fin}:00</span></div>
      <span class="veredicto ${clase}">${svg(st.path, { size: 13, width: 3.2 })}${st.txt}</span>
      <p class="d-texto">${esc(texto)}</p>
    </section>
    ${filasReglas ? `<section class="reglas" aria-label="Reglas"><h3>Las 4 reglas</h3>${filasReglas}</section>` : ''}
    <section class="datos" aria-label="Más datos">
      <div class="dato"><span class="et">Temperatura</span><span class="va">${h.temp == null ? '–' : `${Math.round(h.temp)}°`}</span></div>
      <div class="dato"><span class="et">Ráfagas</span><span class="va">${v && v.raf != null ? `${v.raf} km/h` : '–'}</span></div>
      <div class="dato"><span class="et">Cielo</span><span class="va">${esc(CIELO_TXT[h.cielo] || '–')}</span></div>
      <div class="dato"><span class="et">Ola desde</span><span class="va">${o && o.rumbo ? `${o.rumbo}${o.periodo ? ` · ${Math.round(o.periodo)} s` : ''}` : '–'}</span></div>
      <div class="dato ancho"><span class="et">Marea</span>${marea}${extraMarea}</div>
      ${pique}
      <div class="dato ancho"><span class="et">Sol</span><span class="va">${esc(sol)}</span></div>
    </section>
    <div class="d-pasos">
      <button type="button" class="paso" data-paso="${k - 1}" ${ant ? '' : 'disabled'} aria-label="Hora anterior">${svg(P.atras, { size: 18, width: 2.4 })}${pasoTxt(ant)}</button>
      <button type="button" class="paso sig" data-paso="${k + 1}" ${sig2 ? '' : 'disabled'} aria-label="Hora siguiente">${pasoTxt(sig2)}${svg(P.adelante, { size: 18, width: 2.4 })}</button>
    </div>
  </div>`;
}

/* ─── eventos ─── */
document.addEventListener('click', (e) => {
  const dia = e.target.closest('.dia');
  if (dia) { diaSel = +dia.dataset.i; render(); return; }
  const fila = e.target.closest('.fila');
  if (fila) { abrirDetalle(+fila.dataset.k); return; }
  const paso = e.target.closest('[data-paso]');
  if (paso && !paso.disabled) { renderDetalle(+paso.dataset.paso); return; }
  if (e.target.closest('[data-cerrar]')) { $('#detalle').close(); return; }
  if (e.target === $('#detalle')) $('#detalle').close(); // tocar fuera de la hoja
});

let tResize;
window.addEventListener('resize', () => {
  clearTimeout(tResize);
  tResize = setTimeout(() => { if (datos) renderMarea(datos.dias[diaSel]); }, 150);
});

document.addEventListener('visibilitychange', () => {
  if (document.visibilityState === 'visible' && (!datos || edadMin(datos) > 30)) cargar();
});
window.addEventListener('online', cargar);
window.addEventListener('offline', () => { if (datos) renderEstado(); });

if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
}

cargar();
