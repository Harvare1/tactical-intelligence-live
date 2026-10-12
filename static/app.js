const svg = document.getElementById('pitch');
const scrubber = document.getElementById('scrubber');
const minuteLabel = document.getElementById('minuteLabel');
const list = document.getElementById('insightList');
const scoreline = document.getElementById('scoreline');
const lang = document.getElementById('langSelect');
const sourceSelect = document.getElementById('sourceSelect');
let match, insights, playing = false, mode = 'analyst', selected = null;

const ns = 'http://www.w3.org/2000/svg';
const make = (tag, attrs = {}) => {
  const node = document.createElementNS(ns, tag);
  Object.entries(attrs).forEach(([key, value]) => node.setAttribute(key, value));
  return node;
};

function drawPitch() {
  svg.replaceChildren();
  svg.append(make('rect', {x: .6, y: .6, width: 103.8, height: 66.8, rx: .8, fill: 'none', stroke: '#b8d4c0', 'stroke-width': .45}));
  svg.append(make('path', {d: 'M52.5 .6V67.4 M.6 13H17V55H.6 M104.4 13H88V55H104.4 M.6 24H6V44H.6 M104.4 24H99V44H104.4', fill: 'none', stroke: '#b8d4c0', 'stroke-width': .45}));
  svg.append(make('circle', {cx: 52.5, cy: 34, r: 9.15, fill: 'none', stroke: '#b8d4c0', 'stroke-width': .45}));
  svg.append(make('circle', {cx: 52.5, cy: 34, r: .55, fill: '#b8d4c0'}));
}

function eventPoint(event, highlighted) {
  const color = event.team === 'home' ? '#4ade80' : '#f472b6';
  if (event.type === 'pass' && event.target_x != null) {
    svg.append(make('line', {x1: event.x, y1: event.y, x2: event.target_x, y2: event.target_y,
      stroke: color, 'stroke-width': highlighted ? 1.15 : .35, opacity: highlighted ? 1 : .24}));
  }
  const dot = make('circle', {cx: event.x, cy: event.y, r: highlighted ? 1.5 : .7,
    fill: event.type === 'goal' ? '#fbbf24' : color, class: highlighted ? 'ev-dot highlight' : 'ev-dot'});
  const title = make('title');
  title.textContent = `${event.id} · ${event.minute}:${String(event.second).padStart(2, '0')} · ${event.type}`;
  dot.append(title); svg.append(dot);
}

function render() {
  const minute = Number(scrubber.value);
  minuteLabel.textContent = `${minute}'`;
  const visible = match.events.filter(event => event.minute <= minute);
  const available = insights.filter(insight => insight.minute <= minute);
  const evidence = new Set(selected?.evidence.event_ids || []);
  drawPitch();
  visible.slice(-150).forEach(event => eventPoint(event, evidence.has(event.id)));
  const goals = {home: 0, away: 0};
  visible.filter(event => event.type === 'goal').forEach(event => goals[event.team]++);
  scoreline.textContent = `${match.teams.home} ${goals.home} — ${goals.away} ${match.teams.away}`;
  renderInsights(available);
}

function renderInsights(available) {
  list.replaceChildren();
  if (!available.length) {
    const empty = document.createElement('div');
    empty.className = 'insight-card';
    empty.innerHTML = '<div class="cat">SCANNING THE MATCH</div><div class="headline">No pattern has cleared the evidence threshold yet.</div><div class="evidence">Move to 20′, 50′ or 70′ to reveal the designed tactical stories.</div>';
    list.append(empty); return;
  }
  available.forEach(insight => {
    const card = document.createElement('article');
    card.className = 'insight-card' + (selected?.id === insight.id ? ' selected' : '');
    const team = match.teams[insight.team];
    const narrative = mode === 'fan' ? insight.narrative[`fan_${lang.value}`] : insight.narrative.analyst_en;
    card.innerHTML = `<span class="confidence">${Math.round(insight.confidence * 100)}% rule confidence</span>
      <div class="cat">${insight.category.replaceAll('_', ' ')} · ${insight.minute}'</div>
      <div class="headline"><span class="team-tag ${insight.team}">${team}</span> · ${insight.headline.replace(insight.team, '').trim()}</div>
      <div class="narrative">${narrative}</div>
      <div class="evidence">${insight.evidence.description}<br><b>${insight.evidence.event_ids.length} verified events</b> · click to inspect on pitch</div>`;
    card.onclick = () => { selected = selected?.id === insight.id ? null : insight; render(); };
    list.append(card);
  });
}

document.querySelectorAll('.mode-btn').forEach(button => button.onclick = () => {
  mode = button.dataset.mode;
  document.querySelectorAll('.mode-btn').forEach(item => item.classList.toggle('active', item === button));
  lang.disabled = mode === 'analyst';
  render();
});
lang.onchange = render;
scrubber.oninput = () => { selected = null; render(); };
document.getElementById('playBtn').onclick = event => {
  playing = !playing;
  event.currentTarget.textContent = playing ? 'Ⅱ Pause' : '▶ Play';
};
setInterval(() => {
  if (!playing) return;
  scrubber.value = Math.min(Number(scrubber.max), Number(scrubber.value) + 1);
  if (Number(scrubber.value) === Number(scrubber.max)) {
    playing = false;
    document.getElementById('playBtn').textContent = '▶ Play';
  }
  render();
}, 500);

async function loadSource(key) {
  selected = null; playing = false; document.getElementById('playBtn').textContent = '▶ Play';
  const query = '?source=' + encodeURIComponent(key);
  const [matchResponse, insightResponse] = await Promise.all([fetch('/api/match' + query), fetch('/api/insights' + query)]);
    if (!matchResponse.ok || !insightResponse.ok) throw new Error('API unavailable');
    match = await matchResponse.json(); insights = await insightResponse.json();
    scrubber.max = match.meta.duration || 90;
    scrubber.value = Math.min(70, Number(scrubber.max));
    const label = [match.meta.competition, match.meta.date, match.meta.score].filter(Boolean).join(' · ');
    document.getElementById('attribution').textContent = `${label} · Data: ${match.meta.source}`;
    render();
}

fetch('/api/sources').then(response => response.json()).then(payload => {
  payload.matches.forEach(source => {
    const option = document.createElement('option'); option.value = source.key;
    option.textContent = `${source.kind === 'real' ? 'REAL' : 'TEST'} · ${source.home} v ${source.away}`;
    sourceSelect.append(option);
  });
  sourceSelect.value = payload.default;
  return loadSource(payload.default);
}).catch(error => { list.textContent = `Unable to load match intelligence: ${error.message}`; });
sourceSelect.onchange = () => loadSource(sourceSelect.value).catch(error => { list.textContent = error.message; });
