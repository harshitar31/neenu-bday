# """
# analyze.py — WhatsApp Wrapped  "BROADCAST" edition
# No cards. No glass. Pure editorial. Each section is its own world.
# """
# import json, re, random, math
# from collections import Counter, defaultdict
# from datetime import datetime
# import numpy as np

# try:    import emoji as emoji_lib;  HAS_EMOJI = True
# except: HAS_EMOJI = False
# try:
#     from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
#     sia = SentimentIntensityAnalyzer(); HAS_VADER = True
# except: HAS_VADER = False

# HER      = "Niranjana"
# YOU      = "Harshita"
# JSONL_IN = "chats_clean.jsonl"
# HTML_OUT = "niranjana_wrapped.html"

# STOPWORDS = {
#     "i","you","the","a","to","and","is","it","in","of","that","this","my","me",
#     "we","for","be","with","on","are","was","have","do","not","but","so","if",
#     "or","an","at","can","will","just","what","how","its","yeah","yea","ok",
#     "okay","no","yes","don","like","get","got","go","going","know","one","also",
#     "lol","haha","hahaha","lmao","omg","tbh","idk","ik","rn","bc","tho","btw",
#     "ur","u","r","m","s","k","n","he","she","they","his","her","him","them",
#     "all","out","up","about","from","by","as","more","been","has","had","would",
#     "could","should","did","does","there","when","who","which","then","than",
#     "too","even","back","much","well","really","now","some","any","our","your",
#     "their","here","think","need","want","see","i'm","i've","i'll","don't",
#     "can't","won't","didn't","doesn't","isn't","wasn't","we're","they're",
#     "let","let's","come","said","say","tell","told","give","make","put","take",
#     "made","came","went","into","after","before","until","while","use","used",
#     "still","though","only","first","last","new","old","many","most","other",
#     "same","down","over","where","why","am","being","been","de","la","na","da",
#     "ya","nah","oh","ah","uh","yep","nope","sure","wait","else","maybe","might",
#     "fr","bro","man","girl","hey","hi","hello","bye","wow","send","sent","chat",
#     "text","msg","call","called","gonna","wanna","gotta","kinda","cuz","ngl",
#     "istg","imo","smh","hm","hmm","ohh","ugh","actually","literally","basically",
# }

# def load(path):
#     rows = []
#     with open(path, encoding="utf-8") as f:
#         for line in f:
#             line = line.strip()
#             if not line: continue
#             try: rows.append(json.loads(line))
#             except:
#                 try: rows.append(eval(line))
#                 except: pass
#     return rows

# def parse_dt(row):
#     d, t = row["date"], row["time"]
#     for fmt in ("%d/%m/%y %I:%M:%S %p","%m/%d/%y %I:%M:%S %p",
#                 "%d/%m/%y %I:%M %p",  "%m/%d/%y %I:%M %p"):
#         try: return datetime.strptime(f"{d} {t}", fmt)
#         except: pass
#     return None

# def basic_stats(her, all_msgs):
#     total = len(her)
#     words = sum(len(m["message"].split()) for m in her)
#     days  = sorted(set(m["_dt"].date() for m in her if m["_dt"]))
#     streak = ms = 1
#     for i in range(1, len(days)):
#         if (days[i]-days[i-1]).days == 1: streak += 1; ms = max(ms,streak)
#         else: streak = 1
#     return {"total":total,"words":words,
#             "avg_len":round(words/max(total,1),1),
#             "active_days":len(days),"streak":ms,
#             "share":round(100*total/max(len(all_msgs),1))}

# def peak_hour(msgs):
#     hours = Counter(m["_dt"].hour for m in msgs if m["_dt"])
#     if not hours: return {}
#     total = sum(hours.values())
#     bkts  = {"morning":0,"afternoon":0,"evening":0,"night":0}
#     for h,c in hours.items():
#         if   6<=h<12:  bkts["morning"]   +=c
#         elif 12<=h<18: bkts["afternoon"] +=c
#         elif 18<=h<22: bkts["evening"]   +=c
#         else:          bkts["night"]     +=c
#     peak = hours.most_common(1)[0][0]
#     pb   = max(bkts, key=bkts.get)
#     h12  = peak%12 or 12
#     ampm = "AM" if peak<12 else "PM"
#     # hour bars for radial chart
#     bars = {str(h):v for h,v in sorted(hours.items())}
#     return {"label":f"{h12}{ampm}","hour24":peak,
#             "bucket":pb,"bucket_pct":round(100*bkts[pb]/total),
#             "bars":bars}

# def reply_speed(all_msgs, her, you):
#     deltas = []
#     for i,m in enumerate(all_msgs):
#         if m["sender"]==her and m["_dt"]:
#             for j in range(i-1,max(i-20,-1),-1):
#                 p=all_msgs[j]
#                 if p["sender"]==you and p["_dt"]:
#                     d=(m["_dt"]-p["_dt"]).total_seconds()
#                     if 0<d<86400: deltas.append(d)
#                     break
#     if not deltas: return {"avg":"?","fastest":"?","p90":"?","total":0}
#     def fmt(s):
#         s=int(s)
#         if s<60:   return f"{s}s"
#         if s<3600: return f"{s//60}m {s%60}s"
#         return f"{s//3600}h {(s%3600)//60}m"
#     return {"avg":fmt(np.mean(deltas)),"fastest":fmt(min(deltas)),
#             "p90":fmt(np.percentile(deltas,90)),"total":len(deltas),
#             "avg_raw":int(np.mean(deltas))}

# def emoji_personality(msgs):
#     if not HAS_EMOJI: return {"top":[],"by_year":{},"total":0}
#     all_e,by_year=[],defaultdict(list)
#     for m in msgs:
#         found=[c["emoji"] for c in emoji_lib.emoji_list(m["message"])]
#         all_e.extend(found)
#         if m["_dt"]: by_year[str(m["_dt"].year)].extend(found)
#     return {"top":    [{"emoji":e,"count":c} for e,c in Counter(all_e).most_common(8)],
#             "by_year":{yr:[{"emoji":e,"count":c} for e,c in Counter(em).most_common(4)]
#                        for yr,em in sorted(by_year.items())},
#             "total":len(all_e)}

# def burst_vs_essay(msgs):
#     bursts,solos,bl,sl=0,0,[],[]
#     i=0
#     while i<len(msgs):
#         m=msgs[i]
#         if not m["_dt"]: i+=1; continue
#         if i+1<len(msgs) and msgs[i+1]["_dt"]:
#             gap=(msgs[i+1]["_dt"]-m["_dt"]).total_seconds()
#             if 0<=gap<=90: bursts+=1;bl.append(len(m["message"].split()));i+=1;continue
#         solos+=1;sl.append(len(m["message"].split()));i+=1
#     tot=bursts+solos
#     return {"burst_pct":round(100*bursts/tot) if tot else 0,
#             "avg_burst":round(np.mean(bl),1) if bl else 0,
#             "avg_solo": round(np.mean(sl),1) if sl else 0}

# def slang_era(msgs):
#     by_year=defaultdict(list)
#     for m in msgs:
#         if m["_dt"]:
#             words=[w for w in re.findall(r"[a-z']+",m["message"].lower())
#                    if w not in STOPWORDS and len(w)>2]
#             by_year[m["_dt"].year].extend(words)
#     years=sorted(by_year)
#     if len(years)<2: return {"eras":[]}
#     eras=[]
#     for yr in years:
#         this=Counter(by_year[yr]); other=Counter()
#         for y2 in years:
#             if y2!=yr: other.update(by_year[y2])
#         unique=[w for w,c in this.most_common(300)
#                 if c>=3 and c/(other.get(w,0)+1)>=1.8][:5]
#         eras.append({"year":str(yr),"words":unique})
#     return {"eras":eras}

# def mood_timeline(msgs):
#     if not HAS_VADER: return {"months":[]}
#     by_month=defaultdict(list)
#     for m in msgs:
#         if m["_dt"] and len(m["message"].split())>=2:
#             by_month[m["_dt"].strftime("%Y-%m")].append(
#                 sia.polarity_scores(m["message"])["compound"])
#     months=[]
#     for k in sorted(by_month):
#         avg=round(np.mean(by_month[k]),3)
#         months.append({"key":k,
#                        "label":datetime.strptime(k,"%Y-%m").strftime("%b %y"),
#                        "score":avg})
#     return {"months":months}

# def whats_in_her_head(msgs):
#     words,bigrams=[],[]
#     for m in msgs:
#         ww=[w for w in re.findall(r"[a-z']+",m["message"].lower())
#             if w not in STOPWORDS and len(w)>2]
#         words.extend(ww)
#         for j in range(len(ww)-1): bigrams.append(f"{ww[j]} {ww[j+1]}")
#     tw=Counter(words).most_common(14)
#     tb=[(b,c) for b,c in Counter(bigrams).most_common(40) if c>=3][:6]
#     return {"top_words":  [{"word":w,"count":c} for w,c in tw],
#             "top_bigrams":[{"phrase":b,"count":c} for b,c in tb]}

# def chaos_score(m):
#     t=m["message"]
#     caps=sum(1 for c in t if c.isupper())/max(len(t),1)
#     rep=len(re.findall(r'(.)\1{2,}',t))
#     excl=t.count('!')+t.count('?')
#     emoj=len(emoji_lib.emoji_list(t)) if HAS_EMOJI else 0
#     bonus=1.5 if 1<=len(t.split())<=6 else 1.0
#     return (caps*10+rep*3+excl*2+emoj*1.5)*bonus

# def most_chaotic(msgs):
#     scored=[(chaos_score(m),m) for m in msgs
#             if len(m["message"].strip())>1
#             and "missed" not in m["message"].lower()
#             and "deleted" not in m["message"].lower()]
#     scored.sort(key=lambda x:-x[0])
#     top,seen=[],set()
#     for _,m in scored:
#         t=m["message"].strip()
#         if t in seen: continue
#         seen.add(t); top.append({"message":t[:100]})
#         if len(top)>=5: break
#     return {"top":top}

# # ── radial hour chart SVG ─────────────────────────────────────────────────────
# def radial_hours_svg(bars, peak_h24):
#     if not bars: return ""
#     W=220; cx=W//2; cy=W//2; r_out=90; r_in=34
#     max_v = max(bars.values()) if bars else 1
#     paths=""
#     for h in range(24):
#         v = bars.get(str(h), 0)
#         ang = math.radians(h*(360/24) - 90)
#         r_bar = r_in + (r_out-r_in)*(v/max_v)
#         x1=cx+r_in*math.cos(ang); y1=cy+r_in*math.sin(ang)
#         x2=cx+r_bar*math.cos(ang); y2=cy+r_bar*math.sin(ang)
#         is_peak = (h==peak_h24)
#         col="#FF6040" if is_peak else "#E8C060" if v/max_v>0.5 else "rgba(232,192,96,0.3)"
#         sw=4 if is_peak else 2.5
#         paths+=f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{col}" stroke-width="{sw}" stroke-linecap="round"/>'
#     # labels 12, 6
#     labels=(f'<text x="{cx}" y="10" text-anchor="middle" fill="rgba(232,220,200,0.3)" font-size="9" font-family="Space Mono,monospace">12</text>'
#             f'<text x="{cx}" y="{W-2}" text-anchor="middle" fill="rgba(232,220,200,0.3)" font-size="9" font-family="Space Mono,monospace">12</text>'
#             f'<text x="4" y="{cy+3}" text-anchor="start" fill="rgba(232,220,200,0.3)" font-size="9" font-family="Space Mono,monospace">18</text>'
#             f'<text x="{W-4}" y="{cy+3}" text-anchor="end" fill="rgba(232,220,200,0.3)" font-size="9" font-family="Space Mono,monospace">06</text>')
#     return f'<svg viewBox="0 0 {W} {W}" width="{W}" height="{W}" style="overflow:visible">{paths}<circle cx="{cx}" cy="{cy}" r="{r_in}" fill="none" stroke="rgba(232,192,96,0.08)" stroke-width="1"/>{labels}</svg>'

# # ── mood spark SVG ─────────────────────────────────────────────────────────────
# def mood_spark_svg(mood):
#     months=mood.get("months",[])
#     if len(months)<2: return ""
#     W=520; H=110; pad=16
#     sc=[m["score"] for m in months]
#     mn,mx=min(sc),max(sc); rng=max(mx-mn,0.1)
#     def px(i): return pad+i*(W-2*pad)/(len(months)-1)
#     def py(s): return H-pad-(s-mn)/rng*(H-2*pad)
#     pts=[(px(i),py(m["score"])) for i,m in enumerate(months)]
#     # smooth path
#     path=f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
#     for i in range(1,len(pts)):
#         x0,y0=pts[i-1]; x1,y1=pts[i]; cx2=(x0+x1)/2
#         path+=f" C{cx2:.1f},{y0:.1f} {cx2:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
#     fill=path+f" L{pts[-1][0]:.1f},{H} L{pts[0][0]:.1f},{H} Z"
#     # highlight best/worst
#     bi=sc.index(max(sc)); wi=sc.index(min(sc))
#     annots=""
#     if len(pts)>bi: annots+=f'<circle cx="{pts[bi][0]:.1f}" cy="{pts[bi][1]:.1f}" r="4" fill="#60C860"/><text x="{pts[bi][0]:.1f}" y="{pts[bi][1]-9:.1f}" text-anchor="middle" font-size="8" fill="#60C860" font-family="Space Mono,monospace">{months[bi]["label"]}</text>'
#     if len(pts)>wi: annots+=f'<circle cx="{pts[wi][0]:.1f}" cy="{pts[wi][1]:.1f}" r="4" fill="#6080C8"/><text x="{pts[wi][0]:.1f}" y="{pts[wi][1]+16:.1f}" text-anchor="middle" font-size="8" fill="#6080C8" font-family="Space Mono,monospace">{months[wi]["label"]}</text>'
#     return (f'<svg viewBox="0 0 {W} {H}" width="100%" style="overflow:visible;max-width:{W}px">'
#             f'<defs><linearGradient id="sfill" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#E8C060" stop-opacity="0.18"/><stop offset="100%" stop-color="#E8C060" stop-opacity="0"/></linearGradient></defs>'
#             f'<path d="{fill}" fill="url(#sfill)"/>'
#             f'<path d="{path}" fill="none" stroke="#E8C060" stroke-width="1.5" stroke-linecap="round"/>'
#             f'{annots}</svg>')

# # ── marquee text builder ──────────────────────────────────────────────────────
# def marquee_words(top):
#     words=[t["word"] for t in top.get("top_words",[])[:12]]
#     if not words: words=["..."]
#     segment=" · ".join(w.upper() for w in words)+" · "
#     return (segment*4).strip()

# # ── build HTML ─────────────────────────────────────────────────────────────────
# def build_html(s):
#     name=s["name"]; first=name.split()[0]
#     b=s["basic"]; ph=s["peak"]; rep=s["reply"]
#     em=s["emoji"]; bur=s["burst"]; sl=s["slang"]
#     mood=s["mood"]; top=s["topics"]; chaos=s["chaos"]
#     yr=str(datetime.now().year)

#     # radial chart
#     radial_svg = radial_hours_svg(ph.get("bars",{}), ph.get("hour24",0))

#     # mood spark
#     spark_svg = mood_spark_svg(mood)

#     # marquee
#     mq_text = marquee_words(top)

#     # emoji film strip HTML
#     emoji_strip=""
#     for e in em.get("top",[])[:8]:
#         emoji_strip+=f'<div class="film-frame"><span class="film-emoji">{e["emoji"]}</span><span class="film-count">{e["count"]}</span></div>'

#     # emoji era rows
#     era_rows=""
#     for yr2,items in em.get("by_year",{}).items():
#         glyphs="".join(x["emoji"] for x in items[:4])
#         era_rows+=f'<div class="era-row"><span class="era-yr">{yr2}</span><span class="era-em">{glyphs}</span></div>'

#     # slang
#     slang_blocks=""
#     for e in sl.get("eras",[]):
#         if not e["words"]: continue
#         pills="".join(f'<span class="tag">{w}</span>' for w in e["words"])
#         slang_blocks+=f'<div class="slang-line"><span class="slang-yr">{e["year"]}</span><span class="slang-pills">{pills}</span></div>'
#     if not slang_blocks: slang_blocks='<span style="opacity:0.3;font-size:13px">need more data across years</span>'

#     # word cloud lines (sorted by size)
#     tw=top.get("top_words",[])
#     wcloud_html=""
#     if tw:
#         mc=tw[0]["count"]
#         for t in tw[:12]:
#             sz=int(24+(t["count"]/mc)*60)
#             op=round(0.28+(t["count"]/mc)*0.72,2)
#             wcloud_html+=f'<span class="wc-word" style="font-size:{sz}px;opacity:{op}">{t["word"]}</span>'

#     # bigrams
#     bgrams="".join(f'<span class="tag">"{bg["phrase"]}"</span>' for bg in top.get("top_bigrams",[])[:5])

#     # chaos — staggered
#     random.seed(7)
#     film_holes=''.join('<div class="film-hole"></div>' * 16)
#     chaos_items=""
#     for i,m in enumerate(chaos.get("top",[])[:5]):
#         rot=random.uniform(-1.8,1.8)
#         chaos_items+=f'<div class="chaos-line" style="--r:{rot:.1f}deg;--i:{i}">"{m["message"]}"</div>'

#     return HTML_TEMPLATE.format(
#         FIRST=first, NAME=name, YEAR=yr,
#         TOTAL=f"{b['total']:,}", WORDS=f"{b['words']:,}",
#         AVG_LEN=str(b['avg_len']), DAYS=str(b['active_days']),
#         STREAK=str(b['streak']), SHARE=str(b['share']),
#         PEAK_LABEL=ph.get("label","?"),
#         PEAK_BUCKET=ph.get("bucket","night"),
#         PEAK_PCT=str(ph.get("bucket_pct",0)),
#         RADIAL_SVG=radial_svg,
#         REPLY_AVG=rep.get("avg","?"),
#         REPLY_FAST=rep.get("fastest","?"),
#         REPLY_P90=rep.get("p90","?"),
#         REPLY_TOTAL=f"{rep.get('total',0):,}",
#         EMOJI_STRIP=emoji_strip,
#         ERA_ROWS=era_rows,
#         EMOJI_TOTAL=str(em.get("total",0)),
#         BURST_PCT=str(bur["burst_pct"]),
#         BURST_AVG=str(bur["avg_burst"]),
#         SOLO_AVG=str(bur["avg_solo"]),
#         SLANG_BLOCKS=slang_blocks,
#         SPARK_SVG=spark_svg,
#         WCLOUD_HTML=wcloud_html,
#         BGRAMS=bgrams,
#         CHAOS_ITEMS=chaos_items,
#         MQ_TEXT=mq_text,
#         TOTAL_RAW=b['total'], WORDS_RAW=b['words'],
#         FILM_HOLES=film_holes,
#     )

# # ══════════════════════════════════════════════════════════════════════════════
# # TEMPLATE
# # ══════════════════════════════════════════════════════════════════════════════
# HTML_TEMPLATE = """<!DOCTYPE html>
# <html lang="en">
# <head>
# <meta charset="UTF-8">
# <meta name="viewport" content="width=device-width,initial-scale=1">
# <title>{FIRST}'s Wrapped</title>
# <link rel="preconnect" href="https://fonts.googleapis.com">
# <link href="https://fonts.googleapis.com/css2?family=Unbounded:wght@300;400;700;900&family=Instrument+Serif:ital@0;1&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
# <style>
# *,*::before,*::after{{box-sizing:border-box;margin:0;padding:0}}
# :root{{
#   --ink:#060608;
#   --paper:#F0EAE0;
#   --gold:#D4A840;
#   --hot:#FF4830;
#   --cool:#3860C8;
#   --mint:#28B88A;
#   --lav:#9060D8;
#   --un:'Unbounded',sans-serif;
#   --serif:'Instrument Serif',Georgia,serif;
#   --mono:'Space Mono',monospace;
# }}
# html{{scroll-behavior:smooth;background:var(--ink)}}
# body{{font-family:var(--mono);overflow-x:hidden;color:var(--paper)}}

# /* ── grain ── */
# body::after{{content:'';position:fixed;inset:0;z-index:999;pointer-events:none;
#   background:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.032'/%3E%3C/svg%3E");}}

# /* ══════════════════════════════════════
#    SLIDE SYSTEM
# ══════════════════════════════════════ */
# .slide{{
#   min-height:100vh;
#   width:100%;
#   display:flex;
#   flex-direction:column;
#   justify-content:center;
#   position:relative;
#   overflow:hidden;
#   padding:60px clamp(24px,5vw,80px);
# }}

# /* reveal */
# .rx{{opacity:0;transform:translateY(40px);transition:opacity .8s cubic-bezier(.16,1,.3,1),transform .8s cubic-bezier(.16,1,.3,1)}}
# .rx.in{{opacity:1;transform:none}}
# .rx.d1{{transition-delay:.1s}}.rx.d2{{transition-delay:.22s}}
# .rx.d3{{transition-delay:.34s}}.rx.d4{{transition-delay:.46s}}
# .rx.d5{{transition-delay:.58s}}

# /* ══════════════════════════════════════
#    0 — COVER
# ══════════════════════════════════════ */
# #s0{{background:var(--ink);justify-content:flex-end;padding-bottom:80px}}

# .cover-bg-name{{
#   position:absolute;
#   top:50%; left:50%; transform:translate(-50%,-54%);
#   font-family:var(--un);font-weight:900;
#   font-size:clamp(22vw,28vw,38vw);
#   line-height:0.82;
#   color:rgba(240,234,224,0.032);
#   letter-spacing:-0.04em;
#   white-space:nowrap;
#   pointer-events:none;user-select:none;
# }}
# .cover-tag{{
#   font-family:var(--mono);font-size:11px;
#   letter-spacing:.22em;text-transform:uppercase;
#   color:rgba(240,234,224,0.3);
#   margin-bottom:32px;
# }}
# .cover-headline{{
#   font-family:var(--un);font-weight:900;
#   font-size:clamp(14vw,18vw,22vw);
#   line-height:0.86;
#   letter-spacing:-0.03em;
#   background:linear-gradient(160deg,#F0EAE0 40%,#D4A840 100%);
#   -webkit-background-clip:text;background-clip:text;
#   -webkit-text-fill-color:transparent;
# }}
# .cover-sub{{
#   font-family:var(--serif);font-style:italic;
#   font-size:clamp(18px,3vw,28px);
#   color:rgba(240,234,224,0.45);
#   margin-top:20px;
# }}
# .cover-scroll{{
#   position:absolute;right:clamp(24px,5vw,80px);bottom:60px;
#   writing-mode:vertical-lr;
#   font-size:10px;letter-spacing:.2em;
#   color:rgba(240,234,224,0.2);
#   animation:bob 2.5s ease-in-out infinite;
# }}
# @keyframes bob{{0%,100%{{transform:translateY(0)}}50%{{transform:translateY(8px)}}}}

# /* ══════════════════════════════════════
#    1 — NUMBERS  (split layout)
# ══════════════════════════════════════ */
# #s1{{background:var(--ink);padding:0}}
# .s1-inner{{
#   display:grid;grid-template-columns:1fr 1fr;
#   min-height:100vh;width:100%;
# }}
# .s1-left{{
#   background:#D4A840;
#   display:flex;flex-direction:column;
#   justify-content:flex-end;
#   padding:clamp(32px,5vw,72px);
#   position:relative;overflow:hidden;
# }}
# .s1-big{{
#   font-family:var(--un);font-weight:900;
#   font-size:clamp(18vw,14vw,22vw);
#   line-height:0.82;
#   color:rgba(6,6,8,0.18);
#   position:absolute;top:0;left:-0.05em;
#   letter-spacing:-0.04em;
#   pointer-events:none;
# }}
# .s1-num{{
#   font-family:var(--un);font-weight:900;
#   font-size:clamp(56px,11vw,120px);
#   line-height:0.9;color:#060608;
#   position:relative;z-index:2;
# }}
# .s1-label{{
#   font-family:var(--serif);font-style:italic;
#   font-size:clamp(16px,2.5vw,22px);
#   color:rgba(6,6,8,0.55);
#   margin-top:10px;position:relative;z-index:2;
# }}
# .s1-right{{
#   display:flex;flex-direction:column;justify-content:center;
#   padding:clamp(32px,5vw,72px);gap:32px;
# }}
# .mini-stat .mv{{font-family:var(--un);font-weight:700;
#   font-size:clamp(28px,4.5vw,52px);color:var(--gold)}}
# .mini-stat .ml{{font-size:10px;letter-spacing:.14em;text-transform:uppercase;
#   color:rgba(240,234,224,0.35);margin-top:4px}}
# .s1-rule{{width:40px;height:2px;background:rgba(212,168,64,0.3)}}
# .share-note{{font-size:12px;color:rgba(240,234,224,0.32);line-height:1.8}}
# @media(max-width:600px){{
#   .s1-inner{{grid-template-columns:1fr}}
#   .s1-left{{min-height:50vh}}
#   .s1-right{{min-height:50vh}}
# }}

# /* ══════════════════════════════════════
#    2 — PEAK HOUR  (full bleed + radial)
# ══════════════════════════════════════ */
# #s2{{background:#0C0C18}}
# .s2-kicker{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(255,72,48,0.6);margin-bottom:28px}}
# .s2-layout{{display:flex;align-items:center;gap:clamp(24px,6vw,80px);flex-wrap:wrap}}
# .s2-left{{flex:1;min-width:200px}}
# .s2-hour{{
#   font-family:var(--un);font-weight:900;
#   font-size:clamp(72px,16vw,160px);
#   line-height:0.82;
#   color:var(--hot);
#   letter-spacing:-0.04em;
# }}
# .s2-desc{{font-family:var(--serif);font-style:italic;
#   font-size:clamp(16px,2.4vw,22px);color:rgba(240,234,224,0.5);margin-top:14px}}
# .s2-pct{{font-family:var(--un);font-weight:700;font-size:38px;color:var(--paper);margin-top:20px}}
# .s2-pct-label{{font-size:11px;letter-spacing:.14em;color:rgba(240,234,224,0.3)}}
# .s2-right{{flex-shrink:0;opacity:0.9}}
# /* horizontal rule accent */
# .accent-rule{{display:flex;align-items:center;gap:12px;margin-bottom:24px}}
# .accent-rule span{{flex:1;height:1px;background:rgba(255,72,48,0.2)}}
# .accent-rule i{{font-family:var(--mono);font-style:normal;font-size:10px;color:rgba(255,72,48,0.5);letter-spacing:.1em}}

# /* ══════════════════════════════════════
#    3 — REPLY SPEED  (three-column ticker)
# ══════════════════════════════════════ */
# #s3{{background:var(--ink)}}
# .s3-kicker{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(56,96,200,0.7);margin-bottom:20px}}
# .s3-headline{{
#   font-family:var(--un);font-weight:900;
#   font-size:clamp(48px,10vw,108px);
#   line-height:0.86;color:var(--cool);
#   letter-spacing:-0.03em;margin-bottom:40px;
# }}
# .reply-grid{{display:grid;grid-template-columns:repeat(3,1fr);gap:1px;background:rgba(56,96,200,0.1);margin-top:8px;max-width:680px}}
# .reply-cell{{padding:28px 24px;background:var(--ink)}}
# .reply-cell .rv{{font-family:var(--un);font-weight:700;
#   font-size:clamp(22px,4vw,40px);color:var(--paper)}}
# .reply-cell .rl{{font-size:9px;text-transform:uppercase;letter-spacing:.14em;color:rgba(240,234,224,0.28);margin-top:6px}}
# .reply-note{{font-size:11px;color:rgba(240,234,224,0.25);margin-top:20px;letter-spacing:.05em}}
# @media(max-width:480px){{.reply-grid{{grid-template-columns:1fr 1fr}}}}

# /* ══════════════════════════════════════
#    4 — EMOJI  (film strip)
# ══════════════════════════════════════ */
# #s4{{background:#0A0612}}
# .s4-kicker{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(144,96,216,0.7);margin-bottom:24px}}
# .s4-title{{font-family:var(--un);font-weight:900;
#   font-size:clamp(38px,8vw,88px);line-height:0.88;
#   letter-spacing:-0.03em;color:var(--paper);margin-bottom:40px}}
# .s4-title em{{color:var(--lav);font-style:normal}}

# /* film strip container */
# .film-strip{{
#   display:flex;
#   gap:0;
#   overflow-x:auto;
#   scrollbar-width:none;
#   padding:20px 0;
#   margin:0 -24px;
#   padding-left:clamp(24px,5vw,80px);
#   cursor:grab;
#   user-select:none;
# }}
# .film-strip::-webkit-scrollbar{{display:none}}
# /* film holes row above and below */
# .film-holes{{display:flex;gap:0;padding-left:clamp(24px,5vw,80px)}}
# .film-hole{{
#   width:72px;height:14px;flex-shrink:0;
#   display:flex;align-items:center;justify-content:center;
#   background:var(--ink);
# }}
# .film-hole::before{{content:'';width:22px;height:8px;border-radius:3px;background:rgba(255,255,255,0.06)}}
# .film-frame{{
#   flex-shrink:0;
#   width:72px;
#   background:#111118;
#   border-left:1px solid rgba(255,255,255,0.05);
#   display:flex;flex-direction:column;
#   align-items:center;justify-content:center;
#   padding:14px 8px;gap:6px;
# }}
# .film-emoji{{font-size:34px;line-height:1}}
# .film-count{{font-family:var(--mono);font-size:9px;color:rgba(255,255,255,0.28)}}

# .era-section{{margin-top:36px}}
# .era-title{{font-size:10px;letter-spacing:.2em;text-transform:uppercase;color:rgba(144,96,216,0.4);margin-bottom:14px}}
# .era-row{{display:flex;align-items:center;gap:16px;margin-bottom:10px}}
# .era-yr{{font-family:var(--mono);font-size:11px;color:rgba(240,234,224,0.25);width:32px;flex-shrink:0}}
# .era-em{{font-size:24px;letter-spacing:6px}}
# .emoji-total{{font-size:11px;color:rgba(240,234,224,0.2);margin-top:20px;letter-spacing:.08em}}

# /* ══════════════════════════════════════
#    5 — BURST  (dial layout)
# ══════════════════════════════════════ */
# #s5{{background:var(--ink)}}
# .s5-kicker{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(40,184,138,0.7);margin-bottom:24px}}
# .s5-layout{{display:flex;align-items:center;gap:clamp(24px,6vw,80px);flex-wrap:wrap}}
# .s5-left{{flex:1;min-width:220px}}
# .s5-pct{{
#   font-family:var(--un);font-weight:900;
#   font-size:clamp(80px,16vw,172px);
#   line-height:0.82;color:var(--mint);
#   letter-spacing:-0.04em;
# }}
# .s5-suffix{{font-size:0.45em;color:rgba(240,234,224,0.4);vertical-align:top;margin-top:0.2em;display:inline-block}}
# .s5-label{{font-family:var(--serif);font-style:italic;font-size:clamp(15px,2.2vw,20px);color:rgba(240,234,224,0.4);margin-top:12px}}
# .s5-right{{flex-shrink:0}}
# /* arc gauge */
# .gauge-wrap{{position:relative;width:180px;height:180px}}
# .gauge-label{{
#   position:absolute;inset:0;display:flex;flex-direction:column;
#   align-items:center;justify-content:center;text-align:center;
# }}
# .gauge-label .gv{{font-family:var(--un);font-weight:700;font-size:28px;color:var(--mint)}}
# .gauge-label .gl{{font-size:9px;color:rgba(240,234,224,0.3);letter-spacing:.12em;text-transform:uppercase}}
# .s5-note{{font-size:11px;color:rgba(240,234,224,0.25);margin-top:28px;line-height:2;letter-spacing:.05em}}

# /* ══════════════════════════════════════
#    6 — SLANG ERA  (timeline)
# ══════════════════════════════════════ */
# #s6{{background:#100810}}
# .s6-kicker{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(212,168,64,0.6);margin-bottom:24px}}
# .s6-title{{font-family:var(--un);font-weight:900;
#   font-size:clamp(40px,8vw,88px);line-height:0.88;
#   letter-spacing:-0.03em;color:var(--paper);margin-bottom:44px}}
# .slang-line{{display:flex;align-items:flex-start;gap:20px;margin-bottom:22px;position:relative}}
# .slang-line::before{{
#   content:'';position:absolute;left:38px;top:0;bottom:-22px;
#   width:1px;background:rgba(212,168,64,0.12);
# }}
# .slang-yr{{font-family:var(--mono);font-size:11px;font-weight:700;
#   color:var(--gold);width:36px;flex-shrink:0;padding-top:4px;
#   letter-spacing:.08em}}
# .slang-pills{{display:flex;flex-wrap:wrap;gap:6px}}
# .tag{{
#   display:inline-block;
#   background:rgba(240,234,224,0.05);
#   border:1px solid rgba(240,234,224,0.1);
#   border-radius:2px;padding:4px 10px;
#   font-family:var(--mono);font-size:11px;
#   color:rgba(240,234,224,0.7);
#   letter-spacing:.04em;
# }}

# /* ══════════════════════════════════════
#    7 — MOOD  (full width spark)
# ══════════════════════════════════════ */
# #s7{{background:#060810}}
# .s7-kicker{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(96,200,96,0.5);margin-bottom:24px}}
# .s7-title{{font-family:var(--un);font-weight:900;
#   font-size:clamp(40px,8vw,88px);line-height:0.88;
#   letter-spacing:-0.03em;color:var(--paper);margin-bottom:48px}}
# .s7-title em{{color:rgba(96,200,96,0.8);font-style:normal}}
# .spark-wrap{{width:100%;max-width:800px}}
# .spark-legend{{display:flex;gap:20px;margin-top:18px;flex-wrap:wrap}}
# .sl-item{{font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:rgba(240,234,224,0.25);display:flex;align-items:center;gap:6px}}
# .sl-dot{{width:7px;height:7px;border-radius:50%;flex-shrink:0}}

# /* ══════════════════════════════════════
#    8 — WORD CLOUD  (typographic collision)
# ══════════════════════════════════════ */
# #s8{{background:var(--ink)}}
# .s8-kicker{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(212,168,64,0.5);margin-bottom:32px}}
# .wcloud{{display:flex;flex-wrap:wrap;gap:10px 16px;align-items:baseline;max-width:800px;line-height:1.2}}
# .wc-word{{
#   font-family:var(--serif);font-style:italic;
#   color:var(--paper);line-height:1;
#   transition:opacity .3s;cursor:default;
# }}
# .wc-word:hover{{opacity:1!important;color:var(--gold)}}
# .bigrams{{margin-top:36px;display:flex;flex-wrap:wrap;gap:8px}}

# /* ══════════════════════════════════════
#    9 — CHAOS  (stacked offset cards)
# ══════════════════════════════════════ */
# #s9{{background:#0C0606}}
# .s9-kicker{{font-size:10px;letter-spacing:.24em;text-transform:uppercase;color:rgba(255,72,48,0.6);margin-bottom:24px}}
# .s9-title{{font-family:var(--un);font-weight:900;
#   font-size:clamp(40px,8vw,80px);line-height:0.88;
#   letter-spacing:-0.03em;color:var(--paper);margin-bottom:44px}}
# .chaos-stack{{position:relative;width:100%;max-width:560px}}
# .chaos-line{{
#   font-family:var(--serif);font-style:italic;
#   font-size:clamp(14px,2vw,17px);
#   color:rgba(240,234,224,0.72);
#   background:rgba(255,72,48,0.04);
#   border:1px solid rgba(255,72,48,0.1);
#   border-left:2px solid rgba(255,72,48,0.4);
#   padding:12px 16px;margin-bottom:6px;
#   line-height:1.6;
#   transform:rotate(var(--r));
#   opacity:0;
#   animation:slidein .5s calc(var(--i)*0.12s) cubic-bezier(.16,1,.3,1) both;
# }}
# .card-in .chaos-line{{opacity:1}}
# @keyframes slidein{{from{{opacity:0;transform:rotate(var(--r)) translateX(-20px)}}to{{opacity:1;transform:rotate(var(--r))}}}}

# /* ══════════════════════════════════════
#    MARQUEE
# ══════════════════════════════════════ */
# .marquee-wrap{{
#   background:#D4A840;overflow:hidden;
#   white-space:nowrap;padding:12px 0;
#   border-top:1px solid rgba(0,0,0,0.15);
#   border-bottom:1px solid rgba(0,0,0,0.15);
# }}
# .marquee-inner{{
#   display:inline-block;
#   animation:marquee 22s linear infinite;
#   font-family:var(--un);font-weight:700;
#   font-size:13px;letter-spacing:.12em;
#   color:#060608;
# }}
# @keyframes marquee{{from{{transform:translateX(0)}}to{{transform:translateX(-50%)}}}}

# /* ══════════════════════════════════════
#    10 — END
# ══════════════════════════════════════ */
# #s10{{background:var(--paper);justify-content:center;padding-top:80px;padding-bottom:80px}}
# .end-name{{
#   font-family:var(--un);font-weight:900;
#   font-size:clamp(14vw,18vw,24vw);
#   line-height:0.82;
#   color:var(--ink);
#   letter-spacing:-0.04em;
# }}
# .end-sub{{font-family:var(--serif);font-style:italic;
#   font-size:clamp(18px,3vw,28px);color:rgba(6,6,8,0.38);margin-top:18px}}
# .end-counts{{
#   margin-top:40px;
#   display:flex;gap:clamp(20px,4vw,60px);flex-wrap:wrap;
# }}
# .end-counts .ec-v{{font-family:var(--un);font-weight:700;font-size:clamp(26px,5vw,48px);color:var(--ink)}}
# .end-counts .ec-l{{font-size:10px;color:rgba(6,6,8,0.35);letter-spacing:.14em;text-transform:uppercase;margin-top:4px}}
# .end-rule{{width:48px;height:2px;background:rgba(6,6,8,0.15);margin:32px 0}}
# .end-note{{font-family:var(--serif);font-style:italic;font-size:clamp(15px,2vw,20px);color:rgba(6,6,8,0.38)}}

# /* ══════════════════════════════════════
#    PROGRESS BAR
# ══════════════════════════════════════ */
# #pbar{{
#   position:fixed;top:0;left:0;z-index:1000;
#   height:2px;width:0%;
#   background:linear-gradient(90deg,#D4A840,#FF4830);
#   transition:width .1s linear;
# }}
# </style>
# </head>
# <body>
# <div id="pbar"></div>


# <!-- ══════════════════════════════
#      0 · COVER
# ══════════════════════════════ -->
# <section class="slide" id="s0">
#   <div class="cover-bg-name" aria-hidden="true">{FIRST}</div>
#   <div class="rx" style="position:relative;z-index:2">
#     <div class="cover-tag">your chat · wrapped · {YEAR}</div>
#     <div class="cover-headline">{FIRST}</div>
#     <div class="cover-sub">a data portrait</div>
#   </div>
#   <div class="cover-scroll">scroll ↓</div>
# </section>


# <!-- ══════════════════════════════
#      1 · NUMBERS
# ══════════════════════════════ -->
# <section class="slide" id="s1" style="padding:0">
#   <div class="s1-inner">
#     <div class="s1-left rx">
#       <div class="s1-big" aria-hidden="true">{TOTAL_RAW}</div>
#       <div style="position:relative;z-index:2">
#         <div class="s1-num" data-count="{TOTAL_RAW}">{TOTAL}</div>
#         <div class="s1-label">messages sent</div>
#       </div>
#     </div>
#     <div class="s1-right">
#       <div class="s1-rule rx"></div>
#       <div class="mini-stat rx d1">
#         <div class="mv" data-count="{WORDS_RAW}">{WORDS}</div>
#         <div class="ml">words typed</div>
#       </div>
#       <div class="mini-stat rx d2">
#         <div class="mv">{AVG_LEN}</div>
#         <div class="ml">avg words per message</div>
#       </div>
#       <div class="mini-stat rx d3">
#         <div class="mv">{DAYS}</div>
#         <div class="ml">days active</div>
#       </div>
#       <div class="mini-stat rx d4">
#         <div class="mv">{STREAK}</div>
#         <div class="ml">longest streak</div>
#       </div>
#       <div class="s1-rule rx d5"></div>
#       <div class="share-note rx d5">she carried <strong style="color:var(--gold)">{SHARE}%</strong> of<br>the entire conversation</div>
#     </div>
#   </div>
# </section>


# <!-- ══════════════════════════════
#      2 · PEAK HOUR
# ══════════════════════════════ -->
# <section class="slide" id="s2">
#   <div class="accent-rule rx"><span></span><i>II — peak hour</i><span></span></div>
#   <div class="s2-layout">
#     <div class="s2-left">
#       <div class="s2-kicker rx">most alive at</div>
#       <div class="s2-hour rx d1">{PEAK_LABEL}</div>
#       <div class="s2-desc rx d2">she texts most in the {PEAK_BUCKET}</div>
#       <div class="rx d3">
#         <div class="s2-pct">{PEAK_PCT}%</div>
#         <div class="s2-pct-label">of messages in {PEAK_BUCKET} hours</div>
#       </div>
#     </div>
#     <div class="s2-right rx d2">
#       {RADIAL_SVG}
#     </div>
#   </div>
# </section>


# <!-- ══════════════════════════════
#      3 · REPLY SPEED
# ══════════════════════════════ -->
# <section class="slide" id="s3">
#   <div class="s3-kicker rx">III — how fast she texts back</div>
#   <div class="s3-headline rx d1">{REPLY_AVG}</div>
#   <div class="reply-grid rx d2">
#     <div class="reply-cell">
#       <div class="rv">{REPLY_AVG}</div>
#       <div class="rl">average</div>
#     </div>
#     <div class="reply-cell">
#       <div class="rv">{REPLY_FAST}</div>
#       <div class="rl">fastest ever</div>
#     </div>
#     <div class="reply-cell">
#       <div class="rv">{REPLY_P90}</div>
#       <div class="rl">90th percentile</div>
#     </div>
#   </div>
#   <div class="reply-note rx d3">tracked across {REPLY_TOTAL} reply events</div>
# </section>


# <!-- ══════════════════════════════
#      4 · EMOJI ERA
# ══════════════════════════════ -->
# <section class="slide" id="s4" style="padding-left:0;padding-right:0">
#   <div style="padding:0 clamp(24px,5vw,80px)">
#     <div class="s4-kicker rx">IV — emoji fingerprint</div>
#     <div class="s4-title rx d1">her <em>emoji</em><br>era</div>
#   </div>
#   <div class="film-holes rx d2" aria-hidden="true">
#     {FILM_HOLES}
#   </div>
#   <div class="film-strip rx d2" id="filmStrip">
#     {EMOJI_STRIP}
#   </div>
#   <div class="film-holes rx d2" aria-hidden="true">
#     {FILM_HOLES}
#   </div>
#   <div style="padding:0 clamp(24px,5vw,80px)">
#     <div class="era-section rx d3">
#       <div class="era-title">era by year</div>
#       {ERA_ROWS}
#     </div>
#     <div class="emoji-total rx d4">{EMOJI_TOTAL} emojis in total</div>
#   </div>
# </section>


# <!-- ══════════════════════════════
#      5 · BURST VS ESSAY
# ══════════════════════════════ -->
# <section class="slide" id="s5">
#   <div class="s5-kicker rx">V — texting style</div>
#   <div class="s5-layout">
#     <div class="s5-left">
#       <div class="s5-pct rx d1">
#         {BURST_PCT}<span class="s5-suffix">%</span>
#       </div>
#       <div class="s5-label rx d2">of messages sent as bursts</div>
#       <div class="s5-note rx d3">
#         avg burst: <strong style="color:var(--mint)">{BURST_AVG} words</strong><br>
#         avg solo:  <strong style="color:var(--mint)">{SOLO_AVG} words</strong>
#       </div>
#     </div>
#     <div class="s5-right rx d2">
#       <div class="gauge-wrap">
#         <svg width="180" height="180" viewBox="0 0 180 180">
#           <circle cx="90" cy="90" r="72" fill="none"
#                   stroke="rgba(40,184,138,0.08)" stroke-width="14"/>
#           <circle id="gauge-arc" cx="90" cy="90" r="72" fill="none"
#                   stroke="var(--mint)" stroke-width="14"
#                   stroke-dasharray="452" stroke-dashoffset="452"
#                   stroke-linecap="round"
#                   transform="rotate(-90 90 90)"
#                   style="transition:stroke-dashoffset 1.2s .3s cubic-bezier(.16,1,.3,1)"/>
#         </svg>
#         <div class="gauge-label">
#           <div class="gv">{BURST_PCT}%</div>
#           <div class="gl">burst</div>
#         </div>
#       </div>
#     </div>
#   </div>
# </section>


# <!-- ══════════════════════════════
#      MARQUEE (between 5 and 6)
# ══════════════════════════════ -->
# <div class="marquee-wrap">
#   <span class="marquee-inner">{MQ_TEXT}&nbsp;&nbsp;&nbsp;&nbsp;{MQ_TEXT}&nbsp;&nbsp;&nbsp;&nbsp;</span>
# </div>


# <!-- ══════════════════════════════
#      6 · SLANG ERA
# ══════════════════════════════ -->
# <section class="slide" id="s6">
#   <div class="s6-kicker rx">VI — slang era report</div>
#   <div class="s6-title rx d1">words she<br>lived in</div>
#   <div class="rx d2">{SLANG_BLOCKS}</div>
# </section>


# <!-- ══════════════════════════════
#      7 · MOOD
# ══════════════════════════════ -->
# <section class="slide" id="s7">
#   <div class="s7-kicker rx">VII — emotional journey</div>
#   <div class="s7-title rx d1">her <em>mood</em><br>across time</div>
#   <div class="spark-wrap rx d2">
#     {SPARK_SVG}
#     <div class="spark-legend">
#       <div class="sl-item"><div class="sl-dot" style="background:#E8C060"></div>warm</div>
#       <div class="sl-item"><div class="sl-dot" style="background:#A080C8"></div>neutral</div>
#       <div class="sl-item"><div class="sl-dot" style="background:#6080C8"></div>low</div>
#     </div>
#   </div>
# </section>


# <!-- ══════════════════════════════
#      8 · WORD CLOUD
# ══════════════════════════════ -->
# <section class="slide" id="s8">
#   <div class="s8-kicker rx">VIII — what lives in her head</div>
#   <div class="wcloud rx d1">{WCLOUD_HTML}</div>
#   <div class="bigrams rx d3">{BGRAMS}</div>
# </section>


# <!-- ══════════════════════════════
#      9 · CHAOS
# ══════════════════════════════ -->
# <section class="slide" id="s9">
#   <div class="s9-kicker rx">IX — hall of chaos</div>
#   <div class="s9-title rx d1">her most<br>unhinged<br>moments</div>
#   <div class="chaos-stack rx d2" id="chaosStack">{CHAOS_ITEMS}</div>
# </section>


# <!-- ══════════════════════════════
#      10 · END
# ══════════════════════════════ -->
# <section class="slide" id="s10">
#   <div class="end-name rx">{FIRST}</div>
#   <div class="end-sub rx d1">a portrait in messages</div>
#   <div class="end-counts rx d2">
#     <div><div class="ec-v">{TOTAL}</div><div class="ec-l">messages</div></div>
#     <div><div class="ec-v">{WORDS}</div><div class="ec-l">words</div></div>
#   </div>
#   <div class="end-rule rx d3"></div>
#   <div class="end-note rx d3">and somehow still not enough.</div>
# </section>


# <script>
# // ── Progress bar ──────────────────────────────────────────────────────────────
# const pbar = document.getElementById('pbar');
# window.addEventListener('scroll', () => {{
#   const p = window.scrollY / (document.body.scrollHeight - window.innerHeight);
#   pbar.style.width = Math.min(p * 100, 100) + '%';
# }}, {{passive:true}});

# // ── Intersection reveal ───────────────────────────────────────────────────────
# const revealObs = new IntersectionObserver(entries => {{
#   entries.forEach(e => {{
#     if (e.isIntersecting) {{
#       e.target.classList.add('in');
#       // trigger chaos animation
#       const cs = e.target.closest('#s9');
#       if (cs) cs.querySelectorAll('.chaos-line').forEach(c => c.style.opacity = '1');
#     }}
#   }});
# }}, {{threshold: 0.15}});

# document.querySelectorAll('.rx').forEach(el => revealObs.observe(el));
# // immediately reveal visible elements (cover)
# document.querySelectorAll('#s0 .rx').forEach(el => el.classList.add('in'));

# // ── Counter animation ─────────────────────────────────────────────────────────
# function animateCount(el, target, duration=1600) {{
#   let start = null;
#   const step = ts => {{
#     if (!start) start = ts;
#     const p = Math.min((ts - start) / duration, 1);
#     const ease = 1 - Math.pow(1 - p, 4);
#     el.textContent = Math.floor(ease * target).toLocaleString();
#     if (p < 1) requestAnimationFrame(step);
#   }};
#   requestAnimationFrame(step);
# }}

# const counterObs = new IntersectionObserver(entries => {{
#   entries.forEach(e => {{
#     if (e.isIntersecting) {{
#       const target = parseInt(e.target.dataset.count);
#       if (!isNaN(target)) animateCount(e.target, target);
#       counterObs.unobserve(e.target);
#     }}
#   }});
# }}, {{threshold: 0.3}});
# document.querySelectorAll('[data-count]').forEach(el => counterObs.observe(el));

# // ── Gauge arc ─────────────────────────────────────────────────────────────────
# const gaugeArc = document.getElementById('gauge-arc');
# const gaugeObs = new IntersectionObserver(entries => {{
#   entries.forEach(e => {{
#     if (e.isIntersecting) {{
#       const pct = {BURST_PCT} / 100;
#       const circ = 2 * Math.PI * 72;
#       gaugeArc.style.strokeDashoffset = circ * (1 - pct);
#       gaugeObs.unobserve(e.target);
#     }}
#   }});
# }}, {{threshold: 0.4}});
# if (gaugeArc) gaugeObs.observe(gaugeArc);

# // ── Film strip drag scroll ────────────────────────────────────────────────────
# const strip = document.getElementById('filmStrip');
# if (strip) {{
#   let isDragging = false, startX, scrollLeft;
#   strip.addEventListener('mousedown', e => {{ isDragging=true; startX=e.pageX-strip.offsetLeft; scrollLeft=strip.scrollLeft; strip.style.cursor='grabbing'; }});
#   strip.addEventListener('mouseleave', () => {{ isDragging=false; strip.style.cursor='grab'; }});
#   strip.addEventListener('mouseup',   () => {{ isDragging=false; strip.style.cursor='grab'; }});
#   strip.addEventListener('mousemove', e => {{ if (!isDragging) return; e.preventDefault(); const x=e.pageX-strip.offsetLeft; strip.scrollLeft=scrollLeft-(x-startX); }});
#   // touch
#   strip.addEventListener('touchstart', e => {{ startX=e.touches[0].pageX; scrollLeft=strip.scrollLeft; }},{{passive:true}});
#   strip.addEventListener('touchmove',  e => {{ strip.scrollLeft=scrollLeft-(e.touches[0].pageX-startX); }},{{passive:true}});
# }}

# // ── Chaos card trigger ────────────────────────────────────────────────────────
# const chaosObs = new IntersectionObserver(entries => {{
#   entries.forEach(e => {{
#     if (e.isIntersecting) e.target.classList.add('card-in');
#   }});
# }}, {{threshold:0.2}});
# const chaosStack = document.getElementById('chaosStack');
# if (chaosStack) chaosObs.observe(chaosStack);
# </script>
# </body>
# </html>"""


# def main():
#     print("Loading chats…")
#     all_msgs = load(JSONL_IN)
#     for m in all_msgs: m["_dt"] = parse_dt(m)
#     her = [m for m in all_msgs if m["sender"] == HER]
#     print(f"  {len(all_msgs)} total  ·  {len(her)} from {HER}")
#     print("Computing stats…")
#     stats = {
#         "name":   HER,
#         "basic":  basic_stats(her, all_msgs),
#         "peak":   peak_hour(her),
#         "reply":  reply_speed(all_msgs, HER, YOU),
#         "emoji":  emoji_personality(her),
#         "burst":  burst_vs_essay(her),
#         "slang":  slang_era(her),
#         "mood":   mood_timeline(her),
#         "topics": whats_in_her_head(her),
#         "chaos":  most_chaotic(her),
#     }
#     with open("stats.json","w",encoding="utf-8") as f:
#         json.dump(stats,f,ensure_ascii=False,indent=2,default=str)
#     print("Building HTML…")
#     with open(HTML_OUT,"w",encoding="utf-8") as f:
#         f.write(build_html(stats))
#     print(f"✓  {HTML_OUT}")

# if __name__ == "__main__":
#     main()

"""
analyze.py — WhatsApp Wrapped  "BLOOM" edition
Pink · Daisies · Mango · Mogu Mogu
"""
import json, re, random, math
from collections import Counter, defaultdict
from datetime import datetime
import numpy as np

try:    import emoji as emoji_lib;  HAS_EMOJI = True
except: HAS_EMOJI = False
try:
    from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
    sia = SentimentIntensityAnalyzer(); HAS_VADER = True
except: HAS_VADER = False

HER      = "Niranjana"
YOU      = "Harshita"
JSONL_IN = "chats_clean.jsonl"
HTML_OUT = "niranjana_wrapped.html"

STOPWORDS = {
    "i","you","the","a","to","and","is","it","in","of","that","this","my","me",
    "we","for","be","with","on","are","was","have","do","not","but","so","if",
    "or","an","at","can","will","just","what","how","its","yeah","yea","ok",
    "okay","no","yes","don","like","get","got","go","going","know","one","also",
    "lol","haha","hahaha","lmao","omg","tbh","idk","ik","rn","bc","tho","btw",
    "ur","u","r","m","s","k","n","he","she","they","his","her","him","them",
    "all","out","up","about","from","by","as","more","been","has","had","would",
    "could","should","did","does","there","when","who","which","then","than",
    "too","even","back","much","well","really","now","some","any","our","your",
    "their","here","think","need","want","see","i'm","i've","i'll","don't",
    "can't","won't","didn't","doesn't","isn't","wasn't","we're","they're",
    "let","let's","come","said","say","tell","told","give","make","put","take",
    "made","came","went","into","after","before","until","while","use","used",
    "still","though","only","first","last","new","old","many","most","other",
    "same","down","over","where","why","am","being","been","de","la","na","da",
    "ya","nah","oh","ah","uh","yep","nope","sure","wait","else","maybe","might",
    "fr","bro","man","girl","hey","hi","hello","bye","wow","send","sent","chat",
    "text","msg","call","called","gonna","wanna","gotta","kinda","cuz","ngl",
    "istg","imo","smh","hm","hmm","ohh","ugh","actually","literally","basically",
}

def load(path):
    rows = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            try: rows.append(json.loads(line))
            except:
                try: rows.append(eval(line))
                except: pass
    return rows

def parse_dt(row):
    d, t = row["date"], row["time"]
    for fmt in ("%d/%m/%y %I:%M:%S %p","%m/%d/%y %I:%M:%S %p",
                "%d/%m/%y %I:%M %p",  "%m/%d/%y %I:%M %p"):
        try: return datetime.strptime(f"{d} {t}", fmt)
        except: pass
    return None

def basic_stats(her, all_msgs):
    total = len(her)
    words = sum(len(m["message"].split()) for m in her)
    days  = sorted(set(m["_dt"].date() for m in her if m["_dt"]))
    streak = ms = 1
    for i in range(1, len(days)):
        if (days[i]-days[i-1]).days == 1: streak += 1; ms = max(ms,streak)
        else: streak = 1
    return {"total":total,"words":words,
            "avg_len":round(words/max(total,1),1),
            "active_days":len(days),"streak":ms,
            "share":round(100*total/max(len(all_msgs),1))}

def peak_hour(msgs):
    hours = Counter(m["_dt"].hour for m in msgs if m["_dt"])
    if not hours: return {}
    total = sum(hours.values())
    bkts  = {"morning":0,"afternoon":0,"evening":0,"night":0}
    for h,c in hours.items():
        if   6<=h<12:  bkts["morning"]  +=c
        elif 12<=h<18: bkts["afternoon"]+=c
        elif 18<=h<22: bkts["evening"]  +=c
        else:          bkts["night"]    +=c
    peak = hours.most_common(1)[0][0]
    pb   = max(bkts, key=bkts.get)
    h12  = peak%12 or 12
    return {"label":f"{h12}{'AM' if peak<12 else 'PM'}","hour24":peak,
            "bucket":pb,"bucket_pct":round(100*bkts[pb]/total),
            "bars":{str(h):v for h,v in sorted(hours.items())}}

def reply_speed(all_msgs, her, you):
    deltas = []
    for i,m in enumerate(all_msgs):
        if m["sender"]==her and m["_dt"]:
            for j in range(i-1,max(i-20,-1),-1):
                p=all_msgs[j]
                if p["sender"]==you and p["_dt"]:
                    d=(m["_dt"]-p["_dt"]).total_seconds()
                    if 0<d<86400: deltas.append(d)
                    break
    if not deltas: return {"avg":"?","fastest":"?","p90":"?","total":0}
    def fmt(s):
        s=int(s)
        if s<60:   return f"{s}s"
        if s<3600: return f"{s//60}m {s%60}s"
        return f"{s//3600}h {(s%3600)//60}m"
    return {"avg":fmt(np.mean(deltas)),"fastest":fmt(min(deltas)),
            "p90":fmt(np.percentile(deltas,90)),"total":len(deltas)}

def emoji_personality(msgs):
    if not HAS_EMOJI: return {"top":[],"by_year":{},"total":0}
    all_e,by_year=[],defaultdict(list)
    for m in msgs:
        found=[c["emoji"] for c in emoji_lib.emoji_list(m["message"])]
        all_e.extend(found)
        if m["_dt"]: by_year[str(m["_dt"].year)].extend(found)
    return {"top":    [{"emoji":e,"count":c} for e,c in Counter(all_e).most_common(8)],
            "by_year":{yr:[{"emoji":e,"count":c} for e,c in Counter(em).most_common(4)]
                       for yr,em in sorted(by_year.items())},
            "total":len(all_e)}

def burst_vs_essay(msgs):
    bursts,solos,bl,sl=0,0,[],[]
    i=0
    while i<len(msgs):
        m=msgs[i]
        if not m["_dt"]: i+=1; continue
        if i+1<len(msgs) and msgs[i+1]["_dt"]:
            gap=(msgs[i+1]["_dt"]-m["_dt"]).total_seconds()
            if 0<=gap<=90: bursts+=1;bl.append(len(m["message"].split()));i+=1;continue
        solos+=1;sl.append(len(m["message"].split()));i+=1
    tot=bursts+solos
    return {"burst_pct":round(100*bursts/tot) if tot else 0,
            "avg_burst":round(np.mean(bl),1) if bl else 0,
            "avg_solo": round(np.mean(sl),1) if sl else 0}

def slang_era(msgs):
    by_year=defaultdict(list)
    for m in msgs:
        if m["_dt"]:
            words=[w for w in re.findall(r"[a-z']+",m["message"].lower())
                   if w not in STOPWORDS and len(w)>2]
            by_year[m["_dt"].year].extend(words)
    years=sorted(by_year)
    if len(years)<2: return {"eras":[]}
    eras=[]
    for yr in years:
        this=Counter(by_year[yr]); other=Counter()
        for y2 in years:
            if y2!=yr: other.update(by_year[y2])
        unique=[w for w,c in this.most_common(300)
                if c>=3 and c/(other.get(w,0)+1)>=1.8][:5]
        eras.append({"year":str(yr),"words":unique})
    return {"eras":eras}

def mood_timeline(msgs):
    if not HAS_VADER: return {"months":[]}
    by_month=defaultdict(list)
    for m in msgs:
        if m["_dt"] and len(m["message"].split())>=2:
            by_month[m["_dt"].strftime("%Y-%m")].append(
                sia.polarity_scores(m["message"])["compound"])
    months=[]
    for k in sorted(by_month):
        avg=round(np.mean(by_month[k]),3)
        months.append({"key":k,
                       "label":datetime.strptime(k,"%Y-%m").strftime("%b %y"),
                       "score":avg})
    return {"months":months}

def whats_in_her_head(msgs):
    words,bigrams=[],[]
    for m in msgs:
        ww=[w for w in re.findall(r"[a-z']+",m["message"].lower())
            if w not in STOPWORDS and len(w)>2]
        words.extend(ww)
        for j in range(len(ww)-1): bigrams.append(f"{ww[j]} {ww[j+1]}")
    tw=Counter(words).most_common(14)
    tb=[(b,c) for b,c in Counter(bigrams).most_common(40) if c>=3][:5]
    return {"top_words":  [{"word":w,"count":c} for w,c in tw],
            "top_bigrams":[{"phrase":b,"count":c} for b,c in tb]}

def chaos_score(m):
    t=m["message"]
    caps=sum(1 for c in t if c.isupper())/max(len(t),1)
    rep=len(re.findall(r'(.)\1{2,}',t))
    excl=t.count('!')+t.count('?')
    emoj=len(emoji_lib.emoji_list(t)) if HAS_EMOJI else 0
    bonus=1.5 if 1<=len(t.split())<=6 else 1.0
    return (caps*10+rep*3+excl*2+emoj*1.5)*bonus

def most_chaotic(msgs):
    scored=[(chaos_score(m),m) for m in msgs
            if len(m["message"].strip())>1
            and "missed" not in m["message"].lower()
            and "deleted" not in m["message"].lower()]
    scored.sort(key=lambda x:-x[0])
    top,seen=[],set()
    for _,m in scored:
        t=m["message"].strip()
        if t in seen: continue
        seen.add(t); top.append({"message":t[:100]})
        if len(top)>=5: break
    return {"top":top}

# ── SVG helpers ────────────────────────────────────────────────────────────────

def daisy_svg(cx, cy, r_petal=22, n_petals=8, petal_col="#FFE8F4",
              center_col="#FFD840", stroke="#FF88B4", delay=0, size_cls=""):
    """Blooming daisy SVG group."""
    petals = ""
    for i in range(n_petals):
        ang = math.radians(i * 360 / n_petals)
        px = cx + (r_petal + 4) * math.cos(ang)
        py = cy + (r_petal + 4) * math.sin(ang)
        rot = math.degrees(ang)
        petals += (
            f'<ellipse cx="{px:.1f}" cy="{py:.1f}" rx="{r_petal*.55:.1f}" ry="{r_petal:.1f}" '
            f'fill="{petal_col}" stroke="{stroke}" stroke-width="0.8" opacity="0.92" '
            f'transform="rotate({rot:.1f} {px:.1f} {py:.1f})" '
            f'class="petal{size_cls}" style="transform-origin:{px:.1f}px {py:.1f}px;'
            f'animation-delay:{delay+i*0.06:.2f}s"/>'
        )
    return (f'<g class="daisy-g">{petals}'
            f'<circle cx="{cx}" cy="{cy}" r="{r_petal*0.52:.1f}" fill="{center_col}" '
            f'class="daisy-center{size_cls}" style="animation-delay:{delay:.2f}s"/>'
            f'<circle cx="{cx}" cy="{cy}" r="{r_petal*0.28:.1f}" fill="#FFF8C0" opacity="0.7"/>'
            f'</g>')

def daisy_word_cloud(top):
    """Words arranged in a daisy / flower orbit pattern."""
    words = top.get("top_words", [])
    if not words:
        return '<p style="color:#FF88B4;font-size:14px">not enough data</p>'
    W, H = 600, 460
    cx, cy = W//2, H//2 + 10
    mc = words[0]["count"]
    parts = []

    # Center word in yellow circle
    cw = words[0]
    r_c = 56
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_c}" fill="#FFD840"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_c-6}" fill="#FFE860" opacity="0.5"/>')
    parts.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" '
                 f'font-size="18" font-family="DM Serif Display,Georgia,serif" '
                 f'font-style="italic" fill="#1C0818" font-weight="600">{cw["word"]}</text>')

    # Ring 1 — 6 words on pink petal circles
    ring1 = words[1:7]
    r1 = 148
    for i, w in enumerate(ring1):
        ang = math.radians(i * 360/max(len(ring1),1) - 90)
        wx = cx + r1 * math.cos(ang)
        wy = cy + r1 * math.sin(ang)
        sz = 11 + int((w["count"]/mc) * 6)
        rc = 36 + int((w["count"]/mc) * 10)
        # stem line
        lx1 = cx + r_c*math.cos(ang); ly1 = cy + r_c*math.sin(ang)
        lx2 = wx - rc*math.cos(ang);  ly2 = wy - rc*math.sin(ang)
        parts.append(f'<line x1="{lx1:.1f}" y1="{ly1:.1f}" x2="{lx2:.1f}" y2="{ly2:.1f}" '
                     f'stroke="#FFAAD0" stroke-width="1" opacity="0.4" stroke-dasharray="3,3"/>')
        parts.append(f'<circle cx="{wx:.1f}" cy="{wy:.1f}" r="{rc}" fill="#FFE8F4" stroke="#FFAAD0" stroke-width="0.8"/>')
        parts.append(f'<text x="{wx:.1f}" y="{wy+4:.1f}" text-anchor="middle" '
                     f'font-size="{sz}" font-family="DM Serif Display,Georgia,serif" '
                     f'font-style="italic" fill="#8C1848">{w["word"]}</text>')

    # Ring 2 — remaining words, floating
    ring2 = words[7:13]
    r2 = 250
    for i, w in enumerate(ring2):
        ang = math.radians(i * 360/max(len(ring2),1) - 60)
        wx = cx + r2 * math.cos(ang)
        wy = cy + r2 * math.sin(ang)
        sz = 10 + int((w["count"]/mc) * 5)
        op = round(0.35 + 0.45*(w["count"]/mc), 2)
        parts.append(f'<text x="{wx:.1f}" y="{wy:.1f}" text-anchor="middle" '
                     f'font-size="{sz}" font-family="DM Serif Display,Georgia,serif" '
                     f'font-style="italic" fill="#FF1A6B" opacity="{op}">{w["word"]}</text>')

    return (f'<svg viewBox="0 0 {W} {H}" width="100%" '
            f'style="overflow:visible;max-width:{W}px">{"".join(parts)}</svg>')

def mood_spark(mood):
    months = mood.get("months", [])
    if len(months) < 2: return ""
    W, H, pad = 600, 130, 20
    sc = [m["score"] for m in months]
    mn, mx = min(sc), max(sc); rng = max(mx-mn, 0.1)
    def px(i): return pad + i*(W-2*pad)/(len(months)-1)
    def py(s):  return H - pad - (s-mn)/rng*(H-2*pad)
    pts = [(px(i), py(m["score"])) for i,m in enumerate(months)]
    path = f"M{pts[0][0]:.1f},{pts[0][1]:.1f}"
    for i in range(1, len(pts)):
        x0,y0=pts[i-1]; x1,y1=pts[i]; xm=(x0+x1)/2
        path += f" C{xm:.1f},{y0:.1f} {xm:.1f},{y1:.1f} {x1:.1f},{y1:.1f}"
    fill = path + f" L{pts[-1][0]:.1f},{H} L{pts[0][0]:.1f},{H} Z"
    bi = sc.index(max(sc)); wi = sc.index(min(sc))
    ann = ""
    if len(pts)>bi:
        ann += (f'<circle cx="{pts[bi][0]:.1f}" cy="{pts[bi][1]:.1f}" r="5" fill="#FFD840"/>'
                f'<text x="{pts[bi][0]:.1f}" y="{pts[bi][1]-11:.1f}" text-anchor="middle" '
                f'font-size="9" fill="#FFD840" font-family="Space Mono,monospace">{months[bi]["label"]}</text>')
    if len(pts)>wi:
        ann += (f'<circle cx="{pts[wi][0]:.1f}" cy="{pts[wi][1]:.1f}" r="5" fill="#FF88B4"/>'
                f'<text x="{pts[wi][0]:.1f}" y="{pts[wi][1]+18:.1f}" text-anchor="middle" '
                f'font-size="9" fill="#FF88B4" font-family="Space Mono,monospace">{months[wi]["label"]}</text>')
    return (f'<svg viewBox="0 0 {W} {H}" width="100%" style="overflow:visible;max-width:{W}px">'
            f'<defs><linearGradient id="mg" x1="0" y1="0" x2="0" y2="1">'
            f'<stop offset="0%" stop-color="#FF1A6B" stop-opacity="0.22"/>'
            f'<stop offset="100%" stop-color="#FF1A6B" stop-opacity="0"/>'
            f'</linearGradient></defs>'
            f'<path d="{fill}" fill="url(#mg)"/>'
            f'<path d="{path}" fill="none" stroke="#FF1A6B" stroke-width="2.5" '
            f'stroke-linecap="round"/>{ann}</svg>')

def radial_24(bars, peak_h24):
    if not bars: return ""
    W=200; cx=cy=100; ri=30; ro=88
    mx = max(bars.values()) if bars else 1
    parts = []
    for h in range(24):
        v = bars.get(str(h), 0)
        ang = math.radians(h*15 - 90)
        rb = ri + (ro-ri)*(v/mx)
        x1=cx+ri*math.cos(ang); y1=cy+ri*math.sin(ang)
        x2=cx+rb*math.cos(ang); y2=cy+rb*math.sin(ang)
        col = "#FF1A6B" if h==peak_h24 else "#FFB8D4" if v/mx>0.5 else "rgba(255,184,212,0.25)"
        sw  = 4 if h==peak_h24 else 2.5
        parts.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" '
                     f'stroke="{col}" stroke-width="{sw}" stroke-linecap="round"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{ri}" fill="none" '
                 f'stroke="rgba(255,184,212,0.1)" stroke-width="1"/>')
    return (f'<svg viewBox="0 0 {W} {W}" width="{W}" height="{W}" '
            f'style="overflow:visible">{"".join(parts)}</svg>')


# ── Build HTML ─────────────────────────────────────────────────────────────────
def build_html(s):
    name=s["name"]; first=name.split()[0]
    b=s["basic"]; ph=s["peak"]; rep=s["reply"]
    em=s["emoji"]; bur=s["burst"]; sl=s["slang"]
    mood=s["mood"]; top=s["topics"]; chaos=s["chaos"]
    yr=str(datetime.now().year)

    # Daisies for cover (4 corner daisies + 2 mid)
    daisies_cover = (
        daisy_svg(60,  60,  28, 8, "#FFE8F4","#FFD840","#FF88B4", 0.0)  +
        daisy_svg(940, 60,  22, 8, "#FFDDF0","#FFE060","#FFAAD0", 0.3)  +
        daisy_svg(30,  440, 18, 8, "#FFE8F4","#FFD840","#FF88B4", 0.6)  +
        daisy_svg(920, 430, 26, 8, "#FFDDF0","#FFE060","#FFAAD0", 0.2)  +
        daisy_svg(500, 30,  14, 8, "#FFE8F4","#FFD840","#FF88B4", 0.5)  +
        daisy_svg(480, 460, 16, 8, "#FFDDF0","#FFE060","#FFAAD0", 0.4)
    )
    # Small daisies for end card
    daisies_end = (
        daisy_svg(80,  80,  32, 8, "#FFD4E8","#FF9820","#FF6890", 0.0)  +
        daisy_svg(880, 70,  26, 8, "#FFD4E8","#FF9820","#FF6890", 0.2)  +
        daisy_svg(50,  380, 20, 8, "#FFD4E8","#FF9820","#FF6890", 0.4)  +
        daisy_svg(920, 360, 24, 8, "#FFD4E8","#FF9820","#FF6890", 0.1)
    )

    # Emoji film strip
    emoji_strip = "".join(
        f'<div class="ff"><span class="fe">{e["emoji"]}</span>'
        f'<span class="fc">{e["count"]}</span></div>'
        for e in em.get("top",[])[:8])
    era_rows = "".join(
        f'<div class="era-row"><span class="era-yr">{yr2}</span>'
        f'<span class="era-em">{"".join(x["emoji"] for x in items[:4])}</span></div>'
        for yr2,items in em.get("by_year",{}).items())

    # Slang
    slang_blocks=""
    for e in sl.get("eras",[]):
        if not e["words"]: continue
        pills="".join(f'<span class="stag">{w}</span>' for w in e["words"])
        slang_blocks+=f'<div class="sl-row"><span class="sl-yr">{e["year"]}</span><span class="sl-pills">{pills}</span></div>'
    if not slang_blocks: slang_blocks='<span class="dim-txt">need more data across years</span>'

    # Mood spark
    spark_svg = mood_spark(mood)

    # Word daisy cloud
    word_cloud = daisy_word_cloud(top)

    # Bigrams
    bgrams="".join(
        f'<span class="btag">"{bg["phrase"]}"</span>'
        for bg in top.get("top_bigrams",[])[:5])

    # Chaos stickers
    random.seed(42)
    sticker_cols=["#FFE8F4","#FFF4E0","#E8F4FF","#F0FFE8","#FFE0F0"]
    chaos_html=""
    for i,m in enumerate(chaos.get("top",[])[:5]):
        rot=random.uniform(-3.5,3.5)
        col=sticker_cols[i%len(sticker_cols)]
        chaos_html+=(
            f'<div class="sticker" style="--r:{rot:.1f}deg;--i:{i};background:{col}">'
            f'<div class="sticker-tape"></div>'
            f'<p class="sticker-txt">&ldquo;{m["message"]}&rdquo;</p>'
            f'</div>')

    # Radial chart
    radial = radial_24(ph.get("bars",{}), ph.get("hour24",0))

    # Marquee text
    tw = top.get("top_words",[])
    mq = " 🌸 ".join(w["word"].upper() for w in tw[:10]) + " 🌸 "
    mq = (mq*3)

    # Mogu Mogu bubble data (JSON for canvas)
    bubble_data = json.dumps([
        {"r": random.randint(8,28), "x": random.uniform(0,1),
         "speed": random.uniform(0.3,1.1), "phase": random.uniform(0,6.28),
         "opacity": random.uniform(0.08,0.25)}
        for _ in range(30)
    ])

    # Replace placeholders in template
    html = TEMPLATE
    replacements = {
        "__FIRST__": first, "__NAME__": name, "__YEAR__": yr,
        "__TOTAL__": f"{b['total']:,}", "__WORDS__": f"{b['words']:,}",
        "__AVG_LEN__": str(b['avg_len']), "__DAYS__": str(b['active_days']),
        "__STREAK__": str(b['streak']), "__SHARE__": str(b['share']),
        "__PEAK_LABEL__": ph.get("label","?"),
        "__PEAK_BUCKET__": ph.get("bucket","night"),
        "__PEAK_PCT__": str(ph.get("bucket_pct",0)),
        "__RADIAL__": radial,
        "__REPLY_AVG__": rep.get("avg","?"),
        "__REPLY_FAST__": rep.get("fastest","?"),
        "__REPLY_P90__": rep.get("p90","?"),
        "__REPLY_TOTAL__": f"{rep.get('total',0):,}",
        "__EMOJI_STRIP__": emoji_strip,
        "__ERA_ROWS__": era_rows,
        "__EMOJI_TOTAL__": str(em.get("total",0)),
        "__BURST_PCT__": str(bur["burst_pct"]),
        "__BURST_AVG__": str(bur["avg_burst"]),
        "__SOLO_AVG__": str(bur["avg_solo"]),
        "__SLANG_BLOCKS__": slang_blocks,
        "__SPARK__": spark_svg,
        "__WORD_CLOUD__": word_cloud,
        "__BGRAMS__": bgrams,
        "__CHAOS_HTML__": chaos_html,
        "__MQ__": mq,
        "__DAISIES_COVER__": daisies_cover,
        "__DAISIES_END__": daisies_end,
        "__BUBBLES__": bubble_data,
        "__TOTAL_RAW__": str(b['total']),
        "__WORDS_RAW__": str(b['words']),
        "__BURST_PCT_RAW__": str(bur["burst_pct"]),
    }
    for k,v in replacements.items():
        html = html.replace(k, v)
    return html


# ══════════════════════════════════════════════════════════════════════════════
# TEMPLATE
# ══════════════════════════════════════════════════════════════════════════════
TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>__FIRST__'s Wrapped 🌸</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=DM+Serif+Display:ital@0;1&family=Unbounded:wght@300;700;900&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
:root {
  --plum:   #12040E;
  --hot:    #FF1A6B;
  --soft:   #FFB8D4;
  --blush:  #FFE8F4;
  --mango:  #FF9820;
  --mango-l:#FFD060;
  --cream:  #FFF8F2;
  --daisy-y:#FFD840;
  --ink:    #1C0818;
  --serif: 'DM Serif Display', Georgia, serif;
  --bold:  'Unbounded', sans-serif;
  --mono:  'Space Mono', monospace;
}
html { scroll-behavior:smooth; background:var(--plum); }
body { font-family:var(--mono); color:var(--cream); overflow-x:hidden; }

/* grain */
body::after {
  content:''; position:fixed; inset:0; z-index:999; pointer-events:none;
  background:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.028'/%3E%3C/svg%3E");
}

/* progress bar */
#pbar { position:fixed;top:0;left:0;height:3px;z-index:1000;
  background:linear-gradient(90deg,#FF1A6B,#FFD840,#FF9820);
  width:0; transition:width .1s linear; border-radius:0 99px 99px 0; }

/* ── SLIDES ── */
.slide {
  min-height:100vh; width:100%;
  display:flex; flex-direction:column; justify-content:center;
  position:relative; overflow:hidden;
  padding:clamp(48px,7vh,96px) clamp(24px,5vw,80px);
}

/* reveal */
.rx { opacity:0; transform:translateY(36px);
  transition:opacity .85s cubic-bezier(.16,1,.3,1),
             transform .85s cubic-bezier(.16,1,.3,1); }
.rx.in { opacity:1; transform:none; }
.rx.d1{transition-delay:.1s}.rx.d2{transition-delay:.22s}
.rx.d3{transition-delay:.34s}.rx.d4{transition-delay:.46s}

/* ── DAISY animations ── */
.petal {
  transform-box:fill-box; transform-origin:center center;
  animation:bloomp .7s cubic-bezier(.16,1,.3,1) both;
}
.daisy-center {
  transform-box:fill-box; transform-origin:center center;
  animation:bloomc .6s .2s cubic-bezier(.16,1,.3,1) both;
}
@keyframes bloomp {
  from { transform:scale(0) rotate(-120deg); opacity:0; }
  to   { transform:scale(1) rotate(0deg); opacity:1; }
}
@keyframes bloomc {
  from { transform:scale(0); opacity:0; }
  to   { transform:scale(1); opacity:1; }
}
.daisy-g { opacity:0; transition:opacity .4s ease; }
.daisy-g.bloomed { opacity:1; }

/* ══ 0 COVER ══════════════════════════════════════════════ */
#s0 { background:var(--plum); padding-bottom:80px; justify-content:flex-end; }
#bubble-canvas { position:absolute;inset:0;z-index:0;pointer-events:none; }
.cover-daisy-svg { position:absolute;inset:0;z-index:1;pointer-events:none;overflow:visible; }
.cover-tag {
  font-family:var(--mono); font-size:10px; letter-spacing:.22em;
  text-transform:uppercase; color:rgba(255,184,212,0.4);
  margin-bottom:20px; position:relative; z-index:2;
}
.cover-name {
  font-family:var(--bold); font-weight:900;
  font-size:clamp(14vw,18vw,22vw); line-height:.84;
  letter-spacing:-0.03em;
  background:linear-gradient(140deg,#FFB8D4 0%,#FF1A6B 45%,#FFD060 100%);
  -webkit-background-clip:text; background-clip:text;
  -webkit-text-fill-color:transparent;
  position:relative; z-index:2;
}
.cover-serif {
  font-family:var(--serif); font-style:italic;
  font-size:clamp(18px,3vw,28px);
  color:rgba(255,184,212,0.5); margin-top:18px;
  position:relative; z-index:2;
}
.cover-scroll {
  position:absolute; right:clamp(24px,5vw,80px); bottom:56px; z-index:2;
  writing-mode:vertical-lr; font-size:9px; letter-spacing:.2em;
  color:rgba(255,184,212,0.25); animation:bob 2.6s ease-in-out infinite;
}
@keyframes bob{0%,100%{transform:translateY(0)}50%{transform:translateY(8px)}}

/* ══ TORN DIVIDER ══════════════════════════════════════════ */
.torn {
  width:100%; overflow:hidden; position:relative; z-index:10;
  height:48px; margin:-1px 0;
}
.torn svg { display:block; width:100%; height:100%; }

/* ══ 1 NUMBERS ════════════════════════════════════════════ */
#s1 { background:var(--hot); padding:0; }
.s1-grid { display:grid; grid-template-columns:1fr 1fr; min-height:100vh; }
.s1-left {
  background:#D4005A; display:flex; flex-direction:column;
  justify-content:flex-end; padding:clamp(32px,5vw,72px); position:relative; overflow:hidden;
}
.s1-ghost {
  position:absolute; font-family:var(--bold); font-weight:900;
  font-size:clamp(20vw,16vw,26vw); line-height:.82;
  color:rgba(255,255,255,0.07); top:0; left:-0.04em;
  letter-spacing:-0.04em; pointer-events:none; user-select:none;
}
.s1-num {
  font-family:var(--bold); font-weight:900;
  font-size:clamp(52px,10vw,110px); line-height:.88;
  color:#FFF0F6; position:relative; z-index:2;
}
.s1-lbl {
  font-family:var(--serif); font-style:italic;
  font-size:clamp(14px,2vw,20px); color:rgba(255,240,246,0.55);
  margin-top:8px; position:relative; z-index:2;
}
.s1-right {
  display:flex; flex-direction:column; justify-content:center;
  padding:clamp(32px,5vw,72px); gap:28px; background:var(--hot);
}
.mini-num { font-family:var(--bold); font-weight:700;
  font-size:clamp(26px,4.5vw,48px); color:#FFF0F6; }
.mini-lbl { font-size:9px; letter-spacing:.14em; text-transform:uppercase;
  color:rgba(255,240,246,0.38); margin-top:3px; }
.s1-rule { width:36px; height:1px; background:rgba(255,240,246,0.25); }
.s1-note { font-size:11px; color:rgba(255,240,246,0.35); line-height:1.85; }
@media(max-width:580px){.s1-grid{grid-template-columns:1fr}.s1-left{min-height:48vh}.s1-right{min-height:52vh}}

/* ══ 2 PEAK HOUR ══════════════════════════════════════════ */
#s2 { background:var(--cream); }
.s2-kicker { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(255,26,107,0.5); margin-bottom:24px; }
.s2-layout { display:flex; align-items:center; gap:clamp(24px,6vw,80px); flex-wrap:wrap; }
.s2-left { flex:1; min-width:200px; }
.s2-hour { font-family:var(--bold); font-weight:900;
  font-size:clamp(72px,15vw,156px); line-height:.82;
  color:var(--hot); letter-spacing:-0.04em; }
.s2-desc { font-family:var(--serif); font-style:italic;
  font-size:clamp(15px,2.2vw,21px); color:rgba(28,8,24,0.45); margin-top:12px; }
.s2-pct { font-family:var(--bold); font-weight:700; font-size:36px; color:var(--ink); margin-top:18px; }
.s2-pct-lbl { font-size:10px; letter-spacing:.12em; color:rgba(28,8,24,0.35); }

/* ══ 3 REPLY SPEED ════════════════════════════════════════ */
#s3 { background:var(--plum); }
.s3-kicker { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(255,184,212,0.4); margin-bottom:20px; }
.s3-big { font-family:var(--bold); font-weight:900;
  font-size:clamp(56px,12vw,130px); line-height:.84;
  color:var(--soft); letter-spacing:-0.04em; margin-bottom:36px; }
.reply-grid { display:grid; grid-template-columns:repeat(3,1fr);
  gap:1px; background:rgba(255,184,212,0.1); max-width:640px; }
.rcell { padding:24px 20px; background:var(--plum); }
.rcell .rv { font-family:var(--bold); font-weight:700;
  font-size:clamp(20px,3.5vw,36px); color:var(--cream); }
.rcell .rl { font-size:9px; text-transform:uppercase;
  letter-spacing:.13em; color:rgba(255,184,212,0.3); margin-top:5px; }
.r-note { font-size:11px; color:rgba(255,184,212,0.2); margin-top:18px; letter-spacing:.05em; }
@media(max-width:460px){.reply-grid{grid-template-columns:1fr 1fr}}

/* ══ 4 EMOJI ══════════════════════════════════════════════ */
#s4 { background:#1A0822; padding-left:0; padding-right:0; }
.s4-inner { padding:0 clamp(24px,5vw,80px); }
.s4-kicker { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(255,184,212,0.4); margin-bottom:22px; }
.s4-title { font-family:var(--bold); font-weight:900;
  font-size:clamp(38px,8vw,86px); line-height:.88;
  letter-spacing:-0.03em; color:var(--cream); margin-bottom:36px; }
.s4-title em { color:var(--soft); font-style:normal; }
.film-holes { display:flex; padding-left:clamp(24px,5vw,80px); overflow:hidden; }
.fhole { width:68px; height:16px; flex-shrink:0; display:flex;
  align-items:center; justify-content:center; background:#1A0822; }
.fhole::before { content:''; width:20px; height:9px; border-radius:4px;
  background:rgba(255,255,255,0.05); }
.film-strip { display:flex; overflow-x:auto; scrollbar-width:none;
  padding:16px 0; padding-left:clamp(24px,5vw,80px); cursor:grab; user-select:none; }
.film-strip::-webkit-scrollbar { display:none; }
.ff { flex-shrink:0; width:68px; background:#0E0316;
  border-left:1px solid rgba(255,255,255,0.04);
  display:flex; flex-direction:column; align-items:center;
  justify-content:center; padding:12px 6px; gap:5px; }
.fe { font-size:30px; line-height:1; }
.fc { font-family:var(--mono); font-size:8px; color:rgba(255,255,255,0.22); }
.era-row { display:flex; align-items:center; gap:14px; margin-bottom:10px; }
.era-yr { font-family:var(--mono); font-size:10px; color:rgba(255,184,212,0.3);
  width:28px; flex-shrink:0; }
.era-em { font-size:22px; letter-spacing:5px; }
.et { font-size:10px; color:rgba(255,184,212,0.2); margin-top:16px; letter-spacing:.08em; }

/* ══ 5 BURST ══════════════════════════════════════════════ */
#s5 { background:var(--mango); }
.s5-kicker { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(28,8,24,0.4); margin-bottom:24px; }
.s5-layout { display:flex; align-items:center; gap:clamp(24px,6vw,80px); flex-wrap:wrap; }
.s5-left { flex:1; min-width:200px; }
.s5-pct { font-family:var(--bold); font-weight:900;
  font-size:clamp(80px,16vw,170px); line-height:.82;
  color:var(--plum); letter-spacing:-0.04em; }
.s5-sup { font-size:.45em; vertical-align:top; margin-top:.18em;
  display:inline-block; color:rgba(28,8,24,0.4); }
.s5-lbl { font-family:var(--serif); font-style:italic;
  font-size:clamp(15px,2.2vw,21px); color:rgba(28,8,24,0.45); margin-top:10px; }
.s5-note { font-size:11px; color:rgba(28,8,24,0.35); margin-top:22px; line-height:2; }
/* mogu mogu cup */
.cup-wrap { position:relative; width:160px; height:200px; flex-shrink:0; }
.cup-liq { fill:rgba(255,255,255,0.2); }
/* bubbles in cup */
.cup-bub { fill:rgba(255,255,255,0.55); animation:bubrise 2s ease-in-out infinite; }
@keyframes bubrise{0%,100%{transform:translateY(0)}50%{transform:translateY(-6px)}}

/* ══ 6 SLANG ══════════════════════════════════════════════ */
#s6 { background:var(--cream); }
.s6-kicker { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(255,26,107,0.45); margin-bottom:22px; }
.s6-title { font-family:var(--bold); font-weight:900;
  font-size:clamp(38px,7vw,84px); line-height:.88;
  letter-spacing:-0.03em; color:var(--ink); margin-bottom:40px; }
.sl-row { display:flex; align-items:flex-start; gap:18px;
  margin-bottom:20px; position:relative; }
.sl-row::before { content:''; position:absolute; left:34px; top:4px; bottom:-20px;
  width:1px; background:rgba(255,26,107,0.12); }
.sl-yr { font-family:var(--mono); font-size:11px; font-weight:700;
  color:var(--hot); width:32px; flex-shrink:0; padding-top:3px; }
.sl-pills { display:flex; flex-wrap:wrap; gap:6px; }
.stag { display:inline-block; background:rgba(255,26,107,0.07);
  border:1px solid rgba(255,26,107,0.18); border-radius:99px;
  padding:3px 12px; font-size:12px; color:#8C1848; }
.dim-txt { font-size:12px; color:rgba(28,8,24,0.3); }

/* ══ 7 MOOD ═══════════════════════════════════════════════ */
#s7 { background:var(--plum); }
.s7-kicker { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(255,184,212,0.35); margin-bottom:22px; }
.s7-title { font-family:var(--bold); font-weight:900;
  font-size:clamp(38px,7vw,84px); line-height:.88;
  letter-spacing:-0.03em; color:var(--cream); margin-bottom:44px; }
.s7-title em { color:var(--soft); font-style:normal; }
.spark-wrap { width:100%; max-width:680px; }
.spark-legend { display:flex; gap:18px; margin-top:16px; flex-wrap:wrap; }
.sleg { font-size:10px; letter-spacing:.09em; text-transform:uppercase;
  color:rgba(255,184,212,0.3); display:flex; align-items:center; gap:6px; }
.sleg-dot { width:7px; height:7px; border-radius:50%; flex-shrink:0; }

/* ══ 8 WORD CLOUD ═════════════════════════════════════════ */
#s8 { background:var(--hot); }
.s8-kicker { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(255,240,246,0.4); margin-bottom:22px; }
.s8-title { font-family:var(--bold); font-weight:900;
  font-size:clamp(38px,7vw,84px); line-height:.88;
  letter-spacing:-0.03em; color:#FFF0F6; margin-bottom:36px; }
.cloud-wrap { width:100%; max-width:620px; }
.bgrams { margin-top:24px; display:flex; flex-wrap:wrap; gap:8px; }
.btag { display:inline-block; background:rgba(255,240,246,0.1);
  border:1px solid rgba(255,240,246,0.2); border-radius:99px;
  padding:4px 12px; font-size:11px; color:rgba(255,240,246,0.8); }

/* ══ 9 CHAOS ══════════════════════════════════════════════ */
#s9 { background:var(--blush); }
.s9-kicker { font-size:10px; letter-spacing:.22em; text-transform:uppercase;
  color:rgba(255,26,107,0.45); margin-bottom:22px; }
.s9-title { font-family:var(--bold); font-weight:900;
  font-size:clamp(36px,7vw,80px); line-height:.88;
  letter-spacing:-0.03em; color:var(--ink); margin-bottom:40px; }
.stickers { display:flex; flex-wrap:wrap; gap:16px; max-width:640px; }
.sticker {
  flex:1; min-width:170px; max-width:230px;
  padding:20px 18px 18px; border-radius:4px;
  position:relative; transform:rotate(var(--r));
  box-shadow:2px 4px 20px rgba(28,8,24,0.12), 0 1px 0 rgba(255,255,255,0.6) inset;
  opacity:0;
  animation:stickin .5s calc(var(--i)*0.11s) cubic-bezier(.16,1,.3,1) both;
}
.card-in .sticker { opacity:1; }
@keyframes stickin {
  from { opacity:0; transform:rotate(var(--r)) scale(.7) translateY(20px); }
  to   { opacity:1; transform:rotate(var(--r)) scale(1); }
}
.sticker-tape {
  position:absolute; top:-8px; left:50%; transform:translateX(-50%);
  width:36px; height:16px; background:rgba(255,214,0,0.55);
  border-radius:2px;
}
.sticker-txt { font-family:var(--serif); font-style:italic;
  font-size:clamp(12px,1.8vw,14px); color:var(--ink); line-height:1.55; }

/* ══ MARQUEE ══════════════════════════════════════════════ */
.marquee-wrap { background:var(--hot); overflow:hidden;
  white-space:nowrap; padding:11px 0; position:relative; z-index:10; }
.marquee-inner { display:inline-block;
  animation:mq 24s linear infinite;
  font-family:var(--bold); font-size:12px; letter-spacing:.12em;
  color:rgba(255,240,246,0.7); }
@keyframes mq{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* ══ 10 END ═══════════════════════════════════════════════ */
#s10 { background:var(--mango-l); }
.end-daisy-svg { position:absolute; inset:0; pointer-events:none; overflow:visible; }
.end-name { font-family:var(--bold); font-weight:900;
  font-size:clamp(13vw,17vw,22vw); line-height:.82;
  letter-spacing:-0.04em; color:var(--ink); position:relative; z-index:2; }
.end-sub { font-family:var(--serif); font-style:italic;
  font-size:clamp(16px,2.5vw,24px); color:rgba(28,8,24,0.38);
  margin-top:16px; position:relative; z-index:2; }
.end-grid { display:flex; gap:clamp(20px,4vw,56px); flex-wrap:wrap;
  margin-top:36px; position:relative; z-index:2; }
.end-grid .ev { font-family:var(--bold); font-weight:700;
  font-size:clamp(24px,4.5vw,44px); color:var(--ink); }
.end-grid .el { font-size:9px; color:rgba(28,8,24,0.33); letter-spacing:.14em;
  text-transform:uppercase; margin-top:3px; }
.end-rule { width:44px; height:2px; background:rgba(28,8,24,0.15); margin:28px 0; position:relative; z-index:2; }
.end-note { font-family:var(--serif); font-style:italic;
  font-size:clamp(14px,1.8vw,18px); color:rgba(28,8,24,0.38);
  position:relative; z-index:2; }
</style>
</head>
<body>
<div id="pbar"></div>

<!-- ══════════════════════════════
     0 · COVER
══════════════════════════════ -->
<section class="slide" id="s0">
  <canvas id="bubble-canvas"></canvas>
  <svg class="cover-daisy-svg" id="daisySvg" viewBox="0 0 960 500" preserveAspectRatio="xMidYMid slice">
    __DAISIES_COVER__
  </svg>
  <div class="cover-tag rx">your chat · wrapped · __YEAR__</div>
  <div class="cover-name rx d1">__FIRST__</div>
  <div class="cover-serif rx d2">a data portrait 🌸</div>
  <div class="cover-scroll">scroll ↓</div>
</section>

<!-- torn divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#FF1A6B">
    <path d="M0,48 L0,18 C60,8 120,28 180,16 C240,4 300,24 360,14 C420,4 480,22 540,12 C600,2 660,20 720,10 C780,0 840,18 900,8 C960,-2 1020,16 1080,8 C1140,0 1200,18 1260,10 C1320,2 1380,20 1440,12 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     1 · NUMBERS
══════════════════════════════ -->
<section class="slide" id="s1" style="padding:0">
  <div class="s1-grid">
    <div class="s1-left rx">
      <div class="s1-ghost" aria-hidden="true">__TOTAL_RAW__</div>
      <div style="position:relative;z-index:2">
        <div class="s1-num" data-count="__TOTAL_RAW__">__TOTAL__</div>
        <div class="s1-lbl">messages sent</div>
      </div>
    </div>
    <div class="s1-right">
      <div class="s1-rule rx"></div>
      <div class="rx d1"><div class="mini-num" data-count="__WORDS_RAW__">__WORDS__</div><div class="mini-lbl">words typed</div></div>
      <div class="rx d2"><div class="mini-num">__AVG_LEN__</div><div class="mini-lbl">avg words / msg</div></div>
      <div class="rx d3"><div class="mini-num">__DAYS__</div><div class="mini-lbl">days active</div></div>
      <div class="rx d3"><div class="mini-num">__STREAK__</div><div class="mini-lbl">longest streak</div></div>
      <div class="s1-rule rx d4"></div>
      <div class="s1-note rx d4">she carried <strong style="color:#FFF0F6">__SHARE__%</strong> of the entire conversation</div>
    </div>
  </div>
</section>

<!-- torn divider (cream) -->
<div class="torn" style="background:var(--hot)">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#FFF8F2">
    <path d="M0,48 L0,22 C80,10 160,30 240,18 C320,6 400,26 480,14 C560,2 640,22 720,12 C800,2 880,20 960,10 C1040,0 1120,18 1200,10 C1280,2 1360,20 1440,14 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     2 · PEAK HOUR
══════════════════════════════ -->
<section class="slide" id="s2">
  <div class="s2-kicker rx">II — peak hour</div>
  <div class="s2-layout">
    <div class="s2-left">
      <div class="s2-hour rx d1">__PEAK_LABEL__</div>
      <div class="s2-desc rx d2">she texts most in the __PEAK_BUCKET__</div>
      <div class="rx d3">
        <div class="s2-pct">__PEAK_PCT__%</div>
        <div class="s2-pct-lbl">of all messages in __PEAK_BUCKET__ hours</div>
      </div>
    </div>
    <div class="rx d2">__RADIAL__</div>
  </div>
</section>

<!-- torn (plum) -->
<div class="torn" style="background:var(--cream)">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#12040E">
    <path d="M0,48 L0,16 C90,6 180,24 270,14 C360,4 450,22 540,12 C630,2 720,18 810,10 C900,2 990,16 1080,8 C1170,0 1260,16 1350,10 L1440,6 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     3 · REPLY SPEED
══════════════════════════════ -->
<section class="slide" id="s3">
  <div class="s3-kicker rx">III — how fast she replies</div>
  <div class="s3-big rx d1">__REPLY_AVG__</div>
  <div class="reply-grid rx d2">
    <div class="rcell"><div class="rv">__REPLY_AVG__</div><div class="rl">average</div></div>
    <div class="rcell"><div class="rv">__REPLY_FAST__</div><div class="rl">fastest ever</div></div>
    <div class="rcell"><div class="rv">__REPLY_P90__</div><div class="rl">90th %ile</div></div>
  </div>
  <div class="r-note rx d3">tracked across __REPLY_TOTAL__ replies</div>
</section>

<!-- torn (hot pink) -->
<div class="torn" style="background:var(--plum)">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#FF1A6B">
    <path d="M0,48 L0,20 C70,10 140,28 210,16 C280,4 350,24 420,14 C490,4 560,20 630,12 C700,4 770,18 840,10 C910,2 980,16 1050,8 C1120,0 1190,14 1260,8 C1330,2 1385,14 1440,10 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     4 · EMOJI ERA
══════════════════════════════ -->
<section class="slide" id="s4" style="padding-left:0;padding-right:0">
  <div class="s4-inner">
    <div class="s4-kicker rx">IV — emoji fingerprint</div>
    <div class="s4-title rx d1">her <em>emoji</em> era</div>
  </div>
  <div class="film-holes rx d2">
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
  </div>
  <div class="film-strip rx d2" id="filmStrip">__EMOJI_STRIP__</div>
  <div class="film-holes rx d2">
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
    <div class="fhole"></div><div class="fhole"></div><div class="fhole"></div>
  </div>
  <div class="s4-inner">
    <div class="rx d3" style="margin-top:28px">__ERA_ROWS__</div>
    <div class="et rx d4">__EMOJI_TOTAL__ emojis sent in total</div>
  </div>
</section>

<!-- marquee -->
<div class="marquee-wrap">
  <span class="marquee-inner">__MQ__&nbsp;&nbsp;&nbsp;&nbsp;__MQ__&nbsp;&nbsp;&nbsp;&nbsp;</span>
</div>

<!-- ══════════════════════════════
     5 · BURST VS ESSAY
══════════════════════════════ -->
<section class="slide" id="s5">
  <div class="s5-kicker rx">V — texting style</div>
  <div class="s5-layout">
    <div class="s5-left">
      <div class="s5-pct rx d1">__BURST_PCT__<span class="s5-sup">%</span></div>
      <div class="s5-lbl rx d2">of messages sent in rapid bursts</div>
      <div class="s5-note rx d3">avg burst: <strong>__BURST_AVG__ words</strong><br>avg solo: <strong>__SOLO_AVG__ words</strong></div>
    </div>
    <!-- Mogu Mogu cup illustration -->
    <div class="cup-wrap rx d2">
      <svg width="160" height="220" viewBox="0 0 160 220">
        <defs>
          <linearGradient id="cupG" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#FF88B4"/>
            <stop offset="100%" stop-color="#FF1A6B"/>
          </linearGradient>
          <clipPath id="cupClip">
            <path d="M28,40 L20,200 Q20,210 32,210 L128,210 Q140,210 140,200 L132,40 Z"/>
          </clipPath>
        </defs>
        <!-- cup body -->
        <path d="M28,40 L20,200 Q20,210 32,210 L128,210 Q140,210 140,200 L132,40 Z"
              fill="none" stroke="#FF88B4" stroke-width="2.5" opacity="0.6"/>
        <!-- liquid fill (height based on burst%) -->
        <rect x="21" y="0" width="118" height="210" fill="url(#cupG)" opacity="0.18"
              clip-path="url(#cupClip)"
              style="transform:translateY(__BURST_PCT_RAW__%);transition:transform 1.2s cubic-bezier(.16,1,.3,1)"
              id="cupLiquid"/>
        <!-- bubbles inside cup -->
        <circle cx="55" cy="160" r="7" class="cup-bub" style="animation-delay:0s"/>
        <circle cx="80" cy="175" r="10" class="cup-bub" style="animation-delay:.4s"/>
        <circle cx="105" cy="155" r="6" class="cup-bub" style="animation-delay:.8s"/>
        <circle cx="68" cy="185" r="5" class="cup-bub" style="animation-delay:.2s"/>
        <circle cx="95" cy="168" r="8" class="cup-bub" style="animation-delay:.6s"/>
        <!-- straw -->
        <rect x="85" y="-10" width="8" height="90" rx="4" fill="#FFB8D4" opacity="0.7"/>
        <!-- label band -->
        <rect x="22" y="100" width="116" height="44" fill="rgba(255,26,107,0.08)"/>
        <text x="80" y="118" text-anchor="middle" font-size="9" fill="#FF88B4"
              font-family="Space Mono,monospace" opacity="0.6">MOGU MOGU</text>
        <text x="80" y="132" text-anchor="middle" font-size="7" fill="#FF88B4"
              font-family="Space Mono,monospace" opacity="0.4">BURST FLAVOUR</text>
        <!-- lid -->
        <ellipse cx="80" cy="40" rx="56" ry="10" fill="none" stroke="#FF88B4" stroke-width="2" opacity="0.5"/>
        <ellipse cx="80" cy="40" rx="56" ry="10" fill="rgba(255,136,180,0.08)"/>
      </svg>
    </div>
  </div>
</section>

<!-- torn (cream) -->
<div class="torn" style="background:var(--mango)">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#FFF8F2">
    <path d="M0,48 L0,14 C100,4 200,24 300,14 C400,4 500,22 600,12 C700,2 800,18 900,10 C1000,2 1100,16 1200,8 C1300,0 1370,14 1440,10 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     6 · SLANG ERA
══════════════════════════════ -->
<section class="slide" id="s6">
  <div class="s6-kicker rx">VI — slang era report</div>
  <div class="s6-title rx d1">words she<br>lived in</div>
  <div class="rx d2">__SLANG_BLOCKS__</div>
</section>

<!-- torn (plum) -->
<div class="torn" style="background:var(--cream)">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#12040E">
    <path d="M0,48 L0,18 C80,8 160,26 240,16 C320,6 400,24 480,14 C560,4 640,20 720,12 C800,4 880,18 960,10 C1040,2 1120,16 1200,8 C1280,0 1360,14 1440,8 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     7 · MOOD
══════════════════════════════ -->
<section class="slide" id="s7">
  <div class="s7-kicker rx">VII — emotional journey</div>
  <div class="s7-title rx d1">her <em>mood</em><br>across time</div>
  <div class="spark-wrap rx d2">
    __SPARK__
    <div class="spark-legend">
      <div class="sleg"><div class="sleg-dot" style="background:#FFD840"></div>happy</div>
      <div class="sleg"><div class="sleg-dot" style="background:#FFB8D4"></div>neutral</div>
      <div class="sleg"><div class="sleg-dot" style="background:#FF88B4"></div>low</div>
    </div>
  </div>
</section>

<!-- torn (hot pink) -->
<div class="torn" style="background:var(--plum)">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#FF1A6B">
    <path d="M0,48 L0,16 C90,6 180,24 270,14 C360,4 450,22 540,12 C630,2 720,18 810,10 C900,2 990,16 1080,8 C1170,0 1260,14 1350,8 L1440,6 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     8 · WORD CLOUD (daisy)
══════════════════════════════ -->
<section class="slide" id="s8">
  <div class="s8-kicker rx">VIII — what lives in her head</div>
  <div class="s8-title rx d1">her word<br>garden 🌼</div>
  <div class="cloud-wrap rx d2">__WORD_CLOUD__</div>
  <div class="bgrams rx d3">__BGRAMS__</div>
</section>

<!-- torn (blush) -->
<div class="torn" style="background:var(--hot)">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#FFE8F4">
    <path d="M0,48 L0,20 C70,10 140,28 210,18 C280,8 350,24 420,14 C490,4 560,20 630,12 C700,4 770,18 840,10 C910,2 980,16 1050,8 C1120,0 1190,14 1260,8 C1330,2 1390,14 1440,10 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     9 · CHAOS
══════════════════════════════ -->
<section class="slide" id="s9">
  <div class="s9-kicker rx">IX — hall of chaos</div>
  <div class="s9-title rx d1">her most<br>unhinged<br>moments</div>
  <div class="stickers rx d2" id="stickerWrap">__CHAOS_HTML__</div>
</section>

<!-- torn (mango yellow) -->
<div class="torn" style="background:var(--blush)">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="#FFD060">
    <path d="M0,48 L0,18 C100,8 200,26 300,16 C400,6 500,22 600,12 C700,2 800,18 900,10 C1000,2 1100,16 1200,8 C1300,0 1370,12 1440,8 L1440,48 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     10 · END
══════════════════════════════ -->
<section class="slide" id="s10">
  <svg class="end-daisy-svg" viewBox="0 0 960 500" preserveAspectRatio="xMidYMid slice" id="endDaisySvg">
    __DAISIES_END__
  </svg>
  <div class="end-name rx">__FIRST__</div>
  <div class="end-sub rx d1">a portrait in messages 🌸</div>
  <div class="end-grid rx d2">
    <div><div class="ev">__TOTAL__</div><div class="el">messages</div></div>
    <div><div class="ev">__WORDS__</div><div class="el">words</div></div>
  </div>
  <div class="end-rule rx d3"></div>
  <div class="end-note rx d3">and somehow still not enough.</div>
</section>


<script>
// ── Progress bar ──────────────────────────────────────────────────────────────
const pbar = document.getElementById('pbar');
window.addEventListener('scroll', () => {
  const p = window.scrollY / (document.body.scrollHeight - window.innerHeight);
  pbar.style.width = Math.min(p*100,100)+'%';
},{passive:true});

// ── Reveal on scroll ──────────────────────────────────────────────────────────
const io = new IntersectionObserver(entries => {
  entries.forEach(e => { if(e.isIntersecting) e.target.classList.add('in'); });
},{threshold:0.14});
document.querySelectorAll('.rx').forEach(el => io.observe(el));
document.querySelectorAll('#s0 .rx').forEach(el => el.classList.add('in'));

// ── Counter animation ─────────────────────────────────────────────────────────
function countUp(el, target, dur=1600) {
  let t0 = null;
  (function step(ts) {
    if(!t0) t0=ts;
    const p = Math.min((ts-t0)/dur,1);
    const e = 1-Math.pow(1-p,4);
    el.textContent = Math.floor(e*target).toLocaleString();
    if(p<1) requestAnimationFrame(step);
  })(performance.now());
}
const cio = new IntersectionObserver(entries => {
  entries.forEach(e => {
    if(e.isIntersecting) {
      const v = parseInt(e.target.dataset.count);
      if(!isNaN(v)) countUp(e.target, v);
      cio.unobserve(e.target);
    }
  });
},{threshold:0.3});
document.querySelectorAll('[data-count]').forEach(el => cio.observe(el));

// ── Daisy bloom ───────────────────────────────────────────────────────────────
function bloomDaisies(svgEl) {
  if(!svgEl) return;
  svgEl.querySelectorAll('.daisy-g').forEach((g,i) => {
    setTimeout(() => g.classList.add('bloomed'), i*180);
  });
}
const daisyIo = new IntersectionObserver(entries => {
  entries.forEach(e => { if(e.isIntersecting) bloomDaisies(e.target); });
},{threshold:0.1});
['daisySvg','endDaisySvg'].forEach(id => {
  const el = document.getElementById(id);
  if(el) daisyIo.observe(el);
});

// ── Mogu Mogu bubble canvas (cover) ──────────────────────────────────────────
const bcanvas = document.getElementById('bubble-canvas');
const bctx = bcanvas.getContext('2d');
const BUBBLES = __BUBBLES__;

function resizeBubbleCanvas() {
  bcanvas.width  = window.innerWidth;
  bcanvas.height = window.innerHeight;
}
resizeBubbleCanvas();
window.addEventListener('resize', resizeBubbleCanvas);

// Initialize bubble positions
BUBBLES.forEach(b => {
  b.px = b.x * bcanvas.width;
  b.py = bcanvas.height * (0.3 + Math.random()*0.7);
});

let frame = 0;
function drawBubbles() {
  bctx.clearRect(0,0,bcanvas.width,bcanvas.height);
  frame++;
  BUBBLES.forEach(b => {
    b.py -= b.speed * 0.4;
    b.px += Math.sin(frame*0.012 + b.phase) * 0.3;
    if(b.py < -b.r*2) {
      b.py = bcanvas.height + b.r;
      b.px = b.x * bcanvas.width;
    }
    bctx.beginPath();
    bctx.arc(b.px, b.py, b.r, 0, Math.PI*2);
    bctx.fillStyle = `rgba(255,184,212,${b.opacity})`;
    bctx.fill();
    // highlight
    bctx.beginPath();
    bctx.arc(b.px - b.r*0.28, b.py - b.r*0.3, b.r*0.25, 0, Math.PI*2);
    bctx.fillStyle = `rgba(255,255,255,${b.opacity*1.2})`;
    bctx.fill();
  });
  requestAnimationFrame(drawBubbles);
}
drawBubbles();

// ── Film strip drag ───────────────────────────────────────────────────────────
const strip = document.getElementById('filmStrip');
if(strip) {
  let drag=false, sx, sl;
  strip.addEventListener('mousedown', e=>{drag=true;sx=e.pageX-strip.offsetLeft;sl=strip.scrollLeft;strip.style.cursor='grabbing';});
  strip.addEventListener('mouseleave',()=>{drag=false;strip.style.cursor='grab';});
  strip.addEventListener('mouseup',  ()=>{drag=false;strip.style.cursor='grab';});
  strip.addEventListener('mousemove', e=>{if(!drag)return;e.preventDefault();strip.scrollLeft=sl-(e.pageX-strip.offsetLeft-sx);});
  strip.addEventListener('touchstart',e=>{sx=e.touches[0].pageX;sl=strip.scrollLeft;},{passive:true});
  strip.addEventListener('touchmove', e=>{strip.scrollLeft=sl-(e.touches[0].pageX-sx);},{passive:true});
}

// ── Sticker reveal ────────────────────────────────────────────────────────────
const sio = new IntersectionObserver(entries=>{
  entries.forEach(e=>{if(e.isIntersecting) e.target.classList.add('card-in');});
},{threshold:0.2});
const sw = document.getElementById('stickerWrap');
if(sw) sio.observe(sw);

// ── Mogu cup liquid fill on scroll into view ──────────────────────────────────
const cup = document.getElementById('cupLiquid');
if(cup) {
  const cupIo = new IntersectionObserver(entries=>{
    entries.forEach(e=>{
      if(e.isIntersecting) {
        cup.style.transform = 'translateY(0)';
        cupIo.unobserve(e.target);
      }
    });
  },{threshold:0.4});
  cupIo.observe(cup);
}
</script>
</body>
</html>"""


def main():
    print("Loading chats…")
    all_msgs = load(JSONL_IN)
    for m in all_msgs: m["_dt"] = parse_dt(m)
    her = [m for m in all_msgs if m["sender"] == HER]
    print(f"  {len(all_msgs)} total  ·  {len(her)} from {HER}")
    print("Computing stats…")
    stats = {
        "name":   HER,
        "basic":  basic_stats(her, all_msgs),
        "peak":   peak_hour(her),
        "reply":  reply_speed(all_msgs, HER, YOU),
        "emoji":  emoji_personality(her),
        "burst":  burst_vs_essay(her),
        "slang":  slang_era(her),
        "mood":   mood_timeline(her),
        "topics": whats_in_her_head(her),
        "chaos":  most_chaotic(her),
    }
    with open("stats.json","w",encoding="utf-8") as f:
        json.dump(stats,f,ensure_ascii=False,indent=2,default=str)
    print("Building HTML…")
    with open(HTML_OUT,"w",encoding="utf-8") as f:
        f.write(build_html(stats))
    print(f"✓  {HTML_OUT}")

if __name__ == "__main__":
    main()