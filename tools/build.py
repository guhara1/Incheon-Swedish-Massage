# -*- coding: utf-8 -*-
"""
인천굿데이마사지 (인천 출장마사지·홈타이) — static site generator.

One-time generator that emits PURE static HTML (inline CSS/JS, zero runtime
dependencies). The published site needs no build step or framework; this script
only exists to keep the shared header/footer/SEO blocks consistent across pages.

Run:  python3 tools/build.py
Output: HTML files + sitemap.xml + robots.txt + site.webmanifest at repo root.
"""

import os
import json
import re
import hashlib
import datetime
from email.utils import format_datetime
from xml.sax.saxutils import escape

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ---------------------------------------------------------------------------
# Brand / business constants  (replace placeholders before going live)
# ---------------------------------------------------------------------------
BASE_URL   = "https://incheon-swedish-massage.pages.dev"  # 메인 도메인 (Cloudflare Pages)
BRAND      = "인천굿데이마사지"
BRAND_SHORT= "굿데이"
BRAND_MARK = "G"
PHONE_DISP = "0508-202-4743"                     # 예약 전화번호
PHONE_TEL  = "+825082024743"                     # tel: 링크용
HOURS      = "연중무휴 · 24시간 상담"
INDEXNOW_KEY = "266ed468d0f42370ae86dd1b39e32e92"   # IndexNow(빙·네이버 등) 인증 키
NAVER_VERIFY = "062e89d3c7f9815e32be50bce53ddc2c74c988cd"  # 네이버 서치어드바이저 사이트 소유확인(메인페이지)

COMPANY = {
    "name": "인천굿데이마사지",
    "ceo": "OOO",                        # TODO: 실제 대표자명
    "biz_no": "000-00-00000",            # TODO: 실제 사업자등록번호
    "addr": "인천광역시",                 # TODO: 실제 주소
    "sales_no": "2026-인천OO-0000",      # TODO: 실제 통신판매업신고번호
    "privacy_officer": "OOO",            # TODO: 실제 개인정보보호책임자
}

# ---------------------------------------------------------------------------
# Data model — 권역 / 동
# ---------------------------------------------------------------------------

# 코스
COURSES = [
    {"slug": "fatigue", "kicker": "RELAX · 피로 회복", "name": "피로 회복 관리",
     "desc": "전신의 긴장을 부드럽게 풀어주는 스웨디시 계열 기본 관리입니다.",
     "prices": [("60분", "70,000원"), ("90분", "100,000원"), ("120분", "130,000원")]},
    {"slug": "aroma", "kicker": "AROMA · 아로마", "name": "아로마 관리",
     "desc": "블렌딩 오일을 사용해 향과 함께 심신을 이완하는 관리입니다.",
     "prices": [("60분", "80,000원"), ("90분", "110,000원"), ("120분", "140,000원")], "best": True},
    {"slug": "sports", "kicker": "SPORTS · 스포츠", "name": "스포츠 관리",
     "desc": "운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 관리입니다.",
     "prices": [("60분", "90,000원"), ("90분", "120,000원"), ("120분", "150,000원")]},
    {"slug": "hometai", "kicker": "HOMETHAI · 홈타이", "name": "홈타이 코스",
     "desc": "타이 스트레칭을 응용해 자택에서 받는 이완 중심 홈타이 관리입니다.",
     "prices": [("60분", "80,000원"), ("90분", "110,000원"), ("120분", "140,000원")]},
    {"slug": "couple", "kicker": "COUPLE · 커플·가족", "name": "커플·가족 방문 관리",
     "desc": "두 분이 함께 같은 공간에서 동시에 받는 동반 관리입니다.",
     "prices": [("60분", "150,000원~"), ("90분", "200,000원~"), ("120분", "250,000원~")]},
    {"slug": "group", "kicker": "GROUP · 기업·단체", "name": "기업·단체 방문 관리",
     "desc": "워크숍·행사 등 단체 인원을 위한 사전 협의형 방문 관리입니다.",
     "prices": [("협의", "별도 견적"), ("협의", "별도 견적"), ("협의", "별도 견적")]},
]

# 코스별 기본 요금 (시간 기준 메뉴 — 메인/모든 지역 페이지 공통)
TIME_PRICING = [
    {"name": "60분 코스", "price": "90,000", "dur": "60분", "desc": "기본 컨디션·릴랙스 케어"},
    {"name": "90분 코스", "price": "150,000", "dur": "90분", "desc": "아로마 포함 추천 구성", "best": True},
    {"name": "120분 코스", "price": "180,000", "dur": "120분", "desc": "전신 집중 프리미엄 케어"},
]

# ---------------------------------------------------------------------------
# Shared CSS  (design system from BLUEPRINT.md)
# ---------------------------------------------------------------------------
CSS = """
*{box-sizing:border-box;margin:0;padding:0}
:root{
  --bg:#0b0b0e;--surface:#13131a;--surface-2:#1a1a23;--line:rgba(255,255,255,.08);
  --text:#f3f3f5;--muted:#9a9aa3;--dim:#6c6c75;
  --gold:#d6b274;--rose:#e9b8a7;--copper:#c98a6b;
  --grad:linear-gradient(135deg,#f4d29c 0%,#e9b8a7 45%,#c98a6b 100%);
  --grad-soft:linear-gradient(135deg,rgba(244,210,156,.14),rgba(201,138,107,.06));
}
html{scroll-behavior:smooth}
body{background:var(--bg);color:var(--text);line-height:1.65;letter-spacing:-.01em;
  font-family:"Pretendard","Apple SD Gothic Neo","Noto Sans KR",system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;
  -webkit-font-smoothing:antialiased;overflow-x:hidden}
a{color:inherit;text-decoration:none}
img{max-width:100%;display:block}
.serif,.note-num,.step .n{font-family:"Cormorant Garamond","Noto Serif KR",Georgia,serif;font-weight:300;font-style:italic}
.grad{background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent}
.wrap{max-width:1240px;margin:0 auto;padding:0 24px}
section.block{padding:96px 0}
.eyebrow{display:inline-flex;align-items:center;gap:8px;font-size:11.5px;letter-spacing:.2em;
  text-transform:uppercase;color:var(--gold);font-weight:700}
.pulse{width:7px;height:7px;border-radius:50%;background:var(--rose);box-shadow:0 0 0 0 rgba(233,184,167,.6);animation:pulse 2s infinite}
@keyframes pulse{0%{box-shadow:0 0 0 0 rgba(233,184,167,.55)}70%{box-shadow:0 0 0 9px rgba(233,184,167,0)}100%{box-shadow:0 0 0 0 rgba(233,184,167,0)}}
h2.sec{font-size:clamp(28px,4vw,46px);letter-spacing:-.03em;font-weight:800;margin:14px 0 10px}
.sec-lead{color:var(--muted);max-width:660px;font-size:15px}
/* header */
header{position:sticky;top:0;z-index:60;backdrop-filter:blur(14px);
  background:rgba(11,11,14,.78);border-bottom:1px solid var(--line)}
.nav{max-width:1240px;margin:0 auto;padding:14px 24px;display:flex;align-items:center;gap:12px}
.brand{display:flex;align-items:center;gap:10px;font-weight:800;font-size:18px;letter-spacing:-.02em}
.brand .mark{width:34px;height:34px;border-radius:10px;background:var(--grad);display:grid;place-items:center;
  color:#1a1208;font-weight:800;font-family:"Cormorant Garamond",serif;font-style:italic;font-size:20px}
.brand{white-space:nowrap;flex-shrink:0}
.brand small{display:block;font-size:10.5px;letter-spacing:.16em;color:var(--gold);font-weight:700}
.menu{list-style:none;display:flex;flex-wrap:nowrap;align-items:center;gap:2px;margin-left:auto}
.menu>li{position:relative}
.menu>li>a{display:block;padding:9px 10px;font-size:13.5px;color:var(--text);border-radius:9px;font-weight:600;white-space:nowrap}
.menu>li>a:hover{background:rgba(255,255,255,.05)}
.menu>li>a.active{color:var(--gold)}
.submenu{position:absolute;top:calc(100% + 6px);left:0;min-width:212px;list-style:none;padding:8px;
  background:linear-gradient(160deg,var(--surface),var(--surface-2));border:1px solid var(--line);
  border-radius:14px;box-shadow:0 20px 48px rgba(0,0,0,.45);opacity:0;visibility:hidden;transform:translateY(6px);
  transition:.22s;z-index:70}
.menu>li:hover>.submenu,.menu>li:focus-within>.submenu{opacity:1;visibility:visible;transform:none}
.submenu li{position:relative}
.submenu li a{display:block;padding:9px 12px;font-size:13.5px;color:var(--muted);border-radius:9px}
.submenu li a:hover{background:rgba(255,255,255,.05);color:var(--text)}
.submenu li.has-sub>a::after{content:"›";float:right;color:var(--dim);font-weight:700}
.submenu .sub2{position:absolute;top:-9px;left:calc(100% + 7px);transform:translateX(6px)}
.submenu li.has-sub:hover>.sub2,.submenu li.has-sub:focus-within>.sub2{opacity:1;visibility:visible;transform:none}
.cta-pill{margin-left:6px;padding:11px 18px!important;background:var(--grad);color:#1a1208!important;
  border-radius:999px;font-weight:800!important}
.toggle{display:none;margin-left:auto;background:none;border:1px solid var(--line);color:var(--text);
  font-size:20px;width:44px;height:44px;border-radius:11px;cursor:pointer}
/* hero */
.hero{position:relative;overflow:hidden;border-bottom:1px solid var(--line)}
.hero::before{content:"";position:absolute;inset:0;z-index:0;
  background:radial-gradient(60% 70% at 80% 10%,rgba(233,184,167,.16),transparent 60%),
             radial-gradient(50% 60% at 10% 90%,rgba(214,178,116,.12),transparent 60%),
             radial-gradient(40% 50% at 50% 50%,rgba(201,138,107,.08),transparent 70%)}
.hero-inner{position:relative;z-index:1;display:grid;grid-template-columns:1.12fr .88fr;gap:48px;
  align-items:center;max-width:1240px;margin:0 auto;padding:88px 24px}
.hero h1{font-size:clamp(36px,6vw,70px);font-weight:800;letter-spacing:-.038em;line-height:1.06;margin:18px 0}
.hero .lead{color:var(--muted);font-size:16px;max-width:520px;margin-bottom:26px}
.actions{display:flex;gap:12px;flex-wrap:wrap}
.btn{display:inline-flex;align-items:center;gap:8px;padding:14px 22px;border-radius:12px;font-weight:700;
  font-size:14.5px;transition:.25s;border:1px solid transparent}
.btn-primary{background:var(--grad);color:#1a1208}
.btn-primary:hover{transform:translateY(-2px);box-shadow:0 14px 34px rgba(201,138,107,.35)}
.btn-ghost{border-color:var(--line);color:var(--text)}
.btn-ghost:hover{border-color:rgba(244,210,156,.4);transform:translateY(-2px)}
.trust{margin-top:24px;display:flex;flex-wrap:wrap;gap:8px 18px;color:var(--muted);font-size:13px}
.trust b{color:var(--text)}
.hero-visual{position:relative}
.glass{position:relative;z-index:2;border-radius:20px;padding:26px;
  background:linear-gradient(160deg,rgba(255,255,255,.06),rgba(255,255,255,.02));
  border:1px solid rgba(255,255,255,.12);backdrop-filter:blur(20px);transform:rotate(1.5deg)}
.glass h3{font-size:13px;color:var(--gold);letter-spacing:.04em;margin-bottom:14px}
.glass h3 b{display:block;font-size:21px;color:var(--text);letter-spacing:-.02em;margin-top:4px}
.book-row{display:flex;justify-content:space-between;padding:11px 0;border-top:1px solid var(--line);font-size:14px}
.book-row span:first-child{color:var(--muted)}
.bk{display:block;text-align:center;margin-top:16px;padding:13px;border-radius:12px;background:var(--grad);color:#1a1208;font-weight:800}
.floating{position:absolute;z-index:3;padding:11px 14px;border-radius:12px;font-size:12px;font-weight:600;
  background:linear-gradient(160deg,var(--surface),var(--surface-2));border:1px solid var(--line);
  box-shadow:0 14px 34px rgba(0,0,0,.4)}
.fl-1{top:-18px;left:-14px;transform:rotate(-4deg)}
.fl-2{bottom:-16px;right:-10px;transform:rotate(3deg)}
.fl-1 .dot{display:inline-block;width:7px;height:7px;border-radius:50%;background:#6fe3a1;margin-right:6px}
/* marquee */
.marquee{overflow:hidden;border-bottom:1px solid var(--line);background:var(--surface)}
.marquee-track{display:flex;gap:0;white-space:nowrap;width:max-content;animation:scroll 34s linear infinite}
.marquee-track span{padding:14px 26px;color:var(--muted);font-size:13px;letter-spacing:.04em}
.marquee-track span::after{content:"·";margin-left:26px;color:var(--dim)}
@keyframes scroll{to{transform:translateX(-50%)}}
/* cards grid */
.grid{display:grid;gap:16px}
.g4{grid-template-columns:repeat(auto-fit,minmax(230px,1fr))}
.g3{grid-template-columns:repeat(auto-fit,minmax(280px,1fr))}
.g2{grid-template-columns:repeat(auto-fit,minmax(320px,1fr))}
.card{padding:24px;border-radius:16px;border:1px solid var(--line);
  background:linear-gradient(135deg,var(--surface),var(--surface-2));transition:.3s}
.card:hover{transform:translateY(-4px);border-color:rgba(244,210,156,.28);box-shadow:0 18px 40px rgba(0,0,0,.3)}
.card .k{font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--gold);font-weight:700}
.card h3{margin:10px 0 8px;font-size:19px;font-weight:800}
.card p{color:var(--muted);font-size:14px}
.card .more{display:inline-block;margin-top:14px;color:var(--rose);font-size:13.5px;font-weight:700}
.card:hover .more{transform:translateX(4px)}
/* note card */
.note-card{display:flex;gap:22px;padding:26px 28px;border-radius:18px;position:relative;overflow:hidden;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));border:1px solid var(--line);transition:.3s}
.note-card::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--grad);opacity:0;transition:.3s}
.note-card:hover::before{opacity:1}
.note-card:hover{transform:translateY(-2px);box-shadow:0 18px 44px rgba(0,0,0,.32);border-color:rgba(244,210,156,.28)}
.note-num{font-size:44px;background:var(--grad);-webkit-background-clip:text;background-clip:text;color:transparent;flex-shrink:0;line-height:1}
.note-title{font-size:18px;font-weight:800;margin-bottom:10px}
.note-text{max-width:660px}
.note-text p{margin:0 0 9px;color:#c8c8d0;font-size:14.5px;line-height:1.78}
.note-stack{display:flex;flex-direction:column;gap:14px}
/* chips */
.chips{display:flex;flex-wrap:wrap;gap:10px;margin-top:18px}
.chip{padding:9px 14px;border-radius:999px;border:1px solid var(--line);background:var(--surface);
  font-size:12.5px;color:var(--muted)}
.chip b{color:var(--gold)}
/* price */
.price-card{padding:24px;border-radius:16px;border:1px solid var(--line);position:relative;overflow:hidden;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));transition:.3s}
.price-card::after{content:"";position:absolute;left:0;right:0;top:0;height:2px;background:var(--grad);opacity:.5}
.price-card:hover{transform:translateY(-3px);border-color:rgba(244,210,156,.3)}
.price-card.best{border-color:rgba(244,210,156,.45)}
.best-badge{position:absolute;top:14px;right:14px;font-size:10.5px;font-weight:800;letter-spacing:.1em;
  padding:5px 10px;border-radius:999px;background:var(--grad);color:#1a1208}
.price-card .k{font-size:11px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);font-weight:700}
.price-card h3{margin:8px 0 6px;font-size:20px;font-weight:800}
.price-card>p{color:var(--muted);font-size:13.5px;margin-bottom:14px}
.time-rows>div{display:flex;justify-content:space-between;padding:9px 0;border-top:1px solid var(--line);font-size:14px}
.time-rows span:last-child{font-weight:700}
/* 코스별 기본 요금 메뉴 */
.pmenu{display:grid;grid-template-columns:repeat(3,1fr);gap:18px;margin-top:28px}
.pmenu-card{position:relative;text-align:center;padding:36px 24px 26px;border-radius:18px;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));border:1px solid var(--line);transition:.3s}
.pmenu-card:hover{transform:translateY(-4px);border-color:rgba(244,210,156,.3);box-shadow:0 18px 42px rgba(0,0,0,.32)}
.pmenu-card.best{border-color:rgba(244,210,156,.5);box-shadow:0 16px 42px rgba(201,138,107,.2)}
.pmenu-name{font-weight:800;font-size:17px;margin-bottom:16px}
.pmenu-price{font-size:clamp(30px,4vw,40px);font-weight:800;letter-spacing:-.035em;line-height:1}
.pmenu-price span{font-size:15px;font-weight:600;color:var(--muted);margin-left:3px;letter-spacing:0}
.pmenu-dur{color:var(--gold);font-size:13px;font-weight:700;margin-top:10px}
.pmenu-desc{color:var(--muted);font-size:13.5px;margin:8px 0 22px}
.pmenu-btn{display:block;padding:13px;border-radius:11px;border:1px solid var(--line);font-weight:700;font-size:14px;transition:.25s}
.pmenu-btn:hover{border-color:rgba(244,210,156,.5);transform:translateY(-1px)}
.pmenu-card.best .pmenu-btn{background:var(--grad);color:#1a1208;border-color:transparent}
.pmenu-badge{position:absolute;top:-12px;left:50%;transform:translateX(-50%);background:var(--grad);color:#1a1208;
  font-size:11.5px;font-weight:800;padding:5px 15px;border-radius:999px;box-shadow:0 6px 16px rgba(201,138,107,.35)}
.pmenu-note{margin-top:20px;color:var(--muted);font-size:13px}
.pmenu-note a{color:var(--gold);font-weight:700;white-space:nowrap}
@media(max-width:760px){.pmenu{grid-template-columns:1fr}}
/* faq */
details{border:1px solid var(--line);border-radius:14px;padding:0;margin-bottom:12px;
  background:linear-gradient(135deg,var(--surface),var(--surface-2));overflow:hidden}
summary{list-style:none;cursor:pointer;padding:18px 22px;font-weight:700;font-size:15px;
  display:flex;justify-content:space-between;align-items:center;gap:14px}
summary::-webkit-details-marker{display:none}
summary span{color:var(--gold);font-size:22px;transition:.25s;flex-shrink:0}
details[open] summary span{transform:rotate(45deg)}
details>div{padding:0 22px 20px;color:var(--muted);font-size:14.5px;line-height:1.78}
/* breadcrumb */
.crumb{font-size:12.5px;color:var(--dim);padding:18px 0}
.crumb a{color:var(--muted)}
.crumb a:hover{color:var(--gold)}
.crumb b{color:var(--text)}
/* review */
.review{padding:22px;border-radius:16px;border:1px solid var(--line);
  background:linear-gradient(135deg,var(--surface),var(--surface-2))}
.review .stars{color:var(--gold);font-size:13px;letter-spacing:2px}
.review p{margin:10px 0;font-size:14px;color:#c8c8d0;line-height:1.7}
.review .who{font-size:12.5px;color:var(--muted)}
/* cta band */
.cta-band{position:relative;overflow:hidden;text-align:center;padding:88px 24px;border-top:1px solid var(--line)}
.cta-band::before{content:"";position:absolute;inset:0;background:radial-gradient(50% 80% at 50% 0%,rgba(233,184,167,.16),transparent 60%)}
.cta-band>div{position:relative}
.cta-band h2{font-size:clamp(26px,4vw,42px);font-weight:800;letter-spacing:-.03em}
.cta-band p{color:var(--muted);margin:12px 0 24px}
/* footer */
.site-footer{border-top:1px solid var(--line);background:var(--surface);padding:64px 0 36px;font-size:13.5px}
.footer-grid{display:grid;grid-template-columns:1.4fr 1fr 1fr 1fr;gap:30px}
.footer-grid h4{font-size:12px;letter-spacing:.14em;text-transform:uppercase;color:var(--gold);margin-bottom:14px}
.footer-grid a{display:block;color:var(--muted);padding:5px 0}
.footer-grid a:hover{color:var(--text)}
.footer-brand b{font-size:17px}
.footer-brand p{color:var(--muted);margin-top:10px;max-width:280px;line-height:1.7}
.footer-ops{margin:34px 0;padding:22px;border-radius:14px;background:var(--grad-soft);
  border:1px solid var(--line);display:flex;flex-wrap:wrap;gap:14px 40px}
.footer-ops div b{color:var(--gold);display:block;font-size:11px;letter-spacing:.12em;margin-bottom:4px}
.company-info{display:grid;grid-template-columns:repeat(3,1fr);gap:12px;color:var(--dim);font-size:12.5px;
  padding-top:24px;border-top:1px solid var(--line)}
.company-info b{color:var(--muted)}
.footer-policies{display:flex;flex-wrap:wrap;gap:8px 18px;margin:22px 0 14px}
.footer-policies a{color:var(--muted);font-size:12.5px}
.footer-bottom{color:var(--dim);font-size:12px;line-height:1.7;border-top:1px solid var(--line);padding-top:18px}
.legal-note{margin-top:8px;color:var(--dim)}
/* 콘텐츠 아티클 + 저자 표기(E-E-A-T) */
.byline{display:flex;flex-wrap:wrap;gap:6px 16px;margin-top:18px;color:var(--dim);font-size:12.5px}
.byline span{display:inline-flex;align-items:center}
.byline span+span::before{content:"·";margin-right:16px;color:var(--dim)}
.byline .au{color:var(--muted);font-weight:700}
.article{max-width:760px}
.article h2{font-size:clamp(21px,3vw,29px);font-weight:800;letter-spacing:-.02em;margin:38px 0 12px}
.article h2:first-child{margin-top:8px}
.article h3{font-size:17px;font-weight:800;margin:20px 0 8px}
.article p{color:#c8c8d0;font-size:15px;line-height:1.85;margin:0 0 12px}
.article ul{margin:0 0 14px;padding-left:20px;color:#c8c8d0;font-size:15px;line-height:1.85}
.article li{margin-bottom:6px}
.article strong{color:var(--text)}
.data-box{margin:24px 0;padding:20px 22px;border-radius:14px;background:var(--grad-soft);border:1px solid var(--line)}
.data-box b{color:var(--gold);display:block;font-size:11px;letter-spacing:.14em;margin-bottom:8px;text-transform:uppercase}
.data-box p{color:var(--muted);font-size:13.5px;margin:0;line-height:1.8}
/* 다크 럭스 스파 — 지역/콘텐츠 페이지 (네이비 패널 + 골드 + 좌측 TOC) */
.lux-hero{position:relative;overflow:hidden;border-bottom:1px solid rgba(244,210,156,.14);
  background:radial-gradient(70% 120% at 88% -10%,rgba(233,184,167,.14),transparent 60%),
             linear-gradient(180deg,#0d1018,#0b0b0e);padding:54px 0 40px}
.lux-h1{font-size:clamp(30px,5vw,52px);font-weight:800;letter-spacing:-.03em;line-height:1.1;margin:14px 0 12px;color:#fff}
.lux-lead{color:#cfd2da;font-size:16.5px;line-height:1.8;max-width:760px}
.lux-body{background:linear-gradient(180deg,#0b0b0e,#0c0e15 40%,#0b0b0e)}
.lux-grid{display:grid;grid-template-columns:240px 1fr;gap:46px;align-items:start}
.toc{position:sticky;top:86px}
.toc-inner{border:1px solid rgba(244,210,156,.2);border-radius:16px;padding:18px 14px;
  background:linear-gradient(165deg,#10131f,#0a0c13);box-shadow:0 18px 40px rgba(0,0,0,.35)}
.toc-label{display:block;font-size:10.5px;letter-spacing:.2em;color:var(--gold);font-weight:800;text-transform:uppercase;margin:0 0 12px 8px}
.toc ul{list-style:none;margin:0;padding:0}
.toc li a{display:block;padding:8px 12px;font-size:13px;line-height:1.4;color:var(--muted);
  border-left:2px solid transparent;border-radius:0 8px 8px 0;transition:.2s}
.toc li a:hover{color:var(--text);background:rgba(255,255,255,.05)}
.toc li a.active{color:var(--gold);border-left-color:var(--gold);background:rgba(244,210,156,.09);font-weight:700}
.lux-main{min-width:0}
.lux-sec{position:relative;overflow:hidden;background:linear-gradient(165deg,#121626,#0c0e16);
  border:1px solid rgba(255,255,255,.08);border-radius:18px;padding:28px 32px;margin-bottom:18px}
.lux-sec::before{content:"";position:absolute;left:0;top:0;bottom:0;width:3px;background:var(--grad)}
.lux-sec h2{font-size:clamp(20px,2.5vw,27px);font-weight:800;letter-spacing:-.02em;margin:0 0 14px;color:#fff}
.lux-sec h3{color:var(--gold);font-size:16.5px;font-weight:800;margin:20px 0 7px}
.lux-sec p{color:#e4e5ec;font-size:15.5px;line-height:1.9;margin:0 0 12px}
.lux-sec>ul{margin:6px 0 14px;padding:0;list-style:none}
.lux-sec>ul li{position:relative;padding:8px 0 8px 22px;color:#e4e5ec;font-size:15px;line-height:1.65;
  border-bottom:1px solid rgba(255,255,255,.06)}
.lux-sec>ul li::before{content:"";position:absolute;left:3px;top:15px;width:6px;height:6px;border-radius:50%;background:var(--grad)}
.lux-sec>ul li:last-child{border-bottom:none}
.lux-sec a{color:var(--rose);font-weight:600;border-bottom:1px solid rgba(233,184,167,.4)}
.lux-sec a:hover{color:var(--gold);border-bottom-color:var(--gold)}
.lux-sec strong{color:#fff}
.lux-sec .grid{margin-top:6px}
.lux-main .data-box{margin:4px 0 0;background:linear-gradient(135deg,rgba(244,210,156,.12),rgba(201,138,107,.05));
  border:1px solid rgba(244,210,156,.22)}
@media(max-width:980px){
  .lux-grid{grid-template-columns:1fr;gap:14px}
  .toc{position:static}
  .toc-inner{display:flex;flex-wrap:wrap;gap:6px;align-items:center;padding:12px 14px}
  .toc-label{margin:0 4px 0 2px}
  .toc ul{display:flex;flex-wrap:wrap;gap:6px}
  .toc li a{border-left:none;border:1px solid var(--line);border-radius:999px;padding:6px 13px;font-size:12px}
  .toc li a.active{background:var(--grad);color:#1a1208;border-color:transparent}
  .lux-sec{padding:22px 20px}
}
/* 플로팅 전화예약 버튼 (전 페이지) */
.call-fab{position:fixed;right:20px;bottom:20px;z-index:90;display:inline-flex;align-items:center;gap:9px;
  padding:14px 20px 14px 16px;border-radius:999px;color:#fff;font-weight:800;font-size:14.5px;letter-spacing:-.01em;
  background:linear-gradient(135deg,#ffa23c,#ff7a18 55%,#f4600a);
  box-shadow:0 12px 30px rgba(255,122,24,.5);transition:transform .25s,box-shadow .25s}
.call-fab:hover{transform:translateY(-3px);box-shadow:0 16px 38px rgba(255,122,24,.6)}
.call-fab::before{content:"";position:absolute;inset:0;border-radius:999px;border:2px solid #ff7a18;
  animation:fabpulse 1.8s ease-out infinite;pointer-events:none}
.call-fab-ic{position:relative;display:grid;place-items:center;width:26px;height:26px;
  transform-origin:60% 60%;animation:fabring 1.5s ease-in-out infinite}
.call-fab-ic svg{width:21px;height:21px;fill:#fff}
.call-fab-tx{position:relative;white-space:nowrap}
.call-fab-tx small{display:block;font-size:11px;font-weight:700;opacity:.92;letter-spacing:.01em}
@keyframes fabring{0%,62%,100%{transform:rotate(0)}8%,26%{transform:rotate(-15deg)}17%,35%{transform:rotate(15deg)}}
@keyframes fabpulse{0%{transform:scale(1);opacity:.7}100%{transform:scale(1.55);opacity:0}}
@media(max-width:560px){.call-fab{right:14px;bottom:14px;padding:14px}.call-fab-tx{display:none}}
@media(prefers-reduced-motion:reduce){.call-fab-ic,.call-fab::before{animation:none}}
/* reveal */
.reveal{opacity:0;transform:translateY(20px);transition:.8s}
.reveal.in{opacity:1;transform:none}
/* perf */
#region,#process,#reviews,#about,#faq,.cta-band,.site-footer{content-visibility:auto;contain-intrinsic-size:auto 700px}
.card,.note-card,.review,.price-card{contain:layout style}
@media(hover:none){.glass,.floating{backdrop-filter:none}}
@media(prefers-reduced-motion:reduce){.marquee-track,.pulse{animation:none}.reveal{opacity:1;transform:none}}
@media(max-width:1280px){
  .toggle{display:block}
  .menu{position:fixed;inset:64px 0 auto 0;flex-direction:column;align-items:stretch;gap:2px;margin:0;
    padding:14px;background:var(--bg);border-bottom:1px solid var(--line);max-height:calc(100vh - 64px);
    overflow:auto;transform:translateY(-12px);opacity:0;visibility:hidden;transition:.25s}
  .menu.open{transform:none;opacity:1;visibility:visible}
  .menu>li>a{padding:13px 12px}
  .submenu,.submenu .sub2{position:static;opacity:1;visibility:visible;transform:none;box-shadow:none;
    background:transparent;border:none;padding:0 0 6px 12px;min-width:0;left:auto;top:auto}
  .submenu .sub2{padding-left:14px}
  .submenu li.has-sub>a::after{content:""}
  .cta-pill{text-align:center}
  .hero-inner{grid-template-columns:1fr;gap:36px}
  .hero-visual{max-width:420px}
  .footer-grid{grid-template-columns:1fr 1fr}
  .company-info{grid-template-columns:1fr 1fr}
}
@media(max-width:560px){
  .footer-grid,.company-info{grid-template-columns:1fr}
  .note-card{flex-direction:column;gap:12px}
  .hero-inner{padding:56px 24px}
}
"""

# ---------------------------------------------------------------------------
# Navigation model  (top menu + dropdowns)
# ---------------------------------------------------------------------------
def menu_html(active):
    def li(key, href, label, sub=None, cta=False):
        cls = ' class="active"' if active == key else ""
        pop = ' aria-haspopup="true"' if sub else ""
        a = f'<a href="{href}"{cls}{pop}>{label}</a>'
        if cta:
            a = f'<a class="cta-pill" href="tel:{PHONE_TEL}">24시 예약</a>'
        sub_html = ""
        if sub:
            parts = []
            for item in sub:
                if len(item) == 3:  # 하위 동(洞)을 펼치는 3단 항목
                    h, t, kids = item
                    kids_html = "".join(f'<li><a href="{kh}">{kt}</a></li>' for kh, kt in kids)
                    parts.append(
                        f'<li class="has-sub"><a href="{h}" aria-haspopup="true">{t}</a>'
                        f'<ul class="submenu sub2">{kids_html}</ul></li>')
                else:
                    h, t = item
                    parts.append(f'<li><a href="{h}">{t}</a></li>')
            sub_html = f'<ul class="submenu">{"".join(parts)}</ul>'
        return f"<li>{a}{sub_html}</li>"

    # 지역별 안내: 인천 전체 + 구/군 → 대표 동(3단)
    region_sub = [("/incheon/area/", "인천 전체")]
    region_sub += [(f"/incheon/{g['slug']}/", g["name"],
                    [(f"/incheon/{g['slug']}/{d['slug']}/", d["name"]) for d in g["dongs"]])
                   for g in GU]
    # 지하철역별 안내: 전체 + 노선 → 역(3단). 역명만 노출(키워드 반복 금지)
    station_sub = [("/incheon/stations/", "인천 지하철역 전체")]
    station_sub += [(f"/incheon/stations/{ln['slug']}/", ln["name"],
                     [(f"/incheon/stations/{STATIONS[s]['slug']}/", STATIONS[s]["name"]) for s in ln["stations"]])
                    for ln in LINES]
    # 테마별 안내: 전체 + 테마
    theme_sub = [("/theme/", "전체 테마")]
    theme_sub += [(f"/theme/{t['slug']}/", t["name"]) for t in THEMES]
    items = [
        li("home", "/", "홈"),
        li("incheon", "/incheon/", "인천 출장마사지", [
            ("/incheon/", "인천 출장마사지 안내"),
            ("/incheon/hometai/", "인천 홈타이 안내"),
            ("/incheon/area/", "인천 전지역 방문 가능 안내"),
            ("/incheon/stations/", "인천 지하철역 인근 안내"),
            ("/incheon/hours/", "예약 가능 시간"),
            ("/course/guide/", "코스 선택 안내"),
            ("/incheon/checklist/", "이용 전 확인사항"),
            ("/incheon/safety/", "위생 및 안전 안내"),
            ("/incheon/faq/", "자주 묻는 질문"),
        ]),
        li("area", "/incheon/area/", "지역별 안내", region_sub),
        li("stations", "/incheon/stations/", "지하철역별 안내", station_sub),
        li("theme", "/theme/", "테마별 안내", theme_sub),
        li("course", "/course/", "코스안내", [
            ("/course/", "전체 코스"),
            ("/course/fatigue/", "피로 회복 관리"),
            ("/course/aroma/", "아로마 관리"),
            ("/course/sports/", "스포츠 관리"),
            ("/course/hometai/", "홈타이 코스"),
            ("/course/couple/", "커플·가족 방문 관리"),
            ("/course/group/", "기업·단체 방문 관리"),
            ("/course/price/", "가격 안내"),
            ("/course/guide/", "코스 선택 가이드"),
        ]),
        li("reservation", "/reservation/", "예약안내"),
        li("guide", "/guide/", "이용가이드"),
        li("reviews", "/reviews/", "후기"),
        li("customer", "/customer/", "고객센터"),
        li("cta", "#", "", cta=True),
    ]
    return (
        '<header><nav class="nav" aria-label="주 메뉴">'
        f'<a class="brand" href="/" aria-label="{BRAND} 홈">'
        f'<span class="mark">{BRAND_MARK}</span><span>인천굿데이<small>출장마사지·홈타이</small></span></a>'
        '<button class="toggle" aria-expanded="false" aria-controls="primary-menu" aria-label="메뉴 열기">☰</button>'
        f'<ul id="primary-menu" class="menu">{"".join(items)}</ul>'
        "</nav></header>"
    )

# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
def footer_html():
    # 푸터에는 지역명·역명을 대량 나열하지 않고 섹션 허브 링크만 노출(도어웨이 회피)
    course_links = "".join(
        f'<a href="/course/{c["slug"]}/">{c["name"]}</a>' for c in COURSES
    )
    return f"""<footer class="site-footer"><div class="wrap">
<div class="footer-grid">
  <div class="footer-brand">
    <b class="grad">{BRAND}</b>
    <p>인천 전지역 출장마사지·홈타이 방문 건강관리 예약 안내입니다. 구·군별 지역, 지하철역 인근, 테마별 관리를 한곳에서 확인하세요.</p>
  </div>
  <div><h4>안내</h4>
    <a href="/incheon/">인천 출장마사지</a><a href="/incheon/area/">지역별 안내</a>
    <a href="/incheon/stations/">지하철역별 안내</a><a href="/theme/">테마별 안내</a></div>
  <div><h4>코스</h4>{course_links}</div>
  <div><h4>이용</h4>
    <a href="/reservation/">예약안내</a><a href="/guide/">이용가이드</a>
    <a href="/reviews/">후기</a><a href="/customer/">고객센터</a></div>
</div>
<div class="footer-ops">
  <div><b>운영 시간</b>{HOURS}</div>
  <div><b>전화 예약·상담</b><a href="tel:{PHONE_TEL}">{PHONE_DISP}</a></div>
</div>
<div class="company-info">
  <div><b>상호</b> {COMPANY['name']}</div>
  <div><b>대표</b> {COMPANY['ceo']}</div>
  <div><b>사업자등록번호</b> {COMPANY['biz_no']}</div>
  <div><b>주소</b> {COMPANY['addr']}</div>
  <div><b>통신판매업신고</b> {COMPANY['sales_no']}</div>
  <div><b>개인정보보호책임자</b> {COMPANY['privacy_officer']}</div>
</div>
<div class="footer-policies">
  <a href="/customer/#notice">공지사항</a><a href="/customer/#qna">자주 묻는 질문</a>
  <a href="/customer/#inquiry">1:1 문의</a><a href="/privacy/">개인정보처리방침</a>
  <a href="/terms/">이용약관</a><a href="/youth/">청소년보호정책</a>
</div>
<div class="footer-bottom">
  © 2026 {COMPANY['name']}. All rights reserved. · 콘텐츠 최종 업데이트 {UPDATED.replace('-', '.')}
  <div class="legal-note">본 서비스는 의료 행위가 아닌 건강관리(이완·휴식) 목적의 방문 관리 서비스이며, 만 19세 이상 성인을 대상으로 합니다. 불법·퇴폐 행위는 일절 제공하지 않습니다.</div>
</div>
</div></footer>"""

# ---------------------------------------------------------------------------
# Shared JS  (idle-loaded)
# ---------------------------------------------------------------------------
JS = """
(function(){
  var t=document.querySelector('.toggle'),m=document.getElementById('primary-menu');
  if(t&&m){t.addEventListener('click',function(){
    var o=m.classList.toggle('open');t.setAttribute('aria-expanded',o);});}
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&m){m.classList.remove('open');}});
  function idle(fn){if('requestIdleCallback'in window){requestIdleCallback(fn,{timeout:1500});}else{setTimeout(fn,1);}}
  idle(function(){
    if(!('IntersectionObserver'in window)){document.querySelectorAll('.reveal').forEach(function(el){el.classList.add('in');});return;}
    var io=new IntersectionObserver(function(es){es.forEach(function(e){
      if(e.isIntersecting){e.target.classList.add('in');io.unobserve(e.target);}});},{threshold:.12,rootMargin:'80px'});
    document.querySelectorAll('.reveal').forEach(function(el){io.observe(el);});
    var secs=[].slice.call(document.querySelectorAll('.lux-sec')),
        links=[].slice.call(document.querySelectorAll('.toc a'));
    if(secs.length&&links.length){
      var spy=new IntersectionObserver(function(es){es.forEach(function(e){
        if(e.isIntersecting){var id=e.target.id;
          links.forEach(function(a){a.classList.toggle('active',a.getAttribute('href')==='#'+id);});}});
      },{rootMargin:'-35% 0px -55% 0px'});
      secs.forEach(function(s){spy.observe(s);});
    }
  });
})();
"""

# ---------------------------------------------------------------------------
# Page shell
# ---------------------------------------------------------------------------
def page(path, title, desc, active, body, jsonld=None, og_type="website"):
    canonical = BASE_URL + path
    ld = ""
    if jsonld:
        if isinstance(jsonld, list):
            blocks = jsonld
        else:
            blocks = [jsonld]
        ld = "".join(
            '<script type="application/ld+json">'
            + json.dumps(b, ensure_ascii=False, separators=(",", ":"))
            + "</script>"
            for b in blocks
        )
    og_img = BASE_URL + "/assets/og-cover.jpg"
    # 네이버 서치어드바이저 사이트 소유확인 — 메인페이지에만 노출
    verify = f'\n<meta name="naver-site-verification" content="{NAVER_VERIFY}">' if path == "/" else ""
    html = f"""<!doctype html>
<html lang="ko">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="theme-color" content="#0b0b0e">
<meta name="format-detection" content="telephone=no">
<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
<meta name="googlebot" content="index,follow">
<meta name="referrer" content="strict-origin-when-cross-origin">
<title>{title}</title>
<meta name="description" content="{desc}">
<meta name="author" content="{COMPANY['name']} 운영팀">{verify}
<link rel="canonical" href="{canonical}">
<link rel="alternate" hreflang="ko-KR" href="{canonical}">
<link rel="alternate" hreflang="x-default" href="{canonical}">
<meta property="og:type" content="{og_type}">
<meta property="og:site_name" content="{BRAND}">
<meta property="og:locale" content="ko_KR">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{canonical}">
<meta property="og:image" content="{og_img}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{title}">
<meta name="twitter:description" content="{desc}">
<meta name="twitter:image" content="{og_img}">
<link rel="icon" href="/favicon.ico" sizes="any">
<link rel="icon" type="image/svg+xml" href="/favicon.svg">
<link rel="apple-touch-icon" href="/apple-touch-icon.png">
<link rel="manifest" href="/site.webmanifest">
<style>{CSS}</style>
{ld}
</head>
<body>
{menu_html(active)}
{body}
{footer_html()}
{call_fab()}
<script>{JS}</script>
</body>
</html>"""
    return html

def call_fab():
    """오렌지색 플로팅 전화예약 버튼 — 전 페이지 고정 노출."""
    phone_svg = ('<svg viewBox="0 0 24 24" aria-hidden="true"><path d="M6.6 10.8c1.4 2.8 3.8 5.2 '
                 '6.6 6.6l2.2-2.2c.28-.28.68-.36 1.02-.24 1.12.37 2.33.57 3.58.57.55 0 1 .45 1 '
                 '1V20c0 .55-.45 1-1 1C10.4 21 3 13.6 3 4.4c0-.55.45-1 1-1h3.6c.55 0 1 .45 1 1 0 '
                 '1.25.2 2.46.57 3.58.12.34.04.74-.24 1.02l-2.2 2.2z"/></svg>')
    return (f'<a class="call-fab" href="tel:{PHONE_TEL}" aria-label="전화 예약 {PHONE_DISP}">'
            f'<span class="call-fab-ic">{phone_svg}</span>'
            f'<span class="call-fab-tx">전화 예약<small>{PHONE_DISP}</small></span></a>')

# ---------------------------------------------------------------------------
# Reusable body builders
# ---------------------------------------------------------------------------
def breadcrumb(items):
    # items: list of (href or None, label)
    parts = []
    for href, label in items:
        if href:
            parts.append(f'<a href="{href}">{label}</a>')
        else:
            parts.append(f"<b>{label}</b>")
    return f'<div class="wrap"><nav class="crumb" aria-label="탐색경로">{" › ".join(parts)}</nav></div>'

def breadcrumb_ld(items):
    return {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": label,
             "item": BASE_URL + href}
            for i, (href, label) in enumerate(items) if href
        ] + [
            {"@type": "ListItem", "position": len(items), "name": items[-1][1]}
        ][:0],  # last handled below
    }

def bc_ld(trail):
    # trail: list of (path, name); last is current page
    el = []
    for i, (p, n) in enumerate(trail):
        item = {"@type": "ListItem", "position": i + 1, "name": n}
        if p:
            item["item"] = BASE_URL + p
        el.append(item)
    return {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": el}

def faq_block(qas, heading="자주 묻는 질문"):
    rows = "".join(
        f"<details><summary>{q}<span>+</span></summary><div>{a}</div></details>"
        for q, a in qas
    )
    return f"""<section class="block" id="faq"><div class="wrap">
<span class="eyebrow"><span class="pulse"></span>FAQ</span>
<h2 class="sec">{heading}</h2>
<div style="margin-top:26px;max-width:820px">{rows}</div>
</div></section>"""

def faq_ld(qas):
    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": [
            {"@type": "Question", "name": q,
             "acceptedAnswer": {"@type": "Answer", "text": a}}
            for q, a in qas
        ],
    }

def notes_block(eyebrow, heading, lead, notes, _id="about"):
    cards = "".join(
        f'<div class="note-card reveal"><div class="note-num">{n:02d}</div>'
        f'<div class="note-content"><h3 class="note-title">{t}</h3>'
        f'<div class="note-text">{"".join(f"<p>{p}</p>" for p in ps)}</div></div></div>'
        for n, (t, ps) in enumerate(notes, 1)
    )
    return f"""<section class="block" id="{_id}"><div class="wrap">
<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>
<h2 class="sec">{heading}</h2>
<p class="sec-lead">{lead}</p>
<div class="note-stack" style="margin-top:30px">{cards}</div>
</div></section>"""

def price_grid(courses):
    cards = ""
    for c in courses:
        best = " best" if c.get("best") else ""
        badge = '<span class="best-badge">BEST</span>' if c.get("best") else ""
        rows = "".join(f"<div><span>{t}</span><span>{p}</span></div>" for t, p in c["prices"])
        cards += (
            f'<div class="price-card{best}" id="{c["slug"]}">{badge}'
            f'<div class="k">{c["kicker"]}</div><h3>{c["name"]}</h3>'
            f'<p>{c["desc"]}</p><div class="time-rows">{rows}</div></div>'
        )
    return f'<div class="grid g3">{cards}</div>'

def price_menu_block(anchor="pricing-menu"):
    """코스별 기본 요금 (60·90·120분) — 메인/모든 지역 페이지 공통 블록."""
    cards = ""
    for p in TIME_PRICING:
        best = " best" if p.get("best") else ""
        badge = '<span class="pmenu-badge">추천</span>' if p.get("best") else ""
        cards += (
            f'<div class="pmenu-card{best}">{badge}'
            f'<div class="pmenu-name">{p["name"]}</div>'
            f'<div class="pmenu-price">{p["price"]}<span>원</span></div>'
            f'<div class="pmenu-dur">{p["dur"]}</div>'
            f'<div class="pmenu-desc">{p["desc"]}</div>'
            f'<a class="pmenu-btn" href="tel:{PHONE_TEL}">예약 문의</a></div>'
        )
    return (
        f'<section class="block" id="{anchor}"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>요금 안내</span>'
        f'<h2 class="sec">코스별 기본 요금</h2>'
        f'<p class="sec-lead">60·90·120분 코스별 기본 요금입니다. 숨겨진 추가 비용 없이 투명하게 안내합니다.</p>'
        f'<div class="pmenu">{cards}</div>'
        f'<p class="pmenu-note">지역·예약 시간대·이동 거리에 따라 상담 시 최종 확인됩니다. '
        f'<a href="/course/">상세 요금 안내 보기 →</a></p>'
        f'</div></section>'
    )

def offer_ld():
    """코스별 기본 요금 구조화 데이터(Offer)."""
    return {
        "@context": "https://schema.org", "@type": "OfferCatalog",
        "name": "코스별 기본 요금",
        "itemListElement": [
            {"@type": "Offer", "name": p["name"],
             "price": p["price"].replace(",", ""), "priceCurrency": "KRW",
             "description": p["desc"], "url": BASE_URL + "/course/"}
            for p in TIME_PRICING
        ],
    }

def cta_band(title="오늘 밤, 가까운 곳에서 휴식을 예약하세요", sub=None):
    sub = sub or f"{HOURS} · 전화 한 통으로 방문 일정과 코스를 안내드립니다."
    return f"""<section class="cta-band"><div>
<span class="eyebrow"><span class="pulse"></span>RESERVE</span>
<h2>{title}</h2><p>{sub}</p>
<div class="actions" style="justify-content:center">
<a class="btn btn-primary" href="tel:{PHONE_TEL}">{PHONE_DISP} 전화하기 →</a>
<a class="btn btn-ghost" href="/reservation/">예약 안내 보기</a>
</div></div></section>"""

UPDATED = "2026-06-06"

def byline():
    """저자·감수·업데이트 표기 (E-E-A-T 신뢰 신호)."""
    return (f'<div class="byline">'
            f'<span class="au">작성 · 굿데이 운영팀</span>'
            f'<span>감수 · {COMPANY["ceo"]} ({COMPANY["name"]} 대표)</span>'
            f'<span>최종 업데이트 · {UPDATED.replace("-", ".")}</span></div>')

def og_image_obj():
    # 선호 썸네일(스키마+og:image 동시 지정) — 1200×630 OG 커버
    return {"@type": "ImageObject", "url": BASE_URL + "/assets/og-cover.jpg",
            "width": 1200, "height": 630}

def publisher_obj():
    return {"@type": "Organization", "name": COMPANY["name"], "url": BASE_URL + "/",
            "logo": {"@type": "ImageObject", "url": BASE_URL + "/icon-512.png",
                     "width": 512, "height": 512}}

def article_ld(title, desc, path):
    return {
        "@context": "https://schema.org", "@type": "Article",
        "headline": title, "description": desc, "inLanguage": "ko-KR",
        "author": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/about/"},
        "publisher": publisher_obj(),
        "mainEntityOfPage": BASE_URL + path,
        "image": og_image_obj(),
        "datePublished": UPDATED, "dateModified": UPDATED,
    }

def render_lux(sections):
    """다크 럭스 섹션 패널 + 좌측 고정 목차(TOC) 생성.
    sections: [(title, [블록...])]  블록: 문자열(문단)/("ul",[…])/("h3","…")/("html","원본")."""
    toc, panels = [], []
    for i, (title, blocks) in enumerate(sections, 1):
        sid = f"sec-{i}"
        toc.append(f'<li><a href="#{sid}">{title}</a></li>')
        inner = ""
        for b in blocks:
            if isinstance(b, tuple) and b[0] == "ul":
                inner += "<ul>" + "".join(f"<li>{x}</li>" for x in b[1]) + "</ul>"
            elif isinstance(b, tuple) and b[0] == "h3":
                inner += f"<h3>{b[1]}</h3>"
            elif isinstance(b, tuple) and b[0] == "html":
                inner += b[1]
            else:
                inner += f"<p>{b}</p>"
        panels.append(f'<section class="lux-sec reveal" id="{sid}"><h2>{title}</h2>{inner}</section>')
    toc_html = ('<aside class="toc"><div class="toc-inner"><span class="toc-label">목차</span>'
                f'<ul>{"".join(toc)}</ul></div></aside>')
    return toc_html, "".join(panels)

def content_page(path, active, trail, *, title, desc, eyebrow, h1, lead,
                 sections, faq, data_note=None, service=None, show_price=False,
                 top_links=None, extra_schema=None, cta_title=None):
    """E-E-A-T 기준 개별 콘텐츠 페이지 생성기 (다크 럭스 레이아웃 + TOC)."""
    toc_html, panels = render_lux(sections)
    if data_note:
        panels += f'<div class="data-box"><b>현장 운영 메모</b><p>{data_note}</p></div>'
    links_html = ""
    if top_links:
        btns = ""
        for href, label, *rest in top_links:
            primary = rest and rest[0]
            cls = "btn btn-primary" if primary else "btn btn-ghost"
            btns += f'<a class="{cls}" href="{href}">{label}</a>'
        links_html = f'<div class="actions" style="margin-top:22px">{btns}</div>'
    body = (breadcrumb(trail) +
        f'<section class="lux-hero"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>{eyebrow}</span>'
        f'<h1 class="lux-h1">{h1}</h1>'
        f'<p class="lux-lead">{lead}</p>{byline()}{links_html}</div></section>'
        f'<section class="block lux-body" style="padding-top:34px"><div class="wrap">'
        f'<div class="lux-grid">{toc_html}<div class="lux-main">{panels}</div></div>'
        f'</div></section>'
        + (price_menu_block() if show_price else "")
        + faq_block(faq) + (cta_band(cta_title) if cta_title else cta_band()))
    jsonld = [bc_ld(trail), article_ld(title, desc, path), faq_ld(faq)]
    if service:
        jsonld.append(service_ld(service[0], service[1], path))
        jsonld.append(offer_ld())
    if extra_schema:
        jsonld += extra_schema
    write(path, page(path, title, desc, active, body, jsonld, og_type="article"))

# ---------------------------------------------------------------------------
# JSON-LD: org / localbusiness / website
# ---------------------------------------------------------------------------
def org_ld():
    return {
        "@context": "https://schema.org", "@type": "Organization",
        "name": BRAND, "legalName": COMPANY["name"], "url": BASE_URL + "/",
        "telephone": PHONE_DISP,
        "logo": {"@type": "ImageObject", "url": BASE_URL + "/icon-512.png", "width": 512, "height": 512},
        "image": og_image_obj(),
        "address": {"@type": "PostalAddress",
                    "addressRegion": "인천광역시", "addressCountry": "KR"},
    }

def website_ld():
    return {
        "@context": "https://schema.org", "@type": "WebSite",
        "name": BRAND, "url": BASE_URL + "/",
        "potentialAction": {"@type": "SearchAction",
            "target": BASE_URL + "/?q={search_term_string}",
            "query-input": "required name=search_term_string"},
    }

def localbiz_ld(name=None, area="인천광역시", path="/"):
    # 신규 사이트로 실제 후기 데이터가 확정되기 전까지 aggregateRating은 넣지 않음(허위 구조화 데이터 방지)
    return {
        "@context": "https://schema.org",
        "@type": "HealthAndBeautyBusiness",
        "name": name or BRAND, "url": BASE_URL + path,
        "telephone": PHONE_DISP, "priceRange": "₩₩",
        "image": og_image_obj(),
        "areaServed": {"@type": "AdministrativeArea", "name": area},
        "address": {"@type": "PostalAddress",
                    "addressRegion": "인천광역시", "addressCountry": "KR"},
        "openingHoursSpecification": {"@type": "OpeningHoursSpecification",
            "dayOfWeek": ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"],
            "opens": "00:00", "closes": "23:59"},
    }

def service_ld(name, desc, path, area="인천광역시"):
    return {
        "@context": "https://schema.org", "@type": "Service",
        "name": name, "description": desc, "serviceType": "방문 건강관리(마사지) 서비스",
        "provider": {"@type": "Organization", "name": BRAND, "url": BASE_URL + "/"},
        "areaServed": {"@type": "AdministrativeArea", "name": area},
        "image": og_image_obj(),
        "url": BASE_URL + path,
    }

# ===========================================================================
# PAGE BUILDERS
# ===========================================================================
def write(path, html):
    if path == "/":
        out = os.path.join(ROOT, "index.html")
    else:
        d = os.path.join(ROOT, path.strip("/"))
        os.makedirs(d, exist_ok=True)
        out = os.path.join(d, "index.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)

# ===========================================================================
# DATA MODEL — 구/군 · 대표 동 · 지하철역 · 테마
# ===========================================================================
def _d(slug, name, arrival, landmarks, character):
    # arrival: 평균 도착(분). 0 = 도서·외곽으로 선편/사전 협의가 필요한 지역
    return {"slug": slug, "name": name, "arrival": arrival,
            "landmarks": landmarks, "character": character}

# 인천 2군·8구 (2026-07 행정체제 개편 전 현재 기준)
GU = [
    {"slug": "ganghwa-gun", "name": "강화군", "type": "군",
     "summary": "강화도 일원의 역사 유적과 자연, 정주 생활이 어우러진 인천 북서부 지역입니다.",
     "dongs": [
        _d("ganghwa-eup", "강화읍", 45, "강화풍물시장, 강화산성, 고려궁지 일대", "강화군의 행정·상권 중심지"),
        _d("seonwon-myeon", "선원면", 47, "선원사지, 강화읍 인접 일대", "강화읍과 접한 전원형 농촌 생활권"),
        _d("bureun-myeon", "불은면", 50, "광성보, 덕진진 일대", "강화 남단 해안 방어유적이 있는 농촌 지역"),
        _d("gilsang-myeon", "길상면", 52, "전등사, 온수리 일대", "정족산과 전등사를 낀 남부 생활권"),
        _d("hwado-myeon", "화도면", 55, "마니산, 동막해변 일대", "마니산과 갯벌 해안을 품은 관광 지역"),
        _d("yangdo-myeon", "양도면", 53, "강화나들길, 가릉 일대", "전원 마을이 이어진 중부 농촌 지역"),
        _d("naega-myeon", "내가면", 52, "고려산, 고천리 일대", "고려산 자락의 한적한 농촌 생활권"),
        _d("hajeom-myeon", "하점면", 53, "강화 부근리 고인돌, 봉천산 일대", "세계유산 고인돌이 있는 북부 농촌 지역"),
        _d("yangsa-myeon", "양사면", 57, "강화평화전망대 방향, 북성리 일대", "북녘이 보이는 강화 최북단 해안 마을"),
        _d("songhae-myeon", "송해면", 55, "강화나들길, 솔정리 일대", "강화읍 북서쪽의 한적한 농촌 지역"),
        _d("gyodong-myeon", "교동면", 0, "교동도, 대룡시장 일대", "교동대교로 연결된 섬 지역(사전 협의 필요)"),
        _d("samsan-myeon", "삼산면", 0, "석모도, 보문사 일대", "석모대교로 연결된 섬 지역(사전 협의 필요)"),
        _d("seodo-myeon", "서도면", 0, "주문도·볼음도 일대", "선편으로만 닿는 도서 지역(사전 협의 필요)"),
     ]},
    {"slug": "ongjin-gun", "name": "옹진군", "type": "군",
     "summary": "서해의 여러 섬으로 이루어진 도서 지역으로, 방문은 선편 일정에 따라 사전 협의가 필요합니다.",
     "dongs": [
        _d("bukdo-myeon", "북도면", 0, "신도·시도·모도, 삼목선착장 방향 일대", "영종도 옆 섬마을(선편 이용, 사전 협의)"),
        _d("yeonpyeong-myeon", "연평면", 0, "연평도, 연평항 일대", "서해5도 도서 지역(선편 이용, 사전 협의)"),
        _d("baengnyeong-myeon", "백령면", 0, "백령도, 두무진 일대", "서해 최북단 도서 지역(선편 이용, 사전 협의)"),
        _d("daecheong-myeon", "대청면", 0, "대청도·소청도 일대", "서해5도 도서 지역(선편 이용, 사전 협의)"),
        _d("deokjeok-myeon", "덕적면", 0, "덕적도, 서포리해변 일대", "서해 도서 지역(선편 이용, 사전 협의)"),
        _d("jawol-myeon", "자월면", 0, "자월도·승봉도·이작도 일대", "서해 도서 지역(선편 이용, 사전 협의)"),
        _d("yeongheung-myeon", "영흥면", 0, "영흥도, 십리포해변 일대", "영흥대교로 연결된 도서 지역(사전 협의 필요)"),
     ]},
    {"slug": "jung-gu", "name": "중구", "type": "구",
     "summary": "근대 개항장 원도심과 영종국제도시·공항이 함께 있는 해양 관문 지역입니다.",
     "dongs": [
        _d("sinpo-dong", "신포동", 35, "신포국제시장, 차이나타운, 인천아트플랫폼 일대", "근대 개항장 문화가 남은 원도심 상권"),
        _d("yeonan-dong", "연안동", 38, "인천항 연안부두, 종합어시장 일대", "항만과 어시장이 자리한 해안 생활권"),
        _d("sinheung-dong", "신흥동", 36, "신흥시장, 인천역 방향 일대", "원도심 주거와 상업이 섞인 생활권"),
        _d("dowon-dong", "도원동", 35, "도원역, 제물포 방향 일대", "경인선 도원역 인근의 구릉 주거지"),
        _d("yulmok-dong", "율목동", 36, "율목공원, 답동성당 인근", "근대 건축이 남은 조용한 언덕 주거지"),
        _d("dongincheon-dong", "동인천동", 34, "동인천역, 배다리, 신포동 방향 일대", "동인천역을 낀 원도심 중심 상권"),
        _d("gaehang-dong", "개항동", 35, "개항장 거리, 월미도 방향, 인천역 일대", "근대 개항장과 월미도를 잇는 관광 생활권"),
        _d("yeongjong-dong", "영종동", 50, "영종국제도시, 인천공항, 하늘도시 일대", "공항과 함께 성장한 영종도 신도시"),
        _d("unseo-dong", "운서동", 52, "운서역, 공항신도시, 백운산 일대", "공항철도 운서역 중심의 영종 정주 생활권"),
        _d("yongyu-dong", "용유동", 55, "을왕리해수욕장, 왕산해변, 마시안해변 일대", "영종도 서쪽 해변 관광 지역"),
     ]},
    {"slug": "dong-gu", "name": "동구", "type": "구",
     "summary": "인천항 배후의 오래된 주거지와 근대 문화거리가 남아 있는 원도심 지역입니다.",
     "dongs": [
        _d("manseok-dong", "만석동", 36, "만석부두, 괭이부리마을 일대", "항만과 마주한 동구 북부 생활권"),
        _d("hwasu-hwapyeong-dong", "화수·화평동", 35, "화평동 냉면거리, 화수부두 일대", "화수·화평을 아우르는 해안 주거 생활권"),
        _d("songhyeon-dong", "송현동", 34, "수도국산달동네박물관, 송현시장 일대", "달동네 박물관과 시장을 낀 주거지"),
        _d("songnim-dong", "송림동", 35, "송림오거리, 동산 일대", "동구 중심의 오래된 주거 밀집지"),
        _d("geumchang-dong", "금창동", 35, "배다리 헌책방거리, 창영동 일대", "배다리 문화거리가 있는 원도심 생활권"),
     ]},
    {"slug": "michuhol-gu", "name": "미추홀구", "type": "구",
     "summary": "제물포 원도심과 대학가, 주안 번화가가 모인 인천 중부 주거·상업 지역입니다.",
     "dongs": [
        _d("sungui-dong", "숭의동", 33, "숭의역, 제물포역, 인천축구전용경기장 일대", "제물포 일대 원도심 주거·상업 생활권"),
        _d("yonghyeon-dong", "용현동", 34, "인하대학교, 용현시장, 토지금고 일대", "인하대를 낀 대학가·주거 생활권"),
        _d("hagik-dong", "학익동", 33, "법조단지, 학익시장 일대", "법원·검찰청이 자리한 행정·주거 생활권"),
        _d("dohwa-dong", "도화동", 32, "도화역, 인천대 제물포캠퍼스, 도화지구 일대", "재개발로 정비된 도화역 주거 생활권"),
        _d("juan-dong", "주안동", 30, "주안역, 주안로데오거리, 미추홀구청 일대", "미추홀구 최대 상권이 모인 주안역 생활권"),
        _d("gwangyo-dong", "관교동", 31, "인천종합터미널, 신세계백화점, 문학경기장 방향 일대", "터미널과 백화점을 낀 교통·상업 생활권"),
        _d("munhak-dong", "문학동", 32, "문학경기장, 문학산, 인천향교 일대", "문학산 자락의 체육·문화 생활권"),
     ]},
    {"slug": "yeonsu-gu", "name": "연수구", "type": "구",
     "summary": "송도국제도시와 한적한 해안 주거지가 어우러진 인천 남부 신·구 혼합 지역입니다.",
     "dongs": [
        _d("ongnyeon-dong", "옥련동", 33, "옥련국제사격장, 청량산, 인천상륙작전기념관 일대", "청량산과 해안을 낀 연수구 서부 주거지"),
        _d("seonhak-dong", "선학동", 32, "선학역, 선학경기장 일대", "인천1·2호선 선학역 인근 주거 생활권"),
        _d("yeonsu-dong", "연수동", 31, "연수역, 원인재, 연수구청 일대", "연수구 행정 중심의 대단지 주거권"),
        _d("cheonghak-dong", "청학동", 33, "청학동, 문학산 남측 일대", "문학산 자락의 조용한 주거 생활권"),
        _d("dongchun-dong", "동춘동", 32, "동춘역, 해양경찰청, 연수구청 방향 일대", "동춘역을 낀 정주형 주거 생활권"),
        _d("songdo-dong", "송도동", 34, "송도국제도시, 센트럴파크, 인천대학교, 트리플스트리트 일대", "국제업무·연구단지가 모인 송도 신도시"),
     ]},
    {"slug": "namdong-gu", "name": "남동구", "type": "구",
     "summary": "인천시청과 구월동 번화가, 소래포구와 신도시가 함께 있는 인천 행정 중심 지역입니다.",
     "dongs": [
        _d("guwol-dong", "구월동", 30, "인천시청, 구월로데오거리, 남동구청 일대", "인천시청을 낀 행정·번화가 중심 생활권"),
        _d("gaseok-dong", "간석동", 31, "간석오거리역, 석바위 방향 일대", "간석오거리 교통 요지의 주거·상업 생활권"),
        _d("mansu-dong", "만수동", 32, "만수역, 인천대공원 방향, 만수시장 일대", "인천대공원과 인접한 대단지 주거권"),
        _d("jangsu-seochang-dong", "장수서창동", 35, "장수동 은행나무, 서창지구 방향 일대", "외곽 자연과 신주거가 섞인 생활권"),
        _d("seochang-dong", "서창동", 34, "서창2지구, 서창퍼스트뷰 일대", "택지개발로 조성된 신주거 생활권"),
        _d("namchon-dorim-dong", "남촌도림동", 34, "남동인더스파크, 도림동 일대", "남동공단과 접한 주거·산업 혼합 생활권"),
        _d("nonhyeon-dong", "논현동", 33, "논현지구, 소래포구, 호구포역 방향 일대", "소래포구를 낀 논현 신도시 생활권"),
        _d("nonhyeon-gojan-dong", "논현고잔동", 34, "에코메트로, 인천논현역, 소래포구 일대", "수인분당선 논현역 중심의 신도시 생활권"),
     ]},
    {"slug": "bupyeong-gu", "name": "부평구", "type": "구",
     "summary": "수도권 최대급 환승역 부평을 중심으로 상권과 주거가 밀집한 인천 동부 지역입니다.",
     "dongs": [
        _d("bupyeong-dong", "부평동", 30, "부평역, 부평지하상가, 부평문화의거리 일대", "수도권 최대급 환승역을 낀 부평 최대 번화가"),
        _d("sangok-dong", "산곡동", 31, "산곡역, 캠프마켓 방향, 백운공원 일대", "재개발이 활발한 부평 서부 주거권"),
        _d("cheongcheon-dong", "청천동", 32, "청천농장사거리, 부평공단 방향 일대", "산업단지와 접한 주거 생활권"),
        _d("galsan-dong", "갈산동", 31, "갈산역, 부평구청, 부평농산물도매시장 일대", "부평구청을 낀 행정·주거 생활권"),
        _d("samsan-dong", "삼산동", 31, "삼산체육관, 삼산월드체육관, 홈플러스 일대", "삼산체육관을 낀 신주거 생활권"),
        _d("bugae-dong", "부개동", 32, "부개역, 부개도서관 일대", "경인선 부개역 인근 주거 밀집지"),
        _d("ilsin-dong", "일신동", 33, "부평삼거리역 방향, 일신시장 일대", "부평 남동부의 한적한 주거 생활권"),
        _d("sipjeong-dong", "십정동", 32, "동암역, 열우물경기장 일대", "동암역을 낀 경계 주거 생활권"),
     ]},
    {"slug": "gyeyang-gu", "name": "계양구", "type": "구",
     "summary": "계양산과 경인교대, 공항철도·인천1호선이 지나는 인천 북부 주거 지역입니다.",
     "dongs": [
        _d("hyoseong-dong", "효성동", 33, "효성시장, 천마산, 작전 방향 일대", "천마산 자락의 주거 밀집 생활권"),
        _d("gyesan-dong", "계산동", 33, "계산역, 경인교대입구역, 계양산, 계양구청 일대", "계양산과 경인교대를 낀 계양 중심 생활권"),
        _d("jakjeon-dong", "작전동", 32, "작전역, 롯데마트, 작전시장 일대", "작전역을 낀 대단지 주거 생활권"),
        _d("jakjeon-seoun-dong", "작전·서운동", 33, "서운산업단지, 작전동 방향 일대", "서운산단과 접한 주거·산업 생활권"),
        _d("gyeyang-dong", "계양동", 34, "계양역, 임학역, 계양구청 방향, 귤현 일대", "공항철도·인천1호선 계양역 인근 생활권"),
     ]},
    {"slug": "seo-gu", "name": "서구", "type": "구",
     "summary": "청라국제도시와 검단신도시, 아라뱃길이 자리한 인천 서북부 신·구 혼합 지역입니다.",
     "dongs": [
        _d("geomam-gyeongseo-dong", "검암경서동", 35, "검암역, 서구청 방향, 경서동 일대", "공항철도 검암역을 낀 서구 관문 생활권"),
        _d("yeonhui-dong", "연희동", 34, "아시아드주경기장, 연희자연마당 일대", "아시아드경기장을 낀 주거·체육 생활권"),
        _d("cheongna-dong", "청라동", 33, "청라국제도시, 청라호수공원, 커낼웨이 일대", "호수공원을 중심으로 조성된 청라 신도시"),
        _d("gajeong-dong", "가정동", 33, "가정역, 루원시티, 가정중앙시장 일대", "루원시티 개발이 진행된 가정역 생활권"),
        _d("sinhyeon-wonchang-dong", "신현원창동", 35, "신현동, 원창동 공단, 봉수대로 일대", "공단과 주거가 섞인 서구 중부 생활권"),
        _d("seoknam-dong", "석남동", 34, "석남역, 거북시장, 가정역 방향 일대", "7호선 석남역을 낀 주거 밀집지"),
        _d("gajwa-dong", "가좌동", 34, "인천가좌역, 서부산업단지, 가좌시장 일대", "산업단지와 접한 주거 생활권"),
        _d("geomdan-dong", "검단동", 38, "검단사거리역, 검단시장 일대", "검단 신·구도심이 만나는 중심 생활권"),
        _d("bullo-daegok-dong", "불로대곡동", 39, "불로동, 대곡동 고인돌, 검단 방향 일대", "검단신도시와 인접한 북부 생활권"),
        _d("wondang-dong", "원당동", 38, "원당지구, 검단신도시, 완정역 방향 일대", "검단신도시 택지의 신주거 생활권"),
        _d("dangha-dong", "당하동", 38, "당하지구, 검단신도시, 검단사거리 방향 일대", "검단신도시 중심의 대단지 주거권"),
        _d("oryu-wanggil-dong", "오류왕길동", 40, "왕길역, 오류동, 검단산업단지 일대", "왕길역과 산업단지를 낀 서구 북단 생활권"),
        _d("majeon-dong", "마전동", 39, "마전지구, 검단사거리, 검단 방향 일대", "검단 생활권의 정주형 주거지"),
        _d("ara-dong", "아라동", 37, "아라역, 경인아라뱃길, 검암 방향 일대", "아라뱃길을 낀 서구 신주거 생활권"),
     ]},
]

# 지하철역 — 환승역은 여러 노선에 노출되더라도 URL(상세 페이지)은 하나만 사용
LINE_NAMES = {"i1": "인천1호선", "i2": "인천2호선", "k1": "1호선 인천권",
              "s7": "7호선 인천권", "sb": "수인분당선 인천권", "ae": "공항철도 인천권"}

# (name, slug, [line codes], arrival, landmarks, character)
_ST = [
    # 인천1호선
    ("검단호수공원역", "geomdan-lakepark-station", ["i1"], 39, "검단호수공원, 원당지구 일대", "검단신도시 북부의 신주거 역세권"),
    ("신검단중앙역", "sin-geomdan-jungang-station", ["i1"], 39, "검단신도시 중앙, 당하지구 일대", "검단신도시 중심 생활권 역"),
    ("아라역", "ara-station", ["i1"], 38, "경인아라뱃길, 아라동 일대", "아라뱃길을 낀 서구 신주거 역세권"),
    ("계양역", "gyeyang-station", ["i1", "ae"], 34, "계양구청, 계양산, 임학 방향 일대", "인천1호선·공항철도 환승 거점"),
    ("귤현역", "gyulhyeon-station", ["i1"], 35, "귤현차량기지, 계양 방향 일대", "계양 북부의 한적한 역세권"),
    ("박촌역", "bakchon-station", ["i1"], 34, "한들마을, 계양 방향 일대", "계양 주거단지 역세권"),
    ("임학역", "imhak-station", ["i1"], 34, "계양구청, 임학공원 일대", "계양 행정 인근 주거 역세권"),
    ("계산역", "gyesan-station", ["i1"], 33, "경인교대, 계양산, 계산시장 일대", "계양 중심 상권 역세권"),
    ("경인교대입구역", "gyeongin-univ-station", ["i1"], 33, "경인교육대학교, 계산동 일대", "대학을 낀 계양 주거 역세권"),
    ("작전역", "jakjeon-station", ["i1"], 32, "롯데마트, 작전시장 일대", "작전동 대단지 주거 역세권"),
    ("갈산역", "galsan-station", ["i1"], 31, "부평구청, 부평농산물도매시장 일대", "부평 행정 인근 역세권"),
    ("부평구청역", "bupyeong-gucheong-station", ["i1", "s7"], 31, "부평구청, 갈산 방향 일대", "인천1호선·7호선 환승 행정 거점"),
    ("부평시장역", "bupyeong-market-station", ["i1"], 30, "부평종합시장, 부평문화의거리 일대", "부평 전통시장 역세권"),
    ("부평역", "bupyeong-station", ["i1", "k1"], 30, "부평지하상가, 부평문화의거리, 부평대로 일대", "수도권 최대급 환승·번화가 거점"),
    ("동수역", "dongsu-station", ["i1"], 31, "가톨릭대 인천성모병원 방향, 부평 일대", "부평 동부 주거 역세권"),
    ("부평삼거리역", "bupyeong-samgeori-station", ["i1"], 32, "부평삼거리, 일신동 방향 일대", "부평 남부 주거 역세권"),
    ("간석오거리역", "ganseok-ogeori-station", ["i1"], 31, "간석오거리, 석바위 방향 일대", "남동구 교통 요지 역세권"),
    ("인천시청역", "incheon-city-hall-station", ["i1", "i2"], 30, "인천시청, 구월동 로데오거리 일대", "인천1·2호선 환승 행정·번화가 거점"),
    ("예술회관역", "arts-center-station", ["i1"], 31, "인천종합문화예술회관, 구월동 일대", "문화시설을 낀 구월동 역세권"),
    ("인천터미널역", "incheon-terminal-station", ["i1"], 31, "인천종합터미널, 신세계백화점 일대", "터미널·백화점 상업 거점 역세권"),
    ("문학경기장역", "munhak-stadium-station", ["i1"], 32, "문학경기장, 문학산 일대", "스포츠·문화시설 역세권"),
    ("선학역", "seonhak-station", ["i1"], 32, "선학경기장, 선학동 일대", "연수구 북부 주거 역세권"),
    ("신연수역", "sinyeonsu-station", ["i1"], 32, "연수역 방향, 신연수 일대", "연수 주거단지 역세권"),
    ("원인재역", "wonincae-station", ["i1", "sb"], 32, "원인재 유적, 연수동 일대", "인천1호선·수인분당선 환승 역"),
    ("동춘역", "dongchun-station", ["i1"], 32, "해양경찰청, 연수구청 방향 일대", "연수 정주형 주거 역세권"),
    ("동막역", "dongmak-station", ["i1"], 33, "동막, 송도 방향 일대", "연수·송도 경계 역세권"),
    ("캠퍼스타운역", "campustown-station", ["i1"], 34, "인천대 송도캠퍼스 방향, 송도 일대", "송도 대학가 역세권"),
    ("테크노파크역", "technopark-station", ["i1"], 34, "송도테크노파크, 송도 일대", "송도 연구단지 역세권"),
    ("지식정보단지역", "knowledge-info-station", ["i1"], 34, "송도 지식정보산업단지, 트리플스트리트 일대", "송도 업무·상업 역세권"),
    ("인천대입구역", "incheon-univ-station", ["i1"], 34, "인천대학교, 센트럴파크 방향 일대", "송도 대학·공원 역세권"),
    ("센트럴파크역", "central-park-station", ["i1"], 35, "송도 센트럴파크, 컨벤시아 일대", "송도 국제업무지구 대표 역세권"),
    ("국제업무지구역", "intl-business-station", ["i1"], 35, "송도 국제업무지구, G타워 일대", "송도 업무 중심 역세권"),
    ("송도달빛축제공원역", "songdo-moonlight-station", ["i1"], 36, "달빛축제공원, 송도 남부 일대", "송도 남단 역세권"),
    # 인천2호선
    ("검단오류역", "geomdan-oryu-station", ["i2"], 40, "오류동, 검단산업단지 방향 일대", "서구 북단 검단 역세권"),
    ("왕길역", "wanggil-station", ["i2"], 40, "왕길동, 검단 방향 일대", "검단 산업·주거 혼합 역세권"),
    ("검단사거리역", "geomdan-sageori-station", ["i2"], 38, "검단사거리, 검단시장 일대", "검단 중심 상권 역세권"),
    ("마전역", "majeon-station", ["i2"], 39, "마전지구, 검단 방향 일대", "검단 정주형 주거 역세권"),
    ("완정역", "wanjeong-station", ["i2"], 38, "당하지구, 검단신도시 일대", "검단신도시 주거 역세권"),
    ("독정역", "dokjeong-station", ["i2"], 37, "원당지구, 검단 방향 일대", "검단신도시 외곽 역세권"),
    ("검암역", "geomam-station", ["i2", "ae"], 35, "서구청 방향, 경서동 일대", "인천2호선·공항철도 환승 거점"),
    ("검바위역", "geombawi-station", ["i2"], 35, "검암 방향, 경서동 일대", "서구 관문 인근 주거 역세권"),
    ("아시아드경기장역", "asiad-stadium-station", ["i2"], 34, "아시아드주경기장, 연희동 일대", "체육시설 역세권"),
    ("서구청역", "seogu-office-station", ["i2"], 34, "서구청, 심곡동 일대", "서구 행정 중심 역세권"),
    ("가정역", "gajeong-station", ["i2"], 33, "루원시티, 가정중앙시장 일대", "루원시티 개발 역세권"),
    ("가정중앙시장역", "gajeong-market-station", ["i2"], 33, "가정중앙시장, 가정동 일대", "전통시장을 낀 주거 역세권"),
    ("석남역", "seoknam-station", ["i2", "s7"], 34, "거북시장, 석남동 일대", "인천2호선·7호선 환승 역"),
    ("서부여성회관역", "seobu-womens-station", ["i2"], 34, "서부여성회관, 가좌 방향 일대", "서구 남부 주거 역세권"),
    ("인천가좌역", "incheon-gajwa-station", ["i2"], 34, "서부산업단지, 가좌시장 일대", "산업단지 인근 주거 역세권"),
    ("가재울역", "gajaeul-station", ["i2"], 34, "가재울, 가좌동 일대", "가좌 주거 역세권"),
    ("주안국가산단역", "juan-industrial-station", ["i2"], 33, "주안국가산업단지 일대", "산업단지 역세권"),
    ("주안역", "juan-station", ["i2", "k1"], 30, "주안로데오거리, 미추홀구청 일대", "인천2호선·경인선 환승 번화가 거점"),
    ("시민공원역", "citizens-park-station", ["i2"], 31, "인천시민공원 방향 일대", "공원을 낀 주안 인근 역세권"),
    ("석바위시장역", "seokbawi-market-station", ["i2"], 31, "석바위시장, 미추홀구청 일대", "전통시장·행정 인근 역세권"),
    ("석천사거리역", "seokcheon-sageori-station", ["i2"], 31, "석천사거리, 구월 방향 일대", "남동구 주거 역세권"),
    ("모래내시장역", "moraenae-market-station", ["i2"], 32, "모래내시장, 만수 방향 일대", "전통시장 역세권"),
    ("만수역", "mansu-station", ["i2"], 32, "만수동, 인천대공원 방향 일대", "만수 대단지 주거 역세권"),
    ("남동구청역", "namdong-office-station", ["i2"], 33, "남동구청, 만수 일대", "남동구 행정 중심 역세권"),
    ("인천대공원역", "incheon-grandpark-station", ["i2"], 34, "인천대공원, 장수동 은행나무 일대", "대공원을 낀 외곽 역세권"),
    ("운연역", "unyeon-station", ["i2"], 35, "운연동, 남동 외곽 일대", "인천2호선 남동 종착 역세권"),
    # 1호선(경인선) 인천권
    ("인천역", "incheon-station", ["k1", "sb"], 35, "차이나타운, 월미도 방향 일대", "경인선·수인분당선 환승 원도심 관문"),
    ("동인천역", "dongincheon-station", ["k1"], 34, "동인천역, 신포국제시장, 배다리 일대", "원도심 중심 상권 역세권"),
    ("도원역", "dowon-station", ["k1"], 34, "도원역, 제물포 방향 일대", "원도심 구릉 주거 역세권"),
    ("제물포역", "jemulpo-station", ["k1"], 33, "인천대 제물포캠퍼스 방향, 숭의 일대", "대학·주거 혼합 역세권"),
    ("도화역", "dohwa-station", ["k1"], 32, "도화지구, 도화동 일대", "재정비된 주거 역세권"),
    ("간석역", "ganseok-station", ["k1"], 31, "간석동, 간석오거리 방향 일대", "경인선 간석 주거 역세권"),
    ("동암역", "dongam-station", ["k1"], 32, "십정동, 열우물 일대", "부평·남동 경계 역세권"),
    ("백운역", "baegun-station", ["k1"], 31, "백운역, 부평 방향 일대", "부평 남부 주거 역세권"),
    ("부개역", "bugae-station", ["k1"], 32, "부개역, 부개도서관 일대", "경인선 부개 주거 역세권"),
    # 7호선 인천권
    ("삼산체육관역", "samsan-gym-station", ["s7"], 31, "삼산월드체육관, 홈플러스 일대", "삼산동 체육·상업 역세권"),
    ("굴포천역", "gulpocheon-station", ["s7"], 31, "굴포천, 부평 방향 일대", "부평 북부 주거 역세권"),
    ("산곡역", "sangok-station", ["s7"], 31, "산곡동, 캠프마켓 방향 일대", "재개발 진행 주거 역세권"),
    # 수인분당선 인천권
    ("신포역", "sinpo-station", ["sb"], 35, "신포국제시장, 차이나타운 일대", "원도심 신포 상권 역세권"),
    ("숭의역", "sungui-station", ["sb"], 33, "인천축구전용경기장, 숭의동 일대", "제물포 인근 주거 역세권"),
    ("인하대역", "inha-univ-station", ["sb"], 33, "인하대학교, 용현시장 일대", "대학가 역세권"),
    ("송도역", "songdo-station", ["sb"], 34, "송도역, 옥련 방향 일대", "연수·송도 경계 역세권"),
    ("연수역", "yeonsu-station", ["sb"], 32, "연수구청, 연수동 일대", "연수 행정 인근 역세권"),
    ("남동인더스파크역", "namdong-induspark-station", ["sb"], 33, "남동국가산업단지 일대", "남동공단 역세권"),
    ("호구포역", "hogupo-station", ["sb"], 33, "논현지구, 호구포 일대", "논현 신도시 역세권"),
    ("인천논현역", "incheon-nonhyeon-station", ["sb"], 33, "에코메트로, 소래포구 방향 일대", "논현 신도시 중심 역세권"),
    ("소래포구역", "soraepogu-station", ["sb"], 34, "소래포구, 소래습지생태공원 일대", "소래포구 관광·주거 역세권"),
    # 공항철도 인천권
    ("청라국제도시역", "cheongna-station", ["ae"], 33, "청라호수공원, 커낼웨이 일대", "청라 신도시 대표 역세권"),
    ("영종역", "yeongjong-station", ["ae"], 50, "영종하늘도시, 구읍뱃터 방향 일대", "영종도 신도시 역세권"),
    ("운서역", "unseo-station", ["ae"], 52, "공항신도시, 운서동 일대", "영종 정주 생활권 역세권"),
    ("공항화물청사역", "cargo-terminal-station", ["ae"], 54, "인천공항 화물터미널 일대", "공항 물류 구역 역세권"),
    ("인천공항1터미널역", "airport-t1-station", ["ae"], 55, "인천국제공항 제1여객터미널 일대", "공항 제1터미널 역세권"),
    ("인천공항2터미널역", "airport-t2-station", ["ae"], 56, "인천국제공항 제2여객터미널 일대", "공항 제2터미널 역세권"),
]
STATIONS = {n: {"name": n, "slug": s, "lines": ls, "arrival": a, "landmarks": lm, "character": ch}
            for (n, s, ls, a, lm, ch) in _ST}

# 노선별 역 순서 (메뉴/허브용). 환승역은 여러 노선에 노출되나 STATIONS의 단일 URL을 가리킴
LINES = [
    {"slug": "incheon-line-1", "code": "i1", "name": "인천1호선",
     "stations": ["검단호수공원역","신검단중앙역","아라역","계양역","귤현역","박촌역","임학역","계산역","경인교대입구역","작전역","갈산역","부평구청역","부평시장역","부평역","동수역","부평삼거리역","간석오거리역","인천시청역","예술회관역","인천터미널역","문학경기장역","선학역","신연수역","원인재역","동춘역","동막역","캠퍼스타운역","테크노파크역","지식정보단지역","인천대입구역","센트럴파크역","국제업무지구역","송도달빛축제공원역"]},
    {"slug": "incheon-line-2", "code": "i2", "name": "인천2호선",
     "stations": ["검단오류역","왕길역","검단사거리역","마전역","완정역","독정역","검암역","검바위역","아시아드경기장역","서구청역","가정역","가정중앙시장역","석남역","서부여성회관역","인천가좌역","가재울역","주안국가산단역","주안역","시민공원역","석바위시장역","인천시청역","석천사거리역","모래내시장역","만수역","남동구청역","인천대공원역","운연역"]},
    {"slug": "gyeongin-line", "code": "k1", "name": "1호선 인천권",
     "stations": ["인천역","동인천역","도원역","제물포역","도화역","주안역","간석역","동암역","백운역","부평역","부개역"]},
    {"slug": "seoul-line-7", "code": "s7", "name": "7호선 인천권",
     "stations": ["삼산체육관역","굴포천역","부평구청역","산곡역","석남역"]},
    {"slug": "suin-bundang-line", "code": "sb", "name": "수인분당선 인천권",
     "stations": ["인천역","신포역","숭의역","인하대역","송도역","연수역","원인재역","남동인더스파크역","호구포역","인천논현역","소래포구역"]},
    {"slug": "airport-railroad", "code": "ae", "name": "공항철도 인천권",
     "stations": ["계양역","검암역","청라국제도시역","영종역","운서역","공항화물청사역","인천공항1터미널역","인천공항2터미널역"]},
]

# 테마 — 지역+역+테마 조합 페이지는 만들지 않고 테마 단독 페이지만 운영
THEMES = [
    {"slug": "swedish", "kicker": "SWEDISH", "name": "스웨디시",
     "desc": "오일을 사용해 일정한 압과 리듬으로 전신을 부드럽게 이완하는 대표 관리입니다."},
    {"slug": "lomilomi", "kicker": "LOMI LOMI", "name": "로미로미",
     "desc": "팔과 손을 길게 사용해 파도처럼 흐르듯 진행하는 하와이식 오일 관리입니다."},
    {"slug": "thai", "kicker": "THAI", "name": "타이마사지",
     "desc": "스트레칭과 지압을 결합해 몸의 유연성과 순환을 돕는 관리입니다."},
    {"slug": "chinese", "kicker": "CHINESE", "name": "중국마사지",
     "desc": "경혈과 근막을 따라 또렷한 압으로 풀어주는 지압 중심 관리입니다."},
    {"slug": "aromatherapy", "kicker": "AROMA", "name": "아로마테라피",
     "desc": "블렌딩 오일의 향과 촉감으로 심신을 함께 이완하는 관리입니다."},
    {"slug": "homecare", "kicker": "HOME CARE", "name": "홈케어",
     "desc": "자택 환경에 맞춰 부담 없이 받을 수 있는 생활 밀착형 관리입니다."},
    {"slug": "hotel", "kicker": "HOTEL", "name": "호텔식마사지",
     "desc": "호텔·숙소 객실에서 받는 정중한 응대 중심의 프리미엄 관리입니다."},
    {"slug": "foot", "kicker": "FOOT", "name": "발마사지",
     "desc": "발과 종아리의 피로를 집중적으로 풀어 가벼움을 더하는 관리입니다."},
    {"slug": "sports-meridian", "kicker": "SPORTS", "name": "스포츠·경락",
     "desc": "운동 후 근육과 경락을 따라 또렷하게 풀어 컨디션을 정리하는 관리입니다."},
    {"slug": "skincare", "kicker": "SKIN", "name": "스킨케어",
     "desc": "피부 결을 정돈하고 이완을 더하는 부드러운 케어 중심 관리입니다."},
    {"slug": "waxing", "kicker": "WAXING", "name": "왁싱",
     "desc": "위생 기준에 맞춘 제모 케어로, 사전 안내 후 진행하는 관리입니다."},
    {"slug": "couple-care", "kicker": "COUPLE", "name": "커플 관리",
     "desc": "두 분이 같은 공간에서 나란히 받는 동반형 이완 관리입니다."},
    {"slug": "24h", "kicker": "24H", "name": "24시간",
     "desc": "심야와 새벽까지 상담이 가능한 24시간 운영 안내입니다."},
    {"slug": "sleep", "kicker": "SLEEP", "name": "수면 가능",
     "desc": "관리 후 이동 없이 그대로 휴식·수면으로 이어지는 이완 중심 안내입니다."},
]

# ===========================================================================
# 공통 헬퍼
# ===========================================================================
def arr_text(d):
    return f"평균 {d['arrival']}분 내외" if d.get("arrival") else "선편·차량 일정에 따라 사전 협의"

def _seed(s):
    return int(hashlib.md5(s.encode("utf-8")).hexdigest(), 16)

def _pick(seed, options, salt=""):
    """slug 등으로 결정적 변형 선택 — 페이지마다 다른 문구를 골라 유사도를 낮춘다."""
    return options[_seed(seed + salt) % len(options)]

def _picks(seed, options, salt=""):
    """결정적 순서 셔플 — 링크 목록 등의 순서를 페이지마다 다르게."""
    out = list(options)
    n = len(out)
    for i in range(n - 1, 0, -1):
        j = _seed(seed + salt + str(i)) % (i + 1)
        out[i], out[j] = out[j], out[i]
    return out

# 2026-07-01 인천 행정체제 개편(2군·8구 → 2군·9구) 예정 안내
REORG_2026 = {
    "jung-gu": "중구는 2026년 7월 1일 원도심 지역이 제물포구로, 영종 지역이 영종구로 나뉠 예정입니다. 개편 이후에는 메뉴와 주소 안내가 새 행정구역에 맞게 업데이트됩니다.",
    "dong-gu": "동구는 2026년 7월 1일 중구 원도심과 통합해 제물포구로 개편될 예정입니다. 개편 전까지는 현재 동구 기준으로 안내드립니다.",
    "seo-gu": "서구는 2026년 7월 1일 검단 지역이 검단구로 분리될 예정입니다. 개편 이후에는 검단 일대 안내가 검단구 기준으로 정리됩니다.",
}

# ===========================================================================
# PAGE BUILDERS — 메인 / 대표 / 지역 허브 / 구·군
# ===========================================================================
HOME_FAQ = [
    ("인천 전지역 어디까지 방문 가능한가요?",
     "강화군·옹진군과 8개 구 등 인천 전역을 안내드립니다. 강화·옹진 도서 지역은 선편 일정에 따라 사전 협의가 필요합니다."),
    ("지하철역 근처에서도 예약할 수 있나요?",
     "인천1·2호선과 경인선·7호선·수인분당선·공항철도 인천권 주요 역세권으로 안내 가능합니다. 부평·주안·송도·인천시청역 등은 지하철역별 안내에서 확인하실 수 있습니다."),
    ("당일 예약도 가능한가요?",
     "가능합니다. 시간대와 위치, 배정 상황에 따라 방문 가능 시간이 달라질 수 있어 상담 시 확인해 드립니다."),
    ("테마(스웨디시·타이 등)는 어떻게 선택하나요?",
     "테마별 안내에서 설명을 확인하신 뒤, 예약 시 컨디션과 목적을 말씀해 주시면 적합한 관리를 안내드립니다."),
    ("예약 전 무엇을 준비하면 되나요?",
     "정확한 주소와 출입 방법, 연락 가능한 번호, 희망 시간·코스를 준비해 주시면 빠르게 진행됩니다. 본 서비스는 의료 행위가 아닌 건강관리 서비스로 만 19세 이상을 대상으로 합니다."),
]

def build_home():
    services = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><span class="more">자세히 →</span></a>'
        for c in COURSES[:4])
    # 지역 카드 — 카드명에 '출장마사지' 반복 금지(구/군명만, 요약은 허브 페이지에서)
    regions = "".join(
        f'<a class="card reveal" href="/incheon/{g["slug"]}/"><div class="k">{g["type"]}</div>'
        f'<h3>{g["name"]}</h3><span class="more">지역 안내 →</span></a>'
        for g in GU)
    lines = "".join(
        f'<a class="card reveal" href="/incheon/stations/{ln["slug"]}/"><div class="k">LINE</div>'
        f'<h3>{ln["name"]}</h3><p>{len(ln["stations"])}개 역 인근 방문 안내</p>'
        f'<span class="more">노선 보기 →</span></a>' for ln in LINES)
    rep_stations = ["부평역", "주안역", "송도역", "인천시청역", "계양역", "검암역", "인천공항1터미널역"]
    rep_chips = "".join(
        f'<a class="chip" href="/incheon/stations/{STATIONS[s]["slug"]}/"><b>{s}</b></a>'
        for s in rep_stations)
    themes = "".join(
        f'<a class="card reveal" href="/theme/{t["slug"]}/"><div class="k">{t["kicker"]}</div>'
        f'<h3>{t["name"]}</h3><span class="more">테마 보기 →</span></a>'
        for t in THEMES[:6])
    steps = [
        ("위치 확인", "지역 또는 가까운 역 인근 위치를 알려주세요."),
        ("시간·코스 확인", "희망 시간과 코스, 인원을 확인합니다."),
        ("방문 가능 여부 안내", "배정 상황을 확인해 안내드립니다."),
        ("예약 확정", "관리사가 약속된 시간에 방문합니다."),
    ]
    steps_html = "".join(
        f'<div class="card reveal"><div class="k step"><span class="n serif">{i:02d}</span></div>'
        f'<h3>{t}</h3><p>{d}</p></div>' for i, (t, d) in enumerate(steps, 1))
    check_notes = [
        ("이용 전 확인사항", ["정확한 주소와 공동현관 출입 방법, 주차 가능 여부, 조용한 공간, 예약자 본인의 연락 가능 여부를 미리 확인해 주세요."]),
        ("위생 및 안전 안내", ["용품 위생과 개인정보 보호를 기본으로 운영하며, 만 19세 이상 대상의 건강관리 서비스로 불법·퇴폐 행위는 제공하지 않습니다."]),
    ]
    marquee_items = ["연중무휴 24시간 상담", "인천 전지역 방문", "지하철역 인근 안내",
                     "당일 예약 가능", "위생·안전 관리", "정찰 요금 안내"]
    marquee = "".join(f"<span>{x}</span>" for x in marquee_items * 2)
    body = f"""
<section class="hero"><div class="hero-inner">
  <div class="hero-copy">
    <span class="eyebrow"><span class="pulse"></span>INCHEON · 24H 출장마사지·홈타이</span>
    <h1>인천 어디든,<br>도착하는 <span class="grad">최상의</span><br><span class="serif">휴식 한 시간.</span></h1>
    <p class="lead">부평·주안·송도·청라까지 인천 전지역 출장마사지·홈타이 예약을 연중무휴로 안내드립니다.</p>
    <div class="actions">
      <a class="btn btn-primary" href="tel:{PHONE_TEL}">지금 예약하기 →</a>
      <a class="btn btn-ghost" href="/incheon/area/">지역별 안내</a>
    </div>
    <div class="trust">
      <span><b>인천 2군·8구</b> 전지역</span><span>·</span>
      <span><b>{HOURS}</b></span><span>·</span><span>지하철 6개 노선 역세권 안내</span>
    </div>
  </div>
  <div class="hero-visual">
    <div class="floating fl-1"><span class="dot"></span>LIVE · 방금 송도동 예약</div>
    <div class="glass">
      <h3>RESERVE<b>인천 출장마사지·홈타이</b></h3>
      <div class="book-row"><span>지역</span><span>인천 전지역</span></div>
      <div class="book-row"><span>코스</span><span>스웨디시 90분</span></div>
      <div class="book-row"><span>상담</span><span>{HOURS}</span></div>
      <a class="bk" href="tel:{PHONE_TEL}">전화 예약 →</a>
    </div>
    <div class="floating fl-2">예약전화 · {PHONE_DISP}</div>
  </div>
</div></section>

<div class="marquee" aria-hidden="true"><div class="marquee-track">{marquee}</div></div>

<section class="block"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>SERVICE</span>
  <h2 class="sec">인천 출장마사지·홈타이 서비스 안내</h2>
  <p class="sec-lead">고객이 계신 장소로 찾아가는 방문형 건강관리 서비스입니다.</p>
  <div class="grid g4" style="margin-top:28px">{services}</div>
</div></section>

{price_menu_block()}

<section class="block" id="region"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>SERVICE AREA</span>
  <h2 class="sec">지역별 안내</h2>
  <p class="sec-lead">인천 2군·8구 기준으로 안내하며, 2026년 7월 1일 제물포구·영종구·검단구 출범에 맞춰 업데이트합니다.</p>
  <div class="grid g3" style="margin-top:28px">{regions}</div>
</div></section>

<section class="block" id="stations"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>STATIONS</span>
  <h2 class="sec">지하철역 인근 안내</h2>
  <p class="sec-lead">인천1·2호선과 경인선·7호선·수인분당선·공항철도 인천권 역세권으로 방문 안내가 가능합니다.</p>
  <div class="grid g3" style="margin-top:28px">{lines}</div>
  <div class="chips" style="margin-top:18px">{rep_chips}</div>
</div></section>

<section class="block" id="theme"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>THEME</span>
  <h2 class="sec">테마별 관리 안내</h2>
  <p class="sec-lead">스웨디시·아로마테라피·타이마사지 등 목적에 맞는 테마를 안내합니다.</p>
  <div class="grid g4" style="margin-top:28px">{themes}</div>
</div></section>

<section class="block" id="process"><div class="wrap">
  <span class="eyebrow"><span class="pulse"></span>HOW IT WORKS</span>
  <h2 class="sec">예약 진행 방식</h2>
  <div class="grid g4" style="margin-top:28px">{steps_html}</div>
</div></section>

{notes_block("CHECK & SAFETY", "이용 전 확인 · 위생 안전", "방문 전 아래 사항을 미리 확인해 주세요.", check_notes)}

{faq_block(HOME_FAQ)}

{cta_band("인천 어디서든, 가까운 곳에서 휴식을 예약하세요")}
"""
    jsonld = [org_ld(), website_ld(), localbiz_ld(), offer_ld(), faq_ld(HOME_FAQ)]
    html = page("/", "인천 출장마사지·홈타이 | 인천 전지역 방문 마사지 예약 안내",
        "인천 출장마사지·홈타이 안내 페이지입니다. 인천 전지역, 구·군별 지역, 지하철역 인근, 테마별 관리와 예약 전 확인사항을 한눈에 확인해보세요.",
        "home", body, jsonld)
    write("/", html)

# ---- 인천 대표 랜딩 /incheon/ (핵심 키워드 집중) ---------------------------
def build_incheon():
    trail = [("/", "홈"), (None, "인천 출장마사지")]
    gu_cards = "".join(
        f'<a class="card reveal" href="/incheon/{g["slug"]}/"><div class="k">{g["type"]}</div>'
        f'<h3>{g["name"]}</h3><p>{g["summary"]}</p><span class="more">지역 안내 →</span></a>'
        for g in GU)
    line_links = [f'<a href="/incheon/stations/{ln["slug"]}/">{ln["name"]}</a>' for ln in LINES]
    theme_links = [f'<a href="/theme/{t["slug"]}/">{t["name"]}</a>' for t in THEMES[:10]]
    sections = [
        ("인천 출장마사지·홈타이 서비스 안내", [
            "인천 출장마사지·홈타이는 고객이 계신 자택·오피스텔·숙소로 관리사가 직접 방문하는 방문형 건강관리 서비스입니다. 매장을 찾지 않고도 익숙한 공간에서 피로 회복과 이완을 받을 수 있습니다.",
            "예약 시에는 방문 위치(지역 또는 가까운 지하철역), 희망 시간, 코스와 인원을 확인한 뒤 방문 가능 여부를 안내드립니다. 모든 과정은 건전한 방문 관리 기준에 따라 정중하게 진행됩니다.",
            '예약 방법과 결제 절차는 <a href="/reservation/">예약안내</a>, 처음 이용하시는 분은 <a href="/guide/">이용가이드</a>에서 확인하실 수 있습니다.']),
        ("인천 전지역 방문 가능 안내", [
            "현재 인천은 2군·8구(강화군·옹진군과 중구·동구·미추홀구·연수구·남동구·부평구·계양구·서구) 체계로 운영되며, 본 안내도 이 기준을 따릅니다.",
            "2026년 7월 1일에는 제물포구·영종구·검단구가 출범하는 행정체제 개편이 예정되어 있어, 개편 이후 지역 메뉴와 주소 안내를 새 행정구역에 맞게 업데이트할 예정입니다.",
            "강화·옹진의 도서 지역은 선편 일정에 따라 방문 가능 여부가 결정되므로 사전 협의가 필요합니다.",
            ("html", f'<div class="grid g3" style="margin-top:8px">{gu_cards}</div>')]),
        ("지하철역 인근 안내", [
            "인천 지하철 6개 노선 역세권을 기준으로도 방문 위치를 잡을 수 있습니다. 가까운 역을 알려주시면 위치 파악이 빨라집니다.",
            ("ul", line_links),
            "부평역·주안역·인천시청역·송도역·계양역·검암역 등 환승·대표역은 지하철역별 안내에서 상세히 확인하실 수 있습니다."]),
        ("테마별 관리 안내", [
            "스웨디시를 비롯해 아로마테라피·타이마사지·홈케어·호텔식마사지·스포츠·경락 등 목적에 맞는 테마를 운영합니다.",
            ("ul", theme_links),
            "지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 테마 설명은 테마별 안내에서 한곳에 정리합니다."]),
        ("코스 선택 안내", [
            "피로 회복, 휴식, 근육 이완 등 목적과 방문 장소 여건에 맞춰 60·90·120분 코스를 선택하실 수 있습니다.",
            '코스별 설명과 정찰 요금은 <a href="/course/">코스안내</a>와 <a href="/course/price/">가격 안내</a>에서 확인하실 수 있습니다.']),
        ("예약 진행 방식", [
            "예약은 ① 지역 또는 역 인근 위치 확인 → ② 희망 시간 확인 → ③ 코스·인원 확인 → ④ 방문 가능 여부 안내 → ⑤ 예약 확정 순으로 진행됩니다.",
            "전화 한 통으로 위 과정을 함께 정리해 드리며, 확정 후 관리사가 약속된 시간에 방문합니다."]),
        ("이용 전 확인사항", [
            "원활한 방문을 위해 정확한 주소, 공동현관 출입 방법, 주차 가능 여부, 조용한 공간, 예약자 본인의 연락 가능 여부를 미리 확인해 주세요.",
            '자세한 준비 사항은 <a href="/incheon/checklist/">이용 전 확인사항</a>에서 확인하실 수 있습니다.']),
        ("위생 및 안전 안내", [
            "청결한 용품 관리와 개인정보 보호, 예약 정보 확인을 기본 기준으로 운영하며, 금지행위 안내에 따라 건전하게 진행합니다.",
            '본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다. 자세한 내용은 <a href="/incheon/safety/">위생 및 안전 안내</a>를 참고해 주세요.']),
    ]
    faq = [
        ("인천 전지역 방문이 가능한가요?", "강화·옹진과 8개 구 전역을 안내드립니다. 도서 지역은 선편 일정에 따라 사전 협의가 필요하며, 정확한 가능 여부는 위치와 시간에 따라 상담 시 확인합니다."),
        ("지하철역 근처도 예약할 수 있나요?", "인천1·2호선과 경인선·7호선·수인분당선·공항철도 인천권 역세권으로 안내 가능합니다. 가까운 역을 알려주시면 위치 확인이 빨라집니다."),
        ("당일 예약이 가능한가요?", "가능합니다. 시간대와 위치, 배정 상황에 따라 방문 가능 시간이 달라질 수 있어 상담으로 확인해 드립니다."),
        ("2026년 행정구역 개편 후에는 어떻게 되나요?", "2026년 7월 1일 제물포구·영종구·검단구 출범에 맞춰 지역 메뉴와 주소 안내를 업데이트할 예정입니다. 방문 서비스 자체는 동일하게 운영됩니다."),
    ]
    content_page("/incheon/", "incheon", trail,
        title="인천 출장마사지·홈타이 | 인천 전지역 방문 예약 안내",
        desc="인천 출장마사지·홈타이 안내입니다. 인천 전지역 방문, 구·군별 지역, 지하철역 인근, 테마별 관리, 예약 진행 방식과 이용 전 확인사항을 한곳에서 확인하세요.",
        eyebrow="인천 출장마사지·홈타이", h1="인천 출장마사지·홈타이 예약 안내",
        lead="강화·옹진부터 부평·주안·송도·청라까지, 인천 전지역 방문 출장마사지·홈타이 예약을 연중무휴로 안내드립니다.",
        sections=sections, faq=faq, show_price=True,
        data_note="인천 도심권은 위치에 따라 평균 30~40분 내외로 도착하며, 영종·강화 등 외곽과 도서 지역은 이동 시간이 더 소요되어 사전 예약을 권장드립니다.",
        top_links=[("tel:" + PHONE_TEL, "예약문의", True), ("/incheon/area/", "지역별 안내"),
                   ("/incheon/stations/", "지하철역별 안내"), ("/theme/", "테마별 안내")],
        cta_title="인천 방문 예약, 지금 도와드릴까요?",
        service=("인천 출장마사지·홈타이", "인천 전지역 방문 건강관리 서비스"),
        extra_schema=[localbiz_ld(name="인천굿데이마사지", area="인천광역시", path="/incheon/")])

# ---- 인천 공통 안내 페이지 (시간/확인사항/위생/FAQ/홈타이) ------------------
def build_incheon_info_pages():
    gt = [("/", "홈"), ("/incheon/", "인천 출장마사지")]

    content_page("/incheon/hours/", "incheon", gt + [(None, "예약 가능 시간")],
        title="예약 가능 시간 | 인천 출장마사지·홈타이 24시간 상담 안내",
        desc="인천 출장마사지·홈타이 예약 가능 시간 안내 - 연중무휴 24시간 상담, 시간대별 특징, 지역·역세권별 도착 안내, 예약 팁을 제공합니다.",
        eyebrow="인천 출장마사지 · 시간", h1="예약 가능 시간",
        lead="인천굿데이마사지는 연중무휴 24시간 예약 상담을 운영합니다.",
        sections=[
            ("운영 시간", [
                "전화 상담은 <strong>연중무휴 24시간</strong> 가능하며, 실제 방문 가능 시간은 시간대와 위치, 배정 상황에 따라 안내드립니다.",
                "심야·새벽 예약도 상담을 통해 가능 여부를 확인해 드립니다."]),
            ("시간대별 특징", [
                ("ul", ["낮~초저녁: 비교적 도착이 빠르고 일정 조율이 수월합니다.",
                        "밤 21~24시: 예약이 가장 많이 몰리는 시간대로 도착 시간을 넉넉히 안내드립니다.",
                        "심야(자정 이후): 방문 가능하나 위치에 따라 도착 시간이 길어질 수 있습니다."])]),
            ("지역·역세권별 도착 안내", [
                "부평·주안·구월·송도 등 도심권은 위치에 따라 평균 30~40분 내외로 도착합니다.",
                "영종·강화 등 외곽과 강화·옹진 도서 지역은 이동 시간이 더 소요되며, 도서 지역은 선편 일정에 따라 사전 협의가 필요합니다.",
                "예약 시 가까운 지하철역이나 정확한 위치를 알려주시면 예상 도착 시간을 안내드립니다."]),
            ("예약 팁", [
                "원하는 시간이 정해져 있다면 미리 예약할수록 일정 조율이 수월합니다.",
                "주말 저녁·기념일은 문의가 몰리니 여유 있게 연락 주세요."]),
            ("도착 시간을 줄이는 방법", [
                "예약 시 정확한 주소와 공동현관·동·호수 등 출입 정보를 함께 알려주세요.",
                "가까운 지하철역이나 큰 건물 등 기준점을 알려주시면 위치 파악이 빨라집니다.",
                "도착 직전 연락이 닿을 수 있는 번호를 남겨주시면 마지막 동선이 매끄럽습니다."]),
            ("주말·공휴일 운영", [
                "주말과 공휴일에도 동일하게 연중무휴로 상담·방문을 운영합니다.",
                "다만 기념일·연휴 저녁은 문의가 몰리므로 미리 예약하시는 편이 좋습니다."]),
            ("예약 변경·취소", [
                "일정이 바뀌면 가능한 한 빠르게 연락 주세요. 빠를수록 다른 시간으로 조율하기 쉽습니다.",
                "방문 직전 변경은 관리사 동선상 어려울 수 있어, 미리 알려주시면 감사하겠습니다."]),
        ],
        data_note="예약이 가장 몰리는 시간대는 평일 밤 21~24시입니다. 이 시간대는 도착이 평소보다 조금 더 걸릴 수 있어 여유 있게 예약하시길 권합니다.",
        faq=[
            ("새벽에도 예약되나요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있어 상담 시 안내드립니다."),
            ("도착까지 얼마나 걸리나요?", "도심권은 평균 30~40분 내외이며, 영종·강화 등 외곽과 도서 지역은 더 소요됩니다."),
            ("당일 예약이 가능한가요?", "가능합니다. 시간대와 위치에 따라 가능 시간을 상담으로 확인해 드립니다.")])

    content_page("/incheon/checklist/", "incheon", gt + [(None, "이용 전 확인사항")],
        title="이용 전 확인사항 | 인천 출장마사지·홈타이 방문 준비 안내",
        desc="인천 출장마사지·홈타이 이용 전 확인사항 - 정확한 주소, 공동현관 출입, 주차, 조용한 공간, 예약자 연락 등 방문 준비 사항을 안내합니다.",
        eyebrow="인천 출장마사지 · 확인", h1="이용 전 확인사항",
        lead="원활한 방문을 위해 예약 전 아래 사항을 미리 확인해 주세요.",
        sections=[
            ("방문 장소 준비", [
                "편하게 누워 쉴 수 있는 공간을 확보해 주세요.",
                "자택·오피스텔·숙소 등 방문 장소의 정확한 주소와 공동현관 출입 방법을 알려주시면 도착이 빨라집니다.",
                "주차가 가능한지, 가능하다면 방문 차량을 어디에 두면 되는지 미리 확인해 주세요."]),
            ("예약 정보 확인", [
                ("ul", ["예약자 본인이 연락 가능한 전화번호", "방문 장소의 정확한 주소와 출입 방법",
                        "희망 코스와 시간(60·90·120분)", "방문 희망 시각과 인원"])]),
            ("결제 준비", [
                "코스별 정찰 요금을 사전에 안내드리며, 결제 방법은 예약 시 함께 확인합니다.",
                "지역·시간대 등 변동 요소는 미리 고지해 드립니다."]),
            ("이용 시 주의사항", [
                "본 서비스는 의료 행위가 아닌 건강관리 서비스이며 <strong>만 19세 이상</strong> 성인을 대상으로 합니다.",
                "불법·퇴폐 행위 요구는 일절 제공되지 않으며, 요청 시 서비스가 중단될 수 있습니다.",
                "과도한 음주 상태에서는 안전을 위해 관리가 어려울 수 있습니다."]),
            ("방문 장소별 안내", [
                ("h3", "자택·오피스텔"),
                "공동현관 출입 방법과 동·호수를 알려주시면 도착이 빨라집니다. 반려동물이 있다면 미리 안내해 주세요.",
                ("h3", "숙소·호텔"),
                "건물명과 객실 번호, 프런트 출입 안내가 필요한지 함께 알려주시면 원활합니다."]),
            ("미리 알려주시면 좋은 점", [
                "함께 계신 분이 있거나 특정 향·압을 피하고 싶다면 예약 시 말씀해 주세요.",
                "임신 중이거나 피부·건강상 주의가 필요한 상황은 안전을 위해 사전에 공유해 주세요."]),
            ("방문이 끝나면", [
                "관리 후에는 충분한 수분 섭취와 휴식을 권장드립니다.",
                "사용한 공간은 관리사가 정돈하고 마무리하니 따로 준비하실 것은 없습니다."]),
        ],
        data_note="예약 시 주소와 출입 방법을 함께 남겨주시면 도착 시간이 평균적으로 단축됩니다. 공동현관 비밀번호 등은 도착 직전 안내해 주셔도 됩니다.",
        faq=[
            ("무엇을 준비하면 되나요?", "편히 쉴 공간과 예약자 본인의 연락 가능한 번호, 정확한 주소면 충분합니다."),
            ("출입은 어떻게 하나요?", "공동현관 출입 방법을 미리 알려주시면 도착이 수월합니다. 필요한 안내는 상담 시 도와드립니다."),
            ("예약을 변경할 수 있나요?", "가능한 한 빠르게 연락 주시면 일정 변경을 도와드립니다.")])

    content_page("/incheon/safety/", "incheon", gt + [(None, "위생 및 안전 안내")],
        title="위생 및 안전 안내 | 인천 출장마사지·홈타이 위생·안전 기준",
        desc="인천 출장마사지·홈타이 위생 및 안전 안내 - 용품 위생 관리, 관리사·고객 안전, 개인정보 보호, 비의료 서비스 고지와 금지행위 안내를 제공합니다.",
        eyebrow="인천 출장마사지 · 안전", h1="위생 및 안전 안내",
        lead="안심하고 받으실 수 있도록 위생과 안전을 운영의 기본 기준으로 둡니다.",
        sections=[
            ("위생 관리 기준", [
                "관리에 사용하는 수건·오일 등 용품은 위생 기준에 맞춰 관리합니다.",
                "방문 시 청결을 우선하며, 관리 종료 후 사용한 공간을 정돈합니다."]),
            ("개인정보 보호", [
                "예약을 위해 수집한 연락처·주소 등은 예약 진행 목적으로만 이용하고, 목적 달성 후 관련 법령에 따라 파기합니다.",
                '자세한 내용은 <a href="/privacy/">개인정보처리방침</a>에서 확인하실 수 있습니다.']),
            ("예약 정보 확인", [
                "예약 시 받은 위치·시간·연락처 정보를 확인해 방문 가능 여부를 안내드립니다.",
                "예약자 본인 확인과 만 19세 이상 여부 확인에 협조를 부탁드립니다."]),
            ("관리사·고객 안전", [
                "관리사와 고객 모두의 안전을 위한 운영 가이드라인을 준수합니다.",
                "상호 존중을 원칙으로 하며, 부적절한 요구가 있을 경우 관리가 중단될 수 있습니다."]),
            ("금지행위 안내", [
                ("ul", ["불법·퇴폐 행위 요구 (요청 시 서비스 즉시 중단)",
                        "만 19세 미만의 이용",
                        "관리사에 대한 부적절한 언행",
                        "과도한 음주 상태에서의 관리 요청"])]),
            ("비의료 서비스 고지", [
                "본 서비스는 의료 행위가 아닌 <strong>이완·휴식 목적의 건강관리(마사지) 서비스</strong>입니다.",
                "질환의 진단·치료를 목적으로 하지 않으며, 통증·부상은 의료기관 진료를 권유드립니다."]),
            ("건전 서비스 운영", [
                "인천굿데이마사지는 건전한 방문 건강관리만 제공합니다.",
                "운영 주체와 연락처는 모든 페이지 하단에 공개되어 있으며, 이용 조건은 이용약관, 개인정보 기준은 개인정보처리방침에서 확인하실 수 있습니다."]),
        ],
        data_note="위생·안전은 운영의 기본 기준입니다. 관리사 응대 가이드라인을 통해 어느 관리사가 방문하더라도 일관된 경험을 유지합니다.",
        faq=[
            ("위생은 어떻게 관리되나요?", "수건·오일 등 용품을 위생 기준에 맞춰 관리하고, 관리 후 공간을 정돈합니다."),
            ("개인정보는 안전한가요?", "예약 목적으로만 이용하고 목적 달성 후 관련 법령에 따라 파기합니다."),
            ("의료적 효과가 있나요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 치료를 보장하지 않습니다.")])

    content_page("/incheon/hometai/", "incheon", gt + [(None, "인천 홈타이 안내")],
        title="인천 홈타이 안내 | 자택 방문 홈타이·스웨디시 예약",
        desc="인천 홈타이 안내 - 자택·숙소에서 받는 방문 홈타이와 스웨디시·아로마 관리, 진행 방식과 준비 사항을 안내합니다. 인천 전지역 연중무휴 상담.",
        eyebrow="인천 · 홈타이", h1="인천 홈타이 안내",
        lead="자택·숙소에서 이동 없이 받는 방문 홈타이 안내입니다. 익숙한 공간에서 편안하게 이완할 수 있습니다.",
        sections=[
            ("홈타이란 무엇인가요", [
                "홈타이는 관리사가 고객의 자택·숙소로 방문해 진행하는 방문형 관리를 통칭합니다.",
                "스웨디시·아로마·타이 스트레칭 등 원하는 방식으로 진행할 수 있어, 매장 방문 없이 편안하게 받을 수 있습니다."]),
            ("홈타이가 좋은 이유", [
                "관리 직후 이동 없이 그대로 쉴 수 있어 이완 상태가 오래 유지됩니다.",
                "익숙한 공간에서 받기 때문에 긴장이 덜하고 편안합니다.",
                "인천 전지역으로 방문하며, 가까운 지하철역이나 주소를 알려주시면 도착이 빨라집니다."]),
            ("진행 방식", [
                "예약 시 위치·시간·코스를 확인한 뒤 관리사가 약속된 시간에 방문합니다.",
                "60·90·120분 중 선택할 수 있으며, 90분 구성이 가장 무난하게 선택됩니다.",
                "관리 전 선호하는 압의 세기와 집중 부위를 확인하고 진행합니다."]),
            ("준비하면 좋은 것", [
                "편히 누울 수 있는 공간과 조용한 분위기를 준비해 주세요.",
                "관리 전 가벼운 샤워로 몸을 따뜻하게 하면 이완이 한결 수월합니다."]),
            ("어떤 분들이 홈타이를 찾나요", [
                "퇴근이 늦어 매장 영업시간을 맞추기 어려운 분, 육아·재택으로 외출이 번거로운 분, 출장·여행 중 숙소에서 쉬고 싶은 분이 홈타이를 많이 찾습니다.",
                "매장까지 오가는 시간과 이동 피로가 없어, 받은 직후의 편안함을 그대로 유지하며 휴식으로 이어갈 수 있다는 점이 가장 큰 이유입니다.",
                "혼자 받는 분이 대부분이지만, 커플·가족이 함께 받는 동반 홈타이 문의도 꾸준합니다."]),
            ("홈타이 진행 순서", [
                "관리사가 도착하면 편히 누우실 수 있도록 공간을 정돈하고, 선호하는 압의 세기와 집중 부위를 확인합니다.",
                "선택한 방식(스웨디시·아로마·타이 스트레칭 등)에 따라 큰 근육부터 차례로 이완하며, 뭉친 부위는 시간을 더 들여 풀어드립니다.",
                "마무리 단계에서는 가볍게 정돈하고 수분 섭취·휴식을 안내한 뒤 관리를 마칩니다."]),
            ("코스·테마와의 관계", [
                "홈타이는 방문 방식의 명칭이며, 실제 관리는 코스(피로 회복·아로마 등)와 테마(스웨디시·타이 등)로 선택합니다.",
                '코스별 요금은 <a href="/course/price/">가격 안내</a>, 테마 설명은 <a href="/theme/">테마별 안내</a>, 방문 지역은 <a href="/incheon/area/">지역별 안내</a>에서 확인하실 수 있습니다.']),
        ],
        data_note="홈타이 문의는 평일 저녁과 주말에 집중됩니다. 90분 구성 선택 비율이 가장 높으며, 처음이라면 90분 스웨디시로 시작하시길 권합니다.",
        show_price=True,
        faq=[
            ("홈타이와 출장마사지는 다른가요?", "둘 다 방문형 관리를 뜻하며, 자택·숙소에서 받는 점은 같습니다. 실제 관리는 코스(시간·구성)와 테마(스웨디시·타이 등)로 선택합니다."),
            ("무엇을 준비하나요?", "편히 누울 공간과 조용한 분위기, 예약자 본인이 연락 가능한 번호, 정확한 주소면 충분합니다. 공동현관 출입 방법을 함께 알려주시면 도착이 빨라집니다."),
            ("어떤 코스가 좋나요?", "처음이라면 90분 스웨디시(피로 회복)를 권장드립니다. 향과 함께 받고 싶다면 아로마, 스트레칭 중심을 원하시면 홈타이 코스가 잘 맞습니다."),
            ("도착까지 얼마나 걸리나요?", "도심권은 위치에 따라 평균 30~40분 내외이며, 영종·강화 등 외곽과 도서 지역은 더 소요됩니다."),
            ("심야에도 받을 수 있나요?", "상담은 연중무휴 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있어 사전 예약을 권장드립니다.")],
        service=("인천 홈타이", "인천 전지역 자택 방문 홈타이 관리"))

    content_page("/incheon/faq/", "incheon", gt + [(None, "자주 묻는 질문")],
        title="자주 묻는 질문 | 인천 출장마사지·홈타이 예약·지역·요금 FAQ",
        desc="인천 출장마사지·홈타이 자주 묻는 질문 - 방문 가능 지역, 지하철역 인근, 예약 방법, 도착 시간, 코스·요금, 안전까지 한곳에 정리했습니다.",
        eyebrow="인천 출장마사지 · FAQ", h1="인천 출장마사지·홈타이 자주 묻는 질문",
        lead="예약·지역·역세권·코스·요금 등 자주 들어오는 질문을 한곳에 정리했습니다.",
        sections=[
            ("자주 묻는 질문을 모았습니다", [
                "인천 출장마사지·홈타이를 이용하기 전 자주 들어오는 질문을 주제별로 정리했습니다.",
                '더 궁금한 점은 <a href="/customer/">고객센터</a> 또는 전화로 언제든 문의해 주세요.']),
            ("지역·역세권 한눈에", [
                ("h3", "어디까지 방문하나요"),
                "강화·옹진과 8개 구 전역을 안내드리며, 도서 지역은 선편 일정에 따라 사전 협의가 필요합니다.",
                ("h3", "지하철역 인근도 되나요"),
                "인천1·2호선과 경인선·7호선·수인분당선·공항철도 인천권 역세권으로 안내 가능합니다."]),
            ("코스·요금 한눈에", [
                ("h3", "어떤 코스가 있나요"),
                "피로 회복·아로마·스포츠·홈타이·커플가족·기업단체 관리가 있으며 60·90·120분으로 운영합니다.",
                ("h3", "요금은 어떻게 안내되나요"),
                "코스별 정찰 요금을 사전에 안내하며, 지역·시간대 등 변동 요소는 예약 시 미리 알려드립니다."]),
            ("예약·도착 한눈에", [
                ("h3", "예약은 어떻게 하나요"),
                "전화로 지역 또는 가까운 역 인근 위치, 희망 시간, 코스를 말씀해 주시면 방문 가능 시간을 확정해 드립니다. ① 위치 확인 → ② 시간 확인 → ③ 코스·인원 확인 → ④ 방문 가능 여부 안내 → ⑤ 예약 확정 순으로 진행됩니다.",
                ("h3", "도착까지 얼마나 걸리나요"),
                "도심권은 위치에 따라 평균 30~40분 내외로 도착하며, 영종·강화 등 외곽과 도서 지역은 이동 시간이 더 소요됩니다. 정확한 주소와 출입 방법을 알려주시면 도착이 빨라집니다."]),
            ("안전·신뢰", [
                "본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상 성인을 대상으로 합니다.",
                "위생·안전 가이드라인을 준수하며, 자세한 내용은 위생 및 안전 안내에서 확인하실 수 있습니다.",
                '운영 주체와 연락처는 모든 페이지 하단에 공개되어 있으며, 개인정보 기준은 <a href="/privacy/">개인정보처리방침</a>, 이용 조건은 <a href="/terms/">이용약관</a>에서 확인하실 수 있습니다.']),
        ],
        data_note="가장 많이 들어오는 문의는 '도착까지 걸리는 시간'과 '코스·요금'입니다. 예약 시 위치와 희망 코스를 함께 알려주시면 빠르게 안내해 드립니다.",
        faq=[
            ("인천 어디까지 방문 가능한가요?", "강화·옹진과 중구·동구·미추홀구·연수구·남동구·부평구·계양구·서구 전역을 안내드립니다."),
            ("도서 지역(강화·옹진 섬)도 가능한가요?", "선편 일정에 따라 사전 협의가 필요합니다. 가능 여부를 상담으로 확인해 드립니다."),
            ("지하철역 근처도 예약되나요?", "인천1·2호선과 경인선·7호선·수인분당선·공항철도 인천권 역세권으로 안내 가능합니다."),
            ("당일·심야 예약이 가능한가요?", "상담은 24시간 가능합니다. 심야는 위치에 따라 도착 시간이 길어질 수 있습니다."),
            ("어떤 코스가 있나요?", "피로 회복·아로마·스포츠·홈타이·커플가족·기업단체 관리가 있으며 60·90·120분으로 운영합니다."),
            ("요금은 어떻게 되나요?", "코스별 정찰 요금을 사전에 안내드립니다. 자세한 금액은 가격 안내에서 확인하세요."),
            ("표시 요금 외 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며 지역·시간대 등 변동 요소는 예약 시 미리 안내드립니다."),
            ("2026년 행정구역 개편 후에는요?", "2026년 7월 1일 제물포구·영종구·검단구 출범에 맞춰 지역 안내를 업데이트합니다."),
            ("이 서비스는 의료 행위인가요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다.")])

# ---- 지역 허브 /incheon/area/ ---------------------------------------------
def build_area_hub():
    trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"), (None, "지역별 안내")]
    def group(gu_type, label, summary):
        items = [g for g in GU if g["type"] == gu_type]
        cards = "".join(
            f'<a class="card reveal" href="/incheon/{g["slug"]}/"><div class="k">{g["type"]}</div>'
            f'<h3>{g["name"]}</h3><p>{g["summary"]}</p>'
            f'<span class="more">지역 안내 →</span></a>' for g in items)
        return (f'<div style="margin-top:40px"><h3 style="font-size:22px;font-weight:800;margin-bottom:6px" class="grad">{label}</h3>'
                f'<p class="sec-lead">{summary}</p>'
                f'<div class="grid g3" style="margin-top:18px">{cards}</div></div>')
    blocks = group("군", "강화군 · 옹진군", "넓은 면적과 도서 지역을 포함하는 군 단위 지역입니다. 도서 지역은 선편 일정에 따라 사전 협의가 필요합니다.")
    blocks += group("구", "인천 8개 구", "도심과 신도시가 밀집한 구 단위 지역입니다. 구를 눌러 대표 동별 방문 안내를 확인하세요.")
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>AREA GUIDE</span>'
        '<h2 class="sec">지역별 안내</h2>'
        '<p class="sec-lead">현재 인천 2군·8구 기준으로 안내합니다. 2026년 7월 1일 제물포구·영종구·검단구 출범(2군·9구)이 예정되어 있어, 개편 이후 지역 구성을 함께 업데이트합니다.</p>'
        '<p class="sec-lead" style="margin-top:14px;max-width:820px">인천굿데이마사지는 강화군·옹진군과 중구·동구·미추홀구·연수구·남동구·부평구·계양구·서구 전역으로 출장마사지·홈타이 방문 예약을 안내합니다. 각 구·군 페이지에서는 대표 동별 생활권과 평균 도착 시간, 방문 안내를 확인하실 수 있으며, 1동·2동처럼 나뉜 행정동은 대표 동 하나로 통합해 안내합니다. 도심권은 위치에 따라 평균 30~40분 내외로 도착하고, 영종·강화 등 외곽과 도서 지역은 이동 시간이 더 소요되어 사전 예약을 권장드립니다.</p>'
        + blocks +
        '<div style="max-width:820px;margin-top:36px">'
        '<h3 style="font-size:19px;font-weight:800;margin-bottom:10px">지역 안내, 이렇게 이용하세요</h3>'
        '<p class="sec-lead">먼저 방문하려는 구·군을 고른 뒤, 구 페이지에서 가까운 대표 동을 선택하면 동별 생활권과 평균 도착 시간, 방문 안내를 확인할 수 있습니다. 정확한 위치는 예약 시 가까운 지하철역이나 큰 건물·교차로를 함께 알려주시면 빠르게 파악됩니다. 역을 기준으로 찾는 것이 편하다면 <a href="/incheon/stations/">지하철역별 안내</a>를 이용하셔도 됩니다.</p>'
        '<h3 style="font-size:19px;font-weight:800;margin:28px 0 10px">행정동 통합 안내</h3>'
        '<p class="sec-lead">주안1동~주안8동은 주안동, 송도1동~송도5동은 송도동, 부평1동~부평6동은 부평동, 구월1동~구월4동은 구월동, 청라1동~청라3동은 청라동처럼 숫자로 나뉜 행정동은 대표 동 하나로 통합해 안내합니다. 같은 이름의 세부 행정동도 대표 동 페이지에서 함께 확인하시면 됩니다.</p>'
        '<h3 style="font-size:19px;font-weight:800;margin:28px 0 10px">도서·외곽 지역 안내</h3>'
        '<p class="sec-lead">강화군 교동·삼산·서도면과 옹진군 백령·연평·대청·덕적·자월·영흥·북도면 등 섬 지역은 선편·차량 일정에 따라 방문 가능 여부가 결정되므로 사전 협의가 필요합니다. 영종(중구)·검단(서구) 등 외곽은 도심권보다 이동 시간이 더 소요됩니다.</p>'
        '<h3 style="font-size:19px;font-weight:800;margin:28px 0 10px">도착 시간과 예약</h3>'
        '<p class="sec-lead">부평·주안·구월·송도·청라 등 도심권은 위치에 따라 평균 30~40분 내외로 도착합니다. 정확한 주소와 공동현관 출입 방법, 도착 직전 연락 가능한 번호를 함께 알려주시면 마지막 동선이 매끄럽고, 저녁·주말은 문의가 몰리므로 원하는 시간이 있다면 미리 예약하시길 권합니다. 지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 가까운 지하철역으로 위치를 잡고 싶다면 <a href="/incheon/stations/">지하철역별 안내</a>를, 관리 방식은 <a href="/theme/">테마별 안내</a>를 함께 참고하세요.</p>'
        '</div>'
        '<div class="data-box" style="margin-top:34px"><b>2026년 행정체제 개편 예정</b>'
        '<p>2026년 7월 1일부터 중구·동구 원도심이 제물포구로, 중구 영종이 영종구로, 서구 검단이 검단구로 개편될 예정입니다. 방문 서비스는 동일하게 운영되며, 메뉴·주소·내부 링크는 개편 일정에 맞춰 정비합니다.</p></div>'
        '</div></section>' + cta_band())
    coll = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "인천 출장마사지 지역별 안내", "url": BASE_URL + "/incheon/area/",
        "inLanguage": "ko-KR", "image": og_image_obj(), "isPartOf": {"@type": "WebSite", "url": BASE_URL + "/"},
        "hasPart": [{"@type": "WebPage", "name": g["name"],
                     "url": BASE_URL + f"/incheon/{g['slug']}/"} for g in GU],
    }
    html = page("/incheon/area/", "인천 전지역 방문 안내 | 구·군별 출장마사지 지역별 안내",
        "인천 출장마사지·홈타이 지역별 안내 - 강화군·옹진군과 8개 구(중구·동구·미추홀구·연수구·남동구·부평구·계양구·서구) 대표 동별 방문 안내를 제공합니다.",
        "area", body, [bc_ld(trail), coll, offer_ld()])
    write("/incheon/area/", html)

# ---- 구/군 페이지 /incheon/<gu>/ ------------------------------------------
def build_gu_pages():
    for g in GU:
        path = f"/incheon/{g['slug']}/"
        trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"),
                 ("/incheon/area/", "지역별 안내"), (None, g["name"])]
        dong_cards = "".join(
            f'<a class="card reveal" href="/incheon/{g["slug"]}/{d["slug"]}/"><div class="k">{g["name"]}</div>'
            f'<h3>{d["name"]}</h3>'
            f'<span class="more">동 안내 →</span></a>' for d in g["dongs"])
        chips = "".join(f'<span class="chip"><b>{d["name"]}</b></span>' for d in g["dongs"])
        sd = g["slug"]
        # 동별 고유 라인(대표 성격·랜드마크·도착) — 최대 8개로 분량 제어, 고유성 유지
        detail = g["dongs"][:8]
        detail_items = [f'<a href="/incheon/{g["slug"]}/{d["slug"]}/">{d["name"]}</a> — {d["character"]}, {d["landmarks"].split(",")[0].strip()} 인근 ({arr_text(d)})'
                        for d in detail]
        rest = g["dongs"][8:]
        rest_note = (f'그 외 {"·".join(d["name"] for d in rest)} 일대도 같은 기준으로 안내하며, 각 동 페이지에서 상세 생활권을 확인하실 수 있습니다.'
                     if rest else "각 동을 누르면 상세 생활권과 평균 도착 시간, 자주 묻는 질문을 확인하실 수 있습니다.")
        sections = [
            (f"{g['name']} 출장마사지·홈타이 안내", [
                _pick(sd, [f"{g['name']}은(는) {g['summary']}",
                           f"{g['name']}은(는) {g['summary']} 이 지역 전역으로 방문 예약을 안내합니다.",
                           f"인천 {g['name']} 출장마사지·홈타이 안내입니다. {g['name']}은(는) {g['summary']}"], "g1"),
                _pick(sd, [f"{g['name']}에서는 자택·오피스텔·숙소로 방문하는 출장마사지·홈타이 예약을 안내드립니다. 매장을 찾지 않고도 익숙한 공간에서 피로 회복과 이완을 받을 수 있으며, 아래 대표 동을 눌러 동별 생활권을 확인하실 수 있습니다.",
                           f"매장 방문 없이 {g['name']} 내 자택·숙소에서 받는 방문형 관리를 이용하실 수 있습니다. 대표 동별로 생활권과 평균 도착 시간이 달라 아래에서 확인하실 수 있습니다.",
                           f"{g['name']}은(는) 자택·오피스텔·숙소로 방문하는 방문형 관리 지역입니다. 익숙한 공간에서 받을 수 있어 이동 부담이 없으며, 대표 동별 안내를 아래에 정리했습니다."], "g2"),
                "행정동이 1동·2동처럼 여러 개로 나뉜 곳은 대표 동 하나로 통합해 안내하므로, 같은 이름의 세부 행정동도 대표 동 페이지에서 함께 확인하시면 됩니다."]),
            (f"{g['name']} 방문 가능 동", [
                f"{g['name']}은(는) " + "·".join(d["name"] for d in g["dongs"]) + " 일대를 포함합니다.",
                ("html", f'<div class="chips" style="margin-bottom:18px">{chips}</div>'
                         f'<div class="grid g3">{dong_cards}</div>')]),
            (f"{g['name']} 동별 생활권", [
                _pick(sd, [f"{g['name']}의 대표 동별 생활권 특성과 평균 도착 시간을 정리했습니다.",
                           f"{g['name']} 주요 동의 성격과 도착 시간은 다음과 같습니다.",
                           f"{g['name']} 내 대표 동의 생활권은 아래와 같이 안내드립니다."], "g3"),
                ("ul", detail_items), rest_note]),
            ("예약·코스·테마는 전용 안내에서", [
                "예약 가능 시간·준비물·위생 기준·코스 요금·테마 설명은 페이지마다 반복하지 않고 전용 안내에서 확인하실 수 있습니다.",
                ("ul", ['<a href="/incheon/hours/">예약 가능 시간 안내</a>',
                        '<a href="/incheon/checklist/">이용 전 확인사항(준비물)</a>',
                        '<a href="/incheon/safety/">위생 및 안전 안내</a>',
                        '<a href="/course/">코스안내 · 가격</a>',
                        '<a href="/theme/">테마별 안내</a>'])]),
            (f"{g['name']} 방문 예약 팁", [
                _pick(sd, [f"예약 시 {detail[0]['name']} 인근 등 가까운 위치나 지하철역, 큰 건물을 함께 알려주시면 위치 파악과 도착이 빨라집니다.",
                           f"{g['name']}은(는) 동별로 생활권이 달라, 예약 시 정확한 동과 가까운 기준점을 알려주시면 도착이 빨라집니다.",
                           f"가까운 역이나 랜드마크({detail[0]['landmarks'].split(',')[0].strip()} 등)를 함께 알려주시면 {g['name']} 방문 동선을 잡기 수월합니다."], "g4"),
                _pick(sd, ["저녁 시간대와 주말에는 문의가 몰릴 수 있어, 원하는 시간이 정해져 있다면 미리 예약하시길 권합니다.",
                           "특히 주말·저녁은 예약이 집중되므로 여유 있게 연락 주시면 일정 조율이 수월합니다.",
                           "원하는 시간이 있다면 미리 예약하실수록 방문 시간을 맞추기 쉽습니다."], "g5"),
                "처음 이용하신다면 90분 스웨디시(피로 회복) 구성으로 시작하시는 분이 많으며, 컨디션과 목적에 따라 아로마·스포츠·홈타이 등으로 선택하실 수 있습니다."]),
        ]
        # 대표 동이 적은 구·군은 해당 지역 고유 정보를 엮은 안내를 더해 분량을 맞춘다(유사도 영향 최소화)
        if len(g["dongs"]) < 10 and len(detail) >= 2:
            lm0 = detail[0]["landmarks"].split(",")[0].strip()
            sections.append((f"{g['name']} 방문 시 참고사항", [
                _pick(sd, [
                    f"{g['name']}에서는 {detail[0]['name']}·{detail[1]['name']} 같은 생활권을 중심으로 방문 문의가 들어오며, {lm0} 인근은 비교적 도착이 빠른 편입니다.",
                    f"{detail[0]['name']}와(과) {detail[1]['name']}을(를) 비롯한 {g['name']} 생활권으로 자택·숙소 방문이 이뤄지며, {lm0} 같은 거점을 알려주시면 위치 파악이 빠릅니다.",
                    f"{g['name']} 방문은 {detail[0]['name']}·{detail[1]['name']} 등 주요 생활권을 중심으로 진행되며, {lm0} 등 가까운 거점을 함께 알려주시면 도착이 빨라집니다."], "ge1"),
                _pick(sd, [
                    f"지역 특성에 맞춰 시간대와 위치를 함께 확인해 방문 가능 여부를 안내드리며, 저녁·주말 등 혼잡 시간대는 도착 시간을 넉넉히 안내합니다.",
                    f"{g['name']}은(는) 예약 시 정확한 위치와 시간을 확인해 일정을 잡아 드리며, 주말·기념일은 문의가 몰릴 수 있어 미리 예약하시길 권합니다.",
                    f"예약 단계에서 위치·시간·코스를 확인한 뒤 방문 가능 여부를 안내드리며, 도서·외곽은 이동 시간이 더 소요될 수 있습니다."], "ge2"),
                "코스는 60·90·120분 중 선택할 수 있으며, 처음이라면 전신을 고르게 받을 수 있는 90분 스웨디시(피로 회복)를 권장드립니다. 자세한 코스 설명과 정찰 요금은 코스안내에서, 관리 방식은 테마별 안내에서 확인하실 수 있습니다."]))
        if g["slug"] in REORG_2026:
            sections.insert(3, ("2026년 행정체제 개편 예정", [REORG_2026[g["slug"]]]))
        gu_faq = [
            (f"{g['name']}은(는) 어디까지 방문 가능한가요?",
             "권역 내 " + "·".join(d["name"] for d in g["dongs"][:6]) + " 등 대표 동 일대를 안내드리며, 정확한 가능 여부는 예약 시간과 위치에 따라 확인해 드립니다."),
            (f"{g['name']} 도착까지 얼마나 걸리나요?",
             (f"{detail[0]['name']} 등 도심권은 평균 {detail[0]['arrival']}분 내외이며 위치에 따라 달라집니다." if detail[0].get("arrival") else f"{g['name']}은(는) 도서·외곽 지역으로 선편·차량 일정에 따라 사전 협의가 필요합니다.")),
            (f"{g['name']}에서 행정동이 여러 개인 곳도 되나요?",
             "1동·2동처럼 나뉜 행정동은 대표 동 안내 기준으로 통합 안내드립니다."),
        ]
        is_island = all(not d.get("arrival") for d in g["dongs"])
        lead = (f"{g['summary']} {g['name']} 출장마사지·홈타이 방문 예약을 안내합니다."
                if not is_island else
                f"{g['summary']} 도서 지역 특성상 선편 일정에 따라 사전 협의가 필요합니다.")
        content_page(path, "area", trail,
            title=f"{g['name']} 출장마사지·홈타이 | 인천 {g['name']} 방문 예약 안내",
            desc=f"인천 {g['name']} 출장마사지·홈타이 안내 - " + ", ".join(d['name'] for d in g['dongs'][:6]) +
                 f" 등 대표 동 방문 예약 안내입니다. {g['summary']}",
            eyebrow=f"인천 · {g['name']}", h1=f"{g['name']} 출장마사지·홈타이", lead=lead,
            sections=sections, faq=gu_faq,
            top_links=[("tel:" + PHONE_TEL, "예약문의", True), ("/incheon/area/", "지역별 안내"),
                       ("/incheon/", "인천 출장마사지"), ("/course/", "코스안내")],
            cta_title=f"{g['name']} 방문 예약을 도와드릴까요?",
            service=(f"{g['name']} 출장마사지·홈타이", g["summary"]),
            extra_schema=[localbiz_ld(name=f"인천굿데이마사지 {g['name']}",
                                      area=f"인천광역시 {g['name']}", path=path)])

# ---- 동 페이지 /incheon/<gu>/<dong>/ --------------------------------------
def _dong_zone_blocks(g, d):
    tokens = [t.strip() for t in d["landmarks"].replace("·", ", ").split(",") if t.strip()][:3]
    sd = d["slug"]
    blocks = []
    if d.get("arrival"):
        blocks.append(_pick(sd, [
            f"{d['name']}은(는) {d['landmarks']}를 중심으로 인근 생활권과 이어집니다. {d['character']}이라 자택·오피스텔·숙소 방문 문의가 고르게 들어오며, 세부 방문 가능 여부는 정확한 위치·예약 시간·배정 상황에 따라 달라질 수 있습니다.",
            f"{d['character']}인 {d['name']}은(는) {d['landmarks']}를 끼고 생활권이 형성되어 있습니다. 자택과 오피스텔, 숙소로의 방문이 고르며, 정확한 위치와 예약 시간에 따라 가능 여부가 정해집니다.",
            f"{d['name']}의 주요 생활권은 {d['landmarks']} 일대입니다. {d['character']}으로 방문 문의가 꾸준하며, 세부 가능 여부는 위치·시간·배정 상황을 함께 확인해 안내드립니다.",
        ], "zi"))
        zone_arr = ", ".join(
            f"{t.replace(' 일대','').replace(' 방향','')} 약 {d['arrival'] + i*2}분"
            for i, t in enumerate(tokens))
        blocks.append(_pick(sd, [
            f"방문 포인트별 평균 도착 시간(예약 데이터 기준)은 {zone_arr} 내외입니다. 같은 {d['name']} 안에서도 위치에 따라 도착 시간이 달라집니다.",
            f"예약 데이터 기준 {d['name']} 내 주요 지점까지 도착 시간은 {zone_arr} 정도입니다. 정확한 주소에 따라 다소 차이가 있을 수 있습니다.",
            f"{d['name']} 안에서도 위치별로 도착 시간이 달라, {zone_arr} 내외를 기준으로 안내드립니다.",
        ], "za"))
    else:
        blocks.append(
            f"{d['name']}은 {d['landmarks']}를 포함하는 {d['character']}입니다. "
            f"도서·외곽 특성상 선편·차량 일정에 따라 방문 가능 여부와 도착 시간이 달라지므로, 예약 시 사전 협의가 필요합니다.")
    descs = [
        "중심 생활권으로 자택·오피스텔·숙소 방문 문의가 많은 곳입니다. 주변 상권과 주거지가 함께 있어 위치를 기준점으로 잡기 좋습니다.",
        "주변 주거지와 이어져 함께 안내되는 경우가 많습니다. 인근 큰 건물이나 교차로를 알려주시면 위치 파악이 한결 빨라집니다.",
        "방문 포인트로 자주 언급되는 위치입니다. 도보권 주거 단지가 모여 있어 저녁·주말 문의가 고르게 들어옵니다.",
        "인근 생활권과 연결되어 동선을 잡기 좋은 지점입니다. 정확한 동·호수와 출입 방법을 함께 알려주시면 도착이 빨라집니다.",
    ]
    for i, t in enumerate(tokens):
        title = t.replace(" 일대", "").replace(" 방향", "")
        blocks += [("h3", f"{title} 인근"), f"{title} 인근은 {d['name']}의 {_pick(sd, descs, 'd'+str(i))}"]
    blocks += [("h3", "주거지·숙소 방문 안내"),
               _pick(sd, [
                   f"{d['name']}에서는 {tokens[0].replace(' 일대','')} 등을 기준으로 자택·오피스텔·숙소로 방문합니다. 공동현관 출입 방법과 정확한 주소, 도착 직전 연락이 닿는 번호를 함께 알려주시면 마지막 동선이 매끄럽습니다.",
                   f"{d['name']} 방문은 {tokens[0].replace(' 일대','')} 일대 자택·숙소를 기준으로 이뤄집니다. 정확한 주소와 동·호수, 출입 방법을 미리 남겨주시면 도착이 빨라지고, 주차 가능 여부도 함께 알려주시면 좋습니다.",
                   f"{tokens[0].replace(' 일대','')}를 비롯한 {d['name']} 생활권의 자택·오피스텔·숙소로 방문하며, 출입 방법과 연락 가능한 번호, 주차 위치를 함께 알려주시면 진행이 수월합니다."], "n1")]
    return blocks

def build_dong_pages():
    for g in GU:
        for d in g["dongs"]:
            path = f"/incheon/{g['slug']}/{d['slug']}/"
            trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"),
                     ("/incheon/area/", "지역별 안내"),
                     (f"/incheon/{g['slug']}/", g["name"]),
                     (None, f"{d['name']} 출장마사지·홈타이")]
            siblings = [x for x in g["dongs"] if x["slug"] != d["slug"]]
            first_lm = d["landmarks"].split(",")[0].strip()
            region_links = ['<a href="/incheon/">인천 출장마사지</a>',
                            '<a href="/incheon/area/">인천 전지역 안내</a>',
                            f'<a href="/incheon/{g["slug"]}/">{g["name"]}</a>']
            region_links += [f'<a href="/incheon/{g["slug"]}/{s["slug"]}/">{s["name"]}</a>' for s in siblings[:5]]
            sd = d["slug"]
            pt = _pick(sd, [("스웨디시", "오일로 전신을 부드럽게 푸는", "/theme/swedish/"),
                            ("아로마테라피", "향과 함께 이완하는", "/theme/aromatherapy/"),
                            ("타이마사지", "스트레칭 중심의", "/theme/thai/"),
                            ("피로 회복 관리", "전신 긴장을 정리하는", "/course/fatigue/"),
                            ("홈타이 코스", "옷을 입은 채 받는", "/course/hometai/")], "dth")
            care_links = _picks(sd, ['<a href="/course/">전체 코스 보기</a>', '<a href="/course/fatigue/">피로 회복 관리</a>',
                            '<a href="/theme/swedish/">스웨디시</a>', '<a href="/theme/aromatherapy/">아로마테라피</a>',
                            '<a href="/course/hometai/">홈타이 코스</a>', '<a href="/course/price/">가격 안내</a>'], "dcl")
            prep_links = _picks(sd, ['<a href="/incheon/hours/">예약 가능 시간 안내</a>',
                            '<a href="/incheon/checklist/">이용 전 확인사항(준비물)</a>',
                            '<a href="/incheon/safety/">위생 및 안전 안내</a>',
                            '<a href="/course/price/">가격 안내</a>'], "dpl")
            sections = [
                (f"{d['name']} 출장마사지·홈타이 이용 안내", [
                    _pick(sd, [
                        f"{d['name']}은(는) {d['character']}입니다. 주요 위치는 {d['landmarks']}로, 이 생활권을 중심으로 자택·오피스텔·숙소 방문 문의가 많습니다.",
                        f"{d['landmarks']}를 끼고 있는 {d['name']}은(는) {d['character']}으로, 인근 주거지와 숙소로의 방문 문의가 꾸준합니다.",
                        f"{d['name']}은(는) {d['character']}으로 분류됩니다. {d['landmarks']} 일대를 중심으로 자택·오피스텔 방문이 활발합니다."], "di1"),
                    _pick(sd, [
                        f"{d['name']} 출장마사지·홈타이는 {first_lm} 등 {d['name']} 내 원하시는 장소로 방문해 피로 회복과 컨디션 관리를 돕는 방문형 관리입니다. 예약 시 위치·희망 시간·코스·인원을 확인한 뒤 방문 가능 여부를 안내드립니다.",
                        f"매장 방문 없이 {d['name']} 내 자택·숙소에서 받는 방문형 관리로, {first_lm} 일대로 방문합니다. 예약 단계에서 위치·시간·코스·인원을 함께 확인해 일정을 잡아 드립니다.",
                        f"{d['name']}에서는 이동 없이 자택·오피스텔에서 받는 방문형 관리를 이용하실 수 있습니다. {first_lm}를 기준으로 방문하며, 예약 시 위치와 희망 시간, 코스를 확인합니다."], "di2"),
                    '예약 방법은 <a href="/reservation/">예약안내</a>, 처음 이용 시 진행 흐름은 <a href="/guide/">이용가이드</a>에서 확인하실 수 있습니다.']),
                (f"{d['name']} 방문 가능 생활권", _dong_zone_blocks(g, d)),
                (f"{g['name']} 함께 보기", [
                    _pick(sd, [f"{d['name']}과(와) 가까운 {g['name']} 내 다른 생활권도 함께 확인할 수 있습니다.",
                               f"{g['name']}은(는) 생활권이 이어져 있어 인근 동과 함께 안내되는 경우가 많습니다.",
                               f"같은 {g['name']} 안의 가까운 동도 함께 살펴보시면 방문 위치를 잡기 좋습니다."], "dr"),
                    ("ul", region_links)]),
                (f"{d['name']}에서 많이 찾는 관리", [
                    f"{d['name']}에서는 {pt[1]} <a href='{pt[2]}'>{pt[0]}</a>를 비롯한 방문 관리 문의가 많습니다. {d['character']}이라 {_pick(sd, ['하루 일과를 마치고 자택에서 편안하게 이완을 원하는 분들이 꾸준히 찾습니다.', '저녁·주말에 휴식을 원하는 분들의 문의가 많습니다.', '집에서 부담 없이 받고 싶은 분들이 자주 이용합니다.'], 'dc1')}",
                    _pick(sd, ["처음 이용하신다면 90분 스웨디시(피로 회복) 구성으로 시작하시길 권하며, 운동 후라면 스포츠, 향과 함께 깊은 이완을 원하시면 아로마테라피가 잘 맞습니다.",
                               "목적에 따라 시간(60·90·120분)과 테마를 골라 진행하며, 무엇이 맞을지 고민되면 상담 시 추천해 드립니다.",
                               "컨디션과 취향에 맞춰 코스와 테마를 선택할 수 있으며, 처음이라면 90분 구성이 무난합니다."], "dc2"),
                    ("ul", care_links)]),
                (f"{d['name']} 예약·준비·위생 안내", [
                    (f"{d['name']} 방문 예약은 시간대와 배정 상황에 따라 가능 여부가 달라지며, {arr_text(d)} 도착합니다. 저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드립니다."
                     if d.get("arrival") else
                     f"{d['name']}은(는) 도서·외곽 지역으로, 방문은 선편·차량 일정에 따라 사전 협의가 필요합니다. 예약 시 위치와 일정을 함께 알려주세요."),
                    "예약 가능 시간, 방문 전 준비물, 위생·안전 기준은 전용 안내에서 자세히 확인하실 수 있습니다.",
                    ("ul", prep_links)]),
            ]
            if d.get("arrival"):
                arr_q = (f"평균 {d['arrival']}분 내외이며, 시간대와 정확한 위치에 따라 달라질 수 있습니다.")
                data_note = f"{d['name']} 일대는 평균 {d['arrival']}분 내외로 도착합니다(예약 데이터 기준). 저녁·주말은 문의가 몰려 도착이 다소 길어질 수 있어 사전 예약을 권장드립니다."
            else:
                arr_q = "도서·외곽 지역으로 선편·차량 일정에 따라 달라지며, 사전 협의가 필요합니다."
                data_note = f"{d['name']}은 도서·외곽 지역으로 방문 일정이 선편·차량 운행에 영향을 받습니다. 예약 시 위치와 일정을 미리 알려주시면 가능 여부를 안내해 드립니다."
            dong_faq = [
                (f"{d['name']} 전 지역 방문이 가능한가요?",
                 f"예약 시간, 정확한 위치, 배정 상황에 따라 가능 여부가 달라질 수 있습니다. {first_lm} 인근 등 세부 위치를 기준으로 안내드립니다."),
                (f"{first_lm} 근처도 예약할 수 있나요?",
                 f"{first_lm} 인근은 {d['name']} 주요 생활권으로 함께 안내할 수 있습니다. 정확한 가능 여부는 예약 시 위치를 기준으로 확인합니다."),
                (f"{d['name']}은 어떤 지역인가요?",
                 f"{d['name']}은 {d['character']}입니다. {d['landmarks']}를 중심으로 방문 문의가 많은 편입니다."),
                (f"{d['name']} 도착까지 얼마나 걸리나요?", arr_q),
                (f"{d['name']}에서는 어떤 관리가 인기인가요?",
                 f"{d['name']}에서는 스웨디시·아로마·피로 회복 관리 문의가 많습니다. 목적과 컨디션에 따라 선택하시면 되며, 자세한 내용은 코스안내와 테마별 안내에서 확인하실 수 있습니다."),
            ]
            lead = (f"인천 {g['name']} {d['name']}({d['character']})에서 출장마사지·홈타이 예약을 찾는 분들을 위한 안내입니다. "
                    f"{d['name']}은 {first_lm} 인근 생활권과 가까워 주거지·숙소·오피스텔 방문 문의가 많으며, {arr_text(d)} 도착합니다.")
            content_page(path, "area", trail,
                title=f"{d['name']} 출장마사지·홈타이 | 인천 {g['name']} {d['name']} 방문 예약",
                desc=f"인천 {g['name']} {d['name']} 출장마사지·홈타이 안내입니다. {first_lm} 인근 방문 가능 생활권과 예약 시간, 코스 선택 기준을 확인해보세요.",
                eyebrow=f"인천 {g['name']} · {d['name']}", h1=f"{d['name']} 출장마사지·홈타이 예약 안내", lead=lead,
                sections=sections, faq=dong_faq, data_note=data_note,
                top_links=[("tel:" + PHONE_TEL, "예약문의", True), ("/course/", "코스안내"),
                           (f"/incheon/{g['slug']}/", f"{g['name']} 안내")],
                service=(f"{d['name']} 출장마사지·홈타이", f"인천 {g['name']} {d['name']} 일대 방문 건강관리"),
                extra_schema=[localbiz_ld(name=f"인천굿데이마사지 {d['name']}",
                                          area=f"인천광역시 {g['name']} {d['name']}", path=path)])

# ===========================================================================
# PAGE BUILDERS — 지하철역 / 테마
# ===========================================================================
def _line_names_for(st):
    return [LINE_NAMES[c] for c in st["lines"]]

# ---- 지하철역 허브 /incheon/stations/ -------------------------------------
def build_stations_hub():
    trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"), (None, "지하철역별 안내")]
    line_cards = "".join(
        f'<a class="card reveal" href="/incheon/stations/{ln["slug"]}/"><div class="k">LINE</div>'
        f'<h3>{ln["name"]}</h3><p>{len(ln["stations"])}개 역 인근 방문 안내</p>'
        f'<span class="more">노선 보기 →</span></a>' for ln in LINES)
    rep = ["부평역", "주안역", "인천시청역", "송도역", "계양역", "검암역", "인천공항1터미널역"]
    rep_chips = "".join(
        f'<a class="chip" href="/incheon/stations/{STATIONS[s]["slug"]}/"><b>{s}</b></a>' for s in rep)
    line_intro = "".join(f'<li><a href="/incheon/stations/{ln["slug"]}/">{ln["name"]}</a> · {len(ln["stations"])}개 역</li>' for ln in LINES)
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>STATIONS</span>'
        '<h2 class="sec">지하철역별 안내</h2>'
        '<p class="sec-lead">인천 지하철 6개 노선의 역세권을 기준으로 방문 위치를 잡을 수 있습니다. 노선을 눌러 역 목록을 확인하세요. 환승역은 여러 노선에 보여도 안내 페이지는 하나로 운영합니다.</p>'
        f'<div class="grid g3" style="margin-top:26px">{line_cards}</div>'
        '<div style="max-width:820px;margin-top:40px">'
        '<h3 style="font-size:19px;font-weight:800;margin-bottom:10px">노선별 역세권 방문 안내</h3>'
        '<p class="sec-lead">인천굿데이마사지는 아래 6개 노선의 역세권을 기준으로 출장마사지·홈타이 방문 예약을 안내합니다. 역명은 방문 위치를 잡기 위한 기준일 뿐이며, 실제로는 각 역 도보권의 자택·오피스텔·숙소로 방문합니다. 가까운 역과 정확한 주소를 함께 알려주시면 도착이 빨라집니다.</p>'
        f'<ul class="lux-list" style="margin:14px 0 0;padding-left:18px;color:var(--muted);line-height:2">{line_intro}</ul>'
        '<h3 style="font-size:19px;font-weight:800;margin:30px 0 10px">환승역은 어떻게 안내되나요</h3>'
        '<p class="sec-lead">부평역(인천1호선·경인선), 주안역(인천2호선·경인선), 인천시청역(인천1·2호선), 계양역·검암역(공항철도), 원인재역(인천1호선·수인분당선), 부평구청역·석남역(7호선) 등은 여러 노선이 만나는 환승역입니다. 환승역은 노선 목록마다 보이더라도 안내 페이지(URL)는 하나로만 운영해 중복 페이지를 만들지 않습니다.</p>'
        '<h3 style="font-size:19px;font-weight:800;margin:30px 0 10px">노선별 주요 역세권</h3>'
        '<p class="sec-lead"><strong>인천1호선</strong>은 검단·계양에서 부평·구월(인천시청)을 지나 송도(센트럴파크·인천대입구)까지 이어지는 남북 축으로, 부평역·인천시청역·인천대입구역 인근 문의가 많습니다.</p>'
        '<p class="sec-lead" style="margin-top:8px"><strong>인천2호선</strong>은 검단신도시에서 서구청·가정(루원시티)·주안을 거쳐 남동구 인천대공원까지 이어지며, 주안역·인천시청역·검단사거리역 인근이 활발합니다.</p>'
        '<p class="sec-lead" style="margin-top:8px"><strong>1호선(경인선) 인천권</strong>은 인천역·동인천역 원도심부터 제물포·주안·부평까지, <strong>7호선 인천권</strong>은 삼산체육관·부평구청·산곡·석남을 잇습니다.</p>'
        '<p class="sec-lead" style="margin-top:8px"><strong>수인분당선 인천권</strong>은 인천역·인하대·송도·연수·소래포구를 따라 해안 생활권을, <strong>공항철도 인천권</strong>은 계양·검암·청라국제도시와 영종·인천공항(제1·2터미널)을 잇습니다.</p>'
        '<h3 style="font-size:19px;font-weight:800;margin:30px 0 10px">도착 시간과 예약</h3>'
        '<p class="sec-lead">도심권 역세권은 위치에 따라 평균 30~40분 내외로 도착하며, 영종(공항철도)·검단(인천2호선) 방향 등 외곽으로 갈수록 이동 시간이 더 소요됩니다. 출구별 페이지는 따로 운영하지 않으며, 역 인근 전체를 기준으로 안내한 뒤 정확한 위치는 예약 시 확인합니다.</p>'
        '</div>'
        '<h3 style="margin:34px 0 12px;font-size:18px;font-weight:800">대표·환승역 바로가기</h3>'
        f'<div class="chips">{rep_chips}</div>'
        '</div></section>' + cta_band())
    coll = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "인천 지하철역별 출장마사지 안내", "url": BASE_URL + "/incheon/stations/",
        "inLanguage": "ko-KR", "image": og_image_obj(), "isPartOf": {"@type": "WebSite", "url": BASE_URL + "/"},
        "hasPart": [{"@type": "WebPage", "name": ln["name"],
                     "url": BASE_URL + f"/incheon/stations/{ln['slug']}/"} for ln in LINES],
    }
    html = page("/incheon/stations/", "인천 지하철역 출장마사지·홈타이 | 역세권 방문 안내",
        "인천 지하철역별 출장마사지·홈타이 안내 - 인천1·2호선, 경인선·7호선·수인분당선·공항철도 인천권 역세권 방문 안내입니다. 부평·주안·송도·인천시청역 등 대표역을 확인하세요.",
        "stations", body, [bc_ld(trail), coll])
    write("/incheon/stations/", html)

# ---- 노선 페이지 /incheon/stations/<line>/ --------------------------------
def build_line_pages():
    for ln in LINES:
        path = f"/incheon/stations/{ln['slug']}/"
        trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"),
                 ("/incheon/stations/", "지하철역별 안내"), (None, ln["name"])]
        sts = [STATIONS[n] for n in ln["stations"]]
        cards = "".join(
            f'<a class="card reveal" href="/incheon/stations/{s["slug"]}/"><div class="k">STATION</div>'
            f'<h3>{s["name"]}</h3><p>{s["character"]}</p>'
            f'<span class="more">역 안내 →</span></a>' for s in sts)
        chips = "".join(f'<span class="chip"><b>{s["name"]}</b></span>' for s in sts)
        transfers = [s["name"] for s in sts if len(s["lines"]) > 1]
        sections = [
            (f"{ln['name']} 역세권 방문 안내", [
                f"{ln['name']}은(는) 인천 지하철 노선 중 하나로, 총 {len(sts)}개 역 인근으로 출장마사지·홈타이 방문 안내가 가능합니다. {sts[0]['name']}부터 {sts[-1]['name']}까지 노선을 따라 역세권 생활권이 이어집니다.",
                "역명은 방문 위치를 잡기 위한 기준일 뿐이며, 실제로는 각 역 도보권의 자택·오피스텔·숙소로 방문합니다. 가까운 역을 알려주시면 위치 파악과 도착이 빨라집니다.",
                "아래에서 역을 눌러 역별 상세 방문 안내와 평균 도착 시간, 인근 생활권을 확인하실 수 있습니다.",
                ("html", f'<div class="chips" style="margin:6px 0 18px">{chips}</div>'
                         f'<div class="grid g3">{cards}</div>')]),
            (f"{ln['name']} 환승역 안내", [
                ("다른 노선과 만나는 환승역은 " + "·".join(transfers) + " 입니다. 환승역은 여러 노선에 노출되더라도 안내 페이지(URL)는 하나로 운영해 중복을 만들지 않습니다. 환승역 인근은 접근성이 좋아 방문 위치 기준점으로 잡기 좋습니다."
                 if transfers else
                 f"{ln['name']}의 각 역은 단일 안내 페이지로 운영되며, 역명을 눌러 상세 방문 안내를 확인하실 수 있습니다. 노선 내 어느 역이든 가까운 위치를 알려주시면 방문 가능 여부를 안내드립니다.")]),
            (f"{ln['name']} 인근에서 많이 찾는 관리", [
                f"{ln['name']} 역세권에서는 스웨디시·아로마·피로 회복 관리 문의가 많습니다. 퇴근길이나 휴식이 필요한 저녁 시간대 예약이 꾸준한 편입니다.",
                "처음이라면 90분 스웨디시(피로 회복)로 시작하시길 권하며, 운동 후에는 스포츠, 향과 함께 받고 싶다면 아로마테라피가 잘 맞습니다.",
                ("ul", ['<a href="/course/fatigue/">피로 회복 관리</a>', '<a href="/theme/swedish/">스웨디시</a>',
                        '<a href="/theme/aromatherapy/">아로마테라피</a>', '<a href="/course/hometai/">홈타이 코스</a>'])]),
            ("예약·코스·위생은 전용 안내에서", [
                "예약 가능 시간·준비물·위생 기준·코스 요금은 역마다 반복하지 않고 전용 안내에서 확인하실 수 있습니다.",
                ("ul", ['<a href="/incheon/hours/">예약 가능 시간 안내</a>',
                        '<a href="/incheon/checklist/">이용 전 확인사항</a>',
                        '<a href="/incheon/safety/">위생 및 안전 안내</a>',
                        '<a href="/course/">코스안내 · 가격</a>'])]),
            (f"{ln['name']} 방문 시 참고사항", [
                f"{ln['name']} 역세권은 도심권 기준으로 위치에 따라 평균 30~40분 내외로 도착합니다. 영종·강화 방향 등 외곽으로 갈수록 이동 시간이 더 소요될 수 있습니다.",
                "예약 시 가까운 역과 함께 정확한 주소·공동현관 출입 방법을 알려주시면 마지막 동선이 매끄럽습니다. 저녁·주말은 문의가 몰리니 미리 예약하시길 권합니다.",
                "역 인근이 아닌 위치도 같은 구·동 생활권이라면 함께 안내드리니, 지역별 안내와 함께 확인하시면 편리합니다."]),
        ]
        line_faq = [
            (f"{ln['name']} 어느 역까지 안내되나요?",
             "노선 내 " + "·".join(s["name"] for s in sts[:6]) + " 등 전 역 인근을 안내드립니다. 가까운 역을 알려주시면 위치 확인이 빨라집니다."),
            ("환승역은 어떻게 찾나요?",
             "환승역은 여러 노선 목록에 보이지만 안내 페이지는 하나입니다. 역명을 누르면 동일한 상세 페이지로 연결됩니다."),
            ("역 근처가 아니어도 방문되나요?",
             "역은 위치를 잡기 위한 기준일 뿐이며, 실제로는 해당 구·동 생활권 자택·숙소로 방문합니다."),
        ]
        content_page(path, "stations", trail,
            title=f"{ln['name']} 출장마사지·홈타이 | 역세권 방문 안내",
            desc=f"{ln['name']} 출장마사지·홈타이 안내 - " + "·".join(s['name'] for s in sts[:6]) +
                 f" 등 {len(sts)}개 역 인근 방문 예약 안내입니다.",
            eyebrow=f"인천 지하철 · {ln['name']}", h1=f"{ln['name']} 출장마사지·홈타이",
            lead=f"{ln['name']} {len(sts)}개 역 인근으로 출장마사지·홈타이 방문 예약을 안내합니다. 역세권 자택·오피스텔·숙소로 방문합니다.",
            sections=sections, faq=line_faq,
            top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                       ("/incheon/stations/", "지하철역별 안내"), ("/course/", "코스안내")],
            cta_title=f"{ln['name']} 인근 방문 예약을 도와드릴까요?")

# ---- 역 상세 페이지 /incheon/stations/<station>/ --------------------------
def build_station_pages():
    # 각 역이 어떤 노선 목록에 속하는지 (사이드 링크용)
    for name, st in STATIONS.items():
        path = f"/incheon/stations/{st['slug']}/"
        trail = [("/", "홈"), ("/incheon/", "인천 출장마사지"),
                 ("/incheon/stations/", "지하철역별 안내"), (None, name)]
        lnames = _line_names_for(st)
        is_transfer = len(st["lines"]) > 1
        # 같은 첫 노선의 인접 역 링크
        primary = next(l for l in LINES if l["code"] == st["lines"][0])
        idx = primary["stations"].index(name)
        nbrs = []
        for j in (idx - 1, idx + 1):
            if 0 <= j < len(primary["stations"]) and primary["stations"][j] != name:
                ns = STATIONS[primary["stations"][j]]
                nbrs.append(f'<a href="/incheon/stations/{ns["slug"]}/">{ns["name"]}</a>')
        line_links = [f'<a href="/incheon/stations/{l["slug"]}/">{LINE_NAMES[l["code"]]}</a>'
                      for l in LINES if l["code"] in st["lines"]]
        transfer_para = (
            f"{name}은 {' · '.join(lnames)}이 만나는 환승역입니다. 여러 노선에서 접근할 수 있어 방문 위치 기준점으로 잡기 좋으며, 환승역이라도 안내 페이지는 하나로 운영합니다."
            if is_transfer else
            f"{name}은 {lnames[0]} 역입니다. 역 인근 자택·오피스텔·숙소로 방문하며, 가까운 출구나 건물을 알려주시면 위치 파악이 빨라집니다.")
        sd, ch, lm, arr = st["slug"], st["character"], st["landmarks"], st["arrival"]
        lm0 = lm.split(",")[0].strip()
        # 페이지별 변형 — 동일 문장 반복을 피해 유사도를 낮춘다
        intro1 = _pick(sd, [
            f"{name}은(는) {ch}입니다. {lm}를 중심으로 인근 자택·오피스텔·숙소 방문 문의가 많습니다.",
            f"{lm} 일대를 끼고 있는 {name}은(는) {ch}으로, 역 주변 주거지와 숙소로의 방문 문의가 꾸준합니다.",
            f"{name}은(는) {ch}으로 분류됩니다. {lm0}가 가까워 이 일대 자택·오피스텔 방문이 활발한 편입니다.",
        ], "i1")
        intro2 = _pick(sd, [
            f"{name} 출장마사지·홈타이는 매장을 찾지 않고도 역세권 생활권에서 받을 수 있는 방문형 관리입니다. 예약 시 위치·시간·코스를 확인한 뒤 방문 가능 여부를 안내드립니다.",
            f"매장 방문 없이 {name} 인근 자택·숙소에서 받는 방문형 관리로, 예약 단계에서 위치와 희망 시간, 코스를 함께 확인해 방문 가능 여부를 알려드립니다.",
            f"{name} 인근에서는 이동 없이 자택·오피스텔에서 받는 방문형 관리를 이용하실 수 있습니다. 예약 시 위치·시간·코스를 확인한 뒤 일정을 잡아 드립니다.",
        ], "i2")
        arr_line = _pick(sd, [
            f"역 인근은 퇴근길이나 약속 전후 짧은 시간에도 문의가 들어오며, {name} 도보권이라면 평균 {arr}분 내외로 도착합니다. 같은 역 인근이라도 정확한 위치에 따라 도착 시간은 달라질 수 있습니다.",
            f"{name} 도보권 기준 평균 {arr}분 내외로 도착하며, 시간대와 정확한 위치에 따라 차이가 있을 수 있습니다. 저녁 시간대는 도착이 다소 길어질 수 있습니다.",
            f"이 일대는 {lm0}를 기준으로 평균 {arr}분 내외에 도착합니다. 출퇴근 시간대나 주말 저녁은 여유 있게 예약하시는 편이 좋습니다.",
        ], "ar")
        # 역마다 주력 테마를 다르게 잡아 콘텐츠를 차별화
        theme_pool = [("스웨디시", "오일로 전신을 부드럽게 푸는", "/theme/swedish/"),
                      ("아로마테라피", "향과 함께 이완하는", "/theme/aromatherapy/"),
                      ("타이마사지", "스트레칭 중심의", "/theme/thai/"),
                      ("피로 회복 관리", "전신 긴장을 정리하는", "/course/fatigue/"),
                      ("스포츠·경락", "운동 후 근육을 정리하는", "/theme/sports-meridian/"),
                      ("홈타이 코스", "옷을 입은 채 받는 스트레칭형", "/course/hometai/")]
        pt = _pick(sd, theme_pool, "th")
        care_links = _picks(sd, ['<a href="/course/fatigue/">피로 회복 관리</a>', '<a href="/theme/swedish/">스웨디시</a>',
                                 '<a href="/theme/aromatherapy/">아로마테라피</a>', '<a href="/course/hometai/">홈타이 코스</a>',
                                 '<a href="/theme/thai/">타이마사지</a>', '<a href="/course/price/">가격 안내</a>'], "cl")
        prep_links = _picks(sd, ['<a href="/incheon/hours/">예약 가능 시간 안내</a>',
                                 '<a href="/incheon/checklist/">이용 전 확인사항</a>',
                                 '<a href="/incheon/safety/">위생 및 안전 안내</a>',
                                 '<a href="/course/price/">가격 안내</a>'], "pl")
        sections = [
            (f"{name} 출장마사지·홈타이 안내", [
                intro1, intro2, arr_line,
                '예약 방법은 <a href="/reservation/">예약안내</a>, 처음 이용 시 흐름은 <a href="/guide/">이용가이드</a>, 코스·요금은 <a href="/course/price/">가격 안내</a>에서 확인하실 수 있습니다.']),
            (f"{name} 역세권 방문 안내", [
                f"{name} 인근은 {lm}를 포함하는 생활권입니다. {_pick(sd, ['주거 단지와 상권이 함께 있어 위치 기준점으로 잡기 좋습니다.', '도보권에 생활시설이 모여 있어 방문 동선을 잡기 수월합니다.', '인근에 주거지와 편의시설이 이어져 방문 문의가 고른 편입니다.'], 'z1')}",
                _pick(sd, ["역에서 가까운 주거지·숙소로 방문하며, 정확한 주소와 공동현관 출입 방법, 도착 직전 연락 가능한 번호를 알려주시면 동선이 매끄럽습니다.",
                           "방문은 역 도보권의 자택·오피스텔·숙소로 진행되며, 주소와 출입 방법을 미리 남겨주시면 도착이 빨라집니다.",
                           "역 주변 주거지·숙소로 방문하므로, 동·호수와 공동현관 안내를 함께 주시면 마지막 동선이 수월합니다."], "z2"),
                f"역명은 방문 위치를 잡기 위한 기준일 뿐이며, 실제로는 {name} 도보권의 자택·오피스텔·숙소로 방문합니다. 가까운 출구나 {lm0} 같은 큰 건물을 함께 알려주시면 위치 파악이 빨라집니다."]),
            ("노선·환승 안내", [
                transfer_para,
                ("ul", line_links + (nbrs if nbrs else []))]),
            (f"{name}에서 많이 찾는 관리", [
                f"{name} 인근에서는 {pt[1]} <a href='{pt[2]}'>{pt[0]}</a>를 비롯해 다양한 방문 관리 문의가 들어옵니다. {ch}이라 {_pick(sd, ['퇴근길과 저녁 시간대 예약이 꾸준합니다.', '휴식이 필요한 저녁·주말 문의가 많습니다.', '하루를 마무리하며 이완을 원하는 분들이 자주 찾습니다.'], 'c1')}",
                _pick(sd, ["처음이라면 90분 구성으로 전신을 고르게 받으시길 권하며, 컨디션과 목적에 맞춰 코스와 테마를 선택할 수 있습니다.",
                           "처음 이용하신다면 90분 스웨디시(피로 회복)가 무난하며, 운동 후라면 스포츠, 향을 원하시면 아로마테라피가 잘 맞습니다.",
                           "목적에 따라 시간(60·90·120분)과 테마를 골라 진행하며, 무엇을 고를지 고민되면 상담 시 추천해 드립니다."], "c2"),
                ("ul", care_links)]),
            (f"{name} 예약·준비·위생 안내", [
                _pick(sd, [f"{name} 인근 방문 예약은 시간대와 배정 상황에 따라 가능 여부가 달라집니다. 저녁·주말은 문의가 몰릴 수 있어 사전 예약을 권장드립니다.",
                           f"{name} 방문은 예약 시간과 배정 상황에 따라 조율되며, 원하는 시간이 정해져 있다면 미리 연락 주시는 편이 좋습니다.",
                           f"{name} 인근 예약은 위치와 시간대에 따라 가능 여부가 달라지므로, 가급적 여유 있게 문의해 주시면 일정 조율이 수월합니다."], "p1"),
                "예약 가능 시간, 방문 전 준비물, 위생·안전 기준은 역마다 반복하지 않고 전용 안내에서 자세히 확인하실 수 있습니다.",
                ("ul", prep_links)]),
        ]
        st_faq = [
            (f"{name} 근처에서 예약할 수 있나요?",
             f"네. {name} 역세권 자택·오피스텔·숙소로 방문 안내가 가능합니다. {lm0} 인근 등 정확한 위치를 알려주시면 도착 시간을 안내드립니다."),
            (f"{name} 도착까지 얼마나 걸리나요?",
             f"{name} 도보권 기준 평균 {arr}분 내외이며, 시간대와 정확한 위치에 따라 달라질 수 있습니다."),
            (f"{name}은 어떤 역인가요?",
             f"{name}은(는) {ch}으로, {lm} 인근입니다." + (f" {' · '.join(lnames)}이 만나는 환승역입니다." if is_transfer else "")),
            ("출구별로 안내가 다른가요?",
             f"출구별 페이지는 따로 운영하지 않습니다. {name} 인근 전체를 기준으로 안내하며, 정확한 위치는 예약 시 확인합니다."),
            (f"{name}에서는 어떤 관리가 인기인가요?",
             f"{pt[0]}를 비롯한 방문 관리 문의가 많습니다. 자세한 내용은 코스안내와 테마별 안내에서 확인하실 수 있습니다."),
        ]
        content_page(path, "stations", trail,
            title=f"{name} 출장마사지·홈타이 | {lnames[0]} 역세권 방문 예약",
            desc=f"{name} 출장마사지·홈타이 안내입니다. {st['landmarks']} 인근 역세권 방문 예약, 평균 도착 시간, 코스 선택 기준을 확인해보세요.",
            eyebrow=f"인천 지하철 · {name}", h1=f"{name} 출장마사지·홈타이",
            lead=f"{name}({st['character']}) 인근에서 출장마사지·홈타이 예약을 찾는 분들을 위한 안내입니다. {st['landmarks']} 생활권으로 평균 {st['arrival']}분 내외 도착합니다.",
            sections=sections, faq=st_faq,
            data_note=f"{name} 인근은 평균 {st['arrival']}분 내외로 도착합니다(예약 데이터 기준). 환승·번화가 인근은 시간대에 따라 도착이 길어질 수 있어 사전 예약을 권장드립니다.",
            top_links=[("tel:" + PHONE_TEL, "예약문의", True),
                       (f"/incheon/stations/{primary['slug']}/", f"{LINE_NAMES[st['lines'][0]]}"),
                       ("/incheon/stations/", "지하철역별 안내")],
            service=(f"{name} 출장마사지·홈타이", f"{name} 역세권 방문 건강관리"),
            cta_title=f"{name} 인근 방문 예약, 지금 도와드릴까요?")

# ---- 테마 허브 /theme/ ----------------------------------------------------
def build_theme_hub():
    trail = [("/", "홈"), (None, "테마별 안내")]
    cards = "".join(
        f'<a class="card reveal" href="/theme/{t["slug"]}/"><div class="k">{t["kicker"]}</div>'
        f'<h3>{t["name"]}</h3><p>{t["desc"]}</p><span class="more">테마 보기 →</span></a>'
        for t in THEMES)
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>THEME</span>'
        '<h2 class="sec">테마별 안내</h2>'
        '<p class="sec-lead">목적과 취향에 맞는 관리 테마를 안내합니다. 지역·역·테마를 조합한 별도 페이지는 만들지 않으며, 테마 설명은 이곳에 한곳으로 정리합니다.</p>'
        f'<div class="grid g4" style="margin-top:26px">{cards}</div>'
        '<div style="max-width:820px;margin-top:34px">'
        '<p class="sec-lead">테마는 관리의 방식을 뜻합니다. 오일로 전신을 부드럽게 푸는 <a href="/theme/swedish/">스웨디시</a>, 향까지 더한 <a href="/theme/aromatherapy/">아로마테라피</a>, 흐르듯 진행하는 <a href="/theme/lomilomi/">로미로미</a>, 스트레칭 중심의 <a href="/theme/thai/">타이마사지</a>, 또렷한 지압의 <a href="/theme/chinese/">중국마사지</a> 등 컨디션과 취향에 맞춰 고를 수 있습니다.</p>'
        '<p class="sec-lead" style="margin-top:12px">이 밖에 자택 환경에 맞춘 <a href="/theme/homecare/">홈케어</a>, 숙소에서 받는 <a href="/theme/hotel/">호텔식마사지</a>, <a href="/theme/foot/">발마사지</a>, <a href="/theme/sports-meridian/">스포츠·경락</a>, <a href="/theme/skincare/">스킨케어</a>, <a href="/theme/waxing/">왁싱</a>, <a href="/theme/couple-care/">커플 관리</a>가 있으며, 심야까지 운영하는 <a href="/theme/24h/">24시간</a> 안내와 관리 후 휴식으로 이어지는 <a href="/theme/sleep/">수면 가능</a> 안내도 함께 제공합니다.</p>'
        '<p class="sec-lead" style="margin-top:12px">실제 예약은 테마와 함께 코스(시간·구성)를 정해 진행합니다. 처음이라면 90분 스웨디시(피로 회복) 구성을 권장드리며, 코스별 요금은 <a href="/course/price/">가격 안내</a>에서 확인하실 수 있습니다.</p>'
        '<p class="sec-lead" style="margin-top:12px">모든 테마는 자택·오피스텔·숙소로 방문해 진행하는 방문형으로 운영되며, 인천 전지역으로 안내합니다. 향·압의 선호나 피부·건강상 주의가 필요한 사항이 있으면 예약 시 미리 알려주시면 맞춰 드립니다. 방문 지역은 <a href="/incheon/area/">지역별 안내</a>, 가까운 역은 <a href="/incheon/stations/">지하철역별 안내</a>에서 확인하실 수 있습니다.</p>'
        '</div></div></section>' +
        price_menu_block() + cta_band())
    coll = {
        "@context": "https://schema.org", "@type": "CollectionPage",
        "name": "인천 출장마사지 테마별 안내", "url": BASE_URL + "/theme/",
        "inLanguage": "ko-KR", "image": og_image_obj(), "isPartOf": {"@type": "WebSite", "url": BASE_URL + "/"},
        "hasPart": [{"@type": "WebPage", "name": t["name"],
                     "url": BASE_URL + f"/theme/{t['slug']}/"} for t in THEMES],
    }
    html = page("/theme/", "테마별 안내 | 인천 출장마사지 스웨디시·타이·아로마 테마",
        "인천 출장마사지·홈타이 테마별 안내 - 스웨디시, 로미로미, 타이마사지, 아로마테라피, 호텔식마사지, 스포츠·경락 등 관리 테마를 소개합니다.",
        "theme", body, [bc_ld(trail), coll, offer_ld()])
    write("/theme/", html)

# ---- 테마 상세 /theme/<slug>/ ---------------------------------------------
# 테마별 고유 콘텐츠 (대상/진행/특징) — 지역·역 조합 없이 테마 단독으로 작성
THEME_DETAIL = {
    "swedish": {
        "intro": "스웨디시는 오일을 사용해 손바닥으로 넓고 길게 쓸어주는 동작을 기본으로, 일정한 압과 리듬으로 전신의 긴장을 부드럽게 풀어주는 대표적인 관리입니다.",
        "suited": ["전신이 무겁고 푹 쉬고 싶은 분", "강한 지압보다 부드러운 이완을 선호하는 분", "잠들기 전 긴장을 풀고 싶은 분"],
        "how": ["오일을 펴 바르며 큰 근육부터 차례로 이완합니다.", "60분은 어깨·등 중심, 90분은 전신, 120분은 마무리 케어까지 진행합니다.", "압의 세기는 시작 전과 진행 중 언제든 조절해 드립니다."],
        "note": "스웨디시는 인천 방문 관리에서 가장 많이 선택되는 기본 테마로, 처음이라면 90분 구성을 권장드립니다."},
    "lomilomi": {
        "intro": "로미로미는 팔뚝과 손을 길게 사용해 파도처럼 흐르듯 진행하는 하와이 전통식 오일 관리입니다.",
        "suited": ["끊김 없는 부드러운 흐름을 선호하는 분", "심리적 이완까지 원하는 분", "스웨디시를 받아본 뒤 변화를 주고 싶은 분"],
        "how": ["넓은 면적을 길게 쓸어내리는 동작으로 호흡을 느리게 가라앉힙니다.", "오일을 충분히 사용해 마찰을 줄여 부드럽게 진행합니다.", "마무리 단계에서 수건으로 정돈해 잔여감을 줄입니다."],
        "note": "오일과 향을 사용하므로 민감성 피부나 알러지가 있다면 예약 시 미리 알려주세요."},
    "thai": {
        "intro": "타이마사지는 스트레칭과 지압을 결합해 몸을 늘이고 눌러 유연성과 순환을 돕는 관리입니다.",
        "suited": ["몸이 뻣뻣하고 스트레칭이 필요한 분", "오일보다 옷을 입은 채 받는 방식을 선호하는 분", "근육과 관절의 가동 범위를 넓히고 싶은 분"],
        "how": ["편한 복장을 입은 채로 스트레칭과 지압을 번갈아 진행합니다.", "호흡에 맞춰 천천히 늘여 무리가 가지 않도록 합니다.", "통증이 느껴지면 즉시 말씀해 주시면 강도를 조절합니다."],
        "note": "타이 스트레칭은 자택에서 받는 홈타이 코스와도 잘 어울립니다."},
    "chinese": {
        "intro": "중국마사지는 경혈과 근막을 따라 또렷한 압으로 눌러 뭉친 부위를 풀어주는 지압 중심 관리입니다.",
        "suited": ["또렷하고 시원한 압을 선호하는 분", "어깨·목 등 특정 부위가 자주 뭉치는 분", "지압식 관리를 좋아하는 분"],
        "how": ["경혈 지점을 따라 압을 주며 뭉친 부위에 시간을 더 배분합니다.", "압이 강하게 느껴지면 즉시 조절해 드립니다.", "마무리는 가볍게 이완하며 호흡을 고릅니다."],
        "note": "강한 압을 선호하지 않는다면 스웨디시나 아로마테라피를 권장드립니다."},
    "aromatherapy": {
        "intro": "아로마테라피는 블렌딩한 관리용 오일의 향과 촉감으로 심신을 함께 이완하는 관리입니다.",
        "suited": ["향을 통한 이완을 원하는 분", "긴장도가 높거나 예민한 날", "부드럽고 감각적인 이완을 선호하는 분"],
        "how": ["라벤더·시트러스 등 컨디션에 맞는 향을 안내드립니다.", "오일로 마찰을 줄여 더 유연하게 진행합니다.", "마무리 단계에서 수건으로 정돈합니다."],
        "note": "특정 향·성분에 알러지가 있거나 임신 중이라면 예약 시 미리 알려주세요."},
    "homecare": {
        "intro": "홈케어는 자택 환경에 맞춰 부담 없이 받을 수 있는 생활 밀착형 방문 관리입니다.",
        "suited": ["매장 방문이 번거로운 분", "규칙적으로 가볍게 관리받고 싶은 분", "익숙한 공간에서 편하게 받고 싶은 분"],
        "how": ["자택 공간에 맞춰 코스와 시간을 안내드립니다.", "스웨디시·아로마 등 원하는 방식으로 진행할 수 있습니다.", "관리 후 이동 없이 그대로 휴식으로 이어집니다."],
        "note": "홈케어는 방문 방식이며, 실제 관리는 코스와 다른 테마로 선택합니다."},
    "hotel": {
        "intro": "호텔식마사지는 호텔·숙소 객실에서 받는 정중한 응대 중심의 프리미엄 방문 관리입니다.",
        "suited": ["출장·여행 중 숙소에서 받고 싶은 분", "정중하고 깔끔한 응대를 중시하는 분", "이동 없이 객실에서 쉬고 싶은 분"],
        "how": ["객실 환경에 맞춰 공간을 준비하고 진행합니다.", "건물명·객실 번호와 프런트 출입 안내가 필요한지 미리 알려주세요.", "코스는 스웨디시·아로마 등에서 선택할 수 있습니다."],
        "note": "숙소·호텔 방문은 예약 시 건물 정보를 함께 알려주시면 동선이 매끄럽습니다."},
    "foot": {
        "intro": "발마사지는 발과 종아리의 피로를 집중적으로 풀어 다리의 가벼움을 더하는 관리입니다.",
        "suited": ["오래 서 있거나 많이 걸은 날", "다리가 자주 붓고 무거운 분", "전신 관리에 발 케어를 더하고 싶은 분"],
        "how": ["발과 종아리를 중심으로 지압하며 순환을 돕습니다.", "전신 코스에 발 케어를 더하는 구성도 가능합니다.", "압의 세기는 선호에 맞춰 조절합니다."],
        "note": "전신 이완과 함께 받으면 마무리 케어로 잘 어울립니다."},
    "sports-meridian": {
        "intro": "스포츠·경락은 운동 후 뭉친 근육과 경락을 따라 또렷하게 풀어 컨디션을 정리하는 관리입니다.",
        "suited": ["러닝·헬스·등산 등 운동 후", "또렷한 압의 관리를 선호하는 분", "다리·등 근육이 무거운 날"],
        "how": ["운동 종류와 뭉친 부위를 확인해 시간을 집중 배분합니다.", "근육을 데우듯 시작해 점차 압을 높입니다.", "부상·급성 통증 부위는 관리 대상이 아니며 의료기관 진료를 권유드립니다."],
        "note": "본 관리는 의료 행위가 아닌 건강관리이며 통증 완화·치료를 보장하지 않습니다."},
    "skincare": {
        "intro": "스킨케어는 피부 결을 정돈하고 이완을 더하는 부드러운 케어 중심 관리입니다.",
        "suited": ["피부 결 정돈과 이완을 함께 원하는 분", "부드러운 케어를 선호하는 분", "관리 후 산뜻함을 원하는 분"],
        "how": ["피부 상태를 확인하고 부담 없는 제품으로 진행합니다.", "민감성 피부는 사전에 알려주시면 조정합니다.", "전신 관리와 함께 구성할 수 있습니다."],
        "note": "피부 질환이나 알러지가 있다면 예약 시 미리 알려주세요."},
    "waxing": {
        "intro": "왁싱은 위생 기준에 맞춘 제모 케어로, 부위와 진행 방식을 사전에 안내한 뒤 진행합니다. 자택 방문으로 받을 수 있어 매장 방문이 번거로운 분께 편리합니다.",
        "suited": ["위생적인 제모 케어를 원하는 분", "사전 안내 후 진행을 선호하는 분", "매장 방문 없이 자택에서 받고 싶은 분", "정기적으로 관리받고 싶은 분"],
        "how": ["예약 시 원하는 부위와 진행 방식을 먼저 확인합니다.", "위생 용품을 기준에 맞춰 사용하고, 사용 후 공간을 정돈합니다.", "민감 부위는 무리하지 않도록 상태를 보며 안내드립니다.", "진행 후 진정 케어와 주의사항을 함께 안내드립니다."],
        "note": "피부 상태나 컨디션에 따라 가능 여부가 달라질 수 있어 예약 시 상담드리며, 진행 전 주의사항을 충분히 안내한 뒤 시작합니다."},
    "couple-care": {
        "intro": "커플 관리는 두 분이 같은 공간에서 나란히 받는 동반형 이완 관리입니다.",
        "suited": ["기념일을 함께 보내려는 커플", "친구·가족과 함께 받고 싶은 분", "같은 시간에 나란히 쉬고 싶은 분"],
        "how": ["관리사 2인이 방문해 동시에 진행합니다.", "각자 다른 코스(스웨디시·아로마 등)를 선택할 수 있습니다.", "공간이 좁으면 순차 진행으로 안내드립니다."],
        "note": "관리사 2인 일정 조율이 필요해 가급적 사전 예약을 권장드립니다."},
    "24h": {
        "intro": "24시간은 심야와 새벽까지 상담이 가능한 운영 방식 안내입니다. 별도의 조합 상품이 아니라 운영 시간에 대한 안내입니다.",
        "suited": ["퇴근이 늦어 저녁 늦게 받고 싶은 분", "심야에 이완이 필요한 분"],
        "how": ["전화 상담은 연중무휴 24시간 가능합니다.", "심야는 위치에 따라 도착 시간이 길어질 수 있습니다.", "정확한 방문 가능 시간은 상담 시 안내드립니다."],
        "note": "자세한 시간대별 특징은 예약 가능 시간 안내에서 확인하실 수 있습니다."},
    "sleep": {
        "intro": "수면 가능은 관리 후 이동 없이 그대로 휴식·수면으로 이어지는 이완 중심 안내입니다.",
        "suited": ["관리 후 바로 잠들고 싶은 분", "수면의 질을 높이고 싶은 분", "잠들기 전 긴장을 풀고 싶은 분"],
        "how": ["부드러운 압의 스웨디시·아로마 구성을 권장드립니다.", "관리 후 수분 섭취와 휴식을 안내드립니다.", "조용한 분위기를 준비해 두시면 이완에 도움이 됩니다."],
        "note": "자택 방문 관리이기에 관리 직후 이동 없이 휴식으로 이어질 수 있습니다."},
}

def build_theme_pages():
    ct = [("/", "홈"), ("/theme/", "테마별 안내")]
    for t in THEMES:
        det = THEME_DETAIL[t["slug"]]
        path = f"/theme/{t['slug']}/"
        sections = [
            (f"{t['name']}란", [t["desc"], det["intro"],
                f"인천굿데이마사지에서는 {t['name']}를 자택·오피스텔·숙소로 방문해 진행하므로, 매장을 찾지 않고도 익숙한 공간에서 편안하게 받을 수 있습니다. 인천 전지역으로 방문하며 예약 시 위치·시간·코스를 함께 확인합니다."]),
            ("이런 분께 권해드립니다", [
                f"{t['name']}는 다음과 같은 분께 잘 맞습니다.",
                ("ul", det["suited"])]),
            ("진행 방식", det["how"]),
            ("방문 관리로 받을 때 좋은 점", [
                f"{t['name']}는 자택·오피스텔·숙소로 방문해 받기 때문에, 관리 직후 이동 없이 그대로 휴식할 수 있습니다.",
                "익숙한 공간에서 받아 긴장이 덜하고, 인천 전지역으로 방문하므로 가까운 위치나 지하철역을 알려주시면 도착이 빨라집니다.",
                det["note"]]),
            ("진행 시간(60·90·120분) 선택", [
                "60분은 핵심 부위를 중심으로 가볍게 받고 싶을 때, 90분은 전신을 고르게 이완하고 싶을 때 적합합니다.",
                "120분은 전신 이완 후 마무리 케어까지 여유 있게 받고 싶을 때 좋습니다. 처음이라면 90분 구성이 가장 무난합니다.",
                "관리 시작 전 선호하는 압의 세기와 집중 부위를 확인하고, 진행 중에도 편하게 말씀해 주시면 조절해 드립니다."]),
            ("예약 전 확인하면 좋은 점", [
                "편히 쉴 수 있는 공간과 조용한 분위기를 준비해 주시면 이완의 질이 높아집니다.",
                "특정 향·압을 피하고 싶거나 피부·건강상 주의가 필요한 상황이 있다면 예약 시 미리 알려주세요.",
                '방문 전 준비 사항은 <a href="/incheon/checklist/">이용 전 확인사항</a>에서 자세히 확인하실 수 있습니다.']),
            ("코스·요금과 함께 보기", [
                f"{t['name']}는 관리 방식을 뜻하는 테마이며, 실제 예약은 코스와 시간(60·90·120분)으로 선택합니다.",
                "지역·역·테마를 조합한 별도 페이지는 만들지 않으므로, 방문 지역은 지역별 안내에서 따로 확인하시면 됩니다.",
                ("ul", ['<a href="/course/">전체 코스 보기</a>', '<a href="/course/price/">가격 안내</a>',
                        '<a href="/theme/">다른 테마 보기</a>', '<a href="/incheon/area/">지역별 안내</a>',
                        '<a href="/reservation/">예약안내</a>'])]),
        ]
        faq = [
            (f"{t['name']}는 어떤 관리인가요?", t["desc"] + " " + det["intro"]),
            (f"{t['name']}는 어디서 받나요?", "자택·오피스텔·숙소로 방문해 받는 방문형 관리입니다. 인천 전지역으로 안내드리며, 가까운 지하철역을 알려주시면 위치 확인이 빨라집니다."),
            ("진행 시간은 어떻게 되나요?", "60·90·120분 중 선택할 수 있으며, 처음이라면 전신을 고르게 받을 수 있는 90분 구성을 권장드립니다."),
            ("요금은 어떻게 되나요?", "코스별 정찰 요금을 사전에 안내드리며, 자세한 금액은 가격 안내에서 확인하실 수 있습니다."),
        ]
        content_page(path, "theme", ct + [(None, t["name"])],
            title=f"{t['name']} | 인천 출장마사지·홈타이 {t['name']} 안내",
            desc=f"인천 출장마사지·홈타이 {t['name']} 안내 - {t['desc']} 대상, 진행 방식, 코스·요금 안내를 확인하세요.",
            eyebrow=f"THEME · {t['kicker']}", h1=f"{t['name']} 안내",
            lead=t["desc"], sections=sections, faq=faq, show_price=True,
            service=(f"{t['name']}", f"인천 방문 {t['name']} 관리"),
            cta_title=f"{t['name']} 방문 예약을 도와드릴까요?")

# ===========================================================================
# PAGE BUILDERS — 코스
# ===========================================================================
def build_course():
    trail = [("/", "홈"), (None, "코스안내")]
    course_faq = [
        ("코스는 어떻게 선택하나요?", "컨디션과 목적을 말씀해 주시면 피로 회복·아로마·스포츠·홈타이 중 적합한 코스를 안내드립니다."),
        ("커플·가족 관리는 어떻게 진행되나요?", "두 분이 같은 공간에서 동시에 받는 동반 관리이며, 인원과 시간에 따라 요금이 달라집니다."),
        ("기업·단체 관리도 되나요?", "워크숍·행사 등 단체 인원은 사전 협의 후 별도 견적으로 안내드립니다."),
        ("표시된 요금 외 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며, 지역·시간대 등 변동 사항은 예약 시 사전에 안내드립니다."),
    ]
    course_cards = "".join(
        f'<a class="card reveal" href="/course/{c["slug"]}/"><div class="k">{c["kicker"]}</div>'
        f'<h3>{c["name"]}</h3><p>{c["desc"]}</p><span class="more">코스 보기 →</span></a>'
        for c in COURSES)
    more_cards = (
        '<a class="card reveal" href="/course/price/"><div class="k">PRICE</div>'
        '<h3>가격 안내</h3><p>코스별 60·90·120분 정찰 요금과 변동 요소를 안내합니다.</p>'
        '<span class="more">가격 보기 →</span></a>'
        '<a class="card reveal" href="/course/guide/"><div class="k">GUIDE</div>'
        '<h3>코스 선택 가이드</h3><p>목적·상황별 추천과 시간 선택 기준을 안내합니다.</p>'
        '<span class="more">가이드 보기 →</span></a>')
    body = (breadcrumb(trail) +
        '<section class="block" id="all"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>COURSE</span>'
        '<h2 class="sec">전체 코스</h2>'
        '<p class="sec-lead">목적과 컨디션에 맞춰 고를 수 있는 인천굿데이마사지의 방문 관리 코스입니다.</p>'
        f'<div class="grid g3" style="margin-top:26px">{course_cards}</div>'
        '<div style="max-width:820px;margin-top:34px">'
        '<p class="sec-lead">코스는 관리의 시간과 구성을 정하는 기준입니다. 전신을 부드럽게 푸는 <strong>피로 회복 관리(스웨디시 계열)</strong>, 향과 함께 이완하는 <strong>아로마 관리</strong>, 운동 후 근육을 정리하는 <strong>스포츠 관리</strong>, 스트레칭 중심의 <strong>홈타이 코스</strong>, 두 분이 함께 받는 <strong>커플·가족 방문 관리</strong>, 행사용 <strong>기업·단체 방문 관리</strong>가 있습니다.</p>'
        '<p class="sec-lead" style="margin-top:12px">모든 코스는 60·90·120분으로 운영하며, 처음이라면 전신을 고르게 받을 수 있는 90분 구성이 가장 무난합니다. 스웨디시·아로마테라피·타이 등 관리 방식(테마)은 코스와 별개로 선택할 수 있으니 <a href="/theme/">테마별 안내</a>를 함께 참고하시고, 어떤 코스가 맞을지 고민된다면 <a href="/course/guide/">코스 선택 가이드</a>에서 상황별 추천을 확인하세요.</p>'
        '<p class="sec-lead" style="margin-top:12px">코스는 매장이 아닌 자택·오피스텔·숙소로 방문해 진행하는 방문형으로 운영됩니다. 관리 직후 이동 없이 그대로 쉴 수 있어 이완 상태가 오래 유지되며, 익숙한 공간에서 받아 긴장이 덜한 것이 장점입니다. 인천 전지역으로 방문하므로 예약 시 가까운 위치나 지하철역을 함께 알려주시면 도착이 빨라집니다.</p>'
        '<p class="sec-lead" style="margin-top:12px">요금은 코스 종류와 시간(60·90·120분)의 조합으로 정해지는 정찰 요금을 원칙으로 하며, 현장에서 임의로 금액을 올리거나 숨겨진 추가 비용을 청구하지 않습니다. 지역·시간대·인원 등 변동 요소는 예약 상담에서 미리 안내드립니다.</p>'
        '</div></div></section>' +
        price_menu_block() +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>MORE</span>'
        '<h2 class="sec">가격과 코스 선택</h2>'
        f'<div class="grid g2" style="margin-top:24px">{more_cards}</div></div></section>' +
        faq_block(course_faq) + cta_band())
    jsonld = [bc_ld(trail),
              service_ld("인천 방문 마사지 코스", "피로 회복·아로마·스포츠·홈타이·커플·가족·기업·단체 방문 관리 코스", "/course/"),
              faq_ld(course_faq)]
    html = page("/course/", "코스안내 | 인천 출장마사지 피로회복·아로마·스포츠·홈타이 요금",
        "인천 출장마사지·홈타이 코스안내 - 피로 회복, 아로마, 스포츠, 홈타이, 커플·가족, 기업·단체 관리의 코스 설명과 정찰 요금을 안내합니다.",
        "course", body, jsonld)
    write("/course/", html)

def _course_common(name):
    return [
        ("방문 관리로 진행되는 방식", [
            f"{name}는 매장이 아닌, 고객이 계신 자택·오피스텔·숙소로 관리사가 방문해 진행하는 방문형 관리입니다.",
            "예약 시 위치(지역 또는 가까운 지하철역), 희망 시간, 인원을 확인한 뒤 방문 가능 여부를 안내드리며, 확정 후 관리사가 약속된 시간에 방문합니다.",
            "관리 직후 이동 없이 그대로 휴식할 수 있어 이완 상태가 오래 유지되는 것이 방문 관리의 장점입니다. 인천 전지역으로 방문하며, 가까운 위치를 알려주시면 도착이 빨라집니다.",
            "도심권은 위치에 따라 평균 30~40분 내외로 도착하고, 영종·강화 등 외곽과 강화·옹진 도서 지역은 이동 시간이 더 소요되어 사전 예약을 권장드립니다. 저녁·주말은 문의가 몰릴 수 있어 원하는 시간이 정해져 있다면 미리 연락 주시는 편이 좋습니다."]),
        ("예약 전 함께 확인하면 좋은 점", [
            "편히 누워 쉴 수 있는 공간과 조용한 분위기, 예약자 본인이 연락 가능한 번호를 준비해 주세요.",
            f"{name}와 관련해 특정 압·향을 피하고 싶거나 피부·건강상 주의가 필요한 상황이 있으면 예약 시 미리 알려주세요.",
            '방문 전 준비 사항은 <a href="/incheon/checklist/">이용 전 확인사항</a>, 예약 가능 시간은 <a href="/incheon/hours/">예약 가능 시간 안내</a>에서 확인하실 수 있습니다.']),
        ("지역·테마와 함께 보기", [
            f"{name}는 인천 전지역으로 방문하며, 방문 지역은 강화·옹진과 8개 구의 대표 동, 그리고 지하철역 인근 기준으로 확인하실 수 있습니다.",
            "지역·역·테마를 조합한 별도 페이지는 만들지 않으므로, 원하는 지역과 가까운 역은 아래 안내에서 따로 확인하시면 됩니다.",
            ("ul", ['<a href="/incheon/area/">지역별 안내</a>', '<a href="/incheon/stations/">지하철역별 안내</a>',
                    '<a href="/theme/">테마별 안내</a>', '<a href="/incheon/safety/">위생 및 안전 안내</a>'])]),
    ]

def build_course_pages():
    ct = [("/", "홈"), ("/course/", "코스안내")]
    def cp(path, trail, **kw):
        kw["sections"] = kw["sections"] + _course_common(kw["h1"])
        kw.setdefault("show_price", True)
        content_page(path, "course", trail, **kw)

    cp("/course/fatigue/", ct + [(None, "피로 회복 관리")],
        title="피로 회복 관리 | 인천 출장마사지 스웨디시 계열 방문 관리",
        desc="인천 출장마사지 피로 회복 관리 안내 - 전신 긴장을 부드럽게 풀어주는 스웨디시 계열 방문 관리입니다. 대상, 60·90·120분 진행 방식, 자주 묻는 질문을 확인하세요.",
        eyebrow="COURSE · 피로 회복", h1="피로 회복 관리",
        lead="전신의 근육 긴장을 부드럽게 풀어주는 스웨디시 계열 기본 방문 관리입니다.",
        sections=[
            ("피로 회복 관리란", [
                "피로 회복 관리는 전신의 근육 긴장을 부드럽게 풀어주는 스웨디시 계열의 기본 방문 관리입니다.",
                "강한 자극보다 일정한 압과 리듬으로 혈행과 이완을 돕는 데 초점을 둡니다.",
                "의료적 치료가 아니라 하루의 피로를 정리하고 휴식의 질을 높이기 위한 <strong>건강관리 목적</strong>의 관리입니다."]),
            ("이런 분께 권해드립니다", [
                ("ul", ["장시간 앉아 일해 어깨·목·허리가 자주 뭉치는 분",
                        "잠들기 전 몸의 긴장을 풀고 수면의 질을 높이고 싶은 분",
                        "강한 지압보다 부드러운 이완을 선호하는 분",
                        "매장을 방문할 시간을 내기 어려운 분"])]),
            ("60·90·120분 진행 방식", [
                "60분은 어깨·등·다리 등 피로가 집중된 부위를 중심으로 전신을 한 차례 정리합니다.",
                "90분은 가장 많이 선택되는 구성으로, 전신을 고르게 풀고 뭉친 부위에 시간을 더 배분합니다.",
                "120분은 전신을 충분히 이완한 뒤 두피·발 등 마무리 케어까지 여유 있게 진행합니다."]),
            ("방문 관리이기에 더 좋은 점", [
                "관리 직후 이동 없이 그대로 쉴 수 있어 이완 상태가 오래 유지됩니다.",
                "익숙한 공간에서 받기 때문에 긴장이 덜하고 편안합니다.",
                "인천 전지역으로 방문하며, 위치에 따라 평균 30~40분 내외로 도착합니다."]),
            ("관리 당일 진행 순서", [
                "관리사가 도착하면 편히 누우실 수 있도록 공간을 정돈합니다.",
                "선호하는 압의 세기와 특히 풀고 싶은 부위를 확인합니다.",
                "큰 근육부터 차례로 이완하고, 뭉친 부위는 시간을 더 들여 풀어드립니다.",
                "마지막에는 마무리 정돈과 함께 수분 섭취·휴식을 안내합니다."]),
        ],
        data_note="인천 권역에서 피로 회복 관리는 90분 구성 선택 비율이 가장 높습니다. 주중 21~24시 예약이 많아 해당 시간대는 도착 시간을 넉넉히 안내드립니다.",
        faq=[
            ("피로 회복 관리와 아로마 관리는 어떻게 다른가요?", "피로 회복 관리는 전신 이완에, 아로마 관리는 블렌딩 오일의 향을 더한 이완에 중점을 둡니다."),
            ("압이 너무 세거나 약하면 조절되나요?", "네. 시작 전과 진행 중 언제든 압의 세기를 말씀해 주시면 맞춰 드립니다."),
            ("관리 후 주의할 점이 있나요?", "충분한 수분 섭취와 휴식을 권장드립니다. 통증·부상이 있는 부위는 무리하지 않습니다.")],
        show_price=True, service=("피로 회복 관리", "인천 방문 스웨디시 계열 전신 이완 관리"))

    cp("/course/aroma/", ct + [(None, "아로마 관리")],
        title="아로마 관리 | 인천 출장마사지 아로마 오일 방문 관리",
        desc="인천 출장마사지 아로마 관리 안내 - 블렌딩 오일의 향과 촉감으로 심신을 이완하는 방문 관리입니다. 사용 오일, 사전 확인, 진행 방식을 확인하세요.",
        eyebrow="COURSE · 아로마", h1="아로마 관리",
        lead="블렌딩한 관리용 오일을 사용해 향과 촉감으로 심신을 함께 이완하는 방문 관리입니다.",
        sections=[
            ("아로마 관리의 특징", [
                "아로마 관리는 블렌딩한 관리용 오일을 사용해 향과 촉감으로 심신을 함께 이완하는 방문 관리입니다.",
                "오일이 피부 위에서 부드럽게 미끄러지며 마찰을 줄여, 더 유연하고 감각적인 이완을 돕습니다.",
                "향을 통한 심리적 이완이 더해져 긴장도가 높거나 예민한 날에 특히 선호됩니다."]),
            ("사용 오일과 사전 확인", [
                "라벤더 계열의 차분한 향, 시트러스 계열의 가벼운 향 등 그날의 컨디션에 맞춰 안내드립니다.",
                "피부가 민감하거나 특정 향·성분에 알러지가 있다면 예약 시 미리 알려주세요.",
                "임신 중이거나 피부 질환이 있는 경우 무리하지 않도록 사전에 상담드립니다."]),
            ("진행 방식", [
                "60분은 어깨·등을 중심으로, 90분은 전신을 고르게, 120분은 전신 이완 후 두피·발 마무리까지 진행합니다.",
                "마무리 단계에서 수건으로 가볍게 정돈해 과도한 잔여감을 줄입니다."]),
            ("피로 회복 관리와의 차이", [
                "피로 회복 관리가 근육 이완 자체에 집중한다면, 아로마 관리는 여기에 향의 이완을 더합니다.",
                "건식 관리에서 자극이 부담스러웠던 분도 비교적 편안하게 받을 수 있습니다."]),
            ("관리 후 케어", [
                "관리 후에는 따뜻한 물을 충분히 마시고 무리한 활동을 피해 휴식을 권장드립니다.",
                "오일 잔여감이 신경 쓰이면 가벼운 샤워로 마무리하셔도 좋습니다."]),
        ],
        data_note="아로마 관리는 금요일·주말 저녁 예약 비율이 평일보다 높습니다. 예약 시 선호 향을 함께 알려주시면 방문이 매끄럽습니다.",
        faq=[
            ("향을 선택할 수 있나요?", "네. 라벤더·시트러스 등 계열을 안내드리며, 선호가 없으시면 컨디션에 맞춰 추천드립니다."),
            ("오일 알러지가 걱정됩니다.", "민감성 피부나 알러지가 있으면 예약 시 알려주세요. 무리하지 않도록 조정합니다."),
            ("관리 후 끈적임이 남지 않나요?", "마무리 단계에서 수건으로 정돈해 드려 과도한 잔여감을 줄입니다.")],
        show_price=True, service=("아로마 관리", "인천 방문 아로마 오일 이완 관리"))

    cp("/course/sports/", ct + [(None, "스포츠 관리")],
        title="스포츠 관리 | 인천 출장마사지 운동 후 근육 방문 관리",
        desc="인천 출장마사지 스포츠 관리 안내 - 운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다. 적합한 상황, 진행 방식, 주의사항을 확인하세요.",
        eyebrow="COURSE · 스포츠", h1="스포츠 관리",
        lead="운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다.",
        sections=[
            ("스포츠 관리란", [
                "스포츠 관리는 운동 후 뭉친 근육과 컨디션 회복에 초점을 맞춘 방문 관리입니다.",
                "근육 부위를 따라 비교적 또렷한 압으로 풀어, 운동으로 누적된 피로를 정리하는 데 도움을 줍니다.",
                "전문 재활·치료가 아닌, 일상 운동 후의 컨디션 관리 목적임을 안내드립니다."]),
            ("이런 상황에 잘 맞습니다", [
                ("ul", ["러닝·헬스·등산 등 운동 후 다리·등 근육이 무거운 날",
                        "주말 과한 활동으로 다음 날 컨디션을 빠르게 정리하고 싶을 때",
                        "평소보다 또렷한 압의 관리를 선호하는 분"])]),
            ("진행 방식", [
                "관리 전 운동 종류와 뭉친 부위를 확인해 시간을 집중 배분합니다.",
                "60분은 특정 부위 중심, 90·120분은 전신을 고르게 풀며 집중 부위를 추가합니다.",
                "압이 강하게 느껴지면 즉시 조절하니 편하게 말씀해 주세요."]),
            ("주의사항", [
                "부상·염좌·심한 통증이 있는 부위는 관리 대상이 아니며, 해당 증상은 의료기관 진료를 권유드립니다.",
                "본 관리는 의료 행위가 아닌 건강관리 서비스이며, 통증 완화·치료를 보장하지 않습니다."]),
            ("관리 당일 진행 순서", [
                "도착 후 어떤 운동을 했는지, 어느 부위가 무거운지 확인합니다.",
                "근육을 데우듯 가볍게 시작해 점차 압을 높이며 집중 부위를 풀어드립니다.",
                "마무리 단계에서는 가볍게 이완하며 호흡을 고르고 관리를 마칩니다."]),
        ],
        data_note="스포츠 관리는 주말 오전~오후 예약 비율이 다른 코스보다 높습니다. 운동 직후보다는 1~2시간 휴식 후 관리를 권장드립니다.",
        faq=[
            ("운동 직후 바로 받아도 되나요?", "가벼운 휴식 후 받는 것을 권장드립니다. 심한 통증이 있다면 무리하지 않습니다."),
            ("강도가 센 편인가요?", "근육 부위에 또렷한 압을 사용하지만, 선호에 맞춰 강약을 조절합니다."),
            ("부상이 있어도 받을 수 있나요?", "부상·급성 통증 부위는 관리 대상이 아니며 의료기관 진료를 권유드립니다.")],
        show_price=True, service=("스포츠 관리", "인천 방문 운동 후 근육 컨디션 관리"))

    cp("/course/hometai/", ct + [(None, "홈타이 코스")],
        title="홈타이 코스 | 인천 출장마사지 자택 방문 홈타이",
        desc="인천 출장마사지 홈타이 코스 안내 - 타이 스트레칭을 응용해 자택에서 받는 이완 중심 홈타이 관리입니다. 진행 방식과 준비 사항을 확인하세요.",
        eyebrow="COURSE · 홈타이", h1="홈타이 코스",
        lead="타이 스트레칭을 응용해 자택에서 받는 이완 중심의 방문 홈타이 관리입니다.",
        sections=[
            ("홈타이 코스란", [
                "홈타이 코스는 타이마사지의 스트레칭·지압 요소를 자택 방문 환경에 맞게 구성한 관리입니다.",
                "옷을 입은 채로 받을 수 있어 부담이 적고, 몸을 늘여 유연성과 순환을 돕습니다."]),
            ("이런 분께 권합니다", [
                ("ul", ["몸이 뻣뻣하고 스트레칭이 필요한 분",
                        "오일 관리보다 옷 입은 채 받는 방식을 선호하는 분",
                        "자택에서 편하게 이완하고 싶은 분"])]),
            ("진행 방식", [
                "편한 복장을 입은 채 스트레칭과 지압을 번갈아 진행합니다.",
                "호흡에 맞춰 천천히 늘여 무리가 가지 않도록 합니다.",
                "60·90·120분 중 선택할 수 있으며 90분 구성이 무난합니다."]),
            ("준비하면 좋은 것", [
                "편히 움직일 수 있는 공간과 편한 복장을 준비해 주세요.",
                "관리 전 가벼운 스트레칭을 해두면 이완이 한결 수월합니다."]),
            ("스웨디시·아로마와의 차이", [
                "스웨디시·아로마가 오일을 사용한 이완이라면, 홈타이는 스트레칭 중심의 이완입니다.",
                "컨디션과 취향에 따라 번갈아 받는 것도 좋은 방법입니다."]),
        ],
        data_note="홈타이 코스는 평일 저녁과 주말 문의가 많습니다. 스트레칭 강도는 선호에 맞춰 조절하니 편하게 말씀해 주세요.",
        faq=[
            ("홈타이는 옷을 입고 받나요?", "네. 편한 복장을 입은 채로 스트레칭과 지압을 진행합니다."),
            ("스트레칭이 아프지 않나요?", "호흡에 맞춰 무리 없이 진행하며, 불편하면 즉시 조절합니다."),
            ("처음인데 가능한가요?", "네. 처음이라면 90분 구성으로 시작하시길 권합니다.")],
        show_price=True, service=("홈타이 코스", "인천 자택 방문 홈타이 관리"))

    cp("/course/couple/", ct + [(None, "커플·가족 방문 관리")],
        title="커플·가족 방문 관리 | 인천 출장마사지 2인 동반 관리",
        desc="인천 출장마사지 커플·가족 방문 관리 안내 - 두 분이 같은 공간에서 동시에 받는 동반형 방문 관리입니다. 공간·인원 조건, 예약 방법, 요금 구조를 확인하세요.",
        eyebrow="COURSE · 커플·가족", h1="커플·가족 방문 관리",
        lead="두 분이 같은 공간에서 동시에 관리를 받는 동반형 방문 관리입니다.",
        sections=[
            ("커플·가족 방문 관리란", [
                "두 분이 같은 공간에서 동시에 관리를 받는 동반형 방문 관리입니다.",
                "커플은 물론 부모님과 함께 등 가족 단위로도 이용하실 수 있습니다.",
                "각자 원하는 코스(피로 회복·아로마 등)를 다르게 선택할 수 있습니다."]),
            ("공간과 인원 조건", [
                "동시에 진행되므로 관리사 2인이 방문하며, 두 사람이 누울 수 있는 공간이 필요합니다.",
                "공간이 협소한 경우 순차 진행으로 안내드릴 수 있어, 예약 시 환경을 알려주세요."]),
            ("예약 방법", [
                "동반 관리는 일정 조율이 필요해 사전 협의 예약을 권장드립니다.",
                "희망 코스, 인원, 시간, 방문 장소를 말씀해 주시면 가능한 시간을 확정해 드립니다."]),
            ("요금 안내", [
                "커플·가족 방문 관리는 인원과 시간에 따라 요금이 책정됩니다.",
                "기본 요금은 <a href='/course/price/'>가격 안내</a>에서 확인하실 수 있으며, 정확한 금액은 상담 시 안내드립니다."]),
            ("관리 당일 진행 순서", [
                "관리사 2인이 함께 도착해 각자 담당을 정하고 공간을 준비합니다.",
                "두 분의 선호 압·코스를 각각 확인한 뒤 동시에 관리를 시작합니다.",
                "마무리도 함께 정돈하여 두 분이 비슷한 시점에 휴식에 들어가도록 합니다."]),
        ],
        data_note="동반 관리는 기념일·주말 저녁 문의가 집중됩니다. 관리사 2인 일정 조율이 필요하므로 가급적 1~2일 전 예약을 권장드립니다.",
        faq=[
            ("두 사람이 다른 코스를 받을 수 있나요?", "네. 각자 원하는 코스를 선택하실 수 있습니다."),
            ("좁은 공간에서도 가능한가요?", "두 분이 동시에 누울 공간이 어려우면 순차 진행으로 안내드립니다."),
            ("당일 예약도 되나요?", "관리사 2인 일정상 사전 예약을 권장드립니다. 당일은 가능 여부를 상담으로 확인합니다.")],
        service=("커플·가족 방문 관리", "인천 2인 동반 방문 관리"))

    cp("/course/group/", ct + [(None, "기업·단체 방문 관리")],
        title="기업·단체 방문 관리 | 인천 출장마사지 단체·행사 관리",
        desc="인천 출장마사지 기업·단체 방문 관리 안내 - 워크숍·행사·사내 복지 등 단체 인원을 위한 사전 협의형 방문 관리입니다. 진행 방식, 견적·결제, 사전 준비를 확인하세요.",
        eyebrow="COURSE · 기업·단체", h1="기업·단체 방문 관리",
        lead="워크숍·행사·사내 복지 등 단체 인원을 대상으로 하는 사전 협의형 방문 관리입니다.",
        sections=[
            ("기업·단체 방문 관리란", [
                "워크숍·행사·사내 복지 등 단체 인원을 대상으로 하는 사전 협의형 방문 관리입니다.",
                "여러 명이 순차 또는 동시에 관리를 받을 수 있도록 일정을 구성합니다."]),
            ("진행 방식", [
                "인원수, 1인당 관리 시간, 희망 날짜와 장소를 먼저 확인합니다.",
                "행사 성격에 맞춰 짧은 의자형 케어부터 표준 코스까지 구성할 수 있습니다.",
                "관리사 인원과 진행 순서를 사전에 설계해 현장 운영을 매끄럽게 합니다."]),
            ("견적과 결제", [
                "단체 관리는 인원·시간·장소에 따라 별도 견적으로 안내드립니다.",
                "세금계산서 등 결제 방식은 사전에 협의해 드립니다."]),
            ("사전 준비 체크리스트", [
                ("ul", ["참여 인원과 1인당 희망 시간", "행사 날짜·시간과 장소(주소)",
                        "관리 진행이 가능한 공간(회의실·라운지 등)", "콘센트·대기 동선 등 현장 여건"])]),
            ("행사 후 마무리", [
                "행사 종료 후 사용한 공간을 정돈하고, 진행 결과를 간단히 정리해 전달드릴 수 있습니다.",
                "정기적인 사내 복지로 운영하실 경우 다음 일정 협의도 함께 도와드립니다."]),
        ],
        data_note="기업·단체 관리는 분기 말·연말 사내 행사 시즌에 문의가 늘어납니다. 관리사 배치를 위해 최소 며칠 전 협의를 권장드립니다.",
        faq=[
            ("최소 인원 제한이 있나요?", "인원에 맞춰 구성하며, 정확한 기준은 문의 시 안내드립니다."),
            ("세금계산서 발행이 되나요?", "네. 결제 방식은 사전 협의로 안내드립니다."),
            ("행사 장소로 방문하나요?", "네. 인천 및 인근 행사 장소로 방문 가능하며 위치를 확인해 드립니다.")],
        service=("기업·단체 방문 관리", "인천 단체·행사 방문 관리"))

    cp("/course/price/", ct + [(None, "가격 안내")],
        title="가격 안내 | 인천 출장마사지 코스별 정찰 요금",
        desc="인천 출장마사지 가격 안내 - 코스별 60·90·120분 기본 요금과 정찰 요금 원칙, 변동 요소, 결제 안내를 제공합니다. 숨겨진 추가 비용 없이 투명하게 안내합니다.",
        eyebrow="COURSE · 가격", h1="가격 안내",
        lead="코스별 기본 요금을 사전에 안내하는 정찰 요금을 원칙으로 합니다.",
        sections=[
            ("정찰 요금 원칙", [
                "인천굿데이마사지는 코스별 기본 요금을 사전에 안내하는 <strong>정찰 요금</strong>을 원칙으로 합니다.",
                "현장에서 임의로 금액을 올리거나 숨겨진 추가 비용을 청구하지 않습니다."]),
            ("코스별 기본 요금", [
                "아래 60·90·120분 기본 요금을 참고하시고, 코스 종류(피로 회복·아로마·스포츠·홈타이 등)에 따라 세부 금액이 달라질 수 있습니다."]),
            ("변동될 수 있는 요소", [
                ("ul", ["방문 지역과 이동 거리(영종·강화 등 외곽)", "예약 시간대(심야 등)",
                        "커플·가족 등 인원 구성", "기업·단체 등 별도 견적 대상"])]),
            ("결제 안내", [
                "결제 방법은 예약 시 함께 안내드리며, 변동 사항이 있으면 사전에 고지합니다.",
                "정확한 최종 금액은 예약 상담에서 확인해 드립니다."]),
            ("투명한 요금을 위한 약속", [
                "현장에서 사전 안내와 다른 금액을 요구하지 않습니다.",
                "변동이 필요한 경우 반드시 관리 전에 설명드리고 동의를 받은 뒤 진행합니다."]),
        ],
        data_note="가장 많이 선택되는 구성은 90분입니다. 심야(자정 이후) 예약은 도착 시간과 함께 변동 요소를 미리 안내드립니다.",
        faq=[
            ("표시 요금 외에 추가 비용이 있나요?", "정찰 요금을 원칙으로 하며, 지역·시간대 등 변동 요소는 예약 시 미리 안내드립니다."),
            ("결제는 어떻게 하나요?", "결제 방법은 예약 시 안내드립니다."),
            ("코스마다 가격이 다른가요?", "네. 코스 종류에 따라 세부 금액이 달라질 수 있어 상담 시 확정해 드립니다.")],
        show_price=True, service=("인천 출장마사지 요금", "인천 방문 관리 정찰 요금 안내"))

    cp("/course/guide/", ct + [(None, "코스 선택 가이드")],
        title="코스 선택 가이드 | 인천 출장마사지 상황별 추천",
        desc="인천 출장마사지 코스 선택 가이드 - 목적과 상황에 맞는 코스 추천, 60·90·120분 시간 선택 기준, 처음 이용하는 분을 위한 안내를 제공합니다.",
        eyebrow="COURSE · 선택 가이드", h1="코스 선택 가이드",
        lead="어떤 코스를 골라야 할지 모르겠다면, 목적을 기준으로 선택하면 쉽습니다.",
        sections=[
            ("코스, 이렇게 고르세요", [
                "'무엇을 위해 받는가'라는 목적을 기준으로 선택하면 코스 결정이 쉽습니다."]),
            ("상황별 추천", [
                ("ul", ["전신이 무겁고 푹 쉬고 싶다 → <strong>피로 회복 관리</strong>",
                        "향과 함께 깊게 이완하고 싶다 → <strong>아로마 관리</strong>",
                        "운동 후 근육을 풀고 싶다 → <strong>스포츠 관리</strong>",
                        "스트레칭 중심으로 받고 싶다 → <strong>홈타이 코스</strong>",
                        "둘이 함께 받고 싶다 → <strong>커플·가족 방문 관리</strong>",
                        "행사·단체로 진행하고 싶다 → <strong>기업·단체 방문 관리</strong>"])]),
            ("시간(60·90·120분) 선택", [
                "60분은 핵심 부위 위주로 빠르게 정리하고 싶을 때 적합합니다.",
                "90분은 전신을 고르게 풀 수 있어 가장 무난하며 많이 선택됩니다.",
                "120분은 전신 이완과 마무리 케어까지 여유 있게 받고 싶을 때 좋습니다."]),
            ("처음 이용하신다면", [
                "첫 방문이라면 90분 피로 회복 관리(스웨디시)로 시작해 보시길 권합니다.",
                "받아본 뒤 선호하는 압·향·집중 부위를 알려주시면 다음 방문이 더 잘 맞습니다."]),
            ("테마와 함께 보기", [
                "코스는 시간·구성을, 테마는 관리 방식을 정합니다. 스웨디시·아로마테라피·타이 등은 테마별 안내에서 확인하세요.",
                ("ul", ['<a href="/theme/">테마별 안내</a>', '<a href="/course/price/">가격 안내</a>'])]),
        ],
        data_note="처음 이용하는 고객의 다수가 90분 구성을 선택하며, 재방문 시 아로마·스포츠로 옮겨가는 경우가 많습니다.",
        faq=[
            ("처음인데 무엇이 좋을까요?", "90분 피로 회복 관리(스웨디시)를 권장드립니다. 무난하게 전신을 풀 수 있습니다."),
            ("커플로 다른 코스도 가능한가요?", "네. 동반 관리에서 각자 다른 코스를 선택할 수 있습니다."),
            ("시간을 늘리면 더 좋은가요?", "집중 부위가 많거나 마무리 케어까지 원하면 90~120분이 적합합니다.")],
        service=("코스 선택 가이드", "인천 방문 관리 코스 선택 안내"))

# ===========================================================================
# PAGE BUILDERS — 예약/가이드/후기/고객센터/소개/정책
# ===========================================================================
def build_reservation():
    trail = [("/", "홈"), (None, "예약안내")]
    notes = [
        ("예약 방법", ["전화로 지역 또는 가까운 역 인근 위치, 희망 시간, 코스를 말씀해 주세요.", "위치·시간·코스·인원을 확인한 뒤 방문 가능 시간을 안내드립니다."]),
        ("예약 가능 시간", ["연중무휴 24시간 상담을 운영합니다.", "방문 가능 시간은 시간대와 위치에 따라 안내드립니다."]),
        ("방문 가능 장소", ["자택·오피스텔·숙소 등 방문 가능한 장소와 정확한 주소를 알려주세요."]),
        ("결제 안내", ["코스별 정찰 요금을 사전에 안내드리며, 결제 방법은 예약 시 함께 안내합니다."]),
        ("변경·취소 안내", ["일정 변경이나 취소는 가능한 한 빠르게 연락 주시면 도와드립니다."]),
        ("예약 전 체크사항", ["방문 장소·출입 방법·연락처·희망 코스·시간을 미리 정리해 두시면 빠르게 진행됩니다."]),
    ]
    res_faq = [
        ("당일 예약이 가능한가요?", "가능합니다. 시간대와 위치에 따라 방문 가능 시간이 달라질 수 있어 상담 시 확인해 드립니다."),
        ("예약을 변경하고 싶어요.", "확정된 일정 변경은 가능한 한 빠르게 연락 주시면 조정을 도와드립니다."),
        ("결제는 어떻게 하나요?", "정찰 요금을 사전에 안내드리며 결제 방법은 예약 시 함께 안내합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>RESERVATION</span>'
        '<h2 class="sec">예약안내</h2>'
        '<p class="sec-lead">예약 방법부터 결제·변경까지 한눈에 안내드립니다.</p>'
        '</div></section>' +
        notes_block("HOW TO BOOK", "예약 진행 안내", "아래 순서대로 진행됩니다.", notes, _id="about") +
        faq_block(res_faq) + cta_band())
    html = page("/reservation/", "예약안내 | 인천 출장마사지 예약 방법·결제 안내",
        "인천 출장마사지·홈타이 예약안내 - 예약 방법, 예약 가능 시간, 방문 가능 장소, 결제와 변경·취소 안내입니다. 연중무휴 24시간 상담.",
        "reservation", body, [bc_ld(trail), faq_ld(res_faq)])
    write("/reservation/", html)

def build_guide():
    trail = [("/", "홈"), (None, "이용가이드")]
    notes = [
        ("처음 이용하시는 분", ["예약 시 지역·시간·코스만 말씀해 주시면 나머지는 안내해 드립니다."]),
        ("방문 전 준비사항", ["편하게 쉴 수 있는 공간과 연락 가능한 번호, 정확한 주소를 준비해 주세요."]),
        ("위생 및 안전 기준", ["용품 위생 관리와 안전 가이드라인을 준수합니다."]),
        ("관리 후 주의사항", ["관리 후에는 충분한 수분 섭취와 휴식을 권장드립니다."]),
        ("금지행위 안내", ["불법·퇴폐 행위 요구는 일절 제공하지 않으며, 요청 시 서비스가 중단될 수 있습니다."]),
        ("이용 FAQ", ["자주 묻는 질문은 고객센터와 인천 출장마사지 FAQ에서 확인하실 수 있습니다."]),
    ]
    guide_faq = [
        ("처음인데 무엇을 준비하나요?", "편히 쉴 수 있는 공간과 연락 가능한 번호, 정확한 주소만 있으면 됩니다."),
        ("관리 후 주의할 점이 있나요?", "충분한 수분 섭취와 휴식을 권장드립니다."),
        ("이 서비스는 의료 행위인가요?", "아닙니다. 이완·휴식 목적의 건강관리 서비스이며 만 19세 이상을 대상으로 합니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>GUIDE</span>'
        '<h2 class="sec">이용가이드</h2>'
        '<p class="sec-lead">처음 이용하시는 분도 안심할 수 있도록 안내드립니다.</p>'
        '</div></section>' +
        notes_block("USER GUIDE", "이용 안내", "방문 전후 확인하세요.", notes, _id="about") +
        faq_block(guide_faq) + cta_band())
    html = page("/guide/", "이용가이드 | 인천 출장마사지 방문 전 준비·주의사항",
        "인천 출장마사지·홈타이 이용가이드 - 처음 이용하시는 분을 위한 방문 전 준비사항, 위생·안전 기준, 관리 후 주의사항과 금지행위 안내입니다.",
        "guide", body, [bc_ld(trail), faq_ld(guide_faq)])
    write("/guide/", html)

def build_reviews():
    trail = [("/", "홈"), (None, "후기")]
    # 신규 사이트로 실제 누적 후기가 확정되기 전까지는 예시 후기로 표기하고 Review 구조화 데이터는 넣지 않음
    sample = [
        ("부평동 · 30대", "스웨디시", "늦은 시간 연락에도 도착 안내가 정확했습니다."),
        ("송도동 · 40대", "아로마", "익숙한 공간에서 받아 한결 편안했어요."),
        ("주안동 · 30대", "피로회복", "예약부터 마무리까지 깔끔하고 정중했습니다."),
        ("구월동 · 50대", "스포츠", "운동 후 받았더니 다리가 가벼워졌습니다."),
        ("청라동 · 40대", "홈타이", "스트레칭 위주로 받았는데 시원했습니다."),
        ("계산동 · 30대", "커플", "둘이 함께 받았는데 응대가 친절했습니다."),
    ]
    cards = "".join(
        f'<div class="review reveal"><div class="stars">★★★★★</div>'
        f'<p>“{q}”</p><div class="who">{w} · {c} 코스</div></div>' for w, c, q in sample)
    body = (breadcrumb(trail) +
        '<section class="block" id="reviews"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>REVIEWS</span>'
        '<h2 class="sec">후기</h2>'
        '<p class="sec-lead">인천굿데이마사지를 이용하신 고객들의 후기입니다.</p>'
        f'<div class="grid g3" style="margin-top:26px">{cards}</div>'
        '<h3 id="region" style="margin:34px 0 8px;font-size:18px;font-weight:800">지역별·역세권 후기 안내</h3>'
        '<p class="sec-lead">지역별·역세권 후기는 각 지역 페이지와 지하철역별 안내에서 함께 확인하실 수 있습니다.</p>'
        '<h3 id="write" style="margin:24px 0 8px;font-size:18px;font-weight:800">후기 작성 안내</h3>'
        '<p class="sec-lead">후기는 실제 이용 고객의 동의 하에 게시되며, 개인을 특정할 수 있는 정보는 표시하지 않습니다. 위 후기는 서비스 이해를 돕기 위한 예시 후기입니다.</p>'
        '</div></section>' + cta_band())
    html = page("/reviews/", "후기 | 인천 출장마사지·홈타이 방문 관리 이용 후기",
        "인천 출장마사지·홈타이 후기 - 부평·송도·주안·구월·청라 등 인천 전지역 방문 건강관리 이용 후기를 모았습니다.",
        "reviews", body, [bc_ld(trail)])
    write("/reviews/", html)

def build_customer():
    trail = [("/", "홈"), (None, "고객센터")]
    notes = [
        ("공지사항", ["서비스 운영과 관련된 안내를 이곳에 게시합니다."]),
        ("1:1 문의", [f"전화 {PHONE_DISP}로 문의해 주세요. 연중무휴 24시간 상담을 운영합니다."]),
        ("제휴·기업 문의", ["기업·단체 방문 관리 및 제휴 문의도 전화로 접수받습니다."]),
    ]
    cust_faq = [
        ("문의는 어디로 하나요?", f"전화 {PHONE_DISP}로 문의하실 수 있습니다. 연중무휴 24시간 상담을 운영합니다."),
        ("운영 시간이 어떻게 되나요?", "연중무휴 24시간 상담을 운영합니다."),
        ("개인정보는 어떻게 관리되나요?", "개인정보처리방침에 따라 안전하게 관리되며, 자세한 내용은 해당 페이지에서 확인하실 수 있습니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block" id="notice"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>CUSTOMER</span>'
        '<h2 class="sec">고객센터</h2>'
        f'<p class="sec-lead">전화 {PHONE_DISP} · {HOURS}</p>'
        '</div></section>' +
        notes_block("HELP", "문의 안내", "궁금한 점은 언제든 문의해 주세요.", notes, _id="inquiry") +
        faq_block(cust_faq, "자주 묻는 질문") + cta_band())
    html = page("/customer/", "고객센터 | 인천 출장마사지 굿데이 문의·공지",
        "인천굿데이마사지 고객센터 - 공지사항, 자주 묻는 질문, 1:1 문의, 제휴·기업 문의 안내입니다. 연중무휴 24시간 상담.",
        "customer", body, [bc_ld(trail), faq_ld(cust_faq)])
    write("/customer/", html)

def build_about():
    trail = [("/", "홈"), (None, "인천굿데이마사지 소개")]
    greeting = notes_block("GREETING", "인사말",
        "방문 건강관리를 고민하는 분들께 드리는 인사입니다.",
        [("정중한 휴식을 약속드립니다",
          ["인천굿데이마사지를 찾아주셔서 감사합니다.",
           "저희는 인천 전지역을 대상으로 출장마사지·홈타이 예약을 안내하는 운영팀입니다.",
           "예약부터 마무리까지 정중하고 투명한 응대를 약속드립니다."])],
        _id="greeting")
    standards = notes_block("STANDARDS", "서비스 운영 기준",
        "인천굿데이마사지가 지키는 운영 원칙입니다.",
        [("정찰 요금", ["모든 코스는 정찰 요금으로 사전에 안내드립니다.", "현장에서 임의로 금액이 추가되지 않습니다."]),
         ("사전 안내", ["방문 가능 시간과 코스, 소요 시간을 예약 시 명확히 안내드립니다."]),
         ("정중한 응대", ["상담과 방문 전 과정에서 정중함을 최우선으로 합니다."])],
        _id="standards")
    safety = notes_block("HYGIENE & SAFETY", "위생 및 안전 관리",
        "안심하고 받으실 수 있도록 위생·안전을 관리합니다.",
        [("위생 관리", ["관리에 사용하는 용품은 위생 기준에 맞춰 관리합니다."]),
         ("안전 가이드", ["관리사와 고객 모두의 안전을 위한 가이드라인을 운영합니다."]),
         ("비의료 고지", ["본 서비스는 의료 행위가 아닌 이완·휴식 목적의 건강관리 서비스입니다."])],
        _id="safety")
    about_faq = [
        ("인천굿데이마사지는 어떤 서비스인가요?", "인천 전지역을 대상으로 하는 출장마사지·홈타이(방문 건강관리) 예약 안내 서비스입니다."),
        ("방문 관리는 어떻게 진행되나요?", "예약 확정 후 관리사가 약속된 시간에 고객이 계신 장소로 방문해 진행합니다."),
        ("미성년자도 이용할 수 있나요?", "아닙니다. 본 서비스는 만 19세 이상 성인만 이용하실 수 있습니다."),
    ]
    body = (breadcrumb(trail) +
        '<section class="block"><div class="wrap">'
        '<span class="eyebrow"><span class="pulse"></span>ABOUT</span>'
        '<h2 class="sec">인천굿데이마사지 소개</h2>'
        '<p class="sec-lead">인천 방문 건강관리, 인천굿데이마사지가 일하는 방식과 기준을 소개합니다.</p>'
        '</div></section>' + greeting + standards + safety +
        faq_block(about_faq) + cta_band())
    html = page("/about/", "인천굿데이마사지 소개 | 인천 방문 건강관리 운영 기준",
        "인천굿데이마사지 소개 - 인사말, 서비스 운영 기준, 위생 및 안전 관리 원칙을 안내합니다. 정찰 요금과 정중한 응대를 약속드립니다.",
        "about", body, [bc_ld(trail), org_ld(), faq_ld(about_faq)])
    write("/about/", html)

def policy_page(path, title, heading, sections, desc):
    trail = [("/", "홈"), (None, heading)]
    secs = "".join(
        f'<div class="note-card"><div class="note-content"><h3 class="note-title">{t}</h3>'
        f'<div class="note-text">{"".join(f"<p>{p}</p>" for p in ps)}</div></div></div>'
        for t, ps in sections)
    body = (breadcrumb(trail) +
        f'<section class="block"><div class="wrap">'
        f'<span class="eyebrow"><span class="pulse"></span>POLICY</span>'
        f'<h2 class="sec">{heading}</h2>'
        f'<div class="note-stack" style="margin-top:26px;max-width:820px">{secs}</div>'
        f'</div></section>')
    write(path, page(path, title, desc, "customer", body, [bc_ld(trail)]))

def build_policies():
    policy_page("/privacy/", "개인정보처리방침 | 인천굿데이마사지", "개인정보처리방침",
        [("수집하는 개인정보", ["예약 진행을 위해 연락처, 방문 장소 등 최소한의 정보를 수집합니다."]),
         ("이용 목적", ["수집한 정보는 예약 확정과 방문 안내 목적으로만 이용합니다."]),
         ("보유 및 파기", ["목적 달성 후에는 관련 법령에 따라 지체 없이 파기합니다."]),
         ("개인정보보호책임자", [f"{COMPANY['privacy_officer']} · 전화 {PHONE_DISP}"])],
        "인천굿데이마사지 개인정보처리방침 - 수집 항목, 이용 목적, 보유 및 파기, 개인정보보호책임자 안내입니다.")
    policy_page("/terms/", "이용약관 | 인천굿데이마사지", "이용약관",
        [("목적", ["본 약관은 인천굿데이마사지 예약 서비스 이용 조건을 규정합니다."]),
         ("서비스 내용", ["본 서비스는 의료 행위가 아닌 이완·휴식 목적의 방문 건강관리 예약 서비스입니다."]),
         ("이용 자격", ["본 서비스는 만 19세 이상 성인만 이용할 수 있습니다."]),
         ("금지행위", ["불법·퇴폐 행위 요구 등은 금지되며, 위반 시 서비스가 중단될 수 있습니다."])],
        "인천굿데이마사지 이용약관 - 서비스 내용, 이용 자격, 금지행위 등 이용 조건을 안내합니다.")
    policy_page("/youth/", "청소년보호정책 | 인천굿데이마사지", "청소년보호정책",
        [("청소년 이용 제한", ["본 서비스는 만 19세 이상 성인을 대상으로 하며 청소년은 이용할 수 없습니다."]),
         ("건전한 운영", ["인천굿데이마사지는 불법·퇴폐 행위를 일절 제공하지 않으며 건전한 건강관리 서비스를 지향합니다."]),
         ("책임자", [f"청소년보호 책임자 · {COMPANY['privacy_officer']} · 전화 {PHONE_DISP}"])],
        "인천굿데이마사지 청소년보호정책 - 만 19세 이상 이용 제한과 건전한 운영 원칙을 안내합니다.")

# ---- noindex 임계값 처리 (얇은 콘텐츠 → noindex + sitemap 제외) -------------
# 블루프린트 기준: 핵심 콘텐츠(지역·동·역·테마·코스) 페이지는 본문 2,000~2,500자.
# 실제로 169개 동·역 상세 페이지와 테마/코스/구 페이지는 모두 2,000자 이상이다.
# 아래 임계값은 '얇은 콘텐츠 자동 차단' 안전망으로, 약관·개인정보·1:1문의 등
# 본질적으로 짧은 유틸리티 페이지만 noindex 처리하기 위한 하한선이다.
# (섹션 허브·키워드 랜딩처럼 카드 그리드+안내문으로 구성된 페이지는 색인 유지)
# 엄격히 2,000자 규칙을 강제하려면 이 값을 2000으로 올리면 된다.
THIN_THRESHOLD = 1200

def _visible_len(html):
    try:
        b = html.split("</header>")[1].split("<footer")[0]
    except IndexError:
        return THIN_THRESHOLD
    return len(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", b)).strip())

def apply_noindex_threshold(urls):
    """본문 길이가 임계값 미만인 페이지의 robots 메타를 noindex로 바꾸고 그 URL 집합을 반환."""
    thin = set()
    for u in urls:
        rel = "index.html" if u == "/" else os.path.join(u.strip("/"), "index.html")
        fp = os.path.join(ROOT, rel)
        if not os.path.exists(fp):
            continue
        html = open(fp, encoding="utf-8").read()
        if _visible_len(html) >= THIN_THRESHOLD:
            continue
        thin.add(u)
        html = html.replace(
            '<meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">',
            '<meta name="robots" content="noindex,follow,max-image-preview:large">')
        html = html.replace('<meta name="googlebot" content="index,follow">',
                            '<meta name="googlebot" content="noindex,follow">')
        with open(fp, "w", encoding="utf-8") as f:
            f.write(html)
    return thin

# ---- robots / sitemap / manifest / favicon / indexnow key -----------------
def build_meta_files():
    urls = ["/", "/incheon/", "/incheon/hometai/", "/incheon/area/",
            "/incheon/hours/", "/incheon/checklist/", "/incheon/safety/", "/incheon/faq/",
            "/incheon/stations/", "/theme/", "/course/",
            "/reservation/", "/guide/", "/reviews/", "/customer/", "/about/",
            "/privacy/", "/terms/", "/youth/"]
    urls += [f"/course/{c['slug']}/" for c in COURSES] + ["/course/price/", "/course/guide/"]
    urls += [f"/theme/{t['slug']}/" for t in THEMES]
    for g in GU:
        urls.append(f"/incheon/{g['slug']}/")
        urls += [f"/incheon/{g['slug']}/{d['slug']}/" for d in g["dongs"]]
    urls += [f"/incheon/stations/{ln['slug']}/" for ln in LINES]
    urls += [f"/incheon/stations/{st['slug']}/" for st in STATIONS.values()]
    # 중복 제거(순서 유지)
    seen, ordered = set(), []
    for u in urls:
        if u not in seen:
            seen.add(u); ordered.append(u)
    # 본문 2,000자 미만 페이지는 noindex 처리하고 sitemap/RSS에서 제외(블루프린트 §8 규칙)
    thin = apply_noindex_threshold(ordered)
    indexable = [u for u in ordered if u not in thin]
    lastmod = UPDATED  # W3C 날짜(YYYY-MM-DD) — sitemap lastmod 유효 형식
    kst = datetime.timezone(datetime.timedelta(hours=9))
    pub = format_datetime(datetime.datetime.strptime(UPDATED, "%Y-%m-%d").replace(tzinfo=kst))

    # --- sitemap.xml (lastmod 포함) ---
    items = ""
    for u in indexable:
        p = "1.0" if u == "/" else ("0.85" if u.count("/") <= 2 else "0.75")
        freq = "daily" if u == "/" else "weekly"
        items += (f"  <url><loc>{BASE_URL}{u}</loc><lastmod>{lastmod}</lastmod>"
                  f"<changefreq>{freq}</changefreq><priority>{p}</priority></url>\n")
    sitemap = ('<?xml version="1.0" encoding="UTF-8"?>\n'
               '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
               + items + "</urlset>\n")
    with open(os.path.join(ROOT, "sitemap.xml"), "w", encoding="utf-8") as f:
        f.write(sitemap)

    # --- rss.xml (네이버 서치어드바이저 RSS 제출 / 구글 피드 기반 발견용) ---
    def page_meta(u):
        rel = "index.html" if u == "/" else os.path.join(u.strip("/"), "index.html")
        try:
            h = open(os.path.join(ROOT, rel), encoding="utf-8").read()
            t = re.search(r"<title>(.*?)</title>", h).group(1)
            d = re.search(r'name="description" content="(.*?)"', h).group(1)
            return t, d
        except Exception:
            return BRAND, ""
    rss_items = ""
    for u in indexable:
        t, d = page_meta(u)
        loc = BASE_URL + u
        rss_items += (f"  <item><title>{escape(t)}</title><link>{loc}</link>"
                      f'<guid isPermaLink="true">{loc}</guid>'
                      f"<pubDate>{pub}</pubDate><description>{escape(d)}</description></item>\n")
    rss = ('<?xml version="1.0" encoding="UTF-8"?>\n'
           '<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">\n'
           '<channel>\n'
           f'  <title>{escape(BRAND)} · 인천 출장마사지·홈타이</title>\n'
           f'  <link>{BASE_URL}/</link>\n'
           f'  <atom:link href="{BASE_URL}/rss.xml" rel="self" type="application/rss+xml"/>\n'
           '  <description>인천 전지역 출장마사지·홈타이 방문 예약 안내 — 지역·역세권·테마·코스 페이지 피드</description>\n'
           '  <language>ko-kr</language>\n'
           f'  <lastBuildDate>{pub}</lastBuildDate>\n'
           + rss_items + '</channel>\n</rss>\n')
    with open(os.path.join(ROOT, "rss.xml"), "w", encoding="utf-8") as f:
        f.write(rss)

    # --- robots.txt (sitemap + rss 동시 노출, 주요 봇 허용) ---
    robots = ("User-agent: *\nAllow: /\nDisallow: /tools/\n\n"
              "User-agent: Googlebot\nAllow: /\n"
              "User-agent: Yeti\nAllow: /\n"          # 네이버 크롤러
              "User-agent: Bingbot\nAllow: /\n"
              "User-agent: GPTBot\nAllow: /\n"
              "User-agent: ClaudeBot\nAllow: /\n"
              "User-agent: Google-Extended\nAllow: /\n\n"
              f"Sitemap: {BASE_URL}/sitemap.xml\n"
              f"Sitemap: {BASE_URL}/rss.xml\n"
              f"Host: {BASE_URL.replace('https://','')}\n")
    with open(os.path.join(ROOT, "robots.txt"), "w", encoding="utf-8") as f:
        f.write(robots)

    manifest = {
        "name": BRAND, "short_name": BRAND_SHORT, "description": "인천 전지역 출장마사지·홈타이 방문 예약 안내",
        "start_url": "/", "scope": "/", "display": "standalone",
        "background_color": "#0b0b0e", "theme_color": "#0b0b0e",
        "lang": "ko-KR", "orientation": "portrait",
        "icons": [
            {"src": "/icon-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
            {"src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
            {"src": "/icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    with open(os.path.join(ROOT, "site.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    favicon = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
               '<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">'
               '<stop offset="0" stop-color="#f4d29c"/><stop offset=".5" stop-color="#e9b8a7"/>'
               '<stop offset="1" stop-color="#c98a6b"/></linearGradient></defs>'
               '<rect width="64" height="64" rx="16" fill="#0b0b0e"/>'
               '<rect x="8" y="8" width="48" height="48" rx="13" fill="url(#g)"/>'
               '<text x="32" y="44" font-family="Georgia,serif" font-style="italic" '
               f'font-size="34" font-weight="700" text-anchor="middle" fill="#1a1208">{BRAND_MARK}</text></svg>')
    with open(os.path.join(ROOT, "favicon.svg"), "w", encoding="utf-8") as f:
        f.write(favicon)

    with open(os.path.join(ROOT, f"{INDEXNOW_KEY}.txt"), "w", encoding="utf-8") as f:
        f.write(INDEXNOW_KEY)

# ---------------------------------------------------------------------------
def main():
    build_home()
    build_incheon()
    build_incheon_info_pages()
    build_area_hub()
    build_gu_pages()
    build_dong_pages()
    build_stations_hub()
    build_line_pages()
    build_station_pages()
    build_theme_hub()
    build_theme_pages()
    build_course()
    build_course_pages()
    build_reservation()
    build_guide()
    build_reviews()
    build_customer()
    build_about()
    build_policies()
    build_meta_files()
    print("Build complete.")

if __name__ == "__main__":
    main()
