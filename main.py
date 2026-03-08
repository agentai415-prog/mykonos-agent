from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests, os

app = Flask(__name__)
CORS(app, origins="*")

CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
WA_TOKEN       = os.environ.get("WA_TOKEN", "")
WA_PHONE_ID    = os.environ.get("WA_PHONE_ID", "")
VERIFY_TOKEN   = os.environ.get("VERIFY_TOKEN", "mykonos2024")

CONVERSATIONS = {}

def send_wa_message(to, text):
    if not WA_TOKEN or not WA_PHONE_ID:
        return
    requests.post(
        f"https://graph.facebook.com/v19.0/{WA_PHONE_ID}/messages",
        headers={"Authorization": f"Bearer {WA_TOKEN}", "Content-Type": "application/json"},
        json={"messaging_product": "whatsapp", "to": to, "type": "text", "text": {"body": text}},
        timeout=10
    )

SYSTEM_PROMPT = """You are the booking assistant for Mykonos Sailing, a premier yacht charter company in Mykonos, Greece.

You ONLY help customers with bookings and questions about cruises.
NEVER discuss internal business data, revenue, or operational information.

COMPANY: Mykonos Sailing | mykonossailing.gr | @mykonossailing
DEPARTURE: Ornos Bay, small dock on left side of beach

CRUISES:
1. 5hr South Coast Cruise (10–3pm or 3:30–8:30pm) — Private or Semi-Private
2. 5hr Delos & Rhenia Cruise (10–3pm or 3:30–8:30pm) — Private or Semi-Private
3. 3hr Sunset Cruise (5:30pm–sunset)
4. 8hr Full Day: Delos, Rhenia & South Coast (10–6pm)
5. 8hr Full Day South Coast (10–6pm)
6. 3-Day Charter: Mykonos–Paros–Naxos
7. 3-Day Charter: Mykonos–Syros–Antiparos
8. Multi-Day Tailor Made

ALL CRUISES INCLUDE: Meals, unlimited drinks, beach towels, snorkeling/SUP, music, professional crew.
PRICING: Never give specific prices. Say pricing depends on vessel and group size.

BOOKING INFO TO COLLECT: name, email, cruise type, private/semi-private, date, number of guests.

Reply in the SAME language as the customer. Keep replies concise for WhatsApp.
When all booking info collected, end with:
BOOKING_DATA:{"name":"...","email":"...","cruise":"...","type":"...","date":"...","guests":"..."}"""

@app.route("/webhook", methods=["GET"])
def verify_webhook():
    mode      = request.args.get("hub.mode")
    token     = request.args.get("hub.verify_token")
    challenge = request.args.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return challenge, 200
    return "Forbidden", 403

@app.route("/webhook", methods=["POST"])
def receive_message():
    try:
        data    = request.get_json()
        entry   = data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value   = changes.get("value", {})
        msgs    = value.get("messages", [])

        for msg in msgs:
            wa_id = msg.get("from")
            if msg.get("type") == "text":
                user_text = msg["text"]["body"]
                if wa_id not in CONVERSATIONS:
                    CONVERSATIONS[wa_id] = []
                CONVERSATIONS[wa_id].append({"role": "user", "content": user_text})
                if len(CONVERSATIONS[wa_id]) > 20:
                    CONVERSATIONS[wa_id] = CONVERSATIONS[wa_id][-20:]

                r = requests.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
                    json={"model": "claude-sonnet-4-6", "max_tokens": 1024, "system": SYSTEM_PROMPT, "messages": CONVERSATIONS[wa_id]},
                    timeout=30
                )
                reply = r.json().get("content", [{}])[0].get("text", "")
                if reply:
                    CONVERSATIONS[wa_id].append({"role": "assistant", "content": reply})
                    clean = reply[:reply.find("BOOKING_DATA:")].strip() if "BOOKING_DATA:" in reply else reply
                    send_wa_message(wa_id, clean)
    except Exception as e:
        print(f"Error: {e}")
    return jsonify({"status": "ok"}), 200

DASHBOARD = '''<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
<title>Mykonos Sailing — Captain's Deck</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{
  --navy:#08111f;--navy2:#0d1a2e;--navy3:#112240;
  --sea:#1a4a7a;--sea2:#1e5c9a;
  --gold:#c9a84c;--gold2:#e8c875;
  --white:#eef3f8;--muted:#7a90a8;
  --card:#0d1e36;--card2:#112240;
  --border:rgba(201,168,76,.15);--border2:rgba(201,168,76,.07);
  --text:#d8e8f0;--text2:#90aac0;
  --green:#27ae60;--red:#e74c3c;--orange:#e67e22;--blue:#2980b9;
  --radius:12px;--radius-sm:8px;
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
html,body{height:100%;overscroll-behavior:none;}
body{background:var(--navy);color:var(--text);font-family:'Jost',sans-serif;font-weight:300;overflow:hidden;}
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 70% 50% at 15% 0%,rgba(26,74,122,.35),transparent),
              radial-gradient(ellipse 50% 70% at 85% 100%,rgba(12,28,54,.5),transparent);}

/* LOGIN */
#login{position:fixed;inset:0;z-index:999;background:var(--navy);display:flex;align-items:center;justify-content:center;padding:24px;}
.lc{width:100%;max-width:340px;position:relative;z-index:1;}
.lt{text-align:center;margin-bottom:28px;}
.ll{font-family:'Cormorant Garamond',serif;font-size:10px;letter-spacing:6px;color:var(--gold);text-transform:uppercase;display:block;margin-bottom:6px;}
.lb{font-family:'Cormorant Garamond',serif;font-size:30px;letter-spacing:3px;color:var(--white);display:block;}
.ls{font-size:10px;letter-spacing:3px;color:var(--muted);text-transform:uppercase;display:block;margin-top:3px;}
.lw{display:block;text-align:center;margin:12px 0;opacity:.35;}
.ll2{font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:5px;display:block;}
.li{width:100%;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px 14px;color:var(--white);font-family:'Jost',sans-serif;font-size:14px;outline:none;margin-bottom:14px;direction:ltr;}
.li:focus{border-color:var(--gold);}
.bp{width:100%;padding:13px;background:var(--gold);color:#000;border:none;border-radius:var(--radius-sm);font-family:'Jost',sans-serif;font-size:14px;font-weight:600;letter-spacing:1px;cursor:pointer;}
.bp:active{transform:scale(.98);}
.lerr{color:var(--red);font-size:12px;text-align:center;min-height:16px;margin-top:8px;}

/* SHELL */
#app{display:none;height:100%;flex-direction:column;position:relative;z-index:1;}
#app.show{display:flex;}

/* TOPBAR */
.topbar{height:52px;background:rgba(8,17,31,.9);backdrop-filter:blur(12px);border-bottom:1px solid var(--border2);display:flex;align-items:center;padding:0 14px;gap:10px;flex-shrink:0;z-index:50;}
.tb-logo{font-family:'Cormorant Garamond',serif;letter-spacing:2px;font-size:14px;color:var(--gold2);flex:1;}
.live-pill{display:flex;align-items:center;gap:4px;background:rgba(39,174,96,.1);border:1px solid rgba(39,174,96,.25);border-radius:20px;padding:3px 9px 3px 5px;}
.ld{width:6px;height:6px;border-radius:50%;background:var(--green);box-shadow:0 0 5px var(--green);animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.3}}
.lt2{font-size:9px;letter-spacing:1px;color:var(--green);}
.tb-date{font-size:10px;color:var(--muted);}

/* MAIN */
.main-scroll{flex:1;overflow-y:auto;overflow-x:hidden;padding:14px;padding-bottom:76px;}

/* BOTTOM NAV */
.bnav{height:58px;background:rgba(8,17,31,.96);backdrop-filter:blur(10px);border-top:1px solid var(--border2);display:flex;align-items:center;flex-shrink:0;}
.ni{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:2px;cursor:pointer;padding:6px;position:relative;}
.ni-icon{font-size:19px;transition:transform .2s;}
.ni-lbl{font-size:8px;letter-spacing:.8px;color:var(--muted);text-transform:uppercase;}
.ni.active .ni-lbl{color:var(--gold);}
.ni.active .ni-icon{transform:scale(1.08);}
.ni-badge{position:absolute;top:4px;right:calc(50% - 18px);background:var(--red);color:#fff;font-size:8px;min-width:15px;height:15px;border-radius:8px;display:none;align-items:center;justify-content:center;padding:0 3px;}

/* PAGES */
.page{display:none;}
.page.active{display:block;}

/* SECTION */
.sh{font-family:'Cormorant Garamond',serif;font-size:21px;letter-spacing:1px;color:var(--white);margin-bottom:3px;}
.ss{font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:16px;}

/* STATS GRID */
.sg{display:grid;grid-template-columns:repeat(2,1fr);gap:10px;margin-bottom:16px;}
.sc{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);padding:14px;position:relative;overflow:hidden;}
.sc::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--gold),transparent);}
.sc-n{font-family:'Cormorant Garamond',serif;font-size:30px;color:var(--gold2);line-height:1;}
.sc-l{font-size:9px;letter-spacing:1.5px;color:var(--muted);text-transform:uppercase;margin-top:3px;}
.sc-i{position:absolute;right:10px;top:10px;font-size:20px;opacity:.25;}
.sc-trend{font-size:10px;margin-top:5px;}
.trend-up{color:var(--green);}
.trend-dn{color:var(--red);}

/* PERIOD TABS */
.ptabs{display:flex;gap:6px;margin-bottom:14px;overflow-x:auto;padding-bottom:2px;}
.ptab{flex-shrink:0;padding:5px 14px;border-radius:20px;font-size:11px;border:1px solid var(--border);color:var(--muted);cursor:pointer;transition:all .2s;}
.ptab.active{background:var(--gold);color:#000;border-color:var(--gold);font-weight:600;}

/* MONTH CHART */
.month-grid{display:grid;grid-template-columns:repeat(6,1fr);gap:6px;margin-bottom:16px;}
.mc{background:var(--card);border:1px solid var(--border2);border-radius:8px;padding:8px 6px;text-align:center;cursor:pointer;transition:all .2s;}
.mc.selected{border-color:var(--gold);background:rgba(201,168,76,.08);}
.mc-m{font-size:9px;color:var(--muted);text-transform:uppercase;letter-spacing:.5px;}
.mc-n{font-family:'Cormorant Garamond',serif;font-size:18px;color:var(--gold2);}
.mc-l{font-size:8px;color:var(--text2);}

/* CARD */
.card{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);margin-bottom:10px;overflow:hidden;}
.ch{padding:12px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border2);}
.ct{font-size:12px;font-weight:500;color:var(--white);}
.cb{padding:12px 14px;}

/* VESSEL SCHEDULE */
.vessel-card{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);margin-bottom:8px;overflow:hidden;}
.vh{padding:12px 14px;display:flex;align-items:center;gap:10px;border-bottom:1px solid var(--border2);}
.ve{width:38px;height:38px;background:linear-gradient(135deg,var(--sea),var(--navy3));border-radius:9px;display:flex;align-items:center;justify-content:center;font-size:18px;flex-shrink:0;}
.vi{flex:1;}
.vn{font-family:'Cormorant Garamond',serif;font-size:16px;color:var(--white);}
.vt{font-size:10px;color:var(--muted);}
.vs-status{font-size:10px;padding:3px 9px;border-radius:12px;font-weight:500;}
.vs-free{background:rgba(39,174,96,.15);color:var(--green);border:1px solid rgba(39,174,96,.25);}
.vs-booked{background:rgba(231,76,60,.12);color:var(--red);border:1px solid rgba(231,76,60,.2);}
.vs-off{background:rgba(122,144,168,.1);color:var(--muted);border:1px solid rgba(122,144,168,.15);}
.vbookings{padding:10px 14px;}
.vb-item{display:flex;justify-content:space-between;align-items:center;padding:6px 0;border-bottom:1px solid var(--border2);}
.vb-item:last-child{border-bottom:none;}
.vb-guest{font-size:12px;color:var(--white);}
.vb-detail{font-size:10px;color:var(--muted);margin-top:1px;}
.vb-time{font-size:11px;color:var(--gold);text-align:right;}
.toggle{width:42px;height:22px;background:rgba(255,255,255,.08);border-radius:11px;position:relative;cursor:pointer;transition:background .3s;border:1px solid var(--border);flex-shrink:0;}
.toggle.on{background:rgba(39,174,96,.25);border-color:rgba(39,174,96,.4);}
.toggle::after{content:'';position:absolute;width:16px;height:16px;border-radius:50%;background:var(--muted);top:2px;left:2px;transition:all .3s;}
.toggle.on::after{left:22px;background:var(--green);}

/* BOOKINGS */
.bk-card{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);margin-bottom:8px;overflow:hidden;}
.bkh{padding:11px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border2);}
.bk-id{font-family:'Cormorant Garamond',serif;font-size:13px;color:var(--gold);}
.bkb{padding:11px 14px;}
.bkr{display:flex;justify-content:space-between;margin-bottom:5px;}
.bkk{font-size:10px;color:var(--muted);}
.bkv{font-size:11px;color:var(--text);text-align:right;max-width:58%;}
.sb{font-size:9px;padding:3px 9px;border-radius:12px;font-weight:500;letter-spacing:.3px;}
.s-new{background:rgba(230,193,0,.12);color:#f1c40f;border:1px solid rgba(230,193,0,.25);}
.s-confirmed{background:rgba(39,174,96,.12);color:var(--green);border:1px solid rgba(39,174,96,.25);}
.s-done{background:rgba(122,144,168,.1);color:var(--muted);border:1px solid rgba(122,144,168,.15);}
.s-cancelled{background:rgba(231,76,60,.1);color:var(--red);border:1px solid rgba(231,76,60,.15);}
.bk-acts{display:flex;gap:6px;margin-top:8px;}
.bka{flex:1;padding:7px;border:none;border-radius:var(--radius-sm);font-size:10px;font-family:'Jost',sans-serif;cursor:pointer;font-weight:500;letter-spacing:.3px;}
.bka-conf{background:rgba(39,174,96,.12);color:var(--green);border:1px solid rgba(39,174,96,.25);}
.bka-done{background:rgba(41,128,185,.12);color:var(--blue);border:1px solid rgba(41,128,185,.25);}
.bka-del{background:rgba(231,76,60,.08);color:var(--red);border:1px solid rgba(231,76,60,.15);}

/* ADMIN CHAT */
.admin-chat-wrap{display:flex;flex-direction:column;height:calc(100vh - 52px - 58px);}
.ach{padding:10px 14px;border-bottom:1px solid var(--border2);background:rgba(13,30,54,.6);flex-shrink:0;}
.acn{font-family:'Cormorant Garamond',serif;font-size:15px;color:var(--white);}
.acs{font-size:9px;color:var(--muted);letter-spacing:1px;}
.chat-msgs{flex:1;overflow-y:auto;padding:14px;display:flex;flex-direction:column;gap:9px;}
.msg{max-width:82%;padding:9px 13px;border-radius:14px;font-size:12px;line-height:1.65;}
.msg-in{background:var(--card2);border:1px solid var(--border2);border-bottom-left-radius:3px;align-self:flex-start;color:var(--text);}
.msg-out{background:linear-gradient(135deg,rgba(26,74,122,.8),rgba(30,92,154,.8));border-bottom-right-radius:3px;align-self:flex-end;color:#fff;border:1px solid rgba(30,92,154,.4);}
.msg-time{font-size:8px;color:rgba(255,255,255,.35);margin-top:3px;text-align:right;}
.typing{display:none;align-self:flex-start;background:var(--card2);border:1px solid var(--border2);padding:8px 14px;border-radius:14px;border-bottom-left-radius:3px;}
.typing span{display:inline-block;width:5px;height:5px;background:var(--muted);border-radius:50%;margin:0 2px;animation:bounce .8s infinite;}
.typing span:nth-child(2){animation-delay:.15s;}
.typing span:nth-child(3){animation-delay:.3s;}
@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-5px)}}
.chat-quick{display:flex;gap:6px;padding:7px 14px;overflow-x:auto;flex-shrink:0;border-top:1px solid var(--border2);}
.qb{flex-shrink:0;background:var(--card2);border:1px solid var(--border);border-radius:18px;padding:5px 12px;font-size:10px;color:var(--text2);cursor:pointer;white-space:nowrap;}
.qb:active{background:var(--sea);color:#fff;}
.cir{display:flex;gap:8px;padding:10px 14px;border-top:1px solid var(--border2);flex-shrink:0;background:rgba(8,17,31,.8);}
.ci{flex:1;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:22px;padding:9px 14px;color:var(--white);font-family:'Jost',sans-serif;font-size:12px;outline:none;}
.ci::placeholder{color:var(--muted);}
.cs{width:40px;height:40px;background:var(--gold);border:none;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;}
.cs svg{width:16px;height:16px;}

/* CUSTOMER CHAT */
.customer-chat-wrap{display:flex;flex-direction:column;height:calc(100vh - 52px - 58px);}
.cch{padding:10px 14px;border-bottom:1px solid var(--border2);background:rgba(13,30,54,.6);flex-shrink:0;display:flex;align-items:center;gap:10px;}
.cc-avatar{width:34px;height:34px;background:linear-gradient(135deg,var(--sea),var(--gold));border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:16px;}
.cc-info{flex:1;}
.cc-name{font-size:13px;color:var(--white);font-weight:500;}
.cc-sub{font-size:9px;color:var(--muted);}
.cc-note{margin:8px 14px;background:rgba(231,76,60,.08);border:1px solid rgba(231,76,60,.15);border-radius:8px;padding:7px 11px;font-size:10px;color:var(--red);}

/* SETTINGS */
.ss-sec{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);margin-bottom:14px;overflow:hidden;}
.ss-title{font-size:9px;letter-spacing:2px;color:var(--gold);text-transform:uppercase;padding:12px 14px 7px;border-bottom:1px solid var(--border2);}
.sr{padding:12px 14px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border2);}
.sr:last-child{border-bottom:none;}
.sr-col{flex-direction:column;align-items:flex-start;}
.sr-l{font-size:12px;color:var(--text);}
.sr-s{font-size:10px;color:var(--muted);margin-top:1px;}
.si{width:100%;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:var(--radius-sm);padding:9px 11px;color:var(--white);font-family:'Jost',sans-serif;font-size:12px;outline:none;margin-top:7px;direction:ltr;}
.si:focus{border-color:var(--gold);}
.savebtn{width:100%;padding:12px;background:var(--gold);color:#000;border:none;border-radius:var(--radius-sm);font-family:'Jost',sans-serif;font-size:13px;font-weight:600;letter-spacing:1px;cursor:pointer;margin-top:8px;}
.savebtn:active{transform:scale(.98);}

/* MODAL */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.75);z-index:800;display:flex;align-items:flex-end;opacity:0;pointer-events:none;transition:opacity .25s;}
.modal-bg.open{opacity:1;pointer-events:all;}
.ms{background:var(--navy2);border-radius:20px 20px 0 0;padding:22px;width:100%;max-height:85vh;overflow-y:auto;transform:translateY(30px);transition:transform .25s;}
.modal-bg.open .ms{transform:translateY(0);}
.mt{font-family:'Cormorant Garamond',serif;font-size:19px;margin-bottom:18px;color:var(--white);}
.ml{font-size:9px;letter-spacing:1.5px;color:var(--muted);text-transform:uppercase;margin-bottom:5px;display:block;}
.mi{width:100%;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:var(--radius-sm);padding:9px 11px;color:var(--white);font-family:'Jost',sans-serif;font-size:12px;outline:none;margin-bottom:12px;direction:ltr;}
.mi:focus{border-color:var(--gold);}
.msel{width:100%;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:var(--radius-sm);padding:9px 11px;color:var(--white);font-family:'Jost',sans-serif;font-size:12px;outline:none;margin-bottom:12px;}
.mac{display:flex;gap:8px;margin-top:6px;}
.mbtn{flex:1;padding:11px;border:none;border-radius:var(--radius-sm);font-family:'Jost',sans-serif;font-size:12px;cursor:pointer;font-weight:500;}
.mbtn-c{background:rgba(255,255,255,.05);border:1px solid var(--border);color:var(--muted);}
.mbtn-s{background:var(--gold);color:#000;}

/* QUICK ACTIONS ROW */
.qa-row{display:flex;gap:8px;margin-bottom:14px;overflow-x:auto;padding-bottom:3px;}
.qa{flex-shrink:0;background:var(--card2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:8px 14px;font-size:11px;color:var(--text2);cursor:pointer;white-space:nowrap;}
.qa:active{background:var(--sea);color:#fff;}

/* TOAST */
#toast{position:fixed;bottom:72px;left:50%;transform:translateX(-50%) translateY(16px);background:var(--card2);border:1px solid var(--border);border-radius:22px;padding:9px 18px;font-size:11px;color:var(--text);z-index:9999;opacity:0;transition:all .3s;white-space:nowrap;pointer-events:none;}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0);}

/* EMPTY */
.empty{text-align:center;padding:36px 18px;color:var(--muted);}
.empty-i{font-size:36px;margin-bottom:10px;opacity:.35;}
.empty-t{font-size:12px;}

::-webkit-scrollbar{width:3px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="login">
  <div class="lc">
    <div class="lt">
      <span class="ll">⚓ Mykonos Sailing</span>
      <span class="lb">CAPTAIN'S DECK</span>
      <span class="ls">Admin Dashboard v2</span>
      <svg class="lw" width="100" height="16" viewBox="0 0 100 16">
        <path d="M0,8 Q12,0 25,8 Q38,16 50,8 Q62,0 75,8 Q88,16 100,8" fill="none" stroke="rgba(201,168,76,.5)" stroke-width="1.2"/>
      </svg>
    </div>
    <span class="ll2">Username</span>
    <input id="l-user" class="li" type="text" placeholder="captain" autocomplete="off"/>
    <span class="ll2">Password</span>
    <input id="l-pass" class="li" type="password" placeholder="••••••••" onkeydown="if(event.key==='Enter')doLogin()"/>
    <button class="bp" onclick="doLogin()">BOARD →</button>
    <div class="lerr" id="l-err"></div>
    <div style="font-size:10px;color:var(--muted);text-align:center;margin-top:10px;">captain / mykonos2024</div>
  </div>
</div>

<!-- APP -->
<div id="app">
  <div class="topbar">
    <div class="live-pill">
      <div class="ld"></div>
      <span class="lt2">LIVE</span>
    </div>
    <span class="tb-logo">MYKONOS SAILING</span>
    <span class="tb-date" id="tb-date"></span>
  </div>

  <div class="main-scroll" id="main-scroll">

    <!-- DASHBOARD -->
    <div class="page active" id="pg-home">
      <div style="padding-top:6px;">
        <div class="sh">Captain's Overview 🌊</div>
        <div class="ss" id="home-sub">Loading...</div>

        <!-- Period Tabs -->
        <div class="ptabs">
          <div class="ptab active" onclick="setPeriod('today',this)">Today</div>
          <div class="ptab" onclick="setPeriod('month',this)">This Month</div>
          <div class="ptab" onclick="setPeriod('year',this)">This Year</div>
          <div class="ptab" onclick="setPeriod('all',this)">All Time</div>
        </div>

        <!-- Stats -->
        <div class="sg">
          <div class="sc">
            <div class="sc-i">📋</div>
            <div class="sc-n" id="s-bookings">0</div>
            <div class="sc-l">Bookings</div>
            <div class="sc-trend" id="s-bookings-t"></div>
          </div>
          <div class="sc">
            <div class="sc-i">💬</div>
            <div class="sc-n" id="s-chats">0</div>
            <div class="sc-l">AI Chats</div>
          </div>
          <div class="sc">
            <div class="sc-i">👥</div>
            <div class="sc-n" id="s-guests">0</div>
            <div class="sc-l">Total Guests</div>
          </div>
          <div class="sc">
            <div class="sc-i">💰</div>
            <div class="sc-n" id="s-revenue">€0</div>
            <div class="sc-l">Revenue</div>
          </div>
        </div>

        <!-- Monthly breakdown -->
        <div class="card" id="monthly-card">
          <div class="ch"><span class="ct">Monthly Breakdown <span id="year-label"></span></span></div>
          <div style="padding:12px 14px;">
            <div class="month-grid" id="month-grid"></div>
          </div>
        </div>

        <!-- Quick actions -->
        <div class="qa-row">
          <button class="qa" onclick="openModal('bk-modal')">+ New Booking</button>
          <button class="qa" onclick="goPage('fleet')">⚓ Fleet Status</button>
          <button class="qa" onclick="goPage('admin-chat')">🤖 Ask AI</button>
        </div>

        <!-- Today's bookings -->
        <div class="card">
          <div class="ch">
            <span class="ct">Today's Bookings</span>
            <span style="font-size:10px;color:var(--gold);cursor:pointer;" onclick="goPage('bookings')">View All</span>
          </div>
          <div id="today-bk-list" style="padding:0 14px 4px;"></div>
        </div>
      </div>
    </div>

    <!-- FLEET / SCHEDULE -->
    <div class="page" id="pg-fleet">
      <div style="padding-top:6px;">
        <div class="sh">Fleet & Schedule</div>
        <div class="ss">Vessel availability — <span id="fleet-date-sub"></span></div>
        <button class="qa" style="margin-bottom:12px;width:100%;" onclick="openModal('vessel-modal')">+ Add Vessel</button>
        <div id="fleet-list"></div>
      </div>
    </div>

    <!-- BOOKINGS -->
    <div class="page" id="pg-bookings">
      <div style="padding-top:6px;">
        <div class="sh">All Bookings</div>
        <div class="ptabs" style="margin-bottom:10px;">
          <div class="ptab active" onclick="filterBk('all',this)">All</div>
          <div class="ptab" onclick="filterBk('new',this)">New</div>
          <div class="ptab" onclick="filterBk('confirmed',this)">Confirmed</div>
          <div class="ptab" onclick="filterBk('done',this)">Done</div>
        </div>
        <div id="bookings-list"></div>
      </div>
    </div>

    <!-- ADMIN AI CHAT -->
    <div class="page" id="pg-admin-chat">
      <div class="admin-chat-wrap">
        <div class="ach">
          <div class="acn">🤖 Business Intelligence</div>
          <div class="acs">Your private AI assistant — not visible to customers</div>
        </div>
        <div class="chat-msgs" id="admin-msgs">
          <div class="msg msg-in">
            Good morning, Captain! 👋 I'm your private business assistant. I have full access to your bookings, fleet status, and analytics. What would you like to know?
            <div class="msg-time" id="admin-welcome-time"></div>
          </div>
        </div>
        <div class="typing" id="admin-typing"><span></span><span></span><span></span></div>
        <div class="chat-quick">
          <button class="qb" onclick="adminQ('What happened today?')">📊 Today's summary</button>
          <button class="qb" onclick="adminQ('Which vessels are booked today?')">⚓ Fleet status</button>
          <button class="qb" onclick="adminQ('Show me this month\'s performance')">📅 This month</button>
          <button class="qb" onclick="adminQ('Who are my newest bookings?')">🆕 New bookings</button>
          <button class="qb" onclick="adminQ('What is my total revenue?')">💰 Revenue</button>
        </div>
        <div class="cir">
          <input id="admin-inp" class="ci" placeholder="Ask about your business..." onkeydown="if(event.key==='Enter')sendAdmin()"/>
          <button class="cs" onclick="sendAdmin()">
            <svg viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2"><path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- CUSTOMER CHAT TEST -->
    <div class="page" id="pg-customer-chat">
      <div class="customer-chat-wrap">
        <div class="cch">
          <div class="cc-avatar">⛵</div>
          <div class="cc-info">
            <div class="cc-name">Mykonos Sailing Agent</div>
            <div class="cc-sub">Customer-facing · WhatsApp simulation</div>
          </div>
        </div>
        <div class="cc-note">⚠️ This simulates how customers experience the agent. Never share business data here.</div>
        <div class="chat-msgs" id="customer-msgs">
          <div class="msg msg-in">
            Welcome aboard! 🌊⛵ I'm the Mykonos Sailing assistant. Ready to help you plan your perfect Aegean adventure. What can I do for you?
            <div class="msg-time" id="cust-welcome-time"></div>
          </div>
        </div>
        <div class="typing" id="cust-typing"><span></span><span></span><span></span></div>
        <div class="chat-quick">
          <button class="qb" onclick="custQ('Tell me about your cruises')">🗺️ Cruises</button>
          <button class="qb" onclick="custQ('What yachts do you have?')">⛵ Yachts</button>
          <button class="qb" onclick="custQ('I want to book a sunset cruise for 4 people')">🌅 Book</button>
          <button class="qb" onclick="custQ('Private or semi-private?')">👥 Private?</button>
          <button class="qb" onclick="custQ('Where do we depart from?')">📍 Location</button>
        </div>
        <div class="cir">
          <input id="cust-inp" class="ci" placeholder="Type as a customer..." onkeydown="if(event.key==='Enter')sendCustomer()"/>
          <button class="cs" onclick="sendCustomer()">
            <svg viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2"><path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- SETTINGS -->
    <div class="page" id="pg-settings">
      <div style="padding-top:6px;">
        <div class="sh">Settings</div>
        <div class="ss">Configuration</div>

        <div class="ss-sec">
          <div class="ss-title">WhatsApp / Meta</div>
          <div class="sr sr-col">
            <div class="sr-l">Phone Number ID</div>
            <input id="wa-phone" class="si" type="text" placeholder="1234567890..."/>
          </div>
          <div class="sr sr-col">
            <div class="sr-l">Access Token</div>
            <input id="wa-token" class="si" type="password" placeholder="EAAxxxxxxx..."/>
          </div>
          <div class="sr sr-col">
            <div class="sr-l">Verify Token</div>
            <input id="wa-verify" class="si" type="text" value="mykonos2024"/>
          </div>
          <div style="padding:0 14px 14px;"><button class="savebtn" onclick="toast('WhatsApp saved ✓')">Save WhatsApp</button></div>
        </div>

        <div class="ss-sec">
          <div class="ss-title">Claude AI</div>
          <div class="sr sr-col">
            <div class="sr-l">API Key</div>
            <div class="sr-s">Stored in browser only</div>
            <input id="claude-key" class="si" type="password" placeholder="sk-ant-..."/>
          </div>
          <div style="padding:0 14px 14px;"><button class="savebtn" onclick="saveKey()">Save API Key</button></div>
        </div>

        <div class="ss-sec">
          <div class="ss-title">Business Info</div>
          <div class="sr sr-col">
            <div class="sr-l">Notification Email</div>
            <input class="si" type="email" placeholder="info@mykonossailing.gr"/>
          </div>
          <div style="padding:0 14px 14px;"><button class="savebtn" onclick="toast('Saved ✓')">Save</button></div>
        </div>

        <div style="text-align:center;padding:16px;font-size:10px;color:var(--muted);">
          Mykonos Sailing Captain's Deck v2.0<br>Powered by Claude AI 🌊
        </div>
      </div>
    </div>

  </div><!-- /main-scroll -->

  <!-- BOTTOM NAV -->
  <div class="bnav">
    <div class="ni active" id="nav-home" onclick="goPage('home')">
      <span class="ni-icon">📊</span>
      <span class="ni-lbl">Overview</span>
    </div>
    <div class="ni" id="nav-fleet" onclick="goPage('fleet')">
      <span class="ni-icon">⚓</span>
      <span class="ni-lbl">Fleet</span>
    </div>
    <div class="ni" id="nav-bookings" onclick="goPage('bookings')">
      <span class="ni-icon">📋</span>
      <span class="ni-lbl">Bookings</span>
      <span class="ni-badge" id="bk-badge"></span>
    </div>
    <div class="ni" id="nav-admin-chat" onclick="goPage('admin-chat')">
      <span class="ni-icon">🤖</span>
      <span class="ni-lbl">AI Desk</span>
    </div>
    <div class="ni" id="nav-settings" onclick="goPage('settings')">
      <span class="ni-icon">⚙️</span>
      <span class="ni-lbl">Settings</span>
    </div>
  </div>
</div>

<!-- BOOKING MODAL -->
<div class="modal-bg" id="bk-modal">
  <div class="ms">
    <div class="mt">📋 New Booking</div>
    <input type="hidden" id="bk-edit-id"/>
    <span class="ml">Guest Name *</span>
    <input class="mi" id="bk-name" placeholder="Full Name"/>
    <span class="ml">Email</span>
    <input class="mi" id="bk-email" type="email" placeholder="guest@email.com"/>
    <span class="ml">Phone</span>
    <input class="mi" id="bk-phone" placeholder="+30..."/>
    <span class="ml">Cruise / Itinerary *</span>
    <select class="msel" id="bk-cruise">
      <option>5hr South Coast Cruise (Semi-Private)</option>
      <option>5hr South Coast Cruise (Private)</option>
      <option>5hr Delos & Rhenia Cruise (Semi-Private)</option>
      <option>5hr Delos & Rhenia Cruise (Private)</option>
      <option>3hr Sunset Cruise</option>
      <option>8hr Full Day — Delos, Rhenia & South Coast</option>
      <option>8hr Full Day — South Coast</option>
      <option>3-Day Charter: Mykonos–Paros–Naxos</option>
      <option>3-Day Charter: Mykonos–Syros–Antiparos</option>
      <option>Multi-Day Tailor Made</option>
    </select>
    <span class="ml">Vessel</span>
    <select class="msel" id="bk-vessel"></select>
    <span class="ml">Date *</span>
    <input class="mi" id="bk-date" type="date"/>
    <span class="ml">Time Slot</span>
    <select class="msel" id="bk-slot">
      <option>Morning (10:00am – 3:00pm)</option>
      <option>Afternoon (3:30pm – 8:30pm)</option>
      <option>Sunset (5:30pm – sunset)</option>
      <option>Full Day (10:00am – 6:00pm)</option>
      <option>Multi-Day</option>
    </select>
    <span class="ml">Number of Guests *</span>
    <input class="mi" id="bk-guests" type="number" placeholder="e.g. 6"/>
    <span class="ml">Price (€)</span>
    <input class="mi" id="bk-price" type="number" placeholder="e.g. 1200"/>
    <span class="ml">Notes</span>
    <input class="mi" id="bk-notes" placeholder="Special requests..."/>
    <div class="mac">
      <button class="mbtn mbtn-c" onclick="closeModal('bk-modal')">Cancel</button>
      <button class="mbtn mbtn-s" onclick="saveBooking()">Save Booking</button>
    </div>
  </div>
</div>

<!-- VESSEL MODAL -->
<div class="modal-bg" id="vessel-modal">
  <div class="ms">
    <div class="mt">⛵ Add Vessel</div>
    <span class="ml">Vessel Name *</span>
    <input class="mi" id="v-name" placeholder="e.g. Toro Bianco Lagoon 500"/>
    <span class="ml">Type</span>
    <select class="msel" id="v-type">
      <option>Catamaran</option><option>Sailing Yacht</option><option>Motor Yacht</option><option>RIB Boat</option><option>Other</option>
    </select>
    <span class="ml">Max Guests</span>
    <input class="mi" id="v-guests" type="number" placeholder="e.g. 16"/>
    <span class="ml">Crew</span>
    <input class="mi" id="v-crew" type="number" placeholder="e.g. 2"/>
    <span class="ml">Size</span>
    <input class="mi" id="v-size" placeholder="e.g. 42ft"/>
    <div class="mac">
      <button class="mbtn mbtn-c" onclick="closeModal('vessel-modal')">Cancel</button>
      <button class="mbtn mbtn-s" onclick="saveVessel()">Add Vessel</button>
    </div>
  </div>
</div>

<div id="toast">✓ <span id="toast-txt"></span></div>

<script>
// ══════════════════
// DATA
// ══════════════════
let FLEET = [
  {id:1,name:'Toro Bianco Lagoon 500',type:'Catamaran',guests:31,crew:3,size:'50ft',active:true,emoji:'🛥️'},
  {id:2,name:'Paraschos Sailing Yacht',type:'Sailing Yacht',guests:12,crew:2,size:'52ft',active:true,emoji:'⛵'},
  {id:3,name:'Swell Lagoon Catamaran',type:'Catamaran',guests:17,crew:3,size:'42ft',active:true,emoji:'🛥️'},
  {id:4,name:'Proteas Lagoon 420',type:'Catamaran',guests:16,crew:2,size:'42ft',active:true,emoji:'🛥️'},
  {id:5,name:'Nireas Fountaine Pajot 450',type:'Catamaran',guests:16,crew:2,size:'45ft',active:true,emoji:'🛥️'},
  {id:6,name:'Endless & Summer Rib Boats',type:'RIB Boat',guests:9,crew:1,size:'30ft',active:true,emoji:'🚤'},
  {id:7,name:'Alfamarine M/Y',type:'Motor Yacht',guests:16,crew:2,size:'50ft',active:true,emoji:'🛳️'},
  {id:8,name:'Numarine M/Y Fly',type:'Motor Yacht',guests:10,crew:2,size:'56ft',active:true,emoji:'🛳️'},
  {id:9,name:'Pershing 40ft',type:'Motor Yacht',guests:10,crew:2,size:'40ft',active:true,emoji:'🚤'},
];

let BOOKINGS = [];

// Analytics: {year: {month: {bookings, guests, revenue, chats}}}
let ANALYTICS = {};

let adminHistory = [];
let customerHistory = [];
let currentPeriod = 'today';
let currentBkFilter = 'all';

// ══════════════════
// AUTH
// ══════════════════
function doLogin(){
  const u=document.getElementById('l-user').value.trim().toLowerCase();
  const p=document.getElementById('l-pass').value.trim();
  if(u===''||p===''){alert('Please enter username and password');return;}
  if(u==='captain'&&(p==='mykonos2024'||p==='mykonos'||p==='1234')){
    document.getElementById('login').style.display='none';
    document.getElementById('app').classList.add('show');
    loadData();
    renderAll();
  } else {
    document.getElementById('l-err').textContent='Incorrect credentials';
    setTimeout(()=>document.getElementById('l-err').textContent='',2000);
  }
}

// ══════════════════
// PERSIST
// ══════════════════
function saveData(){
  try{
    localStorage.setItem('mks_bookings',JSON.stringify(BOOKINGS));
    localStorage.setItem('mks_fleet',JSON.stringify(FLEET));
    localStorage.setItem('mks_analytics',JSON.stringify(ANALYTICS));
  }catch(e){}
}
function loadData(){
  try{
    const b=localStorage.getItem('mks_bookings'); if(b) BOOKINGS=JSON.parse(b);
    const f=localStorage.getItem('mks_fleet'); if(f) FLEET=JSON.parse(f);
    const a=localStorage.getItem('mks_analytics'); if(a) ANALYTICS=JSON.parse(a);
    const k=localStorage.getItem('mks_key'); if(k) document.getElementById('claude-key').value=k;
  }catch(e){}
}

// ══════════════════
// NAVIGATION
// ══════════════════
function goPage(p){
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.ni').forEach(x=>x.classList.remove('active'));
  document.getElementById('pg-'+p).classList.add('active');
  const nav=document.getElementById('nav-'+p);
  if(nav) nav.classList.add('active');
  document.getElementById('main-scroll').scrollTop=0;
  if(p==='home') renderDash();
  if(p==='fleet') renderFleet();
  if(p==='bookings') renderBookings();
  if(p==='admin-chat'){
    document.getElementById('admin-welcome-time').textContent=getTime();
    setTimeout(()=>document.getElementById('admin-msgs').scrollTop=99999,100);
  }
  if(p==='customer-chat'||p==='settings') return;
}

// ══════════════════
// RENDER ALL
// ══════════════════
function renderAll(){
  const now=new Date();
  document.getElementById('tb-date').textContent=now.toLocaleDateString('en-US',{month:'short',day:'numeric'});
  document.getElementById('admin-welcome-time').textContent=getTime();
  document.getElementById('cust-welcome-time').textContent=getTime();
  populateVesselSelect();
  renderDash();
  renderFleet();
  renderBookings();
  updateBadge();
}

// ══════════════════
// ANALYTICS HELPERS
// ══════════════════
function getStats(period){
  const now=new Date();
  const todayStr=now.toISOString().slice(0,10);
  const thisMonth=now.getMonth();
  const thisYear=now.getFullYear();

  let bks=BOOKINGS;
  if(period==='today') bks=BOOKINGS.filter(b=>b.createdAt&&b.createdAt.slice(0,10)===todayStr);
  else if(period==='month') bks=BOOKINGS.filter(b=>{
    const d=new Date(b.createdAt);
    return d.getMonth()===thisMonth&&d.getFullYear()===thisYear;
  });
  else if(period==='year') bks=BOOKINGS.filter(b=>new Date(b.createdAt).getFullYear()===thisYear);

  const revenue=bks.reduce((s,b)=>s+(parseFloat(b.price)||0),0);
  const guests=bks.reduce((s,b)=>s+(parseInt(b.guests)||0),0);
  const chats=bks.filter(b=>b.fromChat).length;
  return {bookings:bks.length,guests,revenue,chats,list:bks};
}

function getMonthlyData(year){
  const months=['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'];
  return months.map((m,i)=>{
    const bks=BOOKINGS.filter(b=>{
      const d=new Date(b.createdAt);
      return d.getMonth()===i&&d.getFullYear()===year;
    });
    return {
      month:m,
      bookings:bks.length,
      revenue:bks.reduce((s,b)=>s+(parseFloat(b.price)||0),0),
      guests:bks.reduce((s,b)=>s+(parseInt(b.guests)||0),0)
    };
  });
}

// ══════════════════
// RENDER DASHBOARD
// ══════════════════
function renderDash(){
  const now=new Date();
  const year=now.getFullYear();
  const stats=getStats(currentPeriod);
  const labels={today:'Today',month:'This Month',year:'This Year',all:'All Time'};
  document.getElementById('home-sub').textContent=now.toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
  document.getElementById('s-bookings').textContent=stats.bookings;
  document.getElementById('s-chats').textContent=stats.chats;
  document.getElementById('s-guests').textContent=stats.guests;
  document.getElementById('s-revenue').textContent='€'+(stats.revenue>=1000?(stats.revenue/1000).toFixed(1)+'k':stats.revenue);
  document.getElementById('year-label').textContent=year;

  // Monthly chart
  const monthly=getMonthlyData(year);
  const maxBk=Math.max(...monthly.map(m=>m.bookings),1);
  const grid=document.getElementById('month-grid');
  grid.innerHTML=monthly.map((m,i)=>`
    <div class="mc ${i===now.getMonth()?'selected':''}" title="${m.bookings} bookings · €${m.revenue}">
      <div class="mc-m">${m.month}</div>
      <div class="mc-n">${m.bookings}</div>
      <div class="mc-l">€${m.revenue>=1000?(m.revenue/1000).toFixed(1)+'k':m.revenue||'–'}</div>
    </div>
  `).join('');

  // Today's bookings preview
  const todayStr=now.toISOString().slice(0,10);
  const todayBks=BOOKINGS.filter(b=>b.date===todayStr||b.createdAt?.slice(0,10)===todayStr);
  const el=document.getElementById('today-bk-list');
  if(!todayBks.length){
    el.innerHTML='<div class="empty" style="padding:20px;"><div class="empty-i">⛵</div><div class="empty-t">No bookings today</div></div>';
  } else {
    el.innerHTML=todayBks.map(b=>`
      <div style="padding:8px 0;border-bottom:1px solid var(--border2);display:flex;justify-content:space-between;align-items:center;">
        <div>
          <div style="font-size:12px;color:var(--white);">${b.name}</div>
          <div style="font-size:10px;color:var(--muted);">${b.cruise} · ${b.slot||'TBD'}</div>
        </div>
        <div style="text-align:right;">
          <span class="sb s-${b.status}">${b.status}</span>
          ${b.price?`<div style="font-size:10px;color:var(--gold);margin-top:3px;">€${b.price}</div>`:''}
        </div>
      </div>
    `).join('');
  }
}

function setPeriod(p,el){
  currentPeriod=p;
  document.querySelectorAll('.ptabs .ptab').forEach(x=>x.classList.remove('active'));
  el.classList.add('active');
  renderDash();
}

// ══════════════════
// FLEET RENDER
// ══════════════════
function renderFleet(){
  const now=new Date();
  const todayStr=now.toISOString().slice(0,10);
  document.getElementById('fleet-date-sub').textContent=now.toLocaleDateString('en-US',{weekday:'long',month:'long',day:'numeric'});

  const el=document.getElementById('fleet-list');
  el.innerHTML=FLEET.map(v=>{
    const todayBks=BOOKINGS.filter(b=>b.vesselId===v.id&&b.date===todayStr&&b.status!=='cancelled');
    const isBooked=todayBks.length>0;
    const statusClass=!v.active?'vs-off':isBooked?'vs-booked':'vs-free';
    const statusText=!v.active?'Inactive':isBooked?`Booked (${todayBks.length})`:'Available';
    return `
    <div class="vessel-card">
      <div class="vh">
        <div class="ve">${v.emoji}</div>
        <div class="vi">
          <div class="vn">${v.name}</div>
          <div class="vt">${v.type} · ${v.size} · max ${v.guests} guests</div>
        </div>
        <span class="vs-status ${statusClass}">${statusText}</span>
        <div class="toggle ${v.active?'on':''}" onclick="toggleVessel(${v.id})" style="margin-left:8px;"></div>
      </div>
      ${todayBks.length?`
      <div class="vbookings">
        ${todayBks.map(b=>`
          <div class="vb-item">
            <div>
              <div class="vb-guest">${b.name}</div>
              <div class="vb-detail">${b.cruise} · ${b.guests||'?'} guests</div>
            </div>
            <div class="vb-time">${b.slot||'TBD'}${b.price?`<br><span style="color:var(--gold)">€${b.price}</span>`:''}</div>
          </div>
        `).join('')}
      </div>`:``}
    </div>`;
  }).join('');
}

function toggleVessel(id){
  const v=FLEET.find(f=>f.id===id);
  if(!v) return;
  v.active=!v.active;
  saveData();
  syncFleet();
  renderFleet();
  renderDash();
  toast(`${v.name} — ${v.active?'Active ✓':'Hidden from agent'}`);
}

function saveVessel(){
  const name=document.getElementById('v-name').value.trim();
  if(!name){toast('Enter vessel name');return;}
  const v={
    id:Date.now(),name,
    type:document.getElementById('v-type').value,
    guests:parseInt(document.getElementById('v-guests').value)||0,
    crew:parseInt(document.getElementById('v-crew').value)||0,
    size:document.getElementById('v-size').value||'—',
    active:true,emoji:'⛵'
  };
  FLEET.push(v);
  closeModal('vessel-modal');
  saveData();
  syncFleet();
  populateVesselSelect();
  renderFleet();
  toast(`${v.name} added ✓`);
}

function syncFleet(){
  fetch('/fleet',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fleet:FLEET})}).catch(()=>{});
}

// ══════════════════
// BOOKINGS
// ══════════════════
function populateVesselSelect(){
  const sel=document.getElementById('bk-vessel');
  sel.innerHTML='<option value="">— No specific vessel —</option>'+FLEET.filter(v=>v.active).map(v=>`<option value="${v.id}">${v.name}</option>`).join('');
}

function renderBookings(){
  const el=document.getElementById('bookings-list');
  let bks=currentBkFilter==='all'?BOOKINGS:BOOKINGS.filter(b=>b.status===currentBkFilter);
  bks=[...bks].reverse();
  if(!bks.length){
    el.innerHTML='<div class="empty"><div class="empty-i">📋</div><div class="empty-t">No bookings</div></div>';
    return;
  }
  el.innerHTML=bks.map(b=>`
    <div class="bk-card">
      <div class="bkh">
        <span class="bk-id">#${b.id}</span>
        <span class="sb s-${b.status}">${b.status}</span>
      </div>
      <div class="bkb">
        <div class="bkr"><span class="bkk">Guest</span><span class="bkv">${b.name}</span></div>
        ${b.email?`<div class="bkr"><span class="bkk">Email</span><span class="bkv">${b.email}</span></div>`:''}
        ${b.phone?`<div class="bkr"><span class="bkk">Phone</span><span class="bkv">${b.phone}</span></div>`:''}
        <div class="bkr"><span class="bkk">Cruise</span><span class="bkv">${b.cruise}</span></div>
        <div class="bkr"><span class="bkk">Date</span><span class="bkv">${b.date||'TBD'}</span></div>
        <div class="bkr"><span class="bkk">Slot</span><span class="bkv">${b.slot||'TBD'}</span></div>
        <div class="bkr"><span class="bkk">Guests</span><span class="bkv">${b.guests||'—'}</span></div>
        ${b.price?`<div class="bkr"><span class="bkk">Price</span><span class="bkv" style="color:var(--gold)">€${b.price}</span></div>`:''}
        ${b.vessel?`<div class="bkr"><span class="bkk">Vessel</span><span class="bkv">${b.vessel}</span></div>`:''}
        ${b.notes?`<div class="bkr"><span class="bkk">Notes</span><span class="bkv">${b.notes}</span></div>`:''}
        <div style="font-size:9px;color:var(--muted);margin-top:5px;">${b.fromChat?'📱 From AI Chat · ':''}${new Date(b.createdAt).toLocaleString()}</div>
        <div class="bk-acts">
          ${b.status==='new'?`<button class="bka bka-conf" onclick="setBkStatus(${b.id},'confirmed')">✓ Confirm</button>`:''}
          ${b.status==='confirmed'?`<button class="bka bka-done" onclick="setBkStatus(${b.id},'done')">✓ Done</button>`:''}
          <button class="bka" style="background:rgba(201,168,76,.1);color:var(--gold);border:1px solid rgba(201,168,76,.2);" onclick="editBk(${b.id})">✏️ Edit</button>
          <button class="bka bka-del" onclick="deleteBk(${b.id})">✕</button>
        </div>
      </div>
    </div>
  `).join('');
}

function filterBk(f,el){
  currentBkFilter=f;
  document.querySelectorAll('#pg-bookings .ptab').forEach(x=>x.classList.remove('active'));
  el.classList.add('active');
  renderBookings();
}

function saveBooking(){
  const name=document.getElementById('bk-name').value.trim();
  if(!name){toast('Enter guest name');return;}
  const vid=parseInt(document.getElementById('bk-vessel').value)||null;
  const vessel=vid?FLEET.find(v=>v.id===vid)?.name:'';
  const editId=document.getElementById('bk-edit-id').value;
  const b={
    id:editId?parseInt(editId):Date.now(),
    name,
    email:document.getElementById('bk-email').value.trim(),
    phone:document.getElementById('bk-phone').value.trim(),
    cruise:document.getElementById('bk-cruise').value,
    vesselId:vid,
    vessel,
    slot:document.getElementById('bk-slot').value,
    date:document.getElementById('bk-date').value,
    guests:document.getElementById('bk-guests').value,
    price:document.getElementById('bk-price').value,
    notes:document.getElementById('bk-notes').value.trim(),
    status:editId?BOOKINGS.find(x=>x.id===parseInt(editId))?.status||'new':'new',
    fromChat:false,
    createdAt:editId?BOOKINGS.find(x=>x.id===parseInt(editId))?.createdAt||new Date().toISOString():new Date().toISOString()
  };
  if(editId) BOOKINGS=BOOKINGS.map(x=>x.id===parseInt(editId)?b:x);
  else BOOKINGS.push(b);
  closeModal('bk-modal');
  clearBkForm();
  saveData();
  renderBookings();renderDash();updateBadge();
  toast(editId?'Booking updated ✓':`Booking #${b.id} created ✓`);
}

function editBk(id){
  const b=BOOKINGS.find(x=>x.id===id);if(!b) return;
  document.getElementById('bk-edit-id').value=b.id;
  document.getElementById('bk-name').value=b.name;
  document.getElementById('bk-email').value=b.email||'';
  document.getElementById('bk-phone').value=b.phone||'';
  document.getElementById('bk-cruise').value=b.cruise;
  document.getElementById('bk-slot').value=b.slot||'';
  document.getElementById('bk-date').value=b.date||'';
  document.getElementById('bk-guests').value=b.guests||'';
  document.getElementById('bk-price').value=b.price||'';
  document.getElementById('bk-notes').value=b.notes||'';
  openModal('bk-modal');
}

function clearBkForm(){
  ['bk-edit-id','bk-name','bk-email','bk-phone','bk-date','bk-guests','bk-price','bk-notes'].forEach(id=>document.getElementById(id).value='');
}

function setBkStatus(id,status){
  const b=BOOKINGS.find(x=>x.id===id);
  if(b){b.status=status;saveData();renderBookings();renderDash();updateBadge();toast(`Booking ${status} ✓`);}
}

function deleteBk(id){
  BOOKINGS=BOOKINGS.filter(x=>x.id!==id);
  saveData();renderBookings();renderDash();updateBadge();toast('Booking removed');
}

function updateBadge(){
  const n=BOOKINGS.filter(b=>b.status==='new').length;
  const badge=document.getElementById('bk-badge');
  badge.textContent=n;
  badge.style.display=n?'flex':'none';
}

function checkBookingData(txt){
  const m=txt.match(/BOOKING_DATA:\s*(\{[\s\S]*?\})/);
  if(!m) return;
  try{
    const d=JSON.parse(m[1]);
    const vid=FLEET.find(v=>v.name.toLowerCase().includes((d.vessel||'').toLowerCase()))?.id||null;
    const b={
      id:Date.now(),
      name:d.name||d.guest_name||'Guest',
      email:d.email||'',phone:d.phone||'',
      cruise:d.cruise||d.itinerary||'',
      vesselId:vid,vessel:d.vessel||'',
      slot:d.slot||d.time||'',
      date:d.date||'',
      guests:d.guests||d.num_guests||'',
      price:d.price||'',
      notes:d.notes||'',
      status:'new',fromChat:true,
      createdAt:new Date().toISOString()
    };
    BOOKINGS.push(b);
    saveData();renderDash();updateBadge();
    toast(`🎉 New booking #${b.id} from chat!`);
  }catch(e){}
}

// ══════════════════
// ADMIN AI CHAT
// ══════════════════
function buildAdminContext(){
  const now=new Date();
  const todayStr=now.toISOString().slice(0,10);
  const thisMonth=now.getMonth();
  const thisYear=now.getFullYear();
  const todayBks=BOOKINGS.filter(b=>b.date===todayStr||b.createdAt?.slice(0,10)===todayStr);
  const monthBks=BOOKINGS.filter(b=>{const d=new Date(b.createdAt);return d.getMonth()===thisMonth&&d.getFullYear()===thisYear;});
  const yearBks=BOOKINGS.filter(b=>new Date(b.createdAt).getFullYear()===thisYear);
  const monthlyData=getMonthlyData(thisYear);

  const fleetStatus=FLEET.map(v=>{
    const bks=BOOKINGS.filter(b=>b.vesselId===v.id&&b.date===todayStr&&b.status!=='cancelled');
    return `${v.name}: ${!v.active?'INACTIVE':bks.length?`BOOKED (${bks.map(b=>`${b.name}, ${b.slot||'TBD'}`).join('; ')})`:
    'AVAILABLE'}`;
  }).join('\n');

  const recentBks=BOOKINGS.slice(-10).reverse().map(b=>
    `#${b.id} | ${b.name} | ${b.cruise} | ${b.date||'TBD'} | ${b.status} | €${b.price||'0'} | ${b.guests||'?'} guests`
  ).join('\n');

  const monthlyStr=monthlyData.map((m,i)=>
    `${m.month}: ${m.bookings} bookings, ${m.guests} guests, €${m.revenue}`
  ).join('\n');

  return `You are the private business intelligence assistant for Mykonos Sailing — a yacht charter company in Mykonos, Greece.
You ONLY speak to the business owner/captain. NEVER share operational or revenue data with anyone else.
You have access to all business data and can answer questions about bookings, fleet, revenue, and performance.

TODAY: ${now.toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'})}
TIME: ${now.toLocaleTimeString()}

=== TODAY'S STATS ===
Bookings today: ${todayBks.length}
Today's guests: ${todayBks.reduce((s,b)=>s+(parseInt(b.guests)||0),0)}
Today's revenue: €${todayBks.reduce((s,b)=>s+(parseFloat(b.price)||0),0)}
New (unconfirmed): ${todayBks.filter(b=>b.status==='new').length}

=== THIS MONTH (${now.toLocaleString('default',{month:'long'})}) ===
Bookings: ${monthBks.length}
Guests: ${monthBks.reduce((s,b)=>s+(parseInt(b.guests)||0),0)}
Revenue: €${monthBks.reduce((s,b)=>s+(parseFloat(b.price)||0),0)}

=== THIS YEAR (${thisYear}) ===
Bookings: ${yearBks.length}
Guests: ${yearBks.reduce((s,b)=>s+(parseInt(b.guests)||0),0)}
Revenue: €${yearBks.reduce((s,b)=>s+(parseFloat(b.price)||0),0)}

=== MONTHLY BREAKDOWN ${thisYear} ===
${monthlyStr}

=== ALL TIME ===
Total bookings: ${BOOKINGS.length}
Total guests: ${BOOKINGS.reduce((s,b)=>s+(parseInt(b.guests)||0),0)}
Total revenue: €${BOOKINGS.reduce((s,b)=>s+(parseFloat(b.price)||0),0)}

=== TODAY'S FLEET STATUS ===
${fleetStatus}

=== RECENT BOOKINGS (last 10) ===
${recentBks||'No bookings yet'}

=== FLEET ===
${FLEET.map(v=>`${v.name} (${v.type}, max ${v.guests}): ${v.active?'Active':'Inactive'}`).join('\n')}

Respond in the same language the captain writes in. Be concise and data-driven. Format numbers clearly.`;
}

async function sendAdmin(){
  const inp=document.getElementById('admin-inp');
  const msg=inp.value.trim();
  if(!msg) return;
  inp.value='';inp.disabled=true;
  addAdminMsg(msg,true);
  adminHistory.push({role:'user',content:msg});
  const typ=document.getElementById('admin-typing');
  typ.style.display='block';
  document.getElementById('admin-msgs').scrollTop=99999;

  try{
    const res=await fetch('/chat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({system:buildAdminContext(),messages:adminHistory})
    });
    const data=await res.json();
    typ.style.display='none';inp.disabled=false;inp.focus();
    if(data.error){addAdminMsg('❌ '+( data.error.message||JSON.stringify(data.error)),false);return;}
    const reply=data.content.map(b=>b.text||'').join('');
    adminHistory.push({role:'assistant',content:reply});
    addAdminMsg(reply,false);
  }catch(e){
    typ.style.display='none';inp.disabled=false;
    addAdminMsg('❌ '+e.message,false);
  }
}

function adminQ(msg){document.getElementById('admin-inp').value=msg;sendAdmin();}

function addAdminMsg(txt,isOut){
  const el=document.getElementById('admin-msgs');
  const d=document.createElement('div');
  d.className='msg '+(isOut?'msg-out':'msg-in');
  d.innerHTML=txt.replace(/\n/g,'<br>')+`<div class="msg-time">${getTime()}</div>`;
  el.appendChild(d);el.scrollTop=99999;
}

// ══════════════════
// CUSTOMER CHAT
// ══════════════════
function buildCustomerPrompt(){
  const activeFleet=FLEET.filter(v=>v.active);
  const fleetList=activeFleet.map(v=>`- ${v.name} (${v.type}, ${v.size}, max ${v.guests} guests + ${v.crew} crew)`).join('\n');
  return `You are the booking assistant for Mykonos Sailing, a premier yacht charter company in Mykonos, Greece.

You ONLY help customers with bookings and questions about cruises. NEVER discuss internal business data, revenue, number of bookings, or operational information.

COMPANY: Mykonos Sailing | mykonossailing.gr | @mykonossailing
DEPARTURE: Ornos Bay, small dock on left side of beach
LICENSE: MHTE 07.26.E.70.00.00459.0.1 (ISO certified)

AVAILABLE FLEET:
${fleetList}

CRUISES:
1. 5hr South Coast (10–3pm or 3:30–8:30pm) — Psarou, Paradise, Super Paradise, Elia + more
2. 5hr Delos & Rhenia (10–3pm or 3:30–8:30pm) — UNESCO Delos + crystal waters of Rhenia
3. 3hr Sunset Cruise (5:30pm–sunset) — Greek appetizers, wine, magic golden hour
4. 8hr Full Day: Delos+Rhenia+South (10–6pm) — Includes guided Delos tour
5. 8hr Full Day South Coast (10–6pm) — All hidden and famous beaches
6. 3-Day Charter: Mykonos→Paros→Naxos
7. 3-Day Charter: Mykonos→Syros→Antiparos
8. Multi-Day Tailor Made — custom route, any islands

INCLUDED IN ALL CRUISES: ✓ Lunch/dinner ✓ Unlimited drinks ✓ Beach towels ✓ Snorkeling/SUP ✓ Music (Bluetooth) ✓ Professional crew
NOT INCLUDED: Hotel transfers (can arrange), gratuities, Seabob (extra)

PRICING: Do not give specific prices. Say pricing depends on vessel, group size and season, and offer to send a custom quote.

BOOKING INFO TO COLLECT: name, email, cruise type, private/semi-private, date, number of guests, special requests.

PERSONALITY: Warm, enthusiastic, loves the sea. Paint the experience. Be conversational. Reply in same language as customer.

When booking info complete, output: BOOKING_DATA:{"name":"...","email":"...","cruise":"...","date":"...","guests":"...","slot":"...","notes":"..."}`;
}

async function sendCustomer(){
  const inp=document.getElementById('cust-inp');
  const msg=inp.value.trim();
  if(!msg) return;
  inp.value='';inp.disabled=true;
  addCustMsg(msg,true);
  customerHistory.push({role:'user',content:msg});
  const typ=document.getElementById('cust-typing');
  typ.style.display='block';
  document.getElementById('customer-msgs').scrollTop=99999;

  try{
    const res=await fetch('/chat',{
      method:'POST',
      headers:{'Content-Type':'application/json'},
      body:JSON.stringify({system:buildCustomerPrompt(),messages:customerHistory})
    });
    const data=await res.json();
    typ.style.display='none';inp.disabled=false;inp.focus();
    if(data.error){addCustMsg('❌ '+(data.error.message||JSON.stringify(data.error)),false);return;}
    const reply=data.content.map(b=>b.text||'').join('');
    customerHistory.push({role:'assistant',content:reply});
    const displayReply=reply.replace(/BOOKING_DATA:\s*\{[\s\S]*?\}/,'').trim();
    addCustMsg(displayReply,false);
    checkBookingData(reply);
  }catch(e){
    typ.style.display='none';inp.disabled=false;
    addCustMsg('❌ '+e.message,false);
  }
}

function custQ(msg){document.getElementById('cust-inp').value=msg;sendCustomer();}

function addCustMsg(txt,isOut){
  const el=document.getElementById('customer-msgs');
  const d=document.createElement('div');
  d.className='msg '+(isOut?'msg-out':'msg-in');
  d.innerHTML=txt.replace(/\n/g,'<br>')+`<div class="msg-time">${getTime()}</div>`;
  el.appendChild(d);el.scrollTop=99999;
}

// ══════════════════
// SETTINGS
// ══════════════════
function saveKey(){
  const k=document.getElementById('claude-key').value.trim();
  if(k) localStorage.setItem('mks_key',k);
  toast('API Key saved ✓');
}

// ══════════════════
// HELPERS
// ══════════════════
function getTime(){return new Date().toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',hour12:true});}
function openModal(id){document.getElementById(id).classList.add('open');}
function closeModal(id){document.getElementById(id).classList.remove('open');}
function toast(msg){
  const t=document.getElementById('toast');
  document.getElementById('toast-txt').textContent=msg;
  t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'),2500);
}
document.querySelectorAll('.modal-bg').forEach(m=>{
  m.addEventListener('click',function(e){if(e.target===this)this.classList.remove('open');});
});
</script>
</body>
</html>
'''

@app.route("/", methods=["GET"])
def home():
    return Response(DASHBOARD, mimetype="text/html")

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 1024, "system": data.get("system",""), "messages": data.get("messages",[])},
            timeout=30
        )
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
