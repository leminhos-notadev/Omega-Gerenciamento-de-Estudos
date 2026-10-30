# -*- coding: utf-8 -*-
"""Ômega — núcleo: tema, ícones vetoriais, dados, widgets compartilhados e player de música."""
import sys, os, json, math, time, uuid, weakref, datetime as dt
from pathlib import Path
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtWidgets import *
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

VERSION = "1.2.0"
RES = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "assets"
HOME = Path(os.environ.get("OMEGA_HOME", Path.home() / ".omega"))
CFG, CACHE = HOME / "config.json", HOME / "cache"
NOAUDIO = bool(os.environ.get("OMEGA_NOAUDIO"))
IMG_EXT = {".png", ".jpg", ".jpeg", ".bmp", ".webp", ".gif"}
DIAS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]          # ordem do python (weekday)
DIAS_DOM = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]      # calendário começando no domingo
MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
NAV = [("chart", "Início"), ("timer", "Foco"), ("tasks", "Tarefas"), ("book", "Edital"), ("calendar", "Calendário"),
       ("cycle", "Cronograma / Ciclo"), ("doc", "Simulados"), ("pencil", "Redação"), ("gear", "Configurações")]
PALETTE = ["#ff5a5f", "#ff9f43", "#ffd166", "#7fd957", "#2ecc9a", "#5ec2f2", "#4a7cff", "#8e6bff", "#d96bff", "#f27ab0", "#9aa0a6", "#c58b5a"]
PERIODS = ["Dia", "Semana", "Mês", "Ano", "Total"]
MODE_NAMES = {"timer": "Temporizador", "pomodoro": "Pomodoro", "stopwatch": "Cronômetro", "manual": "Manual"}
ACCENTS = {"Roxo": "#5e17eb", "Amarelo": "#f5b83d", "Verde": "#3ecf6a", "Vermelho": "#f04a4a",
           "Azul claro": "#3fb4f5", "Azul escuro": "#2748d6", "Rosa": "#f05aa8"}
RED, YEL, GRN = "#ff3333", "#ffbd59", "#7fd957"
BLOCK_COLORS = ["#ffbd59", "#5ec2f2", "#7fd957", "#f27ab0", "#b08cff", "#ff7a59", "#4fd1c5", "#e6c84f"]

# ───────────────────────── tema ─────────────────────────
T = {}
def set_theme(mode, accent):
    ac = QColor(ACCENTS.get(accent, ACCENTS["Roxo"])); dark = mode != "light"
    lum = (.299 * ac.red() + .587 * ac.green() + .114 * ac.blue()) / 255
    T.update(dark=dark, accent=ac.name(), accent_h=(ac.lighter(112) if dark else ac.darker(106)).name(),
             on_accent="#ffffff" if lum < .6 else "#17181a",
             bg="#18191b" if dark else "#f1f2f5", side="#1c1d1f" if dark else "#e6e8ed",
             card="#060606" if dark else "#ffffff", row="#101112" if dark else "#ffffff",
             field="#121314" if dark else "#eceef3", btn="#0b0c0c" if dark else "#d9dce3",
             line="#2a2b2e" if dark else "#d3d7de", muted="#6b6d72" if dark else "#7b808b",
             text="#ffffff" if dark else "#15161a")
set_theme("dark", "Roxo")

def qss():
    ac, onac, bg, card, field, line, muted, text = (T[k] for k in ("accent", "on_accent", "bg", "card", "field", "line", "muted", "text"))
    CACHE.mkdir(parents=True, exist_ok=True); arrow = CACHE / f"down_{muted[1:]}.png"; pix("down", muted, 14).save(str(arrow))
    return f"""
QWidget{{color:{text};font-family:'Poppins','Segoe UI','Noto Sans',sans-serif;font-size:13px}}
QDialog,QMessageBox,QInputDialog{{background:{card}}}
QToolTip{{background:{card};color:{text};border:1px solid {line};padding:4px}}
QPushButton{{background:{ac};color:{onac};border:none;border-radius:19px;padding:9px 22px;font-weight:600}}
QPushButton:hover{{background:{T['accent_h']}}}
QPushButton:disabled{{background:{line};color:{muted}}}
QPushButton[pill="true"]{{background:{field};color:{muted}}}
QPushButton[pill="true"]:hover{{color:{text}}}
QPushButton[pill="true"]:checked{{background:{ac};color:{onac}}}
QPushButton[flat2="true"]{{background:transparent;color:{muted};text-align:left;padding:4px 2px;border-radius:6px}}
QPushButton[flat2="true"]:hover{{color:{text}}}
QLineEdit,QTextEdit,QSpinBox,QDoubleSpinBox,QDateEdit,QTimeEdit{{background:{field};border:none;border-radius:14px;padding:8px 14px;selection-background-color:{ac};selection-color:{onac}}}
QSpinBox::up-button,QSpinBox::down-button,QDoubleSpinBox::up-button,QDoubleSpinBox::down-button,QTimeEdit::up-button,QTimeEdit::down-button{{width:0;border:none}}
QDateEdit::drop-down{{width:22px;border:none}}
QComboBox{{background:{field};border:2px solid {ac};border-radius:20px;padding:7px 16px}}
QComboBox::drop-down{{border:none;width:34px}}
QComboBox::down-arrow{{image:url("{arrow.as_posix()}");width:14px;height:14px}}
QComboBox QAbstractItemView{{background:{card};border:1px solid {line};selection-background-color:{ac};selection-color:{onac};outline:0;padding:4px}}
QListWidget,QTableWidget{{background:{field};border:none;border-radius:16px;padding:6px;outline:0}}
QListWidget::item{{padding:7px;border-radius:8px}}
QListWidget::item:selected,QTableWidget::item:selected{{background:{ac};color:{onac}}}
QHeaderView::section{{background:transparent;color:{muted};border:none;padding:6px;font-weight:600}}
QTableCornerButton::section{{background:transparent}}
QScrollArea{{border:none;background:transparent}}
QScrollArea>QWidget>QWidget{{background:transparent}}
QScrollBar:vertical{{background:transparent;width:10px;margin:0}}
QScrollBar::handle:vertical{{background:{line};border-radius:5px;min-height:30px}}
QScrollBar:horizontal{{background:transparent;height:10px;margin:0}}
QScrollBar::handle:horizontal{{background:{line};border-radius:5px;min-width:30px}}
QScrollBar::add-line,QScrollBar::sub-line{{width:0;height:0}}
QScrollBar::add-page,QScrollBar::sub-page{{background:transparent}}
QSlider::groove:horizontal{{height:4px;background:{line};border-radius:2px}}
QSlider::handle:horizontal{{background:{ac};width:14px;margin:-6px 0;border-radius:7px}}
QSlider::sub-page:horizontal{{background:{ac};border-radius:2px}}
QCheckBox::indicator{{width:20px;height:20px;border-radius:10px;background:{field}}}
QCheckBox::indicator:checked{{background:{ac}}}
QMenu{{background:{card};border:1px solid {line};padding:6px;border-radius:8px}}
QMenu::item{{padding:7px 20px;border-radius:6px}}
QMenu::item:selected{{background:{ac};color:{onac}}}
QCalendarWidget QAbstractItemView{{background:{field};color:{text};selection-background-color:{ac};selection-color:{onac};outline:0}}
QCalendarWidget QToolButton{{background:transparent;color:{text};padding:4px 10px}}
QCalendarWidget QWidget#qt_calendar_navigationbar{{background:{card}}}
QCalendarWidget QMenu{{background:{card}}}
"""

def app_icon():
    """Ícone do aplicativo (janela / barra de tarefas): Ω na cor de destaque, fundo transparente."""
    ic = QIcon()
    for sz in (256, 128, 64, 48, 32, 16):
        pm = QPixmap(sz, sz); pm.fill(Qt.transparent); lg = logo_pix(T["accent"], int(sz * .78)); w, h = lg.width() / lg.devicePixelRatio(), lg.height() / lg.devicePixelRatio()
        p = QPainter(pm); p.drawPixmap(QPointF((sz - w) / 2, (sz - h) / 2), lg); p.end(); ic.addPixmap(pm)
    return ic

def apply_theme(app, mode, accent):
    set_theme(mode, accent)
    pal = QPalette()
    for r, k in [(QPalette.Window, "bg"), (QPalette.WindowText, "text"), (QPalette.Base, "field"), (QPalette.AlternateBase, "card"), (QPalette.Text, "text"),
                 (QPalette.Button, "btn"), (QPalette.ButtonText, "text"), (QPalette.Highlight, "accent"), (QPalette.HighlightedText, "on_accent"),
                 (QPalette.PlaceholderText, "muted"), (QPalette.ToolTipBase, "card"), (QPalette.ToolTipText, "text")]: pal.setColor(r, QColor(T[k]))
    app.setPalette(pal); app.setStyleSheet(qss()); retheme_all(); app.setWindowIcon(app_icon())
    for w in app.allWidgets(): w.update()

# ───────────────────────── ícones vetoriais ─────────────────────────
ICONS = {
    "chart": [("L", [(4, 20), (20, 20)]), ("FR", 5, 11, 3.5, 9, 1), ("FR", 10.25, 5, 3.5, 15, 1), ("FR", 15.5, 9, 3.5, 11, 1)],
    "timer": [("C", 12, 13, 8), ("L", [(12, 8), (12, 13), (15, 15)]), ("L", [(9, 2.5), (15, 2.5)])],
    "tasks": [("L", [(4, 7), (6, 9), (10, 5)]), ("L", [(13, 7), (20, 7)]), ("L", [(4, 16), (6, 18), (10, 14)]), ("L", [(13, 16), (20, 16)])],
    "book": [("R", 5, 3, 14, 18, 2), ("L", [(9, 3), (9, 21)]), ("L", [(12, 8), (16, 8)]), ("L", [(12, 12), (16, 12)])],
    "calendar": [("R", 3, 5, 18, 16, 3), ("L", [(3, 10), (21, 10)]), ("L", [(8, 3), (8, 7)]), ("L", [(16, 3), (16, 7)])],
    "cycle": [("ARC", 12, 12, 7.5, 30, 140), ("ARC", 12, 12, 7.5, 210, 140)],
    "doc": [("R", 5, 3, 14, 18, 2), ("L", [(8, 8), (16, 8)]), ("L", [(8, 12), (16, 12)]), ("L", [(8, 16), (13, 16)])],
    "pencil": [("L", [(4, 20), (5, 15), (16.5, 3.5), (20.5, 7.5), (9, 19), (4, 20)]), ("L", [(13.5, 6.5), (17.5, 10.5)])],
    "gear": [("C", 12, 12, 3.2), ("C", 12, 12, 6.6), ("TICKS", 12, 12, 6.6, 10.2, 8)],
    "play": [("P", [(8, 5), (8, 19), (19, 12)])],
    "pause": [("FR", 6, 5, 4, 14, 1.5), ("FR", 14, 5, 4, 14, 1.5)],
    "stop": [("FR", 6, 6, 12, 12, 2)],
    "plus": [("L", [(12, 5), (12, 19)]), ("L", [(5, 12), (19, 12)])],
    "x": [("L", [(6, 6), (18, 18)]), ("L", [(18, 6), (6, 18)])],
    "trash": [("L", [(4, 7), (20, 7)]), ("L", [(9, 7), (9, 4), (15, 4), (15, 7)]), ("L", [(6, 7), (7, 20), (17, 20), (18, 7)]), ("L", [(10, 11), (10, 16)]), ("L", [(14, 11), (14, 16)])],
    "search": [("C", 10.5, 10.5, 6), ("L", [(15, 15), (20, 20)])],
    "music": [("E", 7.5, 18, 3, 2.4), ("E", 16.5, 16, 3, 2.4), ("L", [(10.5, 18), (10.5, 6), (19.5, 4), (19.5, 16)])],
    "prev": [("P", [(18, 5), (18, 19), (8, 12)]), ("FR", 5, 5, 2.5, 14, 1)],
    "next": [("P", [(6, 5), (6, 19), (16, 12)]), ("FR", 16.5, 5, 2.5, 14, 1)],
    "eye": [("PATH", "M2,12 Q12,3,22,12 Q12,21,2,12"), ("FC", 12, 12, 3)],
    "tri_l": [("P", [(16, 4), (16, 20), (5, 12)])], "tri_r": [("P", [(8, 4), (8, 20), (19, 12)])],
    "down": [("P", [(5, 8), (19, 8), (12, 17)])],
    "check": [("W", 2.8), ("L", [(5, 12.5), (10, 17), (19, 7)])],
    "bell": [("FPATH", "M6,17 L6,11 Q6,5,12,5 Q18,5,18,11 L18,17 L20,19 L4,19 Z"), ("FC", 12, 21, 1.6), ("L", [(12, 3), (12, 5)])],
    "volume": [("P", [(4, 9), (8, 9), (13, 5), (13, 19), (8, 15), (4, 15)]), ("PATH", "M16,9 Q18,12,16,15"), ("PATH", "M18.5,6.5 Q22,12,18.5,17.5")],
    "mute": [("P", [(4, 9), (8, 9), (13, 5), (13, 19), (8, 15), (4, 15)]), ("L", [(16, 9), (21, 15)]), ("L", [(21, 9), (16, 15)])],
    "shuffle": [("L", [(3, 7), (8, 7), (16, 17), (19, 17)]), ("L", [(3, 17), (8, 17), (11, 13)]), ("L", [(13, 11), (16, 7), (19, 7)]), ("P", [(18, 4), (18, 10), (22, 7)]), ("P", [(18, 14), (18, 20), (22, 17)])],
    "up": [("W", 2.6), ("L", [(6, 15), (12, 9), (18, 15)])], "down": [("W", 2.6), ("L", [(6, 9), (12, 15), (18, 9)])],
    "repeat": [("PATH", "M5,11 Q5,6,10,6 L18,6"), ("P", [(16, 3), (16, 9), (20, 6)]), ("PATH", "M19,13 Q19,18,14,18 L6,18"), ("P", [(8, 15), (8, 21), (4, 18)])],
    "repeat1": [("PATH", "M5,11 Q5,6,10,6 L18,6"), ("P", [(16, 3), (16, 9), (20, 6)]), ("PATH", "M19,13 Q19,18,14,18 L6,18"), ("P", [(8, 15), (8, 21), (4, 18)]), ("W", 1.8), ("L", [(10.6, 10.8), (12.3, 9.5), (12.3, 14.8)])],
    "eye_off": [("PATH", "M2,12 Q12,3,22,12 Q12,21,2,12"), ("L", [(4, 4), (20, 20)])],
    "sun": [("C", 12, 12, 4), ("TICKS", 12, 12, 7, 10, 8)],
    "list": [("L", [(4, 7), (15, 7)]), ("L", [(4, 12), (15, 12)]), ("L", [(4, 17), (11, 17)]), ("P", [(16, 13), (16, 21), (21, 17)])],
}
_PIX = {}

def _path(s):
    path = QPainterPath()
    for tok in s.split():
        c = tok[0]
        if c == "Z": path.closeSubpath(); continue
        v = [float(x) for x in tok[1:].split(",")]
        if c == "M": path.moveTo(*v)
        elif c == "L": path.lineTo(*v)
        elif c == "Q": path.quadTo(*v)
    return path

def _draw(p, ops, col):
    pen = QPen(col, 2, Qt.SolidLine, Qt.RoundCap, Qt.RoundJoin); p.setPen(pen); poly = lambda pts: QPolygonF([QPointF(*q) for q in pts])
    for op in ops:
        k = op[0]
        if k == "W": pen.setWidthF(op[1]); p.setPen(pen)
        elif k == "L": p.setBrush(Qt.NoBrush); p.drawPolyline(poly(op[1]))
        elif k == "P": p.setBrush(col); p.drawPolygon(poly(op[1]))
        elif k == "R": p.setBrush(Qt.NoBrush); p.drawRoundedRect(QRectF(*op[1:5]), op[5], op[5])
        elif k == "C": p.setBrush(Qt.NoBrush); p.drawEllipse(QPointF(op[1], op[2]), op[3], op[3])
        elif k in ("FR", "FC", "E", "FPATH"):
            p.setBrush(col); p.setPen(Qt.NoPen)
            if k == "FR": p.drawRoundedRect(QRectF(*op[1:5]), op[5], op[5])
            elif k == "FC": p.drawEllipse(QPointF(op[1], op[2]), op[3], op[3])
            elif k == "E": p.drawEllipse(QPointF(op[1], op[2]), op[3], op[4])
            else: p.drawPath(_path(op[1]))
            p.setPen(pen)
        elif k == "PATH": p.setBrush(Qt.NoBrush); p.drawPath(_path(op[1]))
        elif k == "TICKS":
            cx, cy, r1, r2, n = op[1:]
            for i in range(n):
                a = 2 * math.pi * i / n; p.drawLine(QPointF(cx + r1 * math.cos(a), cy + r1 * math.sin(a)), QPointF(cx + r2 * math.cos(a), cy + r2 * math.sin(a)))
        elif k == "ARC":
            cx, cy, r, st, sp = op[1:]; p.setBrush(Qt.NoBrush); p.drawArc(QRectF(cx - r, cy - r, 2 * r, 2 * r), int(st * 16), int(sp * 16))
            th = math.radians(st + sp); tip = (cx + r * math.cos(th), cy - r * math.sin(th)); d = (-math.sin(th), -math.cos(th)); n = (math.cos(th), -math.sin(th))
            p.setBrush(col); p.setPen(Qt.NoPen)
            p.drawPolygon(poly([(tip[0] + d[0] * 4.2, tip[1] + d[1] * 4.2), (tip[0] + n[0] * 3.6, tip[1] + n[1] * 3.6), (tip[0] - n[0] * 3.6, tip[1] - n[1] * 3.6)])); p.setPen(pen)

def pix(name, color, size=24):
    k = (name, color, size)
    if k not in _PIX:
        dpr = 2.0; pm = QPixmap(int(size * dpr), int(size * dpr)); pm.setDevicePixelRatio(dpr); pm.fill(Qt.transparent)
        p = QPainter(pm); p.setRenderHints(QPainter.Antialiasing); p.scale(size / 24, size / 24); _draw(p, ICONS[name], QColor(color)); p.end(); _PIX[k] = pm
    return _PIX[k]

def qicon(name, off, on=None, size=24):
    ic = QIcon(); ic.addPixmap(pix(name, off, size), QIcon.Normal, QIcon.Off); ic.addPixmap(pix(name, on or off, size), QIcon.Normal, QIcon.On); return ic

def logo_pix(color, h):
    k = ("logo", color, h)
    if k not in _PIX:
        src = QPixmap(str(RES / "logo.png")).scaledToHeight(int(h * 2), Qt.SmoothTransformation); out = QPixmap(src.size()); out.fill(Qt.transparent)
        p = QPainter(out); p.drawPixmap(0, 0, src); p.setCompositionMode(QPainter.CompositionMode_SourceIn); p.fillRect(out.rect(), QColor(color)); p.end()
        out.setDevicePixelRatio(2.0); _PIX[k] = out
    return _PIX[k]

LISTEN = weakref.WeakSet()
def retheme_all():
    _PIX.clear()
    for w in list(LISTEN):
        try: w.retheme()
        except RuntimeError: pass

class IBtn(QPushButton):
    """Botão redondo com ícone vetorial. kind: accent | dark | ghost"""
    def __init__(s, name, d=40, kind="accent", tip="", isize=None, checkable=False):
        super().__init__(); s.name, s.kind, s.d = name, kind, d; s.isz = isize or max(12, int(d * .5))
        s.setFixedSize(d, d); s.setCursor(Qt.PointingHandCursor); s.setCheckable(checkable)
        if tip: s.setToolTip(tip)
        LISTEN.add(s); s.retheme()
    def set_icon(s, name): s.name = name; s.retheme()
    def retheme(s):
        if s.kind == "accent": bg, fg, hov, fgon = T["accent"], T["on_accent"], T["accent_h"], T["on_accent"]
        elif s.kind == "dark": bg, fg, hov, fgon = T["btn"], T["text"], QColor(T["btn"]).lighter(130).name() if T["dark"] else QColor(T["btn"]).darker(106).name(), T["on_accent"]
        else: bg, fg, hov, fgon = "transparent", T["muted"], "transparent", T["on_accent"]
        s.setStyleSheet(f"QPushButton{{background:{bg};border:none;border-radius:{s.d // 2}px;padding:0}}QPushButton:hover{{background:{hov}}}QPushButton:checked{{background:{T['accent']}}}")
        if s.kind == "ghost": s.setStyleSheet(s.styleSheet() + f"QPushButton:hover{{background:transparent}}")
        s.setIcon(qicon(s.name, fg, fgon, s.isz)); s.setIconSize(QSize(s.isz, s.isz))

def pill(text, checkable=False, h=40):
    b = QPushButton(text); b.setProperty("pill", True); b.setCheckable(checkable); b.setCursor(Qt.PointingHandCursor); b.setMinimumHeight(h); return b
def flat(text):
    b = QPushButton(text); b.setProperty("flat2", True); b.setCursor(Qt.PointingHandCursor); return b
def heading(text, size=40, weight=700):
    l = QLabel(text); l.setStyleSheet(f"font-size:{size}px;font-weight:{weight}"); return l
def muted(text, size=13, weight=600):
    l = QLabel(text); l.setStyleSheet(f"font-size:{size}px;font-weight:{weight};color:{T['muted']}"); l._w = _MutedWatcher(l, size, weight); LISTEN.add(l._w); return l
class _MutedWatcher:
    def __init__(s, l, size, weight): s.l, s.size, s.weight = weakref.ref(l), size, weight
    def retheme(s):
        l = s.l()
        if l: l.setStyleSheet(f"font-size:{s.size}px;font-weight:{s.weight};color:{T['muted']}")

class Card(QFrame):
    def __init__(s, r=20, key="card", border=False):
        super().__init__(); s.r, s.key, s.border, s.bkey = r, key, border, "line"
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(T[s.key]))
        p.setPen(QPen(QColor(T[s.bkey]), 2 if s.bkey == "accent" else 1.5) if s.border else Qt.NoPen); p.drawRoundedRect(QRectF(s.rect()).adjusted(1, 1, -1, -1), s.r, s.r)

class Page(QWidget):
    def __init__(s, win): super().__init__(); s.win = win; s.st = win.store; LISTEN.add(s)
    @property
    def d(s): return s.st.data
    def retheme(s): pass
    def paintEvent(s, e): QPainter(s).fillRect(s.rect(), QColor(T["bg"]))
    def refresh(s): pass

# ───────────────────────── dados ─────────────────────────
def uid(): return uuid.uuid4().hex[:10]
def today(): return dt.date.today()
def iso(d): return d.isoformat()
def br(s):
    try: return dt.date.fromisoformat(s[:10]).strftime("%d/%m/%Y")
    except Exception: return s or ""
def fmt_min(m):
    m = int(round(m)); h, mm = divmod(m, 60)
    return f"{h}h{mm:02d}" if h else f"{mm}min"

def fresh():
    return {
        "settings": {"user": "", "timer_min": 25, "pomo_study": 25, "pomo_break": 5, "pomo_long": 15, "pomo_cycles": 4,
                     "alarm_timer": "", "alarm_study": "", "alarm_break": "", "bg": "", "vol": 60, "intro": True,
                     "mode": "dark", "accent": "Roxo", "pin": False, "plan_mode": "schedule",
                     "pomo_use_long": True, "pomo_total": 0, "fullscreen": True, "active_cycle": "",
                     "pomo_manual": False, "music_loop": "all", "hidden_tabs": [], "hide_myday": False, "done_open": {}},
        "version": 5, "colors": {"subjects": {}, "tags": {}}, "myday": [], "myday_own": [], "exam_types": [], "streak": {"count": 0, "last": "", "best": 0}, "subjects": [], "tags": [], "sessions": [], "lists": [{"id": uid(), "name": "Lista nº 1", "tasks": []}],
        "syllabus": {}, "events": [], "exams": [], "essays": [], "library": [], "playlists": [],
        "schedules": [{"id": uid(), "name": "Cronograma 1", "blocks": []}], "cycles": [],
    }
OLD_SUBJECTS = (["Matemática", "Português", "Inglês", "Física", "Química", "Biologia", "História", "Geografia", "Redação"],
                ["Matemática", "Português", "Física", "Química", "Biologia", "História", "Geografia", "Redação"])
OLD_TAGS = ["Teoria", "Exercícios", "Revisão"]
def merge(d):
    f = fresh(); ver = d.get("version", 2)
    for k, v in f.items(): d.setdefault(k, v)
    for k, v in f["settings"].items(): d["settings"].setdefault(k, v)
    for k in ("subjects", "tags"): d["colors"].setdefault(k, {})
    ml = d["settings"].get("music_loop")
    d["settings"]["music_loop"] = ml if ml in ("off", "all", "one") else ("off" if ml is False else "all")   # aceita o valor antigo (true/false) e qualquer valor inválido
    d["settings"]["hidden_tabs"] = [n for n in d["settings"]["hidden_tabs"] if n != "Configurações"]
    if ver < 3:   # versões antigas já vinham com matérias/tags de exemplo: remove se ainda forem as originais
        if d["subjects"] in OLD_SUBJECTS: d["subjects"] = []
        if d["tags"] == OLD_TAGS: d["tags"] = []
    if ver < 5: rebuild_streak(d)
    d["version"] = 5
    return d

class Store:
    def __init__(s):
        HOME.mkdir(parents=True, exist_ok=True); s.cfg = {"sync_dir": ""}
        try: s.cfg.update(json.loads(CFG.read_text("utf-8")))
        except Exception: pass
        s.local = HOME / "data.json"; s.data = fresh(); s.known = 0
        c = [p for p in (s.local, s.sync_file()) if p and p.exists()]
        if c: s.read(max(c, key=lambda p: p.stat().st_mtime))
    def sync_file(s): return Path(s.cfg["sync_dir"]) / "omega_data.json" if s.cfg.get("sync_dir") else None
    def save_cfg(s): CFG.write_text(json.dumps(s.cfg), "utf-8")
    def read(s, p):
        try: s.data = merge(json.loads(Path(p).read_text("utf-8")))
        except Exception as e: print("Erro ao ler", p, e); return False
        if p == s.sync_file(): s.known = p.stat().st_mtime
        return True
    def save(s):
        txt = json.dumps(s.data, ensure_ascii=False, indent=1); s.local.write_text(txt, "utf-8"); sf = s.sync_file()
        if sf:
            try: sf.parent.mkdir(parents=True, exist_ok=True); sf.write_text(txt, "utf-8"); s.known = sf.stat().st_mtime
            except Exception as e: print("Sync falhou:", e)
    def pull(s, force=False):
        sf = s.sync_file()
        return bool(sf and sf.exists() and (force or sf.stat().st_mtime > s.known + 1) and s.read(sf))

def iter_tasks(tasks):
    for t in tasks: yield t; yield from iter_tasks(t["subtasks"])
def all_tasks(d):
    for l in d["lists"]: yield from iter_tasks(l["tasks"])
    yield from iter_tasks(d["myday_own"])
def minutes_between(d, a, b, sub="", tag=""):
    return sum(x["minutes"] for x in d["sessions"] if a <= dt.date.fromisoformat(x["start"][:10]) < b and (not sub or x.get("subject") == sub) and (not tag or x.get("tag") == tag))
def buckets(per, n, off):
    t = today(); out = []
    for i in range(n - 1, -1, -1):
        k = i + off * n
        if per == "Dia": a = t - dt.timedelta(days=k); b = a + dt.timedelta(days=1); lab = a.strftime("%d/%m")
        elif per == "Semana": a = t - dt.timedelta(days=t.weekday()) - dt.timedelta(days=7 * k); b = a + dt.timedelta(days=7); lab = a.strftime("%d/%m")
        elif per == "Mês":
            y, m = divmod(t.year * 12 + t.month - 1 - k, 12); m += 1; a = dt.date(y, m, 1); b = dt.date(y + (m == 12), m % 12 + 1, 1); lab = f"{m:02d}/{y % 100:02d}"
        else: a = dt.date(t.year - k, 1, 1); b = dt.date(t.year - k + 1, 1, 1); lab = str(a.year)
        out.append((lab, a, b))
    return out
def period_buckets(per, off, first=None):
    """Retorna (rótulo do intervalo, [(rótulo, início, fim)], início, fim) com datetimes. off = quantos períodos para trás.
    'Total' = todos os meses desde o primeiro registro (first) até o mês atual (mínimo 6 meses)."""
    t = today(); D = dt.datetime.combine; one = dt.timedelta(days=1); mn = dt.time.min
    def months(y, m0, n, yy=False):
        out = []
        for k in range(n):
            y2, m2 = divmod(y * 12 + m0 - 1 + k, 12); m2 += 1; a = dt.date(y2, m2, 1); y3, m3 = divmod(y2 * 12 + m2, 12)
            out.append((MESES[m2 - 1][:3] + (f"/{y2 % 100:02d}" if yy else ""), D(a, mn), D(dt.date(y3, m3 + 1, 1), mn)))
        return out
    if per == "Dia":
        d = t - off * one; a = D(d, mn); bk = [(f"{h:02d}h", a + dt.timedelta(hours=h), a + dt.timedelta(hours=h + 1)) for h in range(24)]; lab = d.strftime("%d/%m/%Y") + "  ·  00:00 – 23:59"
    elif per == "Semana":
        m = t - dt.timedelta(days=t.weekday()) - dt.timedelta(weeks=off); bk = [(f"{DIAS[i]} {(m + i * one).day:02d}", D(m + i * one, mn), D(m + (i + 1) * one, mn)) for i in range(7)]; lab = f"{m.strftime('%d/%m/%Y')} – {(m + 6 * one).strftime('%d/%m/%Y')}"
    elif per == "Mês":
        y, m0 = divmod(t.year * 12 + t.month - 1 - off, 12); m0 += 1; first_ = dt.date(y, m0, 1); y2, m2 = divmod(y * 12 + m0, 12); last = dt.date(y2, m2 + 1, 1); n = (last - first_).days
        bk = [(str(i + 1), D(first_ + i * one, mn), D(first_ + (i + 1) * one, mn)) for i in range(n)]; lab = f"{MESES[m0 - 1]} {y}"
    elif per == "Ano":
        y = t.year - off; bk = months(y, 1, 12); lab = str(y)
    else:   # Total
        f = first or t; start = f.year * 12 + f.month - 1; end = t.year * 12 + t.month - 1; start = min(start, end - 5); y, m0 = divmod(start, 12)
        bk = months(y, m0 + 1, end - start + 1, True); lab = f"Todo o período  ·  {bk[0][0]} – {bk[-1][0]}"
    return lab, bk, bk[0][1], bk[-1][2]
def session_overlap(x, a, b):
    st = dt.datetime.fromisoformat(x["start"]); en = st + dt.timedelta(minutes=x["minutes"]); sec = (min(en, b) - max(st, a)).total_seconds()
    return max(0.0, sec / 60)
def minutes_in(d, a, b, sub="", tag=""):
    return sum(session_overlap(x, a, b) for x in d["sessions"] if (not sub or x.get("subject") == sub) and (not tag or x.get("tag") == tag))

def study_streak(d):
    days = {x["start"][:10] for x in d["sessions"]}; c = today()
    if iso(c) not in days: c -= dt.timedelta(days=1)
    n = 0
    while iso(c) in days: n += 1; c -= dt.timedelta(days=1)
    return n

RECORDS = {
    "exams": dict(title="Simulados", metric=lambda r: r["hits"] / r["total"] * 100 if r.get("total") else None, fmt=lambda v: f"{v:.0f}%", typekey="type"),
    "essays": dict(title="Redações", metric=lambda r: r.get("grade"), fmt=lambda v: f"{v:.0f}", typekey=None)}
def record_series(recs, metric, mode):
    pts = [(r["date"], metric(r)) for r in recs if metric(r) is not None]
    if mode == 0: return [(dt.date.fromisoformat(d).strftime("%d/%m/%y"), v) for d, v in pts]
    g = {}
    for d, v in pts: g.setdefault(d[:7] if mode == 1 else d[:4], []).append(v)
    return [((f"{k[5:7]}/{k[2:4]}" if mode == 1 else k), sum(g[k]) / len(g[k])) for k in sorted(g)]

# ───────────────────────── ciclo de estudos ─────────────────────────
def cycle_blocks(rows, total):
    """Sistema da planilha CICLO ITA: pontos = (dificuldade + conteúdo) × peso; blocos = pontos × total ÷ Σpontos,
    arredondados pelo método do maior resto para a soma fechar exatamente em 'total'. rows = [(nome, dif, cont, peso)]."""
    pts = [(d + c) * p for _, d, c, p in rows]; S = sum(pts)
    if S <= 0 or total <= 0: return [0] * len(rows)
    ex = [x * total / S for x in pts]; fl = [int(math.floor(e + 1e-9)) for e in ex]; rest = total - sum(fl)
    for i in sorted(range(len(ex)), key=lambda i: (-(ex[i] - fl[i]), i))[:max(0, rest)]: fl[i] += 1
    for i in range(len(fl)):   # toda matéria incluída recebe ao menos 1 bloco
        if pts[i] > 0 and fl[i] == 0:
            j = max(range(len(fl)), key=lambda k: fl[k])
            if fl[j] > 1: fl[j] -= 1; fl[i] = 1
    return fl

def cycle_order(cy):
    """Ordem sugerida das sessões restantes: matérias intercaladas, as com mais sessões pendentes aparecem com mais frequência."""
    rem = {i["subject"]: cy["marks"][i["subject"]].count(False) for i in cy["items"]}; tot = {k: max(1, len(cy["marks"][k])) for k in rem}; seq = []; last = None
    while any(rem.values()):
        cand = [k for k, v in rem.items() if v > 0]; pool = [k for k in cand if k != last] or cand
        k = max(pool, key=lambda k: (rem[k] / tot[k], rem[k])); seq.append(k); rem[k] -= 1; last = k
    return seq
def mark_session(cy, subject):
    m = cy["marks"].get(subject)
    if m and False in m: m[m.index(False)] = True; return True
    return False
def cycle_complete(cy): return bool(cy["marks"]) and all(all(m) for m in cy["marks"].values())
def advance_cycle(cy):
    cy["history"].append(iso(today())); cy["number"] += 1; cy["marks"] = {i["subject"]: [False] * i["n"] for i in cy["items"]}
def scolor(name): return BLOCK_COLORS[sum(map(ord, name)) % len(BLOCK_COLORS)]

# ───────────────────────── streak (dias seguidos) ─────────────────────────
STREAK_MIN = 10   # minutos de foco no dia para contar
def focus_minutes_on(d, day):
    return sum(x["minutes"] for x in d["sessions"] if x["start"][:10] == iso(day) and x.get("mode") != "manual")
def streak_add_day(d, day):
    """Soma 1 ao streak para 'day' (uma vez por dia). Retorna True se o streak aumentou."""
    st = d["streak"]; last = st.get("last", "")
    if last and last >= iso(day): return False
    st["count"] = st["count"] + 1 if last and (day - dt.date.fromisoformat(last)).days == 1 else 1
    st["last"] = iso(day); st["best"] = max(st.get("best", 0), st["count"]); return True
def streak_current(d):
    st = d["streak"]
    if not st.get("last"): return 0
    return st["count"] if (today() - dt.date.fromisoformat(st["last"])).days <= 1 else 0
def rebuild_streak(d):
    """Calcula o streak a partir do histórico (primeira abertura desta versão)."""
    mins = {}
    for x in d["sessions"]:
        if x.get("mode") != "manual": mins[x["start"][:10]] = mins.get(x["start"][:10], 0) + x["minutes"]
    days = sorted(dt.date.fromisoformat(k) for k, v in mins.items() if v >= STREAK_MIN); d["streak"] = {"count": 0, "last": "", "best": 0}
    for day in days: streak_add_day(d, day)

def flame_pix(size, number=None, gray=False):
    """Chama do streak: gota laranja arredondada (com número dentro quando 'number' é dado)."""
    k = ("flame", size, number, gray)
    if k in _PIX: return _PIX[k]
    dpr = 2.0; pm = QPixmap(int(size * dpr), int(size * dpr)); pm.setDevicePixelRatio(dpr); pm.fill(Qt.transparent); p = QPainter(pm); p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing); p.scale(size / 100, size / 100)
    o = QPainterPath(); o.moveTo(50, 97); o.cubicTo(24, 97, 10, 78, 10, 60); o.cubicTo(10, 44, 20, 34, 29, 22); o.cubicTo(32, 18, 37, 20, 38, 24); o.cubicTo(40, 30, 45, 34, 49, 36)
    o.cubicTo(50, 22, 54, 12, 62, 4); o.cubicTo(72, 18, 90, 36, 90, 60); o.cubicTo(90, 78, 76, 97, 50, 97); o.closeSubpath()
    g = QLinearGradient(0, 4, 0, 97); g.setColorAt(0, QColor("#6b6d72" if gray else "#ffb000")); g.setColorAt(1, QColor("#55575b" if gray else "#ff7a00")); p.setPen(Qt.NoPen); p.fillPath(o, g)
    if number is None:
        i = QPainterPath(); i.moveTo(50, 90); i.cubicTo(36, 90, 29, 80, 29, 70); i.cubicTo(29, 61, 36, 55, 43, 46); i.cubicTo(46, 52, 52, 55, 56, 58); i.cubicTo(60, 54, 62, 50, 62, 46); i.cubicTo(68, 54, 72, 62, 72, 70); i.cubicTo(72, 80, 64, 90, 50, 90); i.closeSubpath()
        p.fillPath(i, QColor("#8a8c91" if gray else "#ffd45e"))
    else:
        f = QFont("Poppins"); f.setWeight(QFont.Bold); f.setPixelSize(46 if len(str(number)) < 3 else 34); p.setFont(f); p.setPen(QColor("#ffffff")); p.drawText(QRectF(0, 42, 100, 52), Qt.AlignCenter, str(number))
    p.end(); _PIX[k] = pm; return pm

# ───────────────────────── provas (simulados) ─────────────────────────
def exam_type(d, name): return next((t for t in d["exam_types"] if t["name"] == name), None)
def exam_subject_metric(r, sub):
    sc, tt = r.get("scores", {}), r.get("totals", {})
    return sc[sub] / tt[sub] * 100 if sub in sc and tt.get(sub) else None
def exam_subjects(recs):
    out = []
    for r in recs:
        for k in r.get("totals", {}):
            if k not in out: out.append(k)
    return out

# ───────────────────────── áudio ─────────────────────────
class Sound:
    def __init__(s): s.cur = ""; s.off = NOAUDIO; s.p = None
    def _init(s):
        if s.p is None: s.p = QMediaPlayer(); s.o = QAudioOutput(); s.p.setAudioOutput(s.o)
    def play(s, path):
        if s.off or not path or not Path(path).exists(): return
        s._init()
        if str(path) != s.cur: s.p.setSource(QUrl.fromLocalFile(str(path))); s.cur = str(path)
        s.p.setPosition(0); s.p.play()
    def stop(s):
        if s.p: s.p.stop()
    def vol(s, v):
        s._init() if not s.off else None
        if s.p: s.o.setVolume(v / 100)

class MusicPlayer(QObject):
    changed = Signal(); progress = Signal(int, int)
    def __init__(s):
        super().__init__(); s.queue = []; s.i = -1; s.playing = False; s.p = None; s.vol = 60; s.muted = False; s.loop = "all"   # "off" | "all" (playlist) | "one" (música)
        if not NOAUDIO:
            s.p = QMediaPlayer(); s.o = QAudioOutput(); s.p.setAudioOutput(s.o)
            s.p.positionChanged.connect(lambda v: s.progress.emit(v, s.p.duration())); s.p.durationChanged.connect(lambda v: s.progress.emit(s.p.position(), v))
            s.p.mediaStatusChanged.connect(s._status)
            s.p.playbackStateChanged.connect(s._state)
    @property
    def title(s): return s.queue[s.i]["title"] if 0 <= s.i < len(s.queue) else ""
    def _status(s, st):
        if st != QMediaPlayer.MediaStatus.EndOfMedia: return
        if s.loop == "one": s.p.setPosition(0); s.p.play()
        elif s.loop == "all" or s.i < len(s.queue) - 1: s.next(1)
        else: s.p.stop(); s.playing = False; s.changed.emit()
    def _state(s, st): s.playing = st == QMediaPlayer.PlaybackState.PlayingState; s.changed.emit()
    def set_queue(s, tracks, start=0, play=True):
        s.queue = [t for t in tracks if Path(t["path"]).exists()]
        if not s.queue: s.i = -1; s.changed.emit(); return
        s.i = min(start, len(s.queue) - 1); s._load(play)
    def _load(s, play=True):
        if s.p:
            s.p.setSource(QUrl.fromLocalFile(s.queue[s.i]["path"]))
            if play: s.p.play()
        else: s.playing = play
        s.changed.emit()
    def resume(s):
        if not s.queue: return
        if s.p: s.p.play()
        else: s.playing = True; s.changed.emit()
    def pause(s):
        if s.p: s.p.pause()
        else: s.playing = False; s.changed.emit()
    def toggle(s): s.pause() if s.playing else s.resume()
    def next(s, d=1):
        if s.queue: s.i = (s.i + d) % len(s.queue); s._load(True)
    def seek(s, ms):
        if s.p: s.p.setPosition(int(ms))
    def volume(s, v):
        s.vol = v; s._apply_vol()
    def mute(s, on): s.muted = on; s._apply_vol(); s.changed.emit()
    def _apply_vol(s):
        if s.p: s.o.setVolume(0 if s.muted else s.vol / 100)

# ───────────────────────── widgets compartilhados ─────────────────────────
class BarChart(QWidget):
    def __init__(s, fmt=None): super().__init__(); s.data = []; s.fmt = fmt or (lambda v: f"{v:g}"); s.setMinimumHeight(180)
    def set_data(s, data, fmt=None):
        s.data = data; s.fmt = fmt or s.fmt; s.update()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); w, h = s.width(), s.height(); L, R, Tp, B = 56, 12, 18, 32
        mx = max([v for _, v in s.data] or [0])
        if mx <= 0: p.setPen(QColor(T["muted"])); p.drawText(s.rect(), Qt.AlignCenter, "Sem dados para exibir"); return
        mx *= 1.12; ph = h - Tp - B; f = p.font(); f.setPixelSize(11); p.setFont(f); fm = p.fontMetrics()
        for i in range(5):
            y = Tp + ph * (1 - i / 4); p.setPen(QColor(T["line"])); p.drawLine(L, int(y), w - R, int(y))
            p.setPen(QColor(T["muted"])); p.drawText(QRectF(0, y - 9, L - 8, 18), Qt.AlignRight | Qt.AlignVCenter, s.fmt(mx * i / 4))
        n = len(s.data); bw = (w - L - R) / n; step = max(1, math.ceil(n * 46 / (w - L - R)))
        for i, (lab, v) in enumerate(s.data):
            x = L + i * bw + bw * .2; bh = ph * v / mx
            p.setBrush(QColor(T["accent"])); p.setPen(Qt.NoPen); p.drawRoundedRect(QRectF(x, Tp + ph - bh, bw * .6, max(bh, 0)), 5, 5)
            if v > 0 and bw > 38: p.setPen(QColor(T["text"])); p.drawText(QRectF(L + i * bw - 10, Tp + ph - bh - 18, bw + 20, 16), Qt.AlignCenter, s.fmt(v))
            if i % step == 0:
                p.setPen(QColor(T["muted"])); p.drawText(QRectF(L + i * bw - bw * (step - 1) / 2, h - B + 8, bw * step, 16), Qt.AlignHCenter | Qt.AlignTop,
                                                         fm.elidedText(lab, Qt.ElideRight, int(bw * step)))

class PickRow(QWidget):
    changed = Signal(str)
    def __init__(s, filt, test=None):
        super().__init__(); s.filt = filt; l = QHBoxLayout(s); l.setContentsMargins(0, 0, 0, 0); l.setSpacing(6)
        s.e = QLineEdit(); s.e.setReadOnly(True); s.e.setPlaceholderText("padrão / nenhum"); l.addWidget(s.e, 1)
        for ic, fn in [("plus", s.pick), ("x", lambda: s.set(""))] + ([("play", lambda: test(s.text()))] if test else []):
            b = IBtn(ic, 34, "dark"); b.clicked.connect(lambda _, fn=fn: fn()); l.addWidget(b)
    def pick(s):
        p, _ = QFileDialog.getOpenFileName(s, "Escolher arquivo", "", s.filt)
        if p: s.set(p)
    def set(s, p, emit=True):
        s.e.setText(p); s.e.setToolTip(p)
        if emit: s.changed.emit(p)
    def text(s): return s.e.text()

class FilesPicker(QWidget):
    def __init__(s, files=None):
        super().__init__(); l = QVBoxLayout(s); l.setContentsMargins(0, 0, 0, 0)
        s.lw = QListWidget(); s.lw.setMaximumHeight(90); s.lw.addItems(files or []); s.lw.itemDoubleClicked.connect(lambda i: open_file(i.text()))
        r = QHBoxLayout(); a = IBtn("plus", 34); d = IBtn("trash", 34, "dark"); a.clicked.connect(s.add); d.clicked.connect(s.rem)
        r.addWidget(a); r.addWidget(d); r.addWidget(muted("Duplo clique abre o arquivo", 11, 500)); r.addStretch(); l.addWidget(s.lw); l.addLayout(r)
    def add(s):
        ps, _ = QFileDialog.getOpenFileNames(s, "Anexar arquivos")
        for p in ps: s.lw.addItem(p)
    def rem(s):
        for i in s.lw.selectedItems(): s.lw.takeItem(s.lw.row(i))
    def files(s): return [s.lw.item(i).text() for i in range(s.lw.count())]

def clear_layout(l, keep=0):
    while l.count() > keep:
        it = l.takeAt(0); w = it.widget()
        if w: w.hide(); w.setParent(None); w.deleteLater()

def open_file(p):
    if p: QDesktopServices.openUrl(QUrl.fromLocalFile(str(p)))
def confirm(parent, text): return QMessageBox.question(parent, "Ômega", text) == QMessageBox.Yes
def fill(cb, items, blank="—"):
    cur = cb.currentText(); cb.blockSignals(True); cb.clear(); cb.addItem(blank); cb.addItems(items)
    cb.setCurrentIndex(max(0, cb.findText(cur))); cb.blockSignals(False)
def cbval(cb): return "" if cb.currentIndex() <= 0 else cb.currentText()
def setcb(cb, v): i = cb.findText(v); cb.setCurrentIndex(i if i > 0 else 0)
def mk_table(headers):
    t = QTableWidget(0, len(headers)); t.setHorizontalHeaderLabels(headers); t.setSelectionBehavior(QAbstractItemView.SelectRows)
    t.setEditTriggers(QAbstractItemView.NoEditTriggers); t.verticalHeader().hide(); t.horizontalHeader().setStretchLastSection(True); t.setShowGrid(False); return t
def put(t, r, c, text, data=None):
    it = QTableWidgetItem(text)
    if data is not None: it.setData(Qt.UserRole, data)
    t.setItem(r, c, it); return it
def sel_id(t):
    r = t.currentRow(); it = t.item(r, 0) if r >= 0 else None
    return it.data(Qt.UserRole) if it else None

import re
_URL = re.compile(r'(https?://[^\s<>"\']+|www\.[^\s<>"\']+)')
def _trim(u): return u.rstrip(".,;:!?)]}")
def url_at(text, pos):
    for m in _URL.finditer(text):
        u = _trim(m.group(0))
        if m.start() <= pos < m.start() + len(u): return u if u.startswith("http") else "https://" + u
    return None

class LinkHighlighter(QSyntaxHighlighter):
    def highlightBlock(s, text):
        f = QTextCharFormat(); f.setForeground(QColor(T["accent"])); f.setFontUnderline(True)
        for m in _URL.finditer(text): s.setFormat(m.start(), len(_trim(m.group(0))), f)

class LinkTextEdit(QTextEdit):
    """Caixa de texto onde links (http://, https://, www.) ficam destacados e abrem no navegador com um clique."""
    def __init__(s, *a): super().__init__(*a); s.hl = LinkHighlighter(s.document()); s.setMouseTracking(True); s.viewport().setMouseTracking(True)
    def _link(s, pos):
        c = s.cursorForPosition(pos); blk = c.block(); end = QTextCursor(blk); end.movePosition(QTextCursor.EndOfBlock)
        if pos.y() > s.cursorRect(end).bottom() + 2 or (s.cursorRect(c).y() == s.cursorRect(end).y() and pos.x() > s.cursorRect(end).x() + 6): return None
        i = c.positionInBlock(); return url_at(blk.text(), i) or (url_at(blk.text(), i - 1) if i > 0 else None)
    def mouseMoveEvent(s, e):
        s.viewport().setCursor(Qt.PointingHandCursor if s._link(e.position().toPoint()) else Qt.IBeamCursor); super().mouseMoveEvent(e)
    def mouseReleaseEvent(s, e):
        super().mouseReleaseEvent(e)
        if e.button() == Qt.LeftButton and not s.textCursor().hasSelection():
            u = s._link(e.position().toPoint())
            if u: QDesktopServices.openUrl(QUrl(u))
    def retheme(s): s.hl.rehighlight()

class Legend(QWidget):
    """Legenda com bolinhas coloridas e texto, quebrando em várias linhas se preciso. items = [(cor, texto)]"""
    def __init__(s): super().__init__(); s.items = []; s.setFixedHeight(34)
    def set_items(s, items): s.items = items; s.relayout(); s.update()
    def font_(s): f = QFont(s.font()); f.setPixelSize(15); return f
    def flow(s, w):
        fm = QFontMetrics(s.font_()); x = 4; y = 0; pos = []
        for col, txt in s.items:
            iw = 20 + fm.horizontalAdvance(txt) + 26
            if x + iw > w and x > 4: x = 4; y += 30
            pos.append((x, y)); x += iw
        return pos, y + 30
    def relayout(s): s.setFixedHeight(max(34, s.flow(max(200, s.width()))[1] + 4))
    def resizeEvent(s, e): s.relayout()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setFont(s.font_()); pos, _ = s.flow(s.width())
        for (col, txt), (x, y) in zip(s.items, pos):
            p.setPen(Qt.NoPen); p.setBrush(QColor(col)); p.drawEllipse(QRectF(x, y + 6, 15, 15)); p.setPen(QColor(T["text"])); p.drawText(QRectF(x + 24, y, s.width(), 27), Qt.AlignLeft | Qt.AlignVCenter, txt)

class ElidedLabel(QLabel):
    """Texto que termina em reticências quando não cabe."""
    def __init__(s, size=18, weight=QFont.Light):
        super().__init__(); s.full = ""; s.fs, s.fw = size, weight; s.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Preferred); s.setMinimumWidth(30)
    def setFull(s, t): s.full = t; s.setToolTip(t); s.update()
    def sizeHint(s): return QSize(120, s.fs + 14)
    def paintEvent(s, e):
        p = QPainter(s); f = QFont(s.font()); f.setPixelSize(s.fs); f.setWeight(s.fw); p.setFont(f); p.setPen(QColor(T["text"]))
        p.drawText(s.rect(), Qt.AlignLeft | Qt.AlignVCenter, QFontMetrics(f).elidedText(s.full, Qt.ElideRight, s.width()))

class FormDialog(QDialog):
    """fields: (chave, rótulo, tipo, [opções]) — tipos: text,long,date,time,int,float,combo,ecombo,file,files"""
    def __init__(s, parent, title, fields, values=None):
        super().__init__(parent); s.setWindowTitle(title); s.setMinimumWidth(500); s.fields = fields; s.w = {}
        f = QFormLayout(s); f.setSpacing(10); f.setContentsMargins(22, 20, 22, 20); v = values or {}
        f.addRow(heading(title, 24)); 
        for key, label, typ, *opt in fields:
            val = v.get(key)
            if typ == "text": w = QLineEdit(val or "")
            elif typ == "long": w = LinkTextEdit(); w.setPlainText(val or ""); w.setFixedHeight(100)
            elif typ == "date":
                w = QDateEdit(); w.setCalendarPopup(True); w.setDisplayFormat("dd/MM/yyyy"); w.setDate(QDate.fromString(val, Qt.ISODate) if val else QDate.currentDate())
            elif typ == "time": w = QTimeEdit(); w.setDisplayFormat("HH:mm"); w.setTime(QTime.fromString(val, "HH:mm") if val else QTime.currentTime())
            elif typ == "int": w = QSpinBox(); w.setRange(0, 100000); w.setValue(int(val or 0))
            elif typ == "float": w = QDoubleSpinBox(); w.setRange(0, 1000); w.setDecimals(1); w.setValue(float(val or 0))
            elif typ == "combo": w = QComboBox(); w.addItems(["—"] + opt[0]); setcb(w, val or "")
            elif typ == "ecombo": w = QComboBox(); w.setEditable(True); w.addItems(opt[0]); w.setCurrentText(val or "")
            elif typ == "file": w = PickRow("Todos (*)"); w.set(val or "", False)
            else: w = FilesPicker(val)
            f.addRow(muted(label, 12), w); s.w[key] = w
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(s.accept); bb.rejected.connect(s.reject); f.addRow(bb)
    def values(s):
        out = {}
        for key, label, typ, *opt in s.fields:
            w = s.w[key]
            if typ == "text": out[key] = w.text().strip()
            elif typ == "long": out[key] = w.toPlainText().strip()
            elif typ == "date": out[key] = w.date().toString(Qt.ISODate)
            elif typ == "time": out[key] = w.time().toString("HH:mm")
            elif typ in ("int", "float"): out[key] = w.value()
            elif typ == "combo": out[key] = cbval(w)
            elif typ == "ecombo": out[key] = w.currentText().strip()
            elif typ == "file": out[key] = w.text()
            else: out[key] = w.files()
        return out

def color_of(d, kind, name, default=""):
    """Cor definida pelo usuário para uma matéria/tag ('' se não houver)."""
    return d["colors"][kind].get(name) or default
def subj_color(d, name): return color_of(d, "subjects", name) or scolor(name)
def on_color(hex_):
    c = QColor(hex_); return "#17181a" if (.299 * c.red() + .587 * c.green() + .114 * c.blue()) / 255 > .66 else "#ffffff"

class ColorRow(QWidget):
    """Linha de bolinhas de cor: a primeira (riscada) = automática; a última (+) = cor personalizada."""
    changed = Signal(str)
    def __init__(s, value="", auto=True, size=22, gap=5):
        super().__init__(); s.v = value; s.sz = size; s.gap = gap; s.opts = ([""] if auto else []) + PALETTE + ["+"]
        s.setFixedSize(len(s.opts) * (size + gap) + 8, size + 10); s.setCursor(Qt.PointingHandCursor)
    def color(s): return s.v
    def set(s, v): s.v = v; s.update()
    def rc(s, i): return QRectF(5 + i * (s.sz + s.gap), 5, s.sz, s.sz)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing)
        for i, o in enumerate(s.opts):
            r = s.rc(i); custom = o == "+" and s.v and s.v not in PALETTE
            if o == "": p.setPen(QPen(QColor(T["muted"]), 1.6)); p.setBrush(Qt.NoBrush); p.drawEllipse(r.adjusted(2, 2, -2, -2)); p.drawLine(r.bottomLeft() + QPointF(6, -6), r.topRight() + QPointF(-6, 6))
            elif o == "+" and not custom: p.setPen(QPen(QColor(T["muted"]), 1.6)); p.setBrush(Qt.NoBrush); p.drawEllipse(r.adjusted(2, 2, -2, -2)); p.drawPixmap(QPointF(r.x() + (s.sz - 12) / 2, r.y() + (s.sz - 12) / 2), pix("plus", T["muted"], 12))
            else: p.setPen(Qt.NoPen); p.setBrush(QColor(s.v if custom else o)); p.drawEllipse(r.adjusted(2, 2, -2, -2))
            if (o == s.v and o != "+") or custom: p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(T["text"]), 2.2)); p.drawEllipse(r.adjusted(-1, -1, 1, 1))
    def mousePressEvent(s, e):
        for i, o in enumerate(s.opts):
            if s.rc(i).adjusted(-3, -3, 3, 3).contains(e.position()):
                if o == "+":
                    c = QColorDialog.getColor(QColor(s.v or T["accent"]), s, "Escolher cor")
                    if not c.isValid(): return
                    s.v = c.name()
                else: s.v = o
                s.update(); s.changed.emit(s.v); return

def dot_icon(color, d=18):
    pm = QPixmap(d, d); pm.fill(Qt.transparent); p = QPainter(pm); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(QColor(color)); p.drawEllipse(1, 1, d - 2, d - 2); p.end(); return QIcon(pm)

def edit_list(parent, title, items, colors=None):
    """Editor de lista (matérias/tags). Se 'colors' (dict nome→cor) for passado, permite escolher a cor de cada item."""
    dlg = QDialog(parent); dlg.setWindowTitle(title); dlg.setMinimumWidth(470); l = QVBoxLayout(dlg); l.setContentsMargins(22, 20, 22, 20); l.addWidget(heading(title, 24))
    tmp = dict(colors) if colors is not None else None; ic = lambda n: dot_icon((tmp.get(n) if tmp is not None else "") or scolor(n))
    lw = QListWidget()
    for n in items: lw.addItem(QListWidgetItem(ic(n), n))
    l.addWidget(lw); cr = None
    if tmp is not None:
        l.addWidget(muted("Cor do item selecionado (a primeira bolinha = automática)", 12)); cr = ColorRow(); l.addWidget(cr)
        def cur_changed(it, _=None): cr.set(tmp.get(it.text(), "") if it else "")
        def col_changed(v):
            it = lw.currentItem()
            if it:
                if v: tmp[it.text()] = v
                else: tmp.pop(it.text(), None)
                it.setIcon(ic(it.text()))
        lw.currentItemChanged.connect(cur_changed); cr.changed.connect(col_changed)
    r = QHBoxLayout(); ed = QLineEdit(); ed.setPlaceholderText("Novo item…"); a = IBtn("plus", 38); rm = IBtn("trash", 38, "dark")
    def add():
        t = ed.text().strip()
        if t and t not in [lw.item(i).text() for i in range(lw.count())]: lw.addItem(QListWidgetItem(ic(t), t)); ed.clear(); lw.setCurrentRow(lw.count() - 1)
    def rem():
        for i in lw.selectedItems(): lw.takeItem(lw.row(i))
    a.clicked.connect(add); ed.returnPressed.connect(add); rm.clicked.connect(rem); r.addWidget(ed, 1); r.addWidget(a); r.addWidget(rm); l.addLayout(r)
    bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject); l.addWidget(bb)
    if dlg.exec():
        items[:] = [lw.item(i).text() for i in range(lw.count())]
        if tmp is not None: colors.clear(); colors.update({k: v for k, v in tmp.items() if k in items and v})
        return True
    return False

def manage(parent, st, kind, title):
    """Abre o editor de matérias ('subjects') ou tags ('tags') com cores e salva."""
    ok = edit_list(parent, title, st.data[kind], st.data["colors"][kind])
    if ok: st.save()
    return ok

def pick_date(parent, iso_=None, clear=False):
    """Retorna 'AAAA-MM-DD', '' (remover) ou None (cancelar)."""
    dlg = QDialog(parent); dlg.setWindowTitle("Data"); l = QVBoxLayout(dlg); l.setContentsMargins(18, 18, 18, 18); res = [None]
    cal = QCalendarWidget(); cal.setVerticalHeaderFormat(QCalendarWidget.NoVerticalHeader); cal.setMinimumSize(360, 270)
    if iso_: cal.setSelectedDate(QDate.fromString(iso_, Qt.ISODate))
    l.addWidget(cal); r = QHBoxLayout(); ok = QPushButton("Confirmar"); r.addStretch(); r.addWidget(ok)
    ok.clicked.connect(lambda: (res.__setitem__(0, cal.selectedDate().toString(Qt.ISODate)), dlg.accept()))
    if clear: c = pill("Remover data"); c.clicked.connect(lambda: (res.__setitem__(0, ""), dlg.accept())); r.insertWidget(0, c)
    l.addLayout(r); dlg.exec(); return res[0]

def pick_time(parent, cur="", clear=True):
    dlg = QDialog(parent); dlg.setWindowTitle("Horário"); l = QVBoxLayout(dlg); l.setContentsMargins(18, 18, 18, 18); res = [None]
    te = QTimeEdit(); te.setDisplayFormat("HH:mm"); te.setTime(QTime.fromString(cur, "HH:mm") if cur else QTime(9, 0)); te.setStyleSheet("font-size:28px;font-weight:300")
    l.addWidget(te); r = QHBoxLayout(); ok = QPushButton("Confirmar"); r.addStretch(); r.addWidget(ok)
    ok.clicked.connect(lambda: (res.__setitem__(0, te.time().toString("HH:mm")), dlg.accept()))
    if clear: c = pill("Remover"); c.clicked.connect(lambda: (res.__setitem__(0, ""), dlg.accept())); r.insertWidget(0, c)
    l.addLayout(r); dlg.exec(); return res[0]

class Overlay(QDialog):
    """Janela modal arredondada no estilo da referência (Novo Evento / Novo Bloco)."""
    def __init__(s, parent, w=500):
        super().__init__(parent); s.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint); s.setAttribute(Qt.WA_TranslucentBackground); s.setFixedWidth(w)
        s.lay = QVBoxLayout(s); s.lay.setContentsMargins(26, 22, 26, 24); s.lay.setSpacing(12)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(T["card"])); p.setPen(QPen(QColor(T["line"]), 1.5))
        p.drawRoundedRect(QRectF(s.rect()).adjusted(1, 1, -1, -1), 18, 18)
    def head(s, text):
        r = QHBoxLayout(); te = QLineEdit(text); te.setPlaceholderText("Título")
        te.setStyleSheet(f"background:transparent;font-size:32px;font-weight:700;color:{T['muted']};padding:0")
        pe = QLabel(); pe.setPixmap(pix("pencil", T["muted"], 24)); x = IBtn("x", 52); x.clicked.connect(s.reject)
        r.addWidget(te, 1); r.addWidget(pe); r.addSpacing(10); r.addWidget(x); s.lay.addLayout(r); return te
    def ph_edit(s, ph, h=150):
        t = LinkTextEdit(); t.setPlaceholderText(ph); t.setFixedHeight(h); t.setStyleSheet(f"background:{T['field']};border-radius:26px;padding:16px 20px;font-size:14px"); return t
    def pill_combo(s, ph, items, val=""):
        c = QComboBox(); c.addItems([ph] + items); setcb(c, val); c.setStyleSheet(f"QComboBox{{background:{T['field']};border:1px solid {T['field']};border-radius:22px;padding:11px 20px;color:{T['text']}}}")
        return c
class ClickPill(QPushButton):
    def __init__(s, ph): super().__init__(ph); s.ph = ph; s.v = ""; s.setMinimumHeight(46); s.setCursor(Qt.PointingHandCursor); LISTEN.add(s); s.retheme()
    def retheme(s): s.setStyleSheet(f"QPushButton{{border-radius:22px;background:{T['field']};color:{T['text']};font-weight:500}}")
    def setv(s, v): s.v = v; s.setText(v or s.ph)
