# src/ui.py
from flask import Blueprint, Response

ui_bp = Blueprint("ui", __name__)

_PAGE = """
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <title>Workout Tracker • API Playground</title>
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <style>
    :root { font-family: system-ui, -apple-system, Segoe UI, Roboto, sans-serif; }
    body { margin: 24px; color: #111; }
    h1 { margin: 0 0 12px; }
    fieldset { border:1px solid #ddd; border-radius:8px; padding:12px; margin:12px 0; }
    legend { font-weight:600; padding:0 6px; }
    label { display:block; margin:6px 0 4px; font-size: 14px; }
    input, textarea { width:100%; padding:8px; border:1px solid #ccc; border-radius:6px; }
    .row { display:flex; gap:12px; flex-wrap: wrap; }
    .row > div { flex: 1 1 220px; }
    button { cursor:pointer; padding:8px 12px; border:0; border-radius:6px; background:#111; color:#fff; }
    button.secondary { background:#eee; color:#111; }
    .actions { display:flex; gap:8px; align-items:center; flex-wrap: wrap; }
    #tokenBox { font-family: ui-monospace, SFMono-Regular, Menlo, monospace; background:#f6f6f6; padding:8px; border-radius:6px; word-break: break-all; }
    pre { background:#0f172a; color:#e5e7eb; padding:12px; border-radius:8px; overflow:auto; }
    small.hint { color:#555; }
  </style>
</head>
<body>
  <h1>🏋️‍♂️ Workout Tracker • API Playground</h1>
  <p class="hint">Use this page to sign up / log in, then create, list, and schedule workouts — without curl.</p>

  <fieldset>
    <legend>Auth</legend>
    <div class="row">
      <div><label>Email</label><input id="email" placeholder="you@example.com" /></div>
      <div><label>Password</label><input id="password" type="password" placeholder="pass123" /></div>
    </div>
    <div class="actions">
      <button id="btnSignup">Sign Up</button>
      <button id="btnLogin" class="secondary">Log In</button>
      <button id="btnMe" class="secondary">/auth/me</button>
      <span>JWT:</span><span id="tokenBox" title="Your JWT will show here">(none)</span>
      <button id="btnClearToken" class="secondary">Clear</button>
    </div>
  </fieldset>

  <fieldset>
    <legend>Create Workout</legend>
    <div class="row">
      <div><label>Title</label><input id="wTitle" placeholder="Leg Day" /></div>
      <div><label>Notes (optional)</label><input id="wNotes" placeholder="Felt strong!" /></div>
    </div>
    <div class="row">
      <div><label>Exercise ID</label><input id="exId" type="number" placeholder="1" /></div>
      <div><label>Sets</label><input id="exSets" type="number" value="4" /></div>
      <div><label>Reps</label><input id="exReps" type="number" value="10" /></div>
      <div><label>Weight</label><input id="exWeight" type="number" value="135" /></div>
    </div>
    <div class="actions">
      <button id="btnCreate">Create</button>
      <button id="btnList" class="secondary">List Workouts</button>
      <button id="btnGet1" class="secondary">Get Workout by ID…</button>
      <input id="getId" type="number" style="width:120px" placeholder="id" />
      <button id="btnDelete" class="secondary">Delete by ID…</button>
    </div>
  </fieldset>

  <fieldset>
    <legend>Schedule</legend>
    <div class="row">
      <div><label>Workout ID</label><input id="schWid" type="number" placeholder="workout id" /></div>
      <div><label>When (ISO)</label><input id="schWhen" placeholder="2025-08-10T07:00:00" /></div>
    </div>
    <div class="actions">
      <button id="btnSchedule">Schedule</button>
      <button id="btnListSched" class="secondary">List Schedules for Workout</button>
    </div>
  </fieldset>

  <fieldset>
    <legend>Reports</legend>
    <div class="actions">
      <button id="btnOverview">Overview</button>
      <button id="btnWeekly" class="secondary">Weekly (8)</button>
      <button id="btnProgress" class="secondary">Progress for Exercise ID…</button>
      <input id="progExId" type="number" style="width:120px" placeholder="exercise id" />
      <button id="btnUpcoming" class="secondary">Upcoming</button>
    </div>
  </fieldset>

  <h3>Response</h3>
  <pre id="out">{ }</pre>

<script>
let token = localStorage.getItem('jwt') || "";
const out = document.getElementById('out');
const tokenBox = document.getElementById('tokenBox');
function showToken() { tokenBox.textContent = token ? token : "(none)"; }
showToken();

function print(obj) {
  out.textContent = typeof obj === 'string' ? obj : JSON.stringify(obj, null, 2);
}

async function api(path, {method="GET", body=null} = {}) {
  const headers = {"Content-Type":"application/json"};
  if (token) headers["Authorization"] = "Bearer " + token;
  const res = await fetch(path, {method, headers, body: body ? JSON.stringify(body) : null});
  const text = await res.text();
  let data; try { data = JSON.parse(text); } catch { data = { raw: text }; }
  print({status: res.status, data});
  return {res, data};
}

document.getElementById('btnSignup').onclick = async () => {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const {data} = await api('/auth/signup', {method:'POST', body:{email, password}});
  if (data && data.access_token) { token = data.access_token; localStorage.setItem('jwt', token); showToken(); }
};

document.getElementById('btnLogin').onclick = async () => {
  const email = document.getElementById('email').value.trim();
  const password = document.getElementById('password').value;
  const {data} = await api('/auth/login', {method:'POST', body:{email, password}});
  if (data && data.access_token) { token = data.access_token; localStorage.setItem('jwt', token); showToken(); }
};

document.getElementById('btnMe').onclick = () => api('/auth/me');

document.getElementById('btnClearToken').onclick = () => {
  token = ""; localStorage.removeItem('jwt'); showToken(); print({cleared:true});
};

document.getElementById('btnCreate').onclick = async () => {
  const title = document.getElementById('wTitle').value.trim();
  const notes = document.getElementById('wNotes').value.trim();
  const exId = parseInt(document.getElementById('exId').value,10);
  const sets = parseInt(document.getElementById('exSets').value,10);
  const reps = parseInt(document.getElementById('exReps').value,10);
  const weight = parseFloat(document.getElementById('exWeight').value);
  await api('/workouts', {method:'POST', body: { title, notes, exercises: [{exercise_id: exId, sets, reps, weight}] }});
};

document.getElementById('btnList').onclick = () => api('/workouts');

document.getElementById('btnGet1').onclick = () => {
  const id = document.getElementById('getId').value;
  if (!id) return print({error:"Enter an ID"});
  api('/workouts/'+id);
};

document.getElementById('btnDelete').onclick = () => {
  const id = document.getElementById('getId').value;
  if (!id) return print({error:"Enter an ID"});
  api('/workouts/'+id, {method:'DELETE'});
};

document.getElementById('btnSchedule').onclick = () => {
  const wid = document.getElementById('schWid').value;
  const when = document.getElementById('schWhen').value;
  if (!wid || !when) return print({error:"Need workout id and ISO datetime"});
  api(`/workouts/${wid}/schedule`, {method:'POST', body:{scheduled_at: when}});
};

document.getElementById('btnListSched').onclick = () => {
  const wid = document.getElementById('schWid').value;
  if (!wid) return print({error:"Enter workout id"});
  api(`/workouts/${wid}/schedule`);
};

document.getElementById('btnOverview').onclick = () => api('/reports/overview');
document.getElementById('btnWeekly').onclick = () => api('/reports/weekly?weeks=8');
document.getElementById('btnProgress').onclick = () => {
  const ex = document.getElementById('progExId').value || 1;
  api(`/reports/exercise/${ex}/progress?days=30`);
};
document.getElementById('btnUpcoming').onclick = () => api('/reports/upcoming');
</script>
</body>
</html>
"""


@ui_bp.route("/ui")
def ui():
    return Response(_PAGE, mimetype="text/html")
