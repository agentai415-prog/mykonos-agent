from flask import Flask, request, jsonify, Response
from flask_cors import CORS
import requests, os, json

app = Flask(__name__)
CORS(app, origins="*")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")

FLEET_STORE = {"fleet": [
  {"id":1,"name":"Toro Bianco Lagoon 500","type":"Catamaran","guests":31,"crew":3,"size":"50ft","active":True,"emoji":"🛥️"},
  {"id":2,"name":"Paraschos Sailing Yacht","type":"Sailing Yacht","guests":12,"crew":2,"size":"52ft","active":True,"emoji":"⛵"},
  {"id":3,"name":"Swell Lagoon Catamaran","type":"Catamaran","guests":17,"crew":3,"size":"42ft","active":True,"emoji":"🛥️"},
  {"id":4,"name":"Proteas Lagoon 420","type":"Catamaran","guests":16,"crew":2,"size":"42ft","active":True,"emoji":"🛥️"},
  {"id":5,"name":"Nireas Fountaine Pajot 450","type":"Catamaran","guests":16,"crew":2,"size":"45ft","active":True,"emoji":"🛥️"},
  {"id":6,"name":"Endless & Summer Rib Boats","type":"RIB Boat","guests":9,"crew":1,"size":"30ft","active":True,"emoji":"🚤"},
  {"id":7,"name":"Alfamarine M/Y","type":"Motor Yacht","guests":16,"crew":2,"size":"50ft","active":True,"emoji":"🛳️"},
  {"id":8,"name":"Numarine M/Y Fly","type":"Motor Yacht","guests":10,"crew":2,"size":"56ft","active":True,"emoji":"🛳️"},
  {"id":9,"name":"Pershing 40ft","type":"Motor Yacht","guests":10,"crew":2,"size":"40ft","active":True,"emoji":"🚤"},
]}

DASHBOARD = '''<!DOCTYPE html>
<html lang="en" dir="ltr">
<head>
<meta charset="UTF-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no"/>
<title>Mykonos Sailing — Admin</title>
<link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,300;0,400;0,500;1,300;1,400&family=Jost:wght@300;400;500;600&display=swap" rel="stylesheet"/>
<style>
:root{
  --navy:#0a1628;--navy2:#0f2040;--navy3:#152a52;
  --sea:#1a4a7a;--sea2:#1e5c9a;
  --gold:#c9a84c;--gold2:#e8c875;--gold3:#f0d878;
  --white:#f0f4f8;--muted:#8899aa;
  --card:#0d1e36;--card2:#112440;
  --border:rgba(201,168,76,.18);--border2:rgba(201,168,76,.08);
  --text:#dde8f0;--text2:#a0b4c8;
  --green:#2ecc71;--red:#e74c3c;--orange:#f39c12;
  --radius:12px;--radius-sm:8px;
}
*{box-sizing:border-box;margin:0;padding:0;-webkit-tap-highlight-color:transparent;}
html,body{height:100%;overscroll-behavior:none;}
body{background:var(--navy);color:var(--text);font-family:'Jost',sans-serif;font-weight:300;overflow:hidden;}

/* ocean bg */
body::before{content:'';position:fixed;inset:0;pointer-events:none;z-index:0;
  background:radial-gradient(ellipse 80% 60% at 20% 0%,rgba(26,74,122,.4),transparent),
              radial-gradient(ellipse 60% 80% at 80% 100%,rgba(15,32,64,.6),transparent);
}

/* LOGIN */
#login{position:fixed;inset:0;z-index:999;background:var(--navy);display:flex;align-items:center;justify-content:center;padding:24px;}
.login-card{width:100%;max-width:340px;position:relative;z-index:1;}
.login-top{text-align:center;margin-bottom:32px;}
.login-logo{font-family:'Cormorant Garamond',serif;font-size:11px;letter-spacing:6px;color:var(--gold);text-transform:uppercase;display:block;margin-bottom:8px;}
.login-brand{font-family:'Cormorant Garamond',serif;font-size:32px;letter-spacing:3px;color:var(--white);display:block;}
.login-sub{font-size:11px;letter-spacing:3px;color:var(--muted);text-transform:uppercase;margin-top:4px;display:block;}
.login-wave{display:block;text-align:center;margin:16px 0;opacity:.4;}
.l-lbl{font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:6px;display:block;}
.l-inp{width:100%;background:rgba(255,255,255,.05);border:1px solid var(--border);border-radius:var(--radius-sm);padding:12px 14px;color:var(--white);font-family:'Jost',sans-serif;font-size:14px;outline:none;transition:border-color .2s;margin-bottom:16px;direction:ltr;}
.l-inp:focus{border-color:var(--gold);}
.btn-primary{width:100%;padding:14px;background:var(--gold);color:#000;border:none;border-radius:var(--radius-sm);font-family:'Jost',sans-serif;font-size:14px;font-weight:500;letter-spacing:1px;cursor:pointer;transition:all .2s;}
.btn-primary:active{transform:scale(.98);}
.l-err{color:var(--red);font-size:12px;text-align:center;min-height:18px;margin-top:8px;}
.l-hint{font-size:11px;color:var(--muted);text-align:center;margin-top:12px;}

/* APP SHELL */
#app{display:none;height:100%;flex-direction:column;position:relative;z-index:1;}
#app.show{display:flex;}

/* TOPBAR */
.topbar{height:54px;background:rgba(10,22,40,.9);backdrop-filter:blur(10px);border-bottom:1px solid var(--border2);display:flex;align-items:center;padding:0 16px;gap:12px;flex-shrink:0;position:relative;z-index:50;}
.topbar-mark{width:30px;height:30px;display:flex;align-items:center;justify-content:center;border:1px solid var(--border);border-radius:6px;}
.topbar-mark svg{width:18px;height:18px;}
.topbar-name{font-family:'Cormorant Garamond',serif;letter-spacing:3px;font-size:15px;color:var(--gold2);}
.topbar-right{display:flex;align-items:center;gap:8px;margin-left:auto;}
.live-dot-wrap{display:flex;align-items:center;gap:5px;background:rgba(46,204,113,.1);border:1px solid rgba(46,204,113,.3);border-radius:20px;padding:3px 10px 3px 6px;cursor:pointer;}
.live-dot{width:7px;height:7px;border-radius:50%;background:var(--green);box-shadow:0 0 6px var(--green);animation:blink 2s infinite;}
@keyframes blink{0%,100%{opacity:1}50%{opacity:.4}}
.live-text{font-size:10px;letter-spacing:1px;color:var(--green);}
.topbar-menu{width:32px;height:32px;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:5px;cursor:pointer;}
.topbar-menu span{width:18px;height:1px;background:var(--gold);display:block;}

/* MAIN SCROLL */
.main-scroll{flex:1;overflow-y:auto;overflow-x:hidden;padding:16px;padding-bottom:80px;}

/* BOTTOM NAV */
.bottom-nav{height:60px;background:rgba(10,22,40,.95);backdrop-filter:blur(10px);border-top:1px solid var(--border2);display:flex;align-items:center;flex-shrink:0;safe-area-inset-bottom:env(safe-area-inset-bottom);}
.nav-item{flex:1;display:flex;flex-direction:column;align-items:center;justify-content:center;gap:3px;cursor:pointer;padding:8px;position:relative;}
.nav-icon{font-size:20px;transition:transform .2s;}
.nav-label{font-size:9px;letter-spacing:1px;color:var(--muted);text-transform:uppercase;transition:color .2s;}
.nav-item.active .nav-label{color:var(--gold);}
.nav-item.active .nav-icon{transform:scale(1.1);}
.nav-badge{position:absolute;top:6px;right:calc(50% - 16px);background:var(--red);color:#fff;font-size:9px;width:16px;height:16px;border-radius:50%;display:flex;align-items:center;justify-content:center;display:none;}

/* PAGES */
.page{display:none;}
.page.active{display:block;}

/* SECTION TITLE */
.sect-title{font-family:'Cormorant Garamond',serif;font-size:22px;letter-spacing:1px;margin-bottom:4px;color:var(--white);}
.sect-sub{font-size:11px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:20px;}

/* STATS */
.stats-grid{display:grid;grid-template-columns:repeat(2,1fr);gap:12px;margin-bottom:20px;}
.stat-card{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);padding:16px;position:relative;overflow:hidden;}
.stat-card::before{content:'';position:absolute;top:0;left:0;right:0;height:2px;background:linear-gradient(90deg,var(--gold),transparent);}
.stat-num{font-family:'Cormorant Garamond',serif;font-size:32px;color:var(--gold2);line-height:1;}
.stat-lbl{font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-top:4px;}
.stat-icon{position:absolute;right:12px;top:12px;font-size:22px;opacity:.3;}

/* QUICK ACTIONS */
.actions-row{display:flex;gap:10px;margin-bottom:20px;overflow-x:auto;padding-bottom:4px;}
.action-btn{flex-shrink:0;background:var(--card2);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 16px;font-family:'Jost',sans-serif;font-size:12px;color:var(--text2);cursor:pointer;transition:all .2s;white-space:nowrap;}
.action-btn:active{background:var(--sea);color:var(--white);}

/* CARDS */
.card{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);margin-bottom:12px;overflow:hidden;}
.card-header{padding:14px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border2);}
.card-title{font-size:13px;font-weight:500;color:var(--white);}
.card-body{padding:14px 16px;}

/* YACHT CARDS */
.yacht-card{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);margin-bottom:10px;overflow:hidden;}
.yacht-header{padding:14px 16px;display:flex;align-items:center;gap:12px;}
.yacht-icon{width:42px;height:42px;background:linear-gradient(135deg,var(--sea),var(--navy3));border-radius:10px;display:flex;align-items:center;justify-content:center;font-size:20px;flex-shrink:0;}
.yacht-info{flex:1;min-width:0;}
.yacht-name{font-family:'Cormorant Garamond',serif;font-size:17px;color:var(--white);line-height:1.2;}
.yacht-type{font-size:11px;color:var(--muted);margin-top:2px;}
.yacht-capacity{font-size:11px;color:var(--gold);margin-top:2px;}
.yacht-toggle{flex-shrink:0;}
.toggle{width:44px;height:24px;background:rgba(255,255,255,.1);border-radius:12px;position:relative;cursor:pointer;transition:background .3s;border:1px solid var(--border);}
.toggle.on{background:rgba(46,204,113,.3);border-color:rgba(46,204,113,.5);}
.toggle::after{content:'';position:absolute;width:18px;height:18px;border-radius:50%;background:var(--muted);top:2px;left:2px;transition:all .3s;}
.toggle.on::after{left:22px;background:var(--green);}

/* BOOKING CARDS */
.booking-card{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);margin-bottom:10px;overflow:hidden;}
.booking-header{padding:12px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border2);}
.booking-id{font-family:'Cormorant Garamond',serif;font-size:13px;color:var(--gold);}
.booking-body{padding:12px 16px;}
.booking-row{display:flex;justify-content:space-between;margin-bottom:6px;}
.booking-key{font-size:11px;color:var(--muted);}
.booking-val{font-size:12px;color:var(--text);text-align:right;max-width:60%;}
.status-badge{font-size:10px;padding:3px 10px;border-radius:20px;font-weight:500;letter-spacing:.5px;}
.status-new{background:rgba(241,196,15,.15);color:#f1c40f;border:1px solid rgba(241,196,15,.3);}
.status-confirmed{background:rgba(46,204,113,.15);color:var(--green);border:1px solid rgba(46,204,113,.3);}
.status-done{background:rgba(108,122,137,.15);color:var(--muted);border:1px solid rgba(108,122,137,.3);}
.booking-actions{display:flex;gap:8px;margin-top:10px;}
.bk-btn{flex:1;padding:8px;border:none;border-radius:var(--radius-sm);font-size:11px;font-family:'Jost',sans-serif;cursor:pointer;font-weight:500;letter-spacing:.5px;}
.bk-confirm{background:rgba(46,204,113,.15);color:var(--green);border:1px solid rgba(46,204,113,.3);}
.bk-cancel{background:rgba(231,76,60,.1);color:var(--red);border:1px solid rgba(231,76,60,.2);}

/* CHAT */
.chat-wrap{height:calc(100vh - 54px - 60px);display:flex;flex-direction:column;}
.chat-header{padding:12px 16px;border-bottom:1px solid var(--border2);background:rgba(13,30,54,.6);flex-shrink:0;}
.chat-agent-name{font-family:'Cormorant Garamond',serif;font-size:16px;color:var(--white);}
.chat-agent-sub{font-size:10px;color:var(--muted);letter-spacing:1px;}
.chat-msgs{flex:1;overflow-y:auto;padding:16px;display:flex;flex-direction:column;gap:10px;}
.msg{max-width:80%;padding:10px 14px;border-radius:16px;font-size:13px;line-height:1.6;position:relative;}
.msg-in{background:var(--card2);border:1px solid var(--border2);border-bottom-left-radius:4px;align-self:flex-start;color:var(--text);}
.msg-out{background:linear-gradient(135deg,var(--sea),var(--sea2));border-bottom-right-radius:4px;align-self:flex-end;color:#fff;}
.msg-time{font-size:9px;color:rgba(255,255,255,.4);margin-top:4px;text-align:right;}
.typing{display:none;align-self:flex-start;background:var(--card2);border:1px solid var(--border2);padding:10px 16px;border-radius:16px;border-bottom-left-radius:4px;}
.typing span{display:inline-block;width:6px;height:6px;background:var(--muted);border-radius:50%;margin:0 2px;animation:bounce .8s infinite;}
.typing span:nth-child(2){animation-delay:.15s;}
.typing span:nth-child(3){animation-delay:.3s;}
@keyframes bounce{0%,60%,100%{transform:translateY(0)}30%{transform:translateY(-6px)}}
.chat-quick{display:flex;gap:8px;padding:8px 16px;overflow-x:auto;flex-shrink:0;border-top:1px solid var(--border2);}
.quick-btn{flex-shrink:0;background:var(--card2);border:1px solid var(--border);border-radius:20px;padding:6px 14px;font-size:11px;color:var(--text2);cursor:pointer;white-space:nowrap;transition:all .2s;}
.quick-btn:active{background:var(--sea);color:#fff;}
.chat-input-row{display:flex;gap:10px;padding:12px 16px;border-top:1px solid var(--border2);flex-shrink:0;background:rgba(10,22,40,.8);}
.chat-inp{flex:1;background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:24px;padding:10px 16px;color:var(--white);font-family:'Jost',sans-serif;font-size:13px;outline:none;}
.chat-inp::placeholder{color:var(--muted);}
.chat-send{width:42px;height:42px;background:var(--gold);border:none;border-radius:50%;display:flex;align-items:center;justify-content:center;cursor:pointer;flex-shrink:0;transition:all .2s;}
.chat-send:active{transform:scale(.93);}
.chat-send svg{width:18px;height:18px;}

/* SETTINGS */
.settings-section{background:var(--card);border:1px solid var(--border2);border-radius:var(--radius);margin-bottom:16px;overflow:hidden;}
.settings-title{font-size:10px;letter-spacing:2px;color:var(--gold);text-transform:uppercase;padding:14px 16px 8px;border-bottom:1px solid var(--border2);}
.setting-row{padding:14px 16px;display:flex;align-items:center;justify-content:space-between;border-bottom:1px solid var(--border2);}
.setting-row:last-child{border-bottom:none;}
.setting-lbl{font-size:13px;color:var(--text);}
.setting-sub{font-size:11px;color:var(--muted);margin-top:2px;}
.s-inp{background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px;color:var(--white);font-family:'Jost',sans-serif;font-size:13px;width:100%;outline:none;margin-top:8px;direction:ltr;}
.s-inp:focus{border-color:var(--gold);}
.s-select{background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px;color:var(--white);font-family:'Jost',sans-serif;font-size:13px;width:100%;outline:none;margin-top:8px;}
.save-btn{width:100%;padding:13px;background:var(--gold);color:#000;border:none;border-radius:var(--radius-sm);font-family:'Jost',sans-serif;font-size:13px;font-weight:600;letter-spacing:1px;cursor:pointer;margin-top:10px;transition:all .2s;}
.save-btn:active{transform:scale(.98);}

/* MODAL */
.modal-bg{position:fixed;inset:0;background:rgba(0,0,0,.7);z-index:800;display:flex;align-items:flex-end;opacity:0;pointer-events:none;transition:opacity .25s;}
.modal-bg.open{opacity:1;pointer-events:all;}
.modal-sheet{background:var(--navy2);border-radius:20px 20px 0 0;padding:24px;width:100%;max-height:80vh;overflow-y:auto;transform:translateY(30px);transition:transform .25s;}
.modal-bg.open .modal-sheet{transform:translateY(0);}
.modal-title{font-family:'Cormorant Garamond',serif;font-size:20px;margin-bottom:20px;color:var(--white);}
.m-lbl{font-size:10px;letter-spacing:2px;color:var(--muted);text-transform:uppercase;margin-bottom:6px;display:block;}
.m-inp{width:100%;background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px;color:var(--white);font-family:'Jost',sans-serif;font-size:13px;outline:none;margin-bottom:14px;direction:ltr;}
.m-inp:focus{border-color:var(--gold);}
.m-select{width:100%;background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:var(--radius-sm);padding:10px 12px;color:var(--white);font-family:'Jost',sans-serif;font-size:13px;outline:none;margin-bottom:14px;}
.modal-actions{display:flex;gap:10px;margin-top:8px;}
.btn-cancel{flex:1;padding:12px;background:rgba(255,255,255,.06);border:1px solid var(--border);border-radius:var(--radius-sm);color:var(--muted);font-family:'Jost',sans-serif;font-size:13px;cursor:pointer;}
.btn-save{flex:2;padding:12px;background:var(--gold);border:none;border-radius:var(--radius-sm);color:#000;font-family:'Jost',sans-serif;font-size:13px;font-weight:600;cursor:pointer;}

/* TOAST */
#toast{position:fixed;bottom:80px;left:50%;transform:translateX(-50%) translateY(20px);background:var(--card2);border:1px solid var(--border);border-radius:24px;padding:10px 20px;font-size:12px;color:var(--text);z-index:9999;opacity:0;transition:all .3s;white-space:nowrap;}
#toast.show{opacity:1;transform:translateX(-50%) translateY(0);}

/* EMPTY STATE */
.empty{text-align:center;padding:40px 20px;color:var(--muted);}
.empty-icon{font-size:40px;margin-bottom:12px;opacity:.4;}
.empty-text{font-size:13px;}

/* SCROLLBAR */
::-webkit-scrollbar{width:4px;}
::-webkit-scrollbar-track{background:transparent;}
::-webkit-scrollbar-thumb{background:var(--border);border-radius:2px;}
</style>
</head>
<body>

<!-- LOGIN -->
<div id="login">
  <div class="login-card">
    <div class="login-top">
      <span class="login-logo">⚓ Mykonos Sailing</span>
      <span class="login-brand">CAPTAIN'S DECK</span>
      <span class="login-sub">Admin Dashboard</span>
      <svg class="login-wave" width="120" height="20" viewBox="0 0 120 20">
        <path d="M0,10 Q15,0 30,10 Q45,20 60,10 Q75,0 90,10 Q105,20 120,10" fill="none" stroke="rgba(201,168,76,.4)" stroke-width="1.5"/>
      </svg>
    </div>
    <span class="l-lbl">Username</span>
    <input id="l-user" class="l-inp" type="text" placeholder="captain" autocomplete="off"/>
    <span class="l-lbl">Password</span>
    <input id="l-pass" class="l-inp" type="password" placeholder="••••••••" onkeydown="if(event.key==='Enter')doLogin()"/>
    <button class="btn-primary" onclick="doLogin()">BOARD →</button>
    <div class="l-err" id="l-err"></div>
    <div class="l-hint">captain / mykonos2024</div>
  </div>
</div>

<!-- APP -->
<div id="app">
  <!-- TOPBAR -->
  <div class="topbar">
    <div class="live-dot-wrap" onclick="goPage('chat')">
      <div class="live-dot"></div>
      <span class="live-text">ONLINE</span>
    </div>
    <span class="topbar-name">MYKONOS SAILING</span>
    <div class="topbar-right">
      <div class="topbar-mark">
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" style="color:var(--gold)">
          <path d="M3 17l4-8 4 4 4-6 4 10H3z"/>
          <path d="M3 20h18"/>
        </svg>
      </div>
      <div class="topbar-menu" onclick="goPage('settings')">
        <span></span><span></span>
      </div>
    </div>
  </div>

  <!-- MAIN -->
  <div class="main-scroll" id="main-scroll">

    <!-- HOME PAGE -->
    <div class="page active" id="pg-home">
      <div style="padding-top:8px;">
        <div class="sect-title">Good Morning, Captain 🌊</div>
        <div class="sect-sub" id="today-date">— — —</div>
        <div class="stats-grid">
          <div class="stat-card">
            <div class="stat-icon">⚓</div>
            <div class="stat-num" id="stat-fleet">9</div>
            <div class="stat-lbl">Active Vessels</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">📋</div>
            <div class="stat-num" id="stat-bk">0</div>
            <div class="stat-lbl">New Bookings</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">✅</div>
            <div class="stat-num" id="stat-conf">0</div>
            <div class="stat-lbl">Confirmed</div>
          </div>
          <div class="stat-card">
            <div class="stat-icon">💬</div>
            <div class="stat-num" id="stat-today">0</div>
            <div class="stat-lbl">Today's Chats</div>
          </div>
        </div>
        <div class="actions-row">
          <button class="action-btn" onclick="openModal('yacht-modal')">+ Add Vessel</button>
          <button class="action-btn" onclick="openModal('booking-modal')">+ Manual Booking</button>
          <button class="action-btn" onclick="goPage('chat')">💬 Test Agent</button>
          <button class="action-btn" onclick="goPage('fleet')">⚓ Fleet</button>
        </div>

        <!-- Recent Bookings -->
        <div class="card">
          <div class="card-header">
            <span class="card-title">Recent Bookings</span>
            <span style="font-size:11px;color:var(--gold);cursor:pointer;" onclick="goPage('bookings')">View All</span>
          </div>
          <div class="card-body" id="recent-bk-list">
            <div class="empty"><div class="empty-icon">⛵</div><div class="empty-text">No bookings yet</div></div>
          </div>
        </div>
      </div>
    </div>

    <!-- CHAT PAGE -->
    <div class="page" id="pg-chat">
      <div class="chat-wrap">
        <div class="chat-header">
          <div class="chat-agent-name">🤖 Mykonos Sailing Agent</div>
          <div class="chat-agent-sub">Test as a customer</div>
        </div>
        <div class="chat-msgs" id="chat-msgs">
          <div class="msg msg-in">
            Welcome aboard! 🌊⛵ I'm the Mykonos Sailing assistant. How can I help you plan your perfect Aegean adventure?
            <div class="msg-time" id="welcome-time"></div>
          </div>
        </div>
        <div class="typing" id="typing"><span></span><span></span><span></span></div>
        <div class="chat-quick">
          <button class="quick-btn" onclick="sendQ('Tell me about your cruises')">🗺️ Cruises</button>
          <button class="quick-btn" onclick="sendQ('Show me your fleet')">⛵ Fleet</button>
          <button class="quick-btn" onclick="sendQ('How much does it cost?')">💰 Pricing</button>
          <button class="quick-btn" onclick="sendQ('I want to book a sunset cruise')">🌅 Book Now</button>
          <button class="quick-btn" onclick="sendQ('Private vs semi-private?')">👥 Private?</button>
        </div>
        <div class="chat-input-row">
          <input id="chat-inp" class="chat-inp" placeholder="Type your message..." onkeydown="if(event.key==='Enter')sendMsg()"/>
          <button class="chat-send" onclick="sendMsg()">
            <svg viewBox="0 0 24 24" fill="none" stroke="#000" stroke-width="2"><path d="M22 2L11 13M22 2L15 22l-4-9-9-4 20-7z"/></svg>
          </button>
        </div>
      </div>
    </div>

    <!-- FLEET PAGE -->
    <div class="page" id="pg-fleet">
      <div style="padding-top:8px;">
        <div class="sect-title">Fleet Management</div>
        <div class="sect-sub">Toggle vessel availability</div>
        <div id="fleet-list"></div>
        <button class="save-btn" onclick="openModal('yacht-modal')" style="margin-top:8px;">+ Add New Vessel</button>
      </div>
    </div>

    <!-- BOOKINGS PAGE -->
    <div class="page" id="pg-bookings">
      <div style="padding-top:8px;">
        <div class="sect-title">Bookings</div>
        <div class="sect-sub" id="bk-count-sub">All reservations</div>
        <div id="bookings-list"></div>
      </div>
    </div>

    <!-- SETTINGS PAGE -->
    <div class="page" id="pg-settings">
      <div style="padding-top:8px;">
        <div class="sect-title">Settings</div>
        <div class="sect-sub">Configuration</div>

        <div class="settings-section">
          <div class="settings-title">WhatsApp Integration</div>
          <div class="setting-row" style="flex-direction:column;align-items:flex-start;">
            <div class="setting-lbl">Phone Number ID</div>
            <input id="wa-phone" class="s-inp" type="text" placeholder="1234567890"/>
          </div>
          <div class="setting-row" style="flex-direction:column;align-items:flex-start;">
            <div class="setting-lbl">Access Token</div>
            <input id="wa-token" class="s-inp" type="password" placeholder="EAAxxxxxxx..."/>
          </div>
          <div class="setting-row" style="flex-direction:column;align-items:flex-start;">
            <div class="setting-lbl">Verify Token</div>
            <input id="wa-verify" class="s-inp" type="text" value="mykonos2024"/>
          </div>
          <div style="padding:0 16px 16px;">
            <button class="save-btn" onclick="saveWhatsApp()">Save WhatsApp Settings</button>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-title">Claude AI API</div>
          <div class="setting-row" style="flex-direction:column;align-items:flex-start;">
            <div class="setting-lbl">API KEY</div>
            <input id="claude-api-key" class="s-inp" type="password" placeholder="sk-ant-..."/>
          </div>
          <div style="padding:0 16px;margin-bottom:8px;font-size:11px;color:var(--muted);">Key is stored in browser only — never sent to any server</div>
          <div style="padding:0 16px 16px;">
            <button class="save-btn" onclick="saveApiKey()">Save API Key</button>
          </div>
        </div>

        <div class="settings-section">
          <div class="settings-title">Notification Email</div>
          <div class="setting-row" style="flex-direction:column;align-items:flex-start;">
            <div class="setting-lbl">Owner Email</div>
            <input id="notif-email" class="s-inp" type="email" placeholder="info@mykonossailing.gr"/>
          </div>
          <div style="padding:0 16px 16px;">
            <button class="save-btn" onclick="toast('Email saved ✓')">Save</button>
          </div>
        </div>

        <div style="text-align:center;padding:20px;font-size:11px;color:var(--muted);">
          Mykonos Sailing Admin v1.0<br>Powered by Claude AI 🌊
        </div>
      </div>
    </div>

  </div><!-- /main-scroll -->

  <!-- BOTTOM NAV -->
  <div class="bottom-nav">
    <div class="nav-item active" id="nav-home" onclick="goPage('home')">
      <span class="nav-icon">📊</span>
      <span class="nav-label">Dashboard</span>
    </div>
    <div class="nav-item" id="nav-chat" onclick="goPage('chat')">
      <span class="nav-icon">💬</span>
      <span class="nav-label">Agent</span>
    </div>
    <div class="nav-item" id="nav-bookings" onclick="goPage('bookings')">
      <span class="nav-icon">📋</span>
      <span class="nav-label">Bookings</span>
      <span class="nav-badge" id="bk-badge">0</span>
    </div>
    <div class="nav-item" id="nav-fleet" onclick="goPage('fleet')">
      <span class="nav-icon">⚓</span>
      <span class="nav-label">Fleet</span>
    </div>
    <div class="nav-item" id="nav-settings" onclick="goPage('settings')">
      <span class="nav-icon">⚙️</span>
      <span class="nav-label">Settings</span>
    </div>
  </div>
</div>

<!-- YACHT MODAL -->
<div class="modal-bg" id="yacht-modal">
  <div class="modal-sheet">
    <div class="modal-title">⛵ Add / Edit Vessel</div>
    <input type="hidden" id="yacht-id"/>
    <span class="m-lbl">Vessel Name</span>
    <input class="m-inp" id="yacht-name" placeholder="e.g. Toro Bianco Lagoon 500"/>
    <span class="m-lbl">Type</span>
    <select class="m-select" id="yacht-type">
      <option>Catamaran</option>
      <option>Sailing Yacht</option>
      <option>Motor Yacht</option>
      <option>RIB Boat</option>
      <option>Other</option>
    </select>
    <span class="m-lbl">Max Guests</span>
    <input class="m-inp" id="yacht-guests" type="number" placeholder="e.g. 16"/>
    <span class="m-lbl">Crew</span>
    <input class="m-inp" id="yacht-crew" type="number" placeholder="e.g. 2"/>
    <span class="m-lbl">Length (ft)</span>
    <input class="m-inp" id="yacht-size" placeholder="e.g. 52ft"/>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeModal('yacht-modal')">Cancel</button>
      <button class="btn-save" onclick="saveYacht()">Save Vessel</button>
    </div>
  </div>
</div>

<!-- BOOKING MODAL -->
<div class="modal-bg" id="booking-modal">
  <div class="modal-sheet">
    <div class="modal-title">📋 New Booking</div>
    <span class="m-lbl">Guest Name</span>
    <input class="m-inp" id="bk-name" placeholder="Full Name"/>
    <span class="m-lbl">Email</span>
    <input class="m-inp" id="bk-email" type="email" placeholder="email@example.com"/>
    <span class="m-lbl">Cruise / Itinerary</span>
    <select class="m-select" id="bk-cruise">
      <option>5hr South Coast Cruise</option>
      <option>5hr Delos & Rhenia Cruise</option>
      <option>3hr Sunset Cruise</option>
      <option>8hr Full Day - Delos, Rhenia & South Coast</option>
      <option>8hr Full Day South Coast</option>
      <option>3-Day Mykonos–Paros–Naxos Charter</option>
      <option>3-Day Mykonos–Syros–Antiparos Charter</option>
      <option>Multi-Day Tailor Made</option>
    </select>
    <span class="m-lbl">Type</span>
    <select class="m-select" id="bk-type">
      <option>Private</option>
      <option>Semi-Private</option>
    </select>
    <span class="m-lbl">Date</span>
    <input class="m-inp" id="bk-date" type="date"/>
    <span class="m-lbl">Number of Guests</span>
    <input class="m-inp" id="bk-guests" type="number" placeholder="e.g. 6"/>
    <span class="m-lbl">Notes</span>
    <input class="m-inp" id="bk-notes" placeholder="Special requests..."/>
    <div class="modal-actions">
      <button class="btn-cancel" onclick="closeModal('booking-modal')">Cancel</button>
      <button class="btn-save" onclick="saveBooking()">Create Booking</button>
    </div>
  </div>
</div>

<!-- TOAST -->
<div id="toast">✓ <span id="toast-txt"></span></div>

<script>
// ══════════════════════
// DATA
// ══════════════════════
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
let chatHistory = [];
let todayChats = 0;

// ══════════════════════
// AUTH
// ══════════════════════
function doLogin(){
  const u = document.getElementById('l-user').value.trim();
  const p = document.getElementById('l-pass').value.trim();
  if(u==='captain' && p==='mykonos2024'){
    document.getElementById('login').style.display='none';
    document.getElementById('app').classList.add('show');
    renderAll();
  } else {
    document.getElementById('l-err').textContent='Incorrect credentials';
    setTimeout(()=>document.getElementById('l-err').textContent='',2000);
  }
}

// ══════════════════════
// NAVIGATION
// ══════════════════════
function goPage(p){
  document.querySelectorAll('.page').forEach(x=>x.classList.remove('active'));
  document.querySelectorAll('.nav-item').forEach(x=>x.classList.remove('active'));
  document.getElementById('pg-'+p).classList.add('active');
  const nav = document.getElementById('nav-'+p);
  if(nav) nav.classList.add('active');
  document.getElementById('main-scroll').scrollTop=0;
  if(p==='fleet') renderFleet();
  if(p==='bookings') renderBookings();
  if(p==='home') renderDash();
  if(p==='chat'){
    document.getElementById('welcome-time').textContent = getTime();
    setTimeout(()=>{ document.getElementById('chat-msgs').scrollTop=99999; },100);
  }
}

// ══════════════════════
// RENDER
// ══════════════════════
function renderAll(){
  const d = new Date();
  document.getElementById('today-date').textContent = d.toLocaleDateString('en-US',{weekday:'long',year:'numeric',month:'long',day:'numeric'});
  renderDash();
  renderFleet();
  renderBookings();
  updateBadge();
  loadApiKey();
}

function renderDash(){
  const active = FLEET.filter(f=>f.active).length;
  document.getElementById('stat-fleet').textContent = active;
  const newBks = BOOKINGS.filter(b=>b.status==='new').length;
  const confBks = BOOKINGS.filter(b=>b.status==='confirmed').length;
  document.getElementById('stat-bk').textContent = newBks;
  document.getElementById('stat-conf').textContent = confBks;
  document.getElementById('stat-today').textContent = todayChats;

  const recentEl = document.getElementById('recent-bk-list');
  const recent = [...BOOKINGS].reverse().slice(0,3);
  if(!recent.length){
    recentEl.innerHTML='<div class="empty"><div class="empty-icon">⛵</div><div class="empty-text">No bookings yet</div></div>';
    return;
  }
  recentEl.innerHTML = recent.map(b=>`
    <div style="padding:8px 0;border-bottom:1px solid var(--border2);display:flex;justify-content:space-between;align-items:center;">
      <div>
        <div style="font-size:13px;color:var(--white);">${b.name}</div>
        <div style="font-size:11px;color:var(--muted);">${b.cruise} — ${b.date||'TBD'}</div>
      </div>
      <span class="status-badge status-${b.status}">${b.status}</span>
    </div>
  `).join('');
}

function renderFleet(){
  const el = document.getElementById('fleet-list');
  el.innerHTML = FLEET.map(y=>`
    <div class="yacht-card">
      <div class="yacht-header">
        <div class="yacht-icon">${y.emoji}</div>
        <div class="yacht-info">
          <div class="yacht-name">${y.name}</div>
          <div class="yacht-type">${y.type} · ${y.size}</div>
          <div class="yacht-capacity">👥 ${y.guests} guests + ${y.crew} crew</div>
        </div>
        <div class="yacht-toggle">
          <div class="toggle ${y.active?'on':''}" onclick="toggleYacht(${y.id})"></div>
        </div>
      </div>
    </div>
  `).join('');
}

function renderBookings(){
  const el = document.getElementById('bookings-list');
  const sub = document.getElementById('bk-count-sub');
  if(!BOOKINGS.length){
    el.innerHTML='<div class="empty"><div class="empty-icon">📋</div><div class="empty-text">No bookings yet</div></div>';
    sub.textContent='All reservations';
    return;
  }
  sub.textContent = `${BOOKINGS.length} reservation${BOOKINGS.length!==1?'s':''}`;
  el.innerHTML = [...BOOKINGS].reverse().map(b=>`
    <div class="booking-card">
      <div class="booking-header">
        <span class="booking-id">#${b.id}</span>
        <span class="status-badge status-${b.status}">${b.status}</span>
      </div>
      <div class="booking-body">
        <div class="booking-row"><span class="booking-key">Guest</span><span class="booking-val">${b.name}</span></div>
        <div class="booking-row"><span class="booking-key">Email</span><span class="booking-val">${b.email||'—'}</span></div>
        <div class="booking-row"><span class="booking-key">Cruise</span><span class="booking-val">${b.cruise}</span></div>
        <div class="booking-row"><span class="booking-key">Type</span><span class="booking-val">${b.cruiseType||'—'}</span></div>
        <div class="booking-row"><span class="booking-key">Date</span><span class="booking-val">${b.date||'TBD'}</span></div>
        <div class="booking-row"><span class="booking-key">Guests</span><span class="booking-val">${b.guests||'—'}</span></div>
        ${b.notes?`<div class="booking-row"><span class="booking-key">Notes</span><span class="booking-val">${b.notes}</span></div>`:''}
        <div class="booking-actions">
          ${b.status==='new'?`<button class="bk-btn bk-confirm" onclick="confirmBk(${b.id})">✓ Confirm</button>`:''}
          <button class="bk-btn bk-cancel" onclick="cancelBk(${b.id})">✕ Cancel</button>
        </div>
      </div>
    </div>
  `).join('');
}

function updateBadge(){
  const n = BOOKINGS.filter(b=>b.status==='new').length;
  const badge = document.getElementById('bk-badge');
  badge.textContent = n;
  badge.style.display = n ? 'flex' : 'none';
}

// ══════════════════════
// FLEET ACTIONS
// ══════════════════════
function toggleYacht(id){
  const y = FLEET.find(f=>f.id===id);
  if(!y) return;
  y.active = !y.active;
  renderFleet();
  renderDash();
  syncFleet();
  toast(`${y.name} — ${y.active?'Available ✓':'Hidden from agent'}`);
}

function saveYacht(){
  const name = document.getElementById('yacht-name').value.trim();
  if(!name){ toast('Enter vessel name'); return; }
  const y = {
    id: Date.now(),
    name,
    type: document.getElementById('yacht-type').value,
    guests: parseInt(document.getElementById('yacht-guests').value)||0,
    crew: parseInt(document.getElementById('yacht-crew').value)||0,
    size: document.getElementById('yacht-size').value||'—',
    active: true,
    emoji: '⛵'
  };
  FLEET.push(y);
  closeModal('yacht-modal');
  renderFleet();
  renderDash();
  syncFleet();
  toast(`${y.name} added ✓`);
}

function syncFleet(){
  fetch('/fleet',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({fleet:FLEET})})
  .catch(e=>console.log('sync',e));
}

// ══════════════════════
// BOOKING ACTIONS
// ══════════════════════
function saveBooking(){
  const name = document.getElementById('bk-name').value.trim();
  if(!name){ toast('Enter guest name'); return; }
  const b = {
    id: genId(),
    name,
    email: document.getElementById('bk-email').value.trim(),
    cruise: document.getElementById('bk-cruise').value,
    cruiseType: document.getElementById('bk-type').value,
    date: document.getElementById('bk-date').value,
    guests: document.getElementById('bk-guests').value,
    notes: document.getElementById('bk-notes').value.trim(),
    status:'new',
    createdAt: new Date().toISOString()
  };
  BOOKINGS.push(b);
  closeModal('booking-modal');
  renderDash();
  updateBadge();
  toast(`Booking #${b.id} created ✓`);
  // clear form
  ['bk-name','bk-email','bk-date','bk-guests','bk-notes'].forEach(id=>document.getElementById(id).value='');
}

function confirmBk(id){
  const b = BOOKINGS.find(x=>x.id===id);
  if(b){ b.status='confirmed'; renderBookings();renderDash();updateBadge();toast('Booking confirmed ✓'); }
}

function cancelBk(id){
  BOOKINGS = BOOKINGS.filter(x=>x.id!==id);
  renderBookings();renderDash();updateBadge();toast('Booking removed');
}

function checkBookingData(txt){
  const m = txt.match(/BOOKING_DATA:\\s*(\\{[\\s\\S]*?\\})/);
  if(!m) return;
  try{
    const d = JSON.parse(m[1]);
    const b = {
      id: genId(),
      name: d.name||d.guest_name||'Guest',
      email: d.email||'',
      cruise: d.cruise||d.itinerary||'',
      cruiseType: d.type||d.cruise_type||'',
      date: d.date||d.start_date||'',
      guests: d.guests||d.num_guests||'',
      notes: d.notes||'',
      status:'new',
      createdAt: new Date().toISOString()
    };
    BOOKINGS.push(b);
    renderDash();updateBadge();
    toast(`New booking #${b.id} created from chat! 🎉`);
  }catch(e){}
}

// ══════════════════════
// CHAT
// ══════════════════════
function buildSystemPrompt(){
  const activeFleet = FLEET.filter(f=>f.active);
  const fleetList = activeFleet.map(y=>`- ${y.name} (${y.type}, ${y.size}, max ${y.guests} guests)`).join('\\n');

  return `You are the booking assistant for Mykonos Sailing, a premier yacht charter company based in Mykonos, Greece.

COMPANY INFO:
- Name: Mykonos Sailing
- Location: Mykonos, Greece (also Athens)
- Departure point: Ornos Bay, Mykonos — small dock on the left side of the beach
- Website: mykonossailing.gr
- Instagram: @mykonossailing
- License: MHTE 07.26.E.70.00.00459.0.1 (ISO certified)

AVAILABLE FLEET (currently active):
${fleetList}

ITINERARIES:
1. 5hr South Coast Cruise — Ornos, Psarou, Platis Gialos, Paranga, Paradise, Super Paradise, Agrari, Elia. Morning (10am–3pm) or Afternoon (3:30–8:30pm). Private or Semi-Private.
2. 5hr Delos & Rhenia Cruise — UNESCO World Heritage site Delos + secluded island Rhenia. Morning or Afternoon. Private or Semi-Private.
3. 3hr Sunset Cruise — 5:30pm till sunset. Southern beaches, Greek appetizers, wine. Magical.
4. 8hr Full Day: Delos, Rhenia & South Coast — 10am–6pm. Includes guided Delos tour.
5. 8hr Full Day: South Coast — 10am–6pm. All southern beaches including hidden gems.
6. 3-Day Charter: Mykonos–Paros–Naxos — Delos, Rhenia, Naoussa, Naxos City.
7. 3-Day Charter: Mykonos–Syros–Antiparos — Ermoupouli, Antiparos, Parikia.
8. Multi-Day Tailor Made — Fully customized route, any islands, any duration.

ALL CRUISES INCLUDE:
✓ Meals (lunch or dinner) ✓ Unlimited beer, wine & soft drinks ✓ Water ✓ Music (Bluetooth) ✓ Beach towels ✓ Snorkeling equipment & SUP ✓ Professional crew

NOT INCLUDED: Hotel transfers (can be arranged), gratuities, Seabob (extra)

BOOKING INFO TO COLLECT:
1. Preferred itinerary/cruise
2. Private or Semi-Private
3. Date (or approximate dates)
4. Number of guests
5. Name
6. Email
7. Any special requests

PERSONALITY:
- Warm, enthusiastic about the Aegean and Greek hospitality
- Speak like a knowledgeable local who loves the sea
- Don't be robotic — be conversational and paint a picture of the experience
- Never give specific prices — say "Contact us for a custom quote" or that pricing depends on vessel and group size
- Respond in the SAME language the customer writes in (English, Greek, Arabic, French, etc.)
- When all booking info collected, output: BOOKING_DATA:{"name":"...","email":"...","cruise":"...","type":"Private/Semi-Private","date":"...","guests":"...","notes":"..."}`;
}

async function sendMsg(){
  const inp = document.getElementById('chat-inp');
  const msg = inp.value.trim();
  if(!msg) return;
  inp.value = '';
  inp.disabled = true;

  addMsg(msg, true);
  chatHistory.push({role:'user', content: msg});
  todayChats++;

  const typ = document.getElementById('typing');
  typ.style.display = 'block';
  document.getElementById('chat-msgs').scrollTop = 99999;

  try {
    const res = await fetch('/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({
        system: buildSystemPrompt(),
        messages: chatHistory
      })
    });

    const data = await res.json();
    typ.style.display = 'none';
    inp.disabled = false; inp.focus();

    if(data.error){
      addMsg('❌ ' + (data.error.message||JSON.stringify(data.error)), false);
      return;
    }

    let reply = data.content.map(b=>b.text||'').join('');
    chatHistory.push({role:'assistant', content: reply});
    const displayReply = reply.replace(/BOOKING_DATA:\\s*\\{[\\s\\S]*?\\}/,'').trim();
    addMsg(displayReply, false);
    checkBookingData(reply);
    renderDash();

  } catch(e){
    typ.style.display = 'none';
    inp.disabled = false;
    addMsg('❌ ' + e.message, false);
  }
}

function sendQ(msg){ document.getElementById('chat-inp').value=msg; sendMsg(); }

function addMsg(txt, isOut){
  const el = document.getElementById('chat-msgs');
  const d = document.createElement('div');
  d.className = 'msg ' + (isOut?'msg-out':'msg-in');
  d.innerHTML = txt.replace(/\\n/g,'<br>') + `<div class="msg-time">${getTime()}</div>`;
  el.appendChild(d);
  el.scrollTop = 99999;
}

// ══════════════════════
// SETTINGS
// ══════════════════════
function getApiKey(){ return document.getElementById('claude-api-key').value || localStorage.getItem('mks_key') || ''; }
function saveApiKey(){
  const k = document.getElementById('claude-api-key').value.trim();
  if(k) localStorage.setItem('mks_key', k);
  toast('API Key saved ✓');
}
function loadApiKey(){
  const k = localStorage.getItem('mks_key');
  if(k) document.getElementById('claude-api-key').value = k;
}
function saveWhatsApp(){ toast('WhatsApp settings saved ✓'); }

// ══════════════════════
// HELPERS
// ══════════════════════
function genId(){
  const n = new Date();
  return `MS${n.getFullYear()}${String(n.getMonth()+1).padStart(2,'0')}${String(n.getDate()).padStart(2,'0')}-${Math.random().toString(36).substr(2,4).toUpperCase()}`;
}
function getTime(){
  return new Date().toLocaleTimeString('en-US',{hour:'2-digit',minute:'2-digit',hour12:true});
}
function openModal(id){ document.getElementById(id).classList.add('open'); }
function closeModal(id){ document.getElementById(id).classList.remove('open'); }
function toast(msg){
  const t = document.getElementById('toast');
  document.getElementById('toast-txt').textContent = msg;
  t.classList.add('show');
  setTimeout(()=>t.classList.remove('show'), 2500);
}

document.querySelectorAll('.modal-bg').forEach(m=>{
  m.addEventListener('click',function(e){ if(e.target===this) this.classList.remove('open'); });
});
</script>
</body>
</html>
'''

@app.route("/", methods=["GET"])
def home():
    return Response(DASHBOARD, mimetype="text/html")

@app.route("/fleet", methods=["GET"])
def get_fleet():
    return jsonify(FLEET_STORE)

@app.route("/fleet", methods=["POST"])
def set_fleet():
    global FLEET_STORE
    data = request.get_json()
    if data and "fleet" in data:
        FLEET_STORE["fleet"] = data["fleet"]
    return jsonify({"ok": True})

@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        messages = data.get("messages", [])
        system_prompt = data.get("system", "")
        active_fleet = [f for f in FLEET_STORE["fleet"] if f.get("active")]
        fleet_list = "\n".join([f'- {f["name"]} ({f["type"]}, {f["size"]}, max {f["guests"]} guests)' for f in active_fleet])
        system_prompt = system_prompt.replace("ACTIVE_FLEET_PLACEHOLDER", fleet_list)
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-sonnet-4-6", "max_tokens": 1024, "system": system_prompt, "messages": messages},
            timeout=30
        )
        return jsonify(r.json()), r.status_code
    except Exception as e:
        return jsonify({"error": {"message": str(e)}}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
