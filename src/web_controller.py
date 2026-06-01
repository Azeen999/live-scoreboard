"""Mobile phone controller — lightweight HTTP server for remote scoreboard control."""
import json
import socket
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

MOBILE_HTML = r"""<!DOCTYPE html>
<html lang="zh">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1,user-scalable=no">
<title>粗趣计分</title>
<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#1a1a2e;color:#eee;font-family:'PingFang SC','Microsoft YaHei',sans-serif;
  display:flex;flex-direction:column;align-items:center;min-height:100vh;padding:10px}
h2{font-size:18px;margin:8px 0;color:#89b4fa}
.timer{font-size:56px;font-weight:bold;font-family:Consolas,monospace;margin:4px 0;color:#fff}
.period{font-size:16px;color:#a6adc8;margin-bottom:8px}
.teams{display:flex;width:100%;gap:8px;margin:8px 0}
.team{flex:1;background:#313244;border-radius:12px;padding:12px;text-align:center}
.team .name{font-size:14px;color:#a6adc8;margin-bottom:4px}
.team .score{font-size:64px;font-weight:bold;font-family:Consolas,monospace}
.team.a .score{color:#cba6f7}
.team.b .score{color:#f38ba8}
.btns{display:flex;gap:6px;margin-top:8px;justify-content:center}
.btns button{width:48px;height:42px;border:none;border-radius:8px;font-size:22px;font-weight:bold;
  background:#45475a;color:#fff;cursor:pointer}
.btns button:active{background:#89b4fa}
.actions{display:flex;flex-wrap:wrap;gap:6px;margin:10px 0;justify-content:center}
.actions button{padding:10px 16px;border:none;border-radius:8px;font-size:15px;
  background:#313244;color:#cdd6f4;cursor:pointer}
.actions button:active{background:#45475a}
.actions .primary{background:#a6e3a1;color:#1e1e2e}
.actions .warn{background:#f38ba8;color:#1e1e2e}
select{padding:8px 12px;border-radius:8px;background:#313244;color:#cdd6f4;border:1px solid #45475a;font-size:14px}
.state{font-size:11px;color:#585b70;margin-top:8px}
</style>
</head>
<body>
<h2>粗趣计分</h2>
<div class="timer" id="timer">00:00</div>
<div class="period" id="period">上半场</div>
<div class="teams">
  <div class="team a">
    <div class="name" id="name_a">队伍A</div>
    <div class="score" id="score_a">0</div>
    <div class="btns">
      <button onclick="send('score/a/dec')">-1</button>
      <button onclick="send('score/a/inc')">+1</button>
    </div>
  </div>
  <div class="team b">
    <div class="name" id="name_b">队伍B</div>
    <div class="score" id="score_b">0</div>
    <div class="btns">
      <button onclick="send('score/b/dec')">-1</button>
      <button onclick="send('score/b/inc')">+1</button>
    </div>
  </div>
</div>
<div class="actions">
  <button class="primary" onclick="send('timer/start')">▶开始</button>
  <button onclick="send('timer/pause')">⏸暂停</button>
  <button class="warn" onclick="send('timer/reset')">↺重置</button>
  <button onclick="send('swap')">⇄交换</button>
</div>
<div class="actions">
  <select id="period_sel" onchange="setPeriod(this.value)">
  </select>
  <button onclick="send('overtime')">⏱加时</button>
</div>
<div class="state" id="status">等待连接...</div>
<script>
const API = '';
function post(url) { return fetch(API+'/api/'+url, {method:'POST'}) }
function send(url) { post(url).then(r=>r.json()).then(update).catch(e=>document.getElementById('status').textContent='连接失败') }
function setPeriod(n) { post('period/'+n).then(r=>r.json()).then(update) }
function update(s) {
  if (!s) return;
  document.getElementById('timer').textContent = s.timer;
  document.getElementById('period').textContent = s.period_label;
  document.getElementById('name_a').textContent = s.team_a_name;
  document.getElementById('name_b').textContent = s.team_b_name;
  document.getElementById('score_a').textContent = s.team_a_score;
  document.getElementById('score_b').textContent = s.team_b_score;
  document.getElementById('status').textContent = s.running ? '● 计时中' : '○ 已暂停';
  var sel = document.getElementById('period_sel');
  if (s.periods && sel.options.length === 0) {
    s.periods.forEach(function(p,i) {
      var o = document.createElement('option'); o.value = i+1; o.text = p; sel.appendChild(o);
    });
    sel.value = s.current_period;
  }
}
function poll() {
  fetch(API+'/api/state').then(r=>r.json()).then(update).catch(function(){});
  setTimeout(poll, 1000);
}
poll();
</script>
</body>
</html>"""


class MobileHandler(BaseHTTPRequestHandler):
    """HTTP request handler with CORS support for local mobile access."""
    game_state = None  # set externally

    def log_message(self, format, *args):
        pass  # suppress logs

    def _send_json(self, data, status=200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _serve_html(self):
        body = MOBILE_HTML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def _get_state(self):
        gs = self.game_state
        seconds = gs.timer_seconds
        neg = seconds < 0
        s = abs(seconds)
        m, sec = divmod(s, 60)
        timer_str = f"{'-' if neg else ''}{m:02d}:{sec:02d}"
        if gs.is_overtime:
            period_label = gs.sport_config.overtime_label
        else:
            labels = gs.sport_config.period_labels
            period_label = labels[gs.period - 1] if gs.period - 1 < len(labels) else str(gs.period)
        return {
            "team_a_name": gs.team_a_name,
            "team_b_name": gs.team_b_name,
            "team_a_score": gs.team_a_score,
            "team_b_score": gs.team_b_score,
            "timer": timer_str,
            "running": gs.is_running,
            "period_label": period_label,
            "current_period": gs.period,
            "periods": gs.sport_config.period_labels,
            "is_overtime": gs.is_overtime,
        }

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/" or path == "/index.html":
            self._serve_html()
        elif path == "/api/state":
            self._send_json(self._get_state())
        else:
            self._send_json({"error": "not found"}, 404)

    def do_POST(self):
        gs = self.game_state
        path = urlparse(self.path).path
        parts = path.strip("/").split("/")

        try:
            if parts == ["api", "state"]:
                self._send_json(self._get_state())
            elif parts == ["api", "score", "a", "inc"]:
                gs.increment_score("A", 1)
                self._send_json(self._get_state())
            elif parts == ["api", "score", "a", "dec"]:
                gs.increment_score("A", -1)
                self._send_json(self._get_state())
            elif parts == ["api", "score", "b", "inc"]:
                gs.increment_score("B", 1)
                self._send_json(self._get_state())
            elif parts == ["api", "score", "b", "dec"]:
                gs.increment_score("B", -1)
                self._send_json(self._get_state())
            elif parts == ["api", "timer", "start"]:
                gs.start_timer()
                self._send_json(self._get_state())
            elif parts == ["api", "timer", "pause"]:
                gs.pause_timer()
                self._send_json(self._get_state())
            elif parts == ["api", "timer", "reset"]:
                gs.reset_timer()
                self._send_json(self._get_state())
            elif len(parts) >= 3 and parts[0] == "api" and parts[1] == "period":
                period = int(parts[2])
                if gs.sport_config.has_overtime and period == gs.sport_config.periods_count:
                    gs.set_overtime(True)
                else:
                    gs.set_overtime(False)
                    gs.set_period(period)
                self._send_json(self._get_state())
            elif parts == ["api", "swap"]:
                gs.swap_sides()
                self._send_json(self._get_state())
            elif parts == ["api", "overtime"]:
                gs.toggle_overtime()
                self._send_json(self._get_state())
            else:
                self._send_json({"error": "unknown action"}, 404)
        except Exception as e:
            self._send_json({"error": str(e)}, 500)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()


class WebController:
    """Background HTTP server for mobile phone scoreboard control."""

    def __init__(self, game_state, port: int = 5000):
        self._gs = game_state
        self._port = port
        self._server: HTTPServer | None = None
        self._thread: threading.Thread | None = None

    @property
    def address(self) -> str:
        """Return the local network URL for the mobile page."""
        ip = self._get_local_ip()
        return f"http://{ip}:{self._port}"

    @staticmethod
    def _get_local_ip() -> str:
        """Get the LAN IP address."""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return "127.0.0.1"

    def start(self):
        """Start the server in a background daemon thread."""
        MobileHandler.game_state = self._gs
        self._server = HTTPServer(("0.0.0.0", self._port), MobileHandler)
        self._thread = threading.Thread(target=self._server.serve_forever, daemon=True)
        self._thread.start()

    def stop(self):
        """Shut down the server."""
        if self._server:
            self._server.shutdown()
            self._server = None
