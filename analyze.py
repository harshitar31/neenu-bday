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

def daisy_word_cloud(top):
    """Words arranged in a daisy / flower orbit pattern."""
    words = top.get("top_words", [])
    if not words:
        return '<p style="color:#FF88B4;font-size:14px">not enough data</p>'
    W, H = 600, 460
    cx, cy = W//2, H//2 + 10
    mc = words[0]["count"]
    parts = []

    # Center word in dark brown circle (doodle style)
    cw = words[0]
    r_c = 56
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="{r_c}" fill="none" stroke="#2C1810" stroke-width="2" stroke-dasharray="8,4"/>')
    parts.append(f'<text x="{cx}" y="{cy+6}" text-anchor="middle" '
                 f'font-size="20" font-family="' + "Caveat" + '", cursive" '
                 f'fill="#2C1810" font-weight="700">{cw["word"]}</text>')

    # Ring 1 — 6 words on doodle petal circles
    ring1 = words[1:7]
    r1 = 148
    for i, w in enumerate(ring1):
        ang = math.radians(i * 360/max(len(ring1),1) - 90)
        wx = cx + r1 * math.cos(ang)
        wy = cy + r1 * math.sin(ang)
        sz = 14 + int((w["count"]/mc) * 6)
        rc = 36 + int((w["count"]/mc) * 10)
        # stem line
        lx1 = cx + r_c*math.cos(ang); ly1 = cy + r_c*math.sin(ang)
        lx2 = wx - rc*math.cos(ang);  ly2 = wy - rc*math.sin(ang)
        parts.append(f'<line x1="{lx1:.1f}" y1="{ly1:.1f}" x2="{lx2:.1f}" y2="{ly2:.1f}" '
                     f'stroke="#2C1810" stroke-width="1.5" opacity="0.6"/>')
        parts.append(f'<circle cx="{wx:.1f}" cy="{wy:.1f}" r="{rc}" fill="none" stroke="#2C1810" stroke-width="1.5"/>')
        parts.append(f'<text x="{wx:.1f}" y="{wy+5:.1f}" text-anchor="middle" '
                     f'font-size="{sz}" font-family="' + "Caveat" + '", cursive" '
                     f'fill="#2C1810">{w["word"]}</text>')

    # Ring 2 — remaining words, scattered like scribbles
    ring2 = words[7:13]
    r2 = 250
    for i, w in enumerate(ring2):
        ang = math.radians(i * 360/max(len(ring2),1) - 60)
        wx = cx + r2 * math.cos(ang)
        wy = cy + r2 * math.sin(ang)
        sz = 12 + int((w["count"]/mc) * 5)
        op = round(0.4 + 0.4*(w["count"]/mc), 2)
        rot = random.uniform(-15, 15)
        parts.append(f'<text x="{wx:.1f}" y="{wy:.1f}" text-anchor="middle" '
                     f'font-size="{sz}" font-family="' + "Caveat" + '", cursive" '
                     f'fill="#2C1810" opacity="{op}" transform="rotate({rot:.1f},{wx:.1f},{wy:.1f})">{w["word"]}</text>')

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

    # Emoji film strip
    emoji_strip = "".join(
        f'<div class="ff"><span class="fe">{e["emoji"]}</span>'
        f'<span class="fc">{e["count"]}</span></div>'
        for e in em.get("top",[])[:8])
    by_year = em.get("by_year", {})
    all_years = list(by_year.keys())
    latest_year = max(all_years) if all_years else None
    era_sections = []
    for yr2, items in by_year.items():
        old_cls = "" if yr2 == latest_year else " old"
        cards = "".join(
            f'<div class="case-card{old_cls}">'
            f'<div class="case-emoji">{x["emoji"]}</div>'
            f'<div class="case-count">{x["count"]}</div>'
            f'</div>'
            for x in items[:8]
        )
        era_sections.append(
            f'<div class="era-section">'
            f'<div class="era-section-year">{yr2}</div>'
            f'<div class="case-grid">{cards}</div>'
            f'</div>'
        )
    era_rows = "".join(era_sections)

    # Slang
    slang_blocks=""
    for e in sl.get("eras",[]):
        if not e["words"]: continue
        # random rotation for each stamp pill
        pills="".join(
            f'<span class="stag" style="--rand-rot:{random.uniform(-3,3):.1f}">{w}</span>'
            for w in e["words"]
        )
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
        "__BUBBLES__": bubble_data,
        "__TOTAL_RAW__": str(b['total']),
        "__WORDS_RAW__": str(b['words']),
        "__BURST_PCT_RAW__": str(bur["burst_pct"]),
        "__PEAK_HOUR_DEG__": str(int((ph.get("hour", 10) % 12) / 12 * 360)),
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
<title>__FIRST__'s Wrapped </title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link href="https://fonts.googleapis.com/css2?family=Caveat:wght@400;600;700&family=DM+Serif+Display:ital@0;1&family=Unbounded:wght@300;700;900&family=Space+Mono:wght@400;700&display=swap" rel="stylesheet">
<style>
*,*::before,*::after { box-sizing:border-box; margin:0; padding:0; }
:root {
  /* Still Open palette */
  --paper:   #FDF6E3;
  --amber:   #F5A623;
  --pink:    #FF6B9D;
  --ink:     #2C1810;
  --dark-bg: #1A120A;
  --counter: #2E1F0F;
  --glass:   rgba(255,252,240,0.08);
  --serif:   'DM Serif Display', Georgia, serif;
  --hand:    'Caveat', cursive;
  --mono:    'Space Mono', monospace;
  --bold:    'Unbounded', sans-serif;
  /* legacy compat */
  --cream:   #FDF6E3;
  --hot:     #FF6B9D;
  --soft:    #FFBAD6;
  --plum:    #1A120A;
  --mango:   #F5A623;
  --mango-l: #FFD080;
}
html { scroll-behavior:smooth; background:var(--dark-bg); }
body { font-family:var(--mono); color:var(--ink); overflow-x:hidden; }

/* warm paper grain — fixed overlay */
body::after {
  content:''; position:fixed; inset:0; z-index:997; pointer-events:none;
  background:url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.75' numOctaves='4'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)' opacity='0.038'/%3E%3C/svg%3E");
}

/* progress bar — pink checkered */
#pbar {
  position: fixed; top: 0; left: 0; height: 6px; z-index: 1000;
  background-color: #FF1A6B;
  background-image:
    linear-gradient(rgba(255,255,255,0.7) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.7) 1px, transparent 1px);
  background-size: 6px 6px;
  width: 0; transition: width .1s linear;
  border-radius: 0 99px 99px 0;
  box-shadow: 0 0 15px rgba(255, 107, 157, 0.8), 0 0 5px rgba(255, 255, 255, 0.6);
}

/* ── SLIDES ── */
.slide {
  min-height:100vh; width:100%;
  display:flex; flex-direction:column; justify-content:center;
  position:relative; overflow:hidden;
  padding:clamp(48px,7vh,96px) clamp(24px,5vw,80px);
}

/* reveal */
.rx { opacity:0; transform:translateY(28px);
  transition:opacity .9s cubic-bezier(.16,1,.3,1),
             transform .9s cubic-bezier(.16,1,.3,1); }
.rx.in { opacity:1; transform:none; }
.rx.d1{transition-delay:.12s}.rx.d2{transition-delay:.26s}
.rx.d3{transition-delay:.40s}.rx.d4{transition-delay:.54s}

/* ── global fluorescent tube glow (top of each slide) ── */
.fluoro {
  position:absolute; top:0; left:0; right:0; height:120px;
  background:linear-gradient(180deg,rgba(220,230,255,0.18) 0%,transparent 100%);
  pointer-events:none; z-index:2;
  animation:flicker 8s 1s ease-in-out forwards;
}
@keyframes flicker {
  0%  {opacity:1} 4%  {opacity:.7} 6%  {opacity:1} 8%  {opacity:.5}
  10% {opacity:1} 12% {opacity:.8} 14% {opacity:1}
  100%{opacity:1}
}

/* ── rain overlay (fixed, only visible on rain-slide class) ── */
.rain-layer {
  position:absolute; inset:0; z-index:3; pointer-events:none; overflow:hidden;
}
.rain-layer line {
  stroke:rgba(180,210,255,0.18); stroke-width:1;
  animation:rainFall linear infinite;
}
@keyframes rainFall {
  from { transform:translateY(-100px); }
  to   { transform:translateY(110vh); }
}

/* ══ 0 COVER — The Window (slide1.png) ════════════════════════════════════════════════════ */
#s0 {
  background: url('slide1.png') center center / cover no-repeat;
  display:flex; flex-direction:column; justify-content:flex-end; align-items:center;
  padding: clamp(40px,6vh,80px) clamp(24px,5vw,60px);
  min-height:100vh; overflow:hidden; position:relative;
}
/* 'enter store' button */
.enter-btn {
  background-color: #FFD1E3;
  background-image:
    linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px);
  background-size: 8px 8px;
  border: 2px solid #FFF;
  color: #C2185B; /* Dark pink text */
  font-family: var(--hand); font-size: clamp(22px,3.5vw,32px);
  padding: 12px 40px; border-radius: 99px;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(255,209,227,0.4);
  text-transform: lowercase;
  margin-bottom: 4vh;
  z-index: 10;
  text-shadow: none; /* Removed so dark pink text is crisp */
}
.enter-btn:hover {
  background-color: #FFB3CD;
  box-shadow: 0 6px 24px rgba(255,209,227,0.6);
  transform: translateY(-2px);
}


/* ══ TORN DIVIDER ══════════════════════════════════════════ */
.torn {
  width:100%; overflow:hidden; position:relative; z-index:10;
  height:48px; margin:-24px 0;
  background: transparent;
}
.torn svg { display:block; width:100%; height:100%; fill: rgba(255, 220, 232, 0.8); }

/* ══ 1 NUMBERS (slide1.png) ════════════════════════════════════════════════ */
#s1 {
  background: url('s1.png') center center / cover no-repeat;
  display: flex; flex-direction: column; justify-content: flex-end; align-items: center;
  padding: clamp(40px,6vh,80px) clamp(24px,5vw,60px);
  min-height: 100vh; overflow: hidden; position: relative;
}
.down-btn {
  background-color: #FFD1E3;
  background-image:
    linear-gradient(rgba(255,255,255,0.6) 1px, transparent 1px),
    linear-gradient(90deg, rgba(255,255,255,0.6) 1px, transparent 1px);
  background-size: 8px 8px;
  border: 2px solid #FFF;
  color: #C2185B;
  font-size: 28px;
  width: 64px; height: 64px; border-radius: 50%;
  display: flex; align-items: center; justify-content: center;
  cursor: pointer;
  transition: all 0.3s ease;
  box-shadow: 0 4px 16px rgba(255,209,227,0.4);
  position: absolute; right: 4vw; bottom: 4vh;
  z-index: 10;
}
.down-btn:hover {
  background-color: #FFB3CD;
  box-shadow: 0 6px 24px rgba(255,209,227,0.6);
  transform: translateY(-2px);
}

/* ══ 2 PEAK HOUR (slide2.png) ═══════════════════════════════════════════ */
#s2 {
  background: url('s2.png') center center / cover no-repeat;
  min-height: 100vh; position: relative; overflow: hidden;
}

/* ══ 3 REPLY SPEED (slide3.png) ═══════════════════════════════════ */
#s3 {
  background: url('s3.png') center center / cover no-repeat;
  min-height: 100vh; position: relative; overflow: hidden;
}

/* ══ 4 EMOJI ERA (slide4.png) ═══════════════════════════════════ */
#s4 {
  background: url('s4.png') center center / cover no-repeat;
  min-height: 100vh; position: relative; overflow: hidden;
}

/* ══ 5 BURST VS ESSAY (slide5.png) ════════════════════════════════════ */
#s5 {
  background: url('s5.png') center center / cover no-repeat;
  min-height: 100vh; position: relative; overflow: hidden;
}

/* ══ 6 SLANG ERA (slide6.png) ════════════════════════════════════ */
#s6 {
  background: url('s6.png') center center / cover no-repeat;
  min-height: 100vh; position: relative; overflow: hidden;
}

/* ══ 8 WORD CLOUD (slide8.png) ════════════════════════════════ */
#s8 {
  background: url('s8.png') center center / cover no-repeat;
  min-height: 100vh; position: relative; overflow: hidden;
}

/* ══ 9 CHAOS (slide9.png) ══════════════════════════════════════════════ */
#s9 {
  background: url('s9.png') center center / cover no-repeat;
  min-height: 100vh; position: relative; overflow: hidden;
}

/* ══ MARQUEE ══════════════════════════════════════════════ */
.marquee-wrap { background:var(--hot); overflow:hidden;
  white-space:nowrap; padding:11px 0; position:relative; z-index:10; }
.marquee-inner { display:inline-block;
  animation:mq 24s linear infinite;
  font-family:var(--bold); font-size:12px; letter-spacing:.12em;
  color:rgba(255,240,246,0.7); }
@keyframes mq{from{transform:translateX(0)}to{transform:translateX(-50%)}}

/* ══ 10 END (slide10.png) ═══════════════════════════════════════════════ */
#s10 {
  background: url('s10.png') center center / cover no-repeat;
  min-height: 100vh; position: relative; overflow: hidden;
}
</style>
</head>
<body>
<div id="pbar"></div>

<!-- ══════════════════════════════
     0 · COVER — The Window
══════════════════════════════ -->
<section class="slide" id="s0">
  <button class="enter-btn rx" onclick="document.getElementById('s1').scrollIntoView({behavior: 'smooth'})">
    enter store
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     1 · NUMBERS — The Receipt
══════════════════════════════ -->
<section class="slide" id="s1">
  <button class="down-btn rx" onclick="document.getElementById('s2').scrollIntoView({behavior: 'smooth'})">
    &darr;
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     2 · PEAK HOUR — The Clock
══════════════════════════════ -->
<section class="slide" id="s2">
  <button class="down-btn rx" onclick="document.getElementById('s3').scrollIntoView({behavior: 'smooth'})">
    &darr;
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     3 · REPLY SPEED — The Order Chit
══════════════════════════════ -->
<section class="slide" id="s3">
  <button class="down-btn rx" onclick="document.getElementById('s4').scrollIntoView({behavior: 'smooth'})">
    &darr;
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     4 · EMOJI ERA — The Display Case
══════════════════════════════ -->
<section class="slide" id="s4">
  <button class="down-btn rx" onclick="document.getElementById('s5').scrollIntoView({behavior: 'smooth'})">
    &darr;
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     5 · BURST VS ESSAY — Chalkboard
══════════════════════════════ -->
<section class="slide" id="s5">
  <button class="down-btn rx" onclick="document.getElementById('s6').scrollIntoView({behavior: 'smooth'})">
    &darr;
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     6 · SLANG ERA — Monsoon Letter
══════════════════════════════ -->
<section class="slide" id="s6">
  <button class="down-btn rx" onclick="document.getElementById('s8').scrollIntoView({behavior: 'smooth'})">
    &darr;
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     8 · WORD CLOUD
══════════════════════════════ -->
<section class="slide" id="s8">
  <button class="down-btn rx" onclick="document.getElementById('s9').scrollIntoView({behavior: 'smooth'})">
    &darr;
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     9 · CHAOS
══════════════════════════════ -->
<section class="slide" id="s9">
  <button class="down-btn rx" onclick="document.getElementById('s10').scrollIntoView({behavior: 'smooth'})">
    &darr;
  </button>
</section>

<!-- torn subtle divider -->
<div class="torn">
  <svg viewBox="0 0 1440 48" preserveAspectRatio="none" fill="rgba(255, 255, 255, 0.6)">
    <path d="M 0,14 C 100,4 200,24 300,14 C 400,4 500,22 600,12 C 700,2 800,18 900,10 C 1000,2 1100,16 1200,8 C 1300,0 1370,14 1440,10 L 1440,34 C 1370,38 1300,24 1200,32 C 1100,40 1000,26 900,34 C 800,42 700,26 600,36 C 500,46 400,28 300,38 C 200,48 100,28 0,38 Z"/>
  </svg>
</div>

<!-- ══════════════════════════════
     10 · END
══════════════════════════════ -->
<section class="slide" id="s10">
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

// ── Share bar fill ────────────────────────────────────────────────────────────
const shareBar = document.getElementById('shareBar');
if(shareBar) {
  const sbIo = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if(e.isIntersecting) {
        shareBar.style.width = '__SHARE__' + '%';
        sbIo.unobserve(e.target);
      }
    });
  },{threshold:0.4});
  sbIo.observe(shareBar);
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