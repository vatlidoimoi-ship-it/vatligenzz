"""Deterministic slide typography and physically constrained SVG schematics."""
from html import escape
import math
import re
from pathlib import Path


def slide_markup(text):
    lines = [line.strip() for line in str(text).splitlines() if line.strip()]
    cards = []
    for line in lines:
        option = re.match(r'^([A-D])[.)]\s*(.+)', line)
        if option:
            cards.append(f'<div class="slide-unit choice"><span class="choice-letter">{option[1]}</span><span>{escape(option[2])}</span></div>')
        else:
            cards.append(f'<div class="slide-unit key-line">{escape(line)}</div>')
    return ''.join(cards)


def physics_svg(diagram, theme):
    if not isinstance(diagram, dict):
        return ''
    kind = diagram.get('type')
    labels = diagram.get('labels') if isinstance(diagram.get('labels'), dict) else {}
    ink, accent, muted = theme['text'], theme['accent'], theme['muted']
    def text(x, y, value, color=ink, size=22):
        return f'<text x="{x}" y="{y}" fill="{color}" font-size="{size}" text-anchor="middle">{escape(str(value)[:48])}</text>'
    def line(x1,y1,x2,y2,color=ink,arrow=False,dash=False):
        return f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="3"' + (' marker-end="url(#arrow)"' if arrow else '') + (' stroke-dasharray="5 5"' if dash else '') + '/>'
    content = []
    caption = ''
    if kind == 'pendulum':
        try:
            angle = float(diagram.get('angle_deg', 6))
        except (TypeError, ValueError):
            return ''
        if not math.isfinite(angle) or not 0 < angle <= 10:
            return ''
        a = math.radians(angle)
        x, y = 200 + 235 * math.sin(a), 55 + 235 * math.cos(a)
        content += [line(145,45,255,45), line(200,55,200,315,muted,dash=True),
                    line(200,55,x,y,accent),
                    f'<circle cx="200" cy="55" r="5" fill="{ink}"/>',
                    f'<circle cx="{x}" cy="{y}" r="13" fill="{accent}"/>',
                    text(176,79,'O'),text(269,174,labels.get('length','ℓ')),
                    text(287,246,f'α₀ = {angle:g}°' if diagram.get('show_angle', True) else 'Góc nhỏ'),text(162,318,'VTCB',muted,18),
                    text(210,30,'Con lắc đơn',ink,24)]
        caption = 'Dây không dãn · bỏ qua ma sát'
    elif kind == 'spring':
        content += [line(40,95,40,220),line(40,205,380,205,muted),
                    f'<path d="M40 155 L60 155 L70 135 L90 175 L110 135 L130 175 L150 135 L170 175 L190 135 L210 155 L230 155" fill="none" stroke="{accent}" stroke-width="3"/>',
                    f'<rect x="230" y="125" width="65" height="80" rx="8" fill="{theme["accent_light"]}" stroke="{ink}" stroke-width="3"/>',
                    text(260,174,labels.get('mass','m'),size=18),text(145,103,labels.get('stiffness','k'),size=20),
                    line(215,235,215,275,muted,dash=True),line(75,265,370,265,muted,True),
                    text(215,298,'O',muted),text(370,298,'x',muted),text(210,50,'Con lắc lò xo',size=24)]
        caption = 'Sơ đồ ngang · O là vị trí cân bằng'
    elif kind == 'wave':
        # Two complete spatial periods; amplitude is equilibrium-to-crest.
        points = ' '.join(f'{x:.2f},{160-65*math.sin(2*math.pi*(x-40)/160):.2f}' for x in range(40,361,2))
        content += [line(30,160,380,160,muted,True), text(375,188,'x',muted),
                    f'<polyline points="{points}" fill="none" stroke="{accent}" stroke-width="4"/>',
                    line(80,160,80,95,accent),text(61,126,'A',accent),
                    line(80,69,240,69,ink),line(80,63,80,75),line(240,63,240,75),text(160,51,'λ')]
        caption = 'A: biên độ · λ: một bước sóng'
    elif kind == 'circuit':
        topology = diagram.get('topology', 'single')
        if topology not in {'single', 'series', 'parallel'}:
            return ''
        if topology == 'single':
            names = [labels.get('R', 'R')]
        else:
            names = diagram.get('resistors')
            if not isinstance(names,list) or len(names)!=2 or not all(isinstance(n,str) and 0<len(n)<30 for n in names):
                return ''
        # Source interrupts the lower wire; resistor interrupts each relevant branch.
        content += [line(60,90,60,255),line(350,90,350,255),line(60,255,191,255),line(209,255,350,255),
                    line(191,232,191,278),line(209,243,209,267),text(178,227,'+'),text(225,242,'−'),
                    text(205,313,labels.get('U','U'))]
        def resistor(x,y,name):
            return [f'<rect x="{x}" y="{y-12}" width="72" height="24" fill="{theme["card"]}" stroke="{accent}" stroke-width="3"/>',text(x+36,y-25,name)]
        if topology=='single':
            content += [line(60,90,168,90),*resistor(168,90,names[0]),line(240,90,350,90)]
        elif topology=='series':
            content += [line(60,90,90,90),*resistor(90,90,names[0]),line(162,90,248,90),*resistor(248,90,names[1]),line(320,90,350,90)]
        else:
            for y,name in zip([90,172],names):
                content += [line(60,y,168,y),*resistor(168,y,name),line(240,y,350,y)]
        caption = {'single':'Nguồn điện và điện trở','series':'Hai điện trở mắc nối tiếp','parallel':'Hai điện trở mắc song song'}[topology]
    elif kind in {'force','motion'}:
        vectors = diagram.get('vectors')
        if not isinstance(vectors,list) or not 1<=len(vectors)<=4:
            return ''  # Never invent normal force, gravity or force direction.
        content += [f'<rect x="168" y="143" width="74" height="54" rx="9" fill="{theme["accent_light"]}" stroke="{ink}" stroke-width="2"/>',text(205,177,labels.get('m','Vật'),size=17)]
        directions={'right':(242,170,348,170,326,146),'left':(168,170,62,170,85,146),
                    'up':(205,143,205,55,244,67),'down':(205,197,205,288,249,281)}
        seen=set()
        for vector in vectors:
            if not isinstance(vector,dict) or vector.get('direction') not in directions or vector['direction'] in seen:
                return ''
            seen.add(vector['direction'])
            x1,y1,x2,y2,tx,ty=directions[vector['direction']]
            content += [line(x1,y1,x2,y2,accent,True),text(tx,ty,vector.get('label',''),size=18)]
        caption = 'Sơ đồ hướng vectơ · không theo tỉ lệ độ lớn'
    elif kind == 'optics':
        try:
            f, u = float(diagram['focal_length']), float(diagram['object_distance'])
            if not all(math.isfinite(v) for v in [f,u]) or not 0 < f < u or u/f>8 or u/f<1.2:
                return ''
        except (KeyError,TypeError,ValueError):
            return ''
        v=f/(1-f/u)
        if not math.isfinite(v):
            return ''
        scale=150/max(u,v)
        center=205; ox=center-u*scale; ix=center+v*scale
        h=min(65,65*u/v); ih=h*v/u
        content += [line(25,165,390,165,muted),line(center,65,center,265,accent),
                    f'<path d="M197 77 L205 65 L213 77 M197 253 L205 265 L213 253" fill="none" stroke="{accent}" stroke-width="3"/>',
                    line(ox,165,ox,165-h,ink,True),line(ix,165,ix,165+ih,ink,True),
                    line(ox,165-h,center,165-h,accent),line(center,165-h,ix,165+ih,accent),
                    line(ox,165-h,ix,165+ih,ink),text(ox,145-h,'B'),text(ix,192+ih,'B′'),
                    text(center-f*scale,190,'F'),text(center+f*scale,190,'F′'),text(center,190,'O')]
        caption='Thấu kính hội tụ · vật ngoài tiêu điểm'
    elif kind=='heat':
        content += [f'<rect x="110" y="100" width="200" height="150" rx="18" fill="{theme["accent_light"]}" stroke="{ink}" stroke-width="2"/>',
                    text(210,164,'Hệ đang xét'),line(30,205,108,205,accent,True),text(57,185,'Q',accent),text(210,199,labels.get('m','Trao đổi nhiệt'))]
        caption='Q theo chiều truyền vào hệ trên sơ đồ'
    else:
        return ''
    return f'<svg class="geometry-svg physics-svg" viewBox="0 0 420 380" role="img" aria-label="{escape(caption)}"><defs><marker id="arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 Z" fill="{accent}"/></marker></defs>{"".join(content)}{text(210,362,caption,muted,15)}</svg>'


def polish_html(html, theme, scene):
    """Apply one layout system while retaining KaTeX and frame animation hooks."""
    accent, ink = theme['accent'],theme['text']
    font_dir = Path(__file__).resolve().parents[1] / 'static/fonts/video'
    kind = 'question' if re.search(r'(?:^|\n)\s*[A-D][.)]\s', str(scene.get('slide_text',''))) else ('formula' if scene.get('latex') else 'explain')
    style = f'''<style>
      @font-face {{ font-family:VideoSans;src:url("{(font_dir/'NotoSans-Regular.ttf').as_uri()}");font-weight:400; }}
      @font-face {{ font-family:VideoSans;src:url("{(font_dir/'NotoSans-Bold.ttf').as_uri()}");font-weight:700; }}
      body, .geometry-svg, .kicker {{ font-family:VideoSans,Arial,sans-serif; }}
      .scene {{ padding:38px 46px 28px; border:0; gap:22px 32px; grid-template-rows:28px minmax(0,1fr) 36px; }}
      .kicker {{ font-size:15px; letter-spacing:2px; display:flex; align-items:center; gap:12px; }}
      .kicker::before {{ content:"";width:28px;height:4px;background:{accent};border-radius:4px; }}
      .content {{ min-height:0; gap:20px; grid-template-rows:auto minmax(0,1fr) auto; }}
      h1 {{ font-size:42px; line-height:1.18; letter-spacing:-1px; max-height:108px; overflow:hidden; }}
      .narration {{ font-size:28px;line-height:1.4;white-space:normal;display:flex;flex-direction:column;gap:13px; }}
      .slide-unit {{ flex-shrink:0; }}
      .key-line {{ padding:6px 0; }}
      .choice {{ display:grid;grid-template-columns:36px 1fr;gap:14px;align-items:start;padding:12px 16px;border:1px solid {theme['border']};border-radius:14px;background:{theme['card']}; }}
      .choice-letter {{ display:grid;place-items:center;width:32px;height:32px;border-radius:9px;background:{theme['accent_light']};color:{ink};font-size:19px;font-weight:700; }}
      .visual {{ border-radius:24px;padding:20px;background:{theme['card']};box-shadow:0 14px 34px #00000009; }}
      .formula {{ border:1px solid {theme['border']};border-left:5px solid {accent};border-radius:16px;min-height:100px;font-size:32px; }}
      .footer {{ font-size:14px;padding-top:12px;letter-spacing:.4px; }}
      .solution-card {{ border-radius:16px;padding:18px;border-left-width:4px; }}
      .solution-index {{ background:{theme['accent_light']};color:{ink}; }}
      .solution-card h2 {{ font-size:23px;font-weight:600;line-height:1.4; }}
      .solution-line {{ font-size:21px; }}
      .scene[data-kind="question"].text-only .narration {{ font-size:25px;gap:10px; }}
    </style>'''
    html = html.replace('</head>',style+'</head>').replace('<main class="scene', f'<main data-kind="{kind}" class="scene')
    html = html.replace('Lesson Loom','PHYEDU').replace('Video bài giảng tự động','VẬT LÍ · HỌC QUA TỪNG BƯỚC')
    return html
