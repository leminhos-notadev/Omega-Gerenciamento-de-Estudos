# -*- coding: utf-8 -*-
"""Cronograma / Ciclo de estudos, Simulados / Redação e Configurações."""
from omega_core import *

HOUR_H, LEFT = 48, 62
def tmin(s): h, m = s.split(":"); return int(h) * 60 + int(m)
def bcolor(b, cmap): return b.get("color") or cmap.get(b.get("subject", "")) or BLOCK_COLORS[0]

# ───────────────────────── cronograma semanal ─────────────────────────
def hm(m): m = max(0, min(1439, int(m))); return f"{m // 60:02d}:{m % 60:02d}"

class WeekGrid(QWidget):
    new = Signal(int, int); edit = Signal(str); picked = Signal(str); moved = Signal(str, int, int)
    def __init__(s):
        super().__init__(); s.blocks = []; s.rects = []; s.cmap = {}; s.sel = None; s.hover = None; s.pressed = None; s.dragging = False; s.drag_pt = None; s.off_y = 0; s.setFixedHeight(24 * HOUR_H + 10); s.setMouseTracking(True)
    def cw(s): return (s.width() - LEFT) / 7
    def cell_at(s, pt, off_y=0):
        day = max(0, min(6, int((pt.x() - LEFT) // s.cw()))); minute = int(round(((pt.y() - off_y - 5) / HOUR_H * 60) / 15.0) * 15); return day, max(0, min(1425, minute))
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); w = s.width(); cw = s.cw(); f = p.font(); f.setPixelSize(10); p.setFont(f)
        for h in range(25):
            y = h * HOUR_H + 5; p.setPen(QColor(T["line"])); p.drawLine(LEFT, y, w, y)
            if h < 24: p.setPen(QColor(T["muted"])); p.drawText(QRectF(0, y - 8, LEFT - 10, 16), Qt.AlignRight | Qt.AlignVCenter, f"{h:02d}:00")
        for c in range(8): x = int(LEFT + c * cw); p.setPen(QColor(T["line"])); p.drawLine(x, 5, x, 24 * HOUR_H + 5)
        s.rects = []; ghost = None
        for day in range(7):
            bl = sorted([b for b in s.blocks if b["day"] == day], key=lambda b: tmin(b["start"])); lanes = []; pos = {}
            for b in bl:
                for i, end in enumerate(lanes):
                    if end <= tmin(b["start"]): lanes[i] = tmin(b["end"]); pos[b["id"]] = i; break
                else: lanes.append(tmin(b["end"])); pos[b["id"]] = len(lanes) - 1
            nl = max(1, len(lanes))
            for b in bl:
                sm, em = tmin(b["start"]), max(tmin(b["end"]), tmin(b["start"]) + 20); bw = (cw - 6) / nl
                r = QRectF(LEFT + day * cw + 3 + pos[b["id"]] * bw, 5 + sm / 60 * HOUR_H + 1, bw - 2, max(22, (em - sm) / 60 * HOUR_H - 2)); s.rects.append((r, b["id"])); col = bcolor(b, s.cmap)
                if s.dragging and s.pressed == b["id"]: ghost = (r, col); alpha = 70
                else: alpha = 255
                c = QColor(col); c.setAlpha(alpha); p.setBrush(c); p.setPen(Qt.NoPen); p.drawRoundedRect(r, 10, 10); p.setPen(QColor(on_color(col))); ft = p.font(); ft.setPixelSize(11); ft.setWeight(QFont.Bold); p.setFont(ft)
                p.drawText(r.adjusted(8, 3, -6, -2), Qt.AlignLeft | Qt.AlignTop, QFontMetrics(ft).elidedText(b["title"], Qt.ElideRight, int(r.width() - 14)))
                if r.height() > 36: ft.setWeight(QFont.Normal); ft.setPixelSize(10); p.setFont(ft); p.drawText(r.adjusted(8, 19, -6, -2), Qt.AlignLeft | Qt.AlignTop, f"{b['start']} – {b['end']}")
                f2 = p.font(); f2.setPixelSize(10); p.setFont(f2)
                if b["id"] == s.sel and not (s.dragging and s.pressed == b["id"]): p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(T["text"]), 2.2)); p.drawRoundedRect(r.adjusted(-1, -1, 1, 1), 10, 10)
        if ghost and s.drag_pt is not None:
            r, col = ghost; day, minute = s.cell_at(s.drag_pt, s.off_y); g = QRectF(LEFT + day * cw + 3, 5 + minute / 60 * HOUR_H + 1, r.width(), r.height()); c = QColor(col); c.setAlpha(210)
            p.setBrush(c); p.setPen(QPen(QColor(T["text"]), 2)); p.drawRoundedRect(g, 10, 10)
    def mousePressEvent(s, e):
        pt = e.position(); hit = next(((r, i) for r, i in reversed(s.rects) if r.contains(pt)), None); s.sel = hit[1] if hit else None; s.pressed = s.sel; s.press_pt = pt; s.dragging = False; s.off_y = pt.y() - hit[0].top() if hit else 0
        s.picked.emit(s.sel or ""); s.update()
    def mouseMoveEvent(s, e):
        pt = e.position(); s.hover = s.cell_at(pt)
        if s.pressed and (pt - s.press_pt).manhattanLength() > 8: s.dragging = True; s.drag_pt = pt; s.update()
    def mouseReleaseEvent(s, e):
        if s.dragging and s.pressed: day, minute = s.cell_at(e.position(), s.off_y); bid = s.pressed; s.dragging = False; s.pressed = None; s.moved.emit(bid, day, minute)
        s.dragging = False; s.pressed = None; s.update()
    def mouseDoubleClickEvent(s, e):
        pt = e.position(); hit = next((i for r, i in reversed(s.rects) if r.contains(pt)), None)
        if hit: s.edit.emit(hit)
        elif pt.x() > LEFT: day, minute = s.cell_at(pt); s.new.emit(day, minute // 60)

class BlockDialog(Overlay):
    def __init__(s, parent, win, blk, day, hour):
        super().__init__(parent, 520); d = win.store.data; s.deleted = False; s.blk = blk; s.title = s.head(blk["title"] if blk else "Novo Bloco")
        r = QHBoxLayout(); r.setSpacing(8); lab = lambda t: (lambda l: (l.setStyleSheet("font-size:26px;font-weight:300"), l)[1])(QLabel(t))
        ts = f"QTimeEdit{{background:transparent;color:{T['accent']};font-size:26px;font-weight:300;padding:0}}"
        s.t1, s.t2 = QTimeEdit(), QTimeEdit()
        for w, v in ((s.t1, blk["start"] if blk else f"{hour:02d}:00"), (s.t2, blk["end"] if blk else f"{min(hour + 1, 23):02d}:{'00' if hour < 23 else '59'}")): w.setDisplayFormat("HH:mm"); w.setTime(QTime.fromString(v, "HH:mm")); w.setStyleSheet(ts)
        s.dc = QComboBox(); s.dc.addItems(DIAS_DOM); s.dc.setCurrentIndex(blk["day"] if blk else day); s.dc.setMinimumWidth(84); s.dc.setSizeAdjustPolicy(QComboBox.AdjustToContents)
        s.dc.setStyleSheet(f"QComboBox{{background:transparent;border:none;color:{T['accent']};font-size:26px;font-weight:300;padding:0}}QComboBox::drop-down{{width:0}}")
        for w in (lab("Das"), s.t1, lab("às"), s.t2, lab("("), s.dc, lab(")")): r.addWidget(w)
        r.addStretch(); s.lay.addLayout(r); q = QHBoxLayout(); s.sub = s.pill_combo("Adicionar Matéria", d["subjects"], blk["subject"] if blk else ""); s.tag = s.pill_combo("Adicionar Tag", d["tags"], blk["tag"] if blk else "")
        q.addWidget(s.sub); q.addWidget(s.tag); s.lay.addLayout(q); s.desc = s.ph_edit("Adicionar Descrição", 150); s.desc.setPlainText(blk["desc"] if blk else ""); s.lay.addWidget(s.desc)
        s.lay.addWidget(muted("Cor do bloco (a primeira bolinha = automática: cor da matéria ou laranja)", 11, 500)); s.cr = ColorRow(blk.get("color", "") if blk else ""); s.lay.addWidget(s.cr)
        b = QHBoxLayout()
        if blk: tr = IBtn("trash", 46, "dark", "Excluir bloco"); tr.clicked.connect(lambda: (setattr(s, "deleted", True), s.accept())); b.addWidget(tr)
        b.addStretch(); sv = QPushButton("Salvar"); sv.setMinimumWidth(140); sv.clicked.connect(s.accept); b.addWidget(sv); s.lay.addLayout(b)
    def result(s):
        a, b = s.t1.time().toString("HH:mm"), s.t2.time().toString("HH:mm")
        if tmin(b) <= tmin(a): b = QTime.fromString(a, "HH:mm").addSecs(3600).toString("HH:mm") if tmin(a) < 23 * 60 else "23:59"
        return dict(title=s.title.text().strip() or "Novo Bloco", day=s.dc.currentIndex(), start=a, end=b, subject=cbval(s.sub), tag=cbval(s.tag), desc=s.desc.toPlainText().strip(), color=s.cr.color())

class ScheduleView(QWidget):
    clip = None   # área de transferência dos blocos (compartilhada entre cronogramas)
    def __init__(s, win):
        super().__init__(); s.win = win; s.sched = None; L = QVBoxLayout(s); L.setContentsMargins(0, 0, 0, 0); L.setSpacing(4)
        L.addWidget(muted("Clique 1x para selecionar · 2x para abrir (ou criar em área vazia) · arraste para mover · Ctrl+C copiar · Ctrl+X recortar · Ctrl+V colar onde o mouse está · Del apagar", 11, 500))
        s.head = QWidget(); hl = QHBoxLayout(s.head); hl.setContentsMargins(0, 0, 14, 0); hl.setSpacing(0); hl.addSpacing(LEFT); s.dl = []
        for i in range(7): l = QLabel(DIAS_DOM[i] + "."); l.setAlignment(Qt.AlignCenter); hl.addWidget(l, 1); s.dl.append(l)
        L.addWidget(s.head); card = Card(22); cl = QVBoxLayout(card); cl.setContentsMargins(6, 8, 6, 8); s.sc = QScrollArea(); s.sc.setWidgetResizable(True); s.grid = WeekGrid(); s.sc.setWidget(s.grid); cl.addWidget(s.sc); L.addWidget(card, 1)
        s.grid.new.connect(s.new_block); s.grid.edit.connect(s.edit_block); s.grid.moved.connect(s.move_block); QTimer.singleShot(0, lambda: s.sc.verticalScrollBar().setValue(6 * HOUR_H))
    @property
    def d(s): return s.win.store.data
    def load(s, sched):
        s.sched = sched; s.grid.cmap = s.d["colors"]["subjects"]; s.grid.blocks = sched["blocks"] if sched else []; s.grid.update(); wd = (today().weekday() + 1) % 7
        for i, l in enumerate(s.dl): l.setStyleSheet(f"font-size:15px;font-weight:700;color:{T['accent'] if i == wd else T['text']}")
    def block(s, bid): return next((x for x in s.sched["blocks"] if x["id"] == bid), None) if s.sched else None
    def new_block(s, day, hour):
        if not s.sched: return
        dlg = BlockDialog(s.win, s.win, None, day, hour)
        if dlg.exec(): b = dict(dlg.result(), id=uid()); s.sched["blocks"].append(b); s.grid.sel = b["id"]; s.win.store.save(); s.load(s.sched)
    def edit_block(s, bid):
        b = s.block(bid)
        if not b: return
        dlg = BlockDialog(s.win, s.win, b, 0, 0)
        if dlg.exec():
            if dlg.deleted: s.sched["blocks"].remove(b); s.grid.sel = None
            else: b.update(dlg.result())
            s.win.store.save(); s.load(s.sched)
    def move_block(s, bid, day, minute):
        b = s.block(bid)
        if b: dur = tmin(b["end"]) - tmin(b["start"]); minute = max(0, min(minute, 1439 - dur)); b.update(day=day, start=hm(minute), end=hm(minute + dur)); s.win.store.save(); s.load(s.sched)
    def on_shortcut(s, key):
        import copy
        b = s.block(s.grid.sel)
        if key in ("copy", "cut") and b: ScheduleView.clip = {k: v for k, v in copy.deepcopy(b).items() if k != "id"}
        if key in ("cut", "delete") and b: s.sched["blocks"].remove(b); s.grid.sel = None; s.win.store.save(); s.load(s.sched)
        elif key == "paste" and ScheduleView.clip and s.sched:   # cola no dia/horário em que o mouse está
            c = ScheduleView.clip; dur = tmin(c["end"]) - tmin(c["start"]); day, minute = s.grid.hover or (c["day"], tmin(c["start"])); minute = max(0, min(minute, 1439 - dur))
            n = dict(copy.deepcopy(c), id=uid(), day=day, start=hm(minute), end=hm(minute + dur)); s.sched["blocks"].append(n); s.grid.sel = n["id"]; s.win.store.save(); s.load(s.sched)

# ───────────────────────── ciclo de estudos ─────────────────────────
class SessionGrid(QWidget):
    changed = Signal()
    BOX, GAP, ROW = 30, 4, 46
    def __init__(s, marks): super().__init__(); s.marks = marks; s.setFixedSize(5 * (s.BOX + s.GAP) + 14, ((len(marks) + 4) // 5) * s.ROW + 4)
    def box(s, i): r, c = divmod(i, 5); return QRectF(8 + c * (s.BOX + s.GAP), 8 + r * s.ROW, s.BOX, s.BOX)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); n = len(s.marks)
        for r in range((n + 4) // 5):
            cnt = min(5, n - r * 5); p.setPen(Qt.NoPen); p.setBrush(QColor(T["field"])); p.drawRoundedRect(QRectF(2, 2 + r * s.ROW, cnt * (s.BOX + s.GAP) + 10, s.BOX + 12), 9, 9)
        for i, m in enumerate(s.marks):
            b = s.box(i); p.setBrush(QColor(T["accent"] if m else T["btn"])); p.setPen(QPen(QColor(T["line"]), 1) if not m else Qt.NoPen); p.drawRoundedRect(b, 7, 7)
            if m: k = 18; p.drawPixmap(QPointF(b.x() + (s.BOX - k) / 2, b.y() + (s.BOX - k) / 2), pix("check", T["on_accent"], k))
    def mousePressEvent(s, e):
        for i in range(len(s.marks)):
            if s.box(i).contains(e.position()): s.marks[i] = not s.marks[i]; s.update(); s.changed.emit(); return

class ProgressBar(QWidget):
    def __init__(s): super().__init__(); s.v = 0.0; s.setFixedHeight(30)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); r = QRectF(s.rect()); p.setBrush(QColor(T["line"])); p.drawRoundedRect(r, 15, 15)
        if s.v > 0: p.setBrush(QColor(T["accent"])); p.drawRoundedRect(QRectF(0, 0, max(30, r.width() * s.v), r.height()), 15, 15)

class CycleView(QWidget):
    created = Signal(str); modified = Signal()
    def __init__(s, win):
        super().__init__(); s.win = win; s.cy = None; L = QVBoxLayout(s); L.setContentsMargins(0, 0, 0, 0); s.stack = QStackedWidget(); L.addWidget(s.stack)
        # criar
        c = QWidget(); cl = QVBoxLayout(c); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(8); sub = muted("Crie seu Ciclo de Estudos", 22, 700); sub.setAlignment(Qt.AlignCenter); cl.addWidget(sub)
        tr = QHBoxLayout(); tr.setContentsMargins(60, 0, 60, 0); tr.addWidget(muted("Total de blocos do ciclo", 13, 700)); s.total = QSpinBox(); s.total.setRange(1, 999); s.total.setValue(50); s.total.setFixedSize(84, 40); s.total.setAlignment(Qt.AlignCenter)
        s.total.setStyleSheet("font-size:16px;font-weight:700;padding:0"); s.total.valueChanged.connect(lambda _: s.recalc()); tr.addWidget(s.total); s.info = muted("", 12, 500); tr.addWidget(s.info, 1); cl.addLayout(tr)
        sc = QScrollArea(); sc.setWidgetResizable(True); w = QWidget(); s.rows = QVBoxLayout(w); s.rows.setSpacing(12); s.rows.setContentsMargins(60, 6, 60, 6); sc.setWidget(w); cl.addWidget(sc, 1)
        br_ = QHBoxLayout(); br_.addStretch(); mg = QPushButton("Gerenciar Matérias"); mg.setMinimumWidth(230); mg.clicked.connect(s.manage); cr = QPushButton("Criar Ciclo"); cr.setMinimumWidth(180); cr.clicked.connect(s.create)
        s.cancel = pill("Cancelar", False, 40); s.cancel.clicked.connect(lambda: s.created.emit("")); [br_.addWidget(x) for x in (mg, cr, s.cancel)]; br_.addStretch(); cl.addLayout(br_); s.stack.addWidget(c)
        # visualizar
        v = QWidget(); vl = QVBoxLayout(v); vl.setContentsMargins(0, 0, 0, 0); vl.setSpacing(8); h = QHBoxLayout(); s.name = QLabel(); s.name.setStyleSheet("font-size:38px;font-weight:700"); h.addWidget(s.name)
        for ic, tip, fn in [("pencil", "Renomear ciclo", s.rename), ("trash", "Excluir ciclo", s.delete)]: b = IBtn(ic, 40, "ghost", tip, 22); b.clicked.connect(lambda _, fn=fn: fn()); h.addWidget(b)
        h.addStretch(); vl.addLayout(h); pr = QHBoxLayout(); s.plab = QLabel(); s.plab.setStyleSheet("font-size:18px;font-weight:700"); s.pb = ProgressBar(); pr.addWidget(s.plab); pr.addWidget(s.pb, 1); vl.addLayout(pr)
        nx = QHBoxLayout(); nx.setSpacing(12); s.nextbtn = QPushButton(); s.nextbtn.setMinimumHeight(40); s.nextbtn.clicked.connect(s.do_next); nx.addWidget(s.nextbtn)
        s.auto = QCheckBox("Contar automaticamente os blocos de foco da matéria"); s.auto.toggled.connect(s.set_auto); nx.addWidget(s.auto); nx.addStretch(); vl.addLayout(nx)
        s.chipsrow = QHBoxLayout(); s.chipsrow.setSpacing(6); cw = QWidget(); cw.setLayout(s.chipsrow); vl.addWidget(cw)
        sc2 = QScrollArea(); sc2.setWidgetResizable(True); w2 = QWidget(); s.cards = QHBoxLayout(w2); s.cards.setSpacing(18); s.cards.setAlignment(Qt.AlignLeft | Qt.AlignTop); sc2.setWidget(w2); vl.addWidget(sc2, 1); s.stack.addWidget(v)
    @property
    def d(s): return s.win.store.data
    def manage(s):
        if manage(s, s.win.store, "subjects", "Matérias"): s.show_create()
    def show_create(s, can_cancel=False):
        """Sistema da planilha CICLO ITA: pontos = (dificuldade + conteúdo) × peso; os blocos do ciclo são divididos em proporção aos pontos."""
        clear_layout(s.rows, 0); s.spins = {}; s.res = {}; s.cancel.setVisible(can_cancel)
        for n in s.d["subjects"]:
            c = Card(30); c.setFixedHeight(104); l = QHBoxLayout(c); l.setContentsMargins(28, 8, 28, 8); t = QLabel(n); t.setStyleSheet("font-size:28px;font-weight:700"); l.addWidget(t, 1); sp = []
            for lab, dec in (("Dificuldade (1-5)", False), ("Qnt. de Conteúdo (1-5)", False), ("Peso", True)):
                v = QVBoxLayout(); v.setSpacing(2); m = muted(lab, 13, 700); m.setAlignment(Qt.AlignCenter); v.addWidget(m)
                if dec: q = QDoubleSpinBox(); q.setRange(0, 10); q.setDecimals(1); q.setSingleStep(0.5)
                else: q = QSpinBox(); q.setRange(0, 5)
                q.setSpecialValueText(" "); q.setAlignment(Qt.AlignCenter); q.setFixedSize(66, 58); q.setStyleSheet("font-size:22px;font-weight:700;border-radius:8px;padding:0"); q.valueChanged.connect(lambda _: s.recalc()); v.addWidget(q, 0, Qt.AlignHCenter); l.addSpacing(22); l.addLayout(v); sp.append(q)
            v = QVBoxLayout(); v.setSpacing(2); m = muted("Blocos", 13, 700); m.setAlignment(Qt.AlignCenter); v.addWidget(m); r = QLabel("–"); r.setAlignment(Qt.AlignCenter); r.setFixedSize(66, 58); r.setStyleSheet(f"font-size:26px;font-weight:700;color:{T['accent']}"); v.addWidget(r, 0, Qt.AlignHCenter); l.addSpacing(22); l.addLayout(v)
            s.spins[n] = sp; s.res[n] = r; s.rows.addWidget(c)
        if not s.d["subjects"]: s.rows.addWidget(muted("Nenhuma matéria cadastrada ainda. Clique em “Gerenciar Matérias” para adicionar.", 15, 600), 0, Qt.AlignCenter)
        s.rows.addStretch(); s.stack.setCurrentIndex(0); s.recalc()
    def rows_data(s): return [(n, sp[0].value(), sp[1].value(), sp[2].value()) for n, sp in s.spins.items()]
    def recalc(s):
        if not hasattr(s, "res"): return
        rows = s.rows_data(); blocks = cycle_blocks(rows, s.total.value()); S = sum((d + c) * p for _, d, c, p in rows)
        for (n, d, c, p), b in zip(rows, blocks): s.res[n].setText(str(b) if (d + c) * p > 0 else "–")
        s.info.setText(f"Σ pontos = {S:g}  ·  blocos por ponto = {s.total.value() / S:.3f}" if S > 0 else "Preencha dificuldade, conteúdo e peso das matérias que entram no ciclo.")
    def create(s):
        rows = s.rows_data(); blocks = cycle_blocks(rows, s.total.value()); items = [dict(subject=n, dif=d, cont=c, peso=p, n=b) for (n, d, c, p), b in zip(rows, blocks) if b > 0]
        if not items: QMessageBox.information(s, "Ômega", "Preencha dificuldade, conteúdo e peso de pelo menos uma matéria."); return
        nm, ok = QInputDialog.getText(s, "Novo ciclo", "Nome do ciclo:", text="Ciclo")
        if not ok: return
        cy = dict(id=uid(), name=nm.strip() or "Ciclo", number=1, auto=True, total=s.total.value(), items=items, marks={i["subject"]: [False] * i["n"] for i in items}, history=[])
        s.d["cycles"].append(cy); s.win.store.save(); s.created.emit(cy["id"])
    def load(s, cy):
        s.cy = cy; s.stack.setCurrentIndex(1); clear_layout(s.cards, 0); s.badges = {}; s.grids = {}
        s.auto.blockSignals(True); s.auto.setChecked(cy.get("auto", True)); s.auto.blockSignals(False)
        for it in cy["items"]:
            n = it["subject"]; m = cy["marks"][n]; c = Card(22, "card", True); c.setFixedWidth(380); l = QVBoxLayout(c); l.setContentsMargins(20, 18, 20, 18); l.setSpacing(10); h = QHBoxLayout(); v = QVBoxLayout(); v.setSpacing(0)
            t = QLabel(n); t.setStyleSheet("font-size:20px;font-weight:700"); v.addWidget(t); v.addWidget(muted(f"{len(m)} SESSÕES", 11, 700)); h.addLayout(v, 1)
            bd = QLabel(); bd.setFixedSize(46, 38); bd.setAlignment(Qt.AlignCenter); bd.setStyleSheet(f"border:1.5px solid {T['line']};border-radius:9px;font-size:12px;font-weight:700"); h.addWidget(bd); l.addLayout(h)
            sc = QScrollArea(); sc.setWidgetResizable(False); g = SessionGrid(m); g.changed.connect(s.after_change); sc.setWidget(g); sc.setFixedHeight(min(g.height() + 4, 420)); sc.setFrameShape(QFrame.NoFrame); l.addWidget(sc); s.cards.addWidget(c, 0, Qt.AlignTop)
            s.badges[n] = bd; s.grids[n] = g
        s.update_progress()
    def update_progress(s):
        """Atualiza textos, barra e sequência sem recriar os cartões (assim a página não 'pula' ao marcar uma sessão)."""
        cy = s.cy; tot = sum(len(m) for m in cy["marks"].values()); dn = sum(sum(m) for m in cy["marks"].values())
        s.name.setText(f"{cy['name']} número {cy['number']}"); s.plab.setText(f"Progresso: {dn * 100 // max(1, tot)}%  ({dn}/{tot})"); s.pb.v = dn / max(1, tot); s.pb.update()
        for n, bd in s.badges.items(): m = cy["marks"][n]; bd.setText(f"{sum(m) * 100 // max(1, len(m))}%")
        seq = cycle_order(cy); clear_layout(s.chipsrow, 0); s.chipsrow.addWidget(muted("Sequência sugerida:", 12, 600))
        for n in seq[:14]:
            col = subj_color(s.win.store.data, n); c = QLabel(n); c.setStyleSheet(f"background:{col};color:{on_color(col)};border-radius:12px;padding:3px 11px;font-size:11px;font-weight:700"); s.chipsrow.addWidget(c)
        if len(seq) > 14: s.chipsrow.addWidget(muted(f"+{len(seq) - 14}", 12))
        s.chipsrow.addStretch(); s.nextbtn.setText(f"Concluir próxima sessão: {seq[0]}" if seq else "Ciclo completo"); s.nextbtn.setEnabled(bool(seq))
    def after_change(s):
        cy = s.cy
        if cycle_complete(cy):
            advance_cycle(cy); s.win.store.save(); QMessageBox.information(s, "Ômega", f"Ciclo concluído! Começando o ciclo número {cy['number']}."); s.load(cy)
        else: s.win.store.save(); s.update_progress()
    def do_next(s):
        seq = cycle_order(s.cy)
        if seq: mark_session(s.cy, seq[0]); s.grids[seq[0]].update(); s.after_change()
    def set_auto(s, v): s.cy["auto"] = v; s.win.store.save()
    def rename(s):
        n, ok = QInputDialog.getText(s, "Renomear", "Nome do ciclo:", text=s.cy["name"])
        if ok and n.strip(): s.cy["name"] = n.strip(); s.win.store.save(); s.modified.emit()
    def delete(s):
        if confirm(s, f"Excluir o ciclo '{s.cy['name']}'?"): s.d["cycles"].remove(s.cy); s.win.store.save(); s.modified.emit()

class PlanPage(Page):
    def __init__(s, win):
        super().__init__(win); s.creating = False; lay = QVBoxLayout(s); lay.setContentsMargins(60, 22, 44, 22); lay.setSpacing(8)
        h = QHBoxLayout(); h.addStretch(); s.title = heading("Cronograma", 42); h.addWidget(s.title); h.addSpacing(10); s.swap = IBtn("cycle", 46, "accent", "Alternar entre Cronograma e Ciclo", 28); s.swap.clicked.connect(s.switch); h.addWidget(s.swap); h.addStretch(); lay.addLayout(h)
        r = QHBoxLayout(); s.cb = QComboBox(); s.cb.setMinimumWidth(300); s.cb.setFixedHeight(46); s.cb.currentIndexChanged.connect(lambda _: s.load()); r.addWidget(s.cb)
        s.bnew = IBtn("plus", 42, "accent", "Novo"); s.bnew.clicked.connect(s.new); s.bren = IBtn("pencil", 42, "ghost", "Renomear"); s.bren.clicked.connect(s.rename); s.bdel = IBtn("trash", 42, "ghost", "Excluir"); s.bdel.clicked.connect(s.delete)
        for b in (s.bnew, s.bren, s.bdel): r.addWidget(b)
        r.addStretch(); lay.addLayout(r); s.stack = QStackedWidget(); s.sv = ScheduleView(win); s.cv = CycleView(win); s.stack.addWidget(s.sv); s.stack.addWidget(s.cv); lay.addWidget(s.stack, 1)
        s.cv.created.connect(s.cycle_created); s.cv.modified.connect(s.refresh)
    @property
    def mode(s): return s.d["settings"]["plan_mode"]
    def on_shortcut(s, key):
        if s.mode == "schedule": s.sv.on_shortcut(key)
    def switch(s): s.d["settings"]["plan_mode"] = "cycle" if s.mode == "schedule" else "schedule"; s.creating = False; s.st.save(); s.refresh()
    def lst(s): return s.d["schedules"] if s.mode == "schedule" else s.d["cycles"]
    def refresh(s):
        sch = s.mode == "schedule"; s.title.setText("Cronograma" if sch else "Ciclo"); i = max(0, s.cb.currentIndex()); s.cb.blockSignals(True); s.cb.clear()
        s.cb.addItems([x["name"] for x in s.lst()]); s.cb.setCurrentIndex(min(i, len(s.lst()) - 1)); s.cb.blockSignals(False); s.bren.setVisible(sch); s.bdel.setVisible(sch); s.cb.setVisible(bool(s.lst()) or sch); s.load()
    def cur(s): i = s.cb.currentIndex(); return s.lst()[i] if 0 <= i < len(s.lst()) else None
    def load(s):
        if s.mode == "schedule": s.stack.setCurrentIndex(0); s.sv.load(s.cur())
        else:
            s.stack.setCurrentIndex(1); c = s.cur()
            if s.creating or not c: s.cv.show_create(bool(c))
            else:
                s.cv.load(c)
                if s.d["settings"].get("active_cycle") != c["id"]: s.d["settings"]["active_cycle"] = c["id"]; s.st.save()
    def new(s):
        if s.mode == "schedule":
            n, ok = QInputDialog.getText(s, "Novo cronograma", "Nome:", text=f"Cronograma {len(s.d['schedules']) + 1}")
            if ok and n.strip(): s.d["schedules"].append(dict(id=uid(), name=n.strip(), blocks=[])); s.st.save(); s.refresh(); s.cb.setCurrentIndex(len(s.d["schedules"]) - 1)
        else: s.creating = True; s.load()
    def cycle_created(s, cid):
        s.creating = False; s.refresh()
        if cid: s.cb.setCurrentIndex(next(i for i, c in enumerate(s.d["cycles"]) if c["id"] == cid))
    def rename(s):
        c = s.cur()
        if c:
            n, ok = QInputDialog.getText(s, "Renomear", "Nome:", text=c["name"])
            if ok and n.strip(): c["name"] = n.strip(); s.st.save(); s.refresh()
    def delete(s):
        c = s.cur()
        if c and len(s.d["schedules"]) > 1 and confirm(s, f"Excluir '{c['name']}'?"): s.d["schedules"].remove(c); s.st.save(); s.refresh()

# ───────────────────────── simulados / redação ─────────────────────────
class RecordsPage(Page):
    def __init__(s, win, key, fields, cols, defaults=None, extra=()):
        super().__init__(win); s.key, s.fields, s.cols, s.defaults = key, fields, cols, defaults or {}; lay = QVBoxLayout(s); lay.setContentsMargins(60, 26, 44, 26); lay.setSpacing(14)
        h = QHBoxLayout(); h.addWidget(heading(RECORDS[key]["title"], 44)); h.addStretch()
        for ic, tip, name in extra: b = IBtn(ic, 48, "dark", tip); b.clicked.connect(lambda _, n=name: getattr(s, n)()); h.addWidget(b)
        for ic, tip, fn, k in [("plus", "Adicionar", lambda: s.edit(True), "accent"), ("pencil", "Editar", s.edit, "dark"), ("trash", "Excluir", s.delete, "dark"), ("doc", "Abrir arquivo anexado", s.open, "dark")]:
            b = IBtn(ic, 48, k, tip); b.clicked.connect(lambda _, fn=fn: fn()); h.addWidget(b)
        lay.addLayout(h); s.hint = muted("As estatísticas e a evolução aparecem na página Início.", 13, 500); lay.addWidget(s.hint)
        card = Card(22); cl = QVBoxLayout(card); cl.setContentsMargins(14, 14, 14, 14); s.tb = mk_table([c[0] for c in cols]); s.tb.setStyleSheet("QTableWidget{background:transparent}"); s.tb.doubleClicked.connect(lambda _: s.edit()); cl.addWidget(s.tb); lay.addWidget(card, 1)
    def refresh(s):
        rs = sorted(s.d[s.key], key=lambda r: r["date"], reverse=True); s.tb.setRowCount(len(rs))
        for i, r in enumerate(rs):
            for j, (_, fn) in enumerate(s.cols): put(s.tb, i, j, fn(r), r["id"] if j == 0 else None)
        s.tb.resizeColumnsToContents(); s.tb.horizontalHeader().setStretchLastSection(True)
    def edit(s, new=False):
        r = None if new else next((x for x in s.d[s.key] if x["id"] == sel_id(s.tb)), None)
        if not new and not r: return
        dlg = FormDialog(s, "Registro", s.fields, r or s.defaults)
        if dlg.exec():
            v = dlg.values()
            if r: r.update(v)
            else: s.d[s.key].append(dict(v, id=uid()))
            s.st.save(); s.refresh()
    def delete(s):
        i = sel_id(s.tb)
        if i and confirm(s, "Excluir registro?"): s.d[s.key][:] = [x for x in s.d[s.key] if x["id"] != i]; s.st.save(); s.refresh()
    def open(s):
        r = next((x for x in s.d[s.key] if x["id"] == sel_id(s.tb)), None)
        if r: open_file(r.get("file"))

class ExamTypesDialog(QDialog):
    """Cadastro de tipos de prova: nº de questões por matéria; matérias podem ser gerais ou específicas daquele tipo."""
    def __init__(s, parent, win):
        super().__init__(parent); s.win = win; s.setWindowTitle("Tipos de prova"); s.setMinimumSize(920, 540); L = QHBoxLayout(s); L.setContentsMargins(24, 22, 24, 22); L.setSpacing(18)
        lf = QVBoxLayout(); lf.addWidget(heading("Tipos de prova", 22)); s.lw = QListWidget(); s.lw.setFixedWidth(230); lf.addWidget(s.lw, 1); br_ = QHBoxLayout(); a = IBtn("plus", 40, "accent", "Novo tipo de prova"); d = IBtn("trash", 40, "dark", "Excluir tipo")
        a.clicked.connect(s.new_type); d.clicked.connect(s.del_type); br_.addWidget(a); br_.addWidget(d); br_.addStretch(); lf.addLayout(br_); L.addLayout(lf)
        rt = QVBoxLayout(); s.name = QLineEdit(); s.name.setPlaceholderText("Nome do tipo (ex.: ENEM, FUVEST, Simulado da escola)"); s.name.setStyleSheet("font-size:18px;font-weight:700"); s.name.editingFinished.connect(s.rename); rt.addWidget(s.name)
        s.tb = QTableWidget(0, 3); s.tb.setHorizontalHeaderLabels(["Matéria", "Questões", "Escopo"]); s.tb.verticalHeader().hide(); s.tb.setEditTriggers(QAbstractItemView.NoEditTriggers); s.tb.setSelectionBehavior(QAbstractItemView.SelectRows); s.tb.setShowGrid(False)
        s.tb.horizontalHeader().setStretchLastSection(True); s.tb.setColumnWidth(0, 300); s.tb.setColumnWidth(1, 120); rt.addWidget(s.tb, 1)
        r = QHBoxLayout(); g = QPushButton("+ Matéria geral"); g.clicked.connect(s.add_general); lo = QPushButton("+ Matéria específica deste tipo"); lo.clicked.connect(s.add_local); rm = IBtn("trash", 40, "dark", "Remover matéria do tipo"); rm.clicked.connect(s.remove_row)
        r.addWidget(g); r.addWidget(lo); r.addWidget(rm); r.addStretch(); rt.addLayout(r); s.sum = muted("", 13); rt.addWidget(s.sum)
        s.note = muted("Matérias específicas só existem dentro deste tipo de prova: não entram na lista geral de matérias nem nas estatísticas de tempo de estudo.", 11, 500); s.note.setWordWrap(True); rt.addWidget(s.note)
        cl = QPushButton("Fechar"); cl.clicked.connect(s.accept); rt.addWidget(cl, 0, Qt.AlignRight); L.addLayout(rt, 1); s.lw.currentRowChanged.connect(lambda _: s.show_type()); s.fill_list()
    @property
    def d(s): return s.win.store.data
    def cur(s): i = s.lw.currentRow(); return s.d["exam_types"][i] if 0 <= i < len(s.d["exam_types"]) else None
    def fill_list(s, keep=0):
        s.lw.blockSignals(True); s.lw.clear(); s.lw.addItems([t["name"] for t in s.d["exam_types"]]); s.lw.blockSignals(False); s.lw.setCurrentRow(min(keep, s.lw.count() - 1)); s.show_type()
    def show_type(s):
        t = s.cur(); s.name.setEnabled(bool(t)); s.name.setText(t["name"] if t else ""); s.tb.setRowCount(0)
        for i, sb in enumerate(t["subjects"] if t else []):
            s.tb.insertRow(i); it = QTableWidgetItem(sb["name"]); it.setIcon(dot_icon(subj_color(s.d, sb["name"]) if not sb.get("local") else scolor(sb["name"]))); s.tb.setItem(i, 0, it)
            q = QSpinBox(); q.setRange(1, 999); q.setValue(sb["n"]); q.setAlignment(Qt.AlignCenter); q.valueChanged.connect(lambda v, sb=sb: s.set_n(sb, v)); s.tb.setCellWidget(i, 1, q); s.tb.setItem(i, 2, QTableWidgetItem("Específica deste tipo" if sb.get("local") else "Geral"))
        s.upd_sum()
    def upd_sum(s): t = s.cur(); s.sum.setText(f"Total: {sum(x['n'] for x in t['subjects'])} questões em {len(t['subjects'])} matéria(s)" if t else "Crie um tipo de prova com o botão +.")
    def set_n(s, sb, v): sb["n"] = v; s.win.store.save(); s.upd_sum()
    def new_type(s):
        n, ok = QInputDialog.getText(s, "Novo tipo de prova", "Nome do tipo:")
        if ok and n.strip() and not exam_type(s.d, n.strip()): s.d["exam_types"].append(dict(id=uid(), name=n.strip(), subjects=[])); s.win.store.save(); s.fill_list(len(s.d["exam_types"]) - 1)
    def del_type(s):
        t = s.cur()
        if t and confirm(s, f"Excluir o tipo '{t['name']}'? Os simulados já registrados continuam salvos."): s.d["exam_types"].remove(t); s.win.store.save(); s.fill_list()
    def rename(s):
        t = s.cur(); n = s.name.text().strip()
        if t and n and n != t["name"] and not exam_type(s.d, n):
            for r in s.d["exams"]:
                if r.get("type") == t["name"]: r["type"] = n
            t["name"] = n; s.win.store.save(); s.lw.currentItem().setText(n)
    def add_general(s):
        t = s.cur()
        if not t: return
        have = {x["name"] for x in t["subjects"]}; opts = [x for x in s.d["subjects"] if x not in have]; m = QMenu(s)
        if not opts: m.addAction("(todas as matérias gerais já foram adicionadas)").setEnabled(False)
        acts = {m.addAction(x): x for x in opts}; a = m.exec(QCursor.pos())
        if a in acts: t["subjects"].append(dict(name=acts[a], n=10, local=False)); s.win.store.save(); s.show_type()
    def add_local(s):
        t = s.cur()
        if not t: return
        n, ok = QInputDialog.getText(s, "Matéria específica", "Nome da matéria (só existirá neste tipo de prova):")
        if ok and n.strip() and n.strip() not in [x["name"] for x in t["subjects"]]: t["subjects"].append(dict(name=n.strip(), n=10, local=True)); s.win.store.save(); s.show_type()
    def remove_row(s):
        t = s.cur(); r = s.tb.currentRow()
        if t and 0 <= r < len(t["subjects"]): t["subjects"].pop(r); s.win.store.save(); s.show_type()

class ExamDialog(QDialog):
    def __init__(s, parent, win, rec=None):
        super().__init__(parent); s.win = win; s.rec = rec or {}; d = win.store.data; s.setWindowTitle("Simulado"); s.setMinimumWidth(540); L = QVBoxLayout(s); L.setContentsMargins(24, 22, 24, 22); L.setSpacing(10); L.addWidget(heading("Simulado", 24))
        f = QFormLayout(); f.setSpacing(10); s.dt = QDateEdit(); s.dt.setCalendarPopup(True); s.dt.setDisplayFormat("dd/MM/yyyy"); s.dt.setDate(QDate.fromString(s.rec["date"], Qt.ISODate) if s.rec.get("date") else QDate.currentDate())
        s.tp = QComboBox(); s.tp.addItem("— sem tipo cadastrado —"); s.tp.addItems([t["name"] for t in d["exam_types"]]); cur = s.rec.get("type")
        if cur and exam_type(d, cur): s.tp.setCurrentIndex(s.tp.findText(cur))
        f.addRow(muted("Data", 12), s.dt); f.addRow(muted("Tipo de prova", 12), s.tp); L.addLayout(f)
        if not d["exam_types"]: L.addWidget(muted("Dica: cadastre tipos de prova (botão ao lado de “+” na página Simulados) para lançar o acerto de cada matéria.", 11, 500))
        s.af = QFormLayout(); s.af.setSpacing(8); L.addLayout(s.af); s.tot = muted("", 13); L.addWidget(s.tot)
        s.fl = PickRow("Todos (*)"); s.fl.set(s.rec.get("file", ""), False); s.nt = LinkTextEdit(); s.nt.setPlainText(s.rec.get("notes", "")); s.nt.setFixedHeight(90)
        g = QFormLayout(); g.addRow(muted("Arquivo da prova", 12), s.fl); g.addRow(muted("Comentários", 12), s.nt); L.addLayout(g)
        bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(s.accept); bb.rejected.connect(s.reject); L.addWidget(bb); s.tp.currentIndexChanged.connect(lambda _: s.build()); s.build()
    def build(s):
        while s.af.rowCount(): s.af.removeRow(0)
        d = s.win.store.data; s.spins = {}; t = exam_type(d, s.tp.currentText()) if s.tp.currentIndex() > 0 else None; s.t = t
        if t:
            for sb in t["subjects"]:
                q = QSpinBox(); q.setRange(0, sb["n"]); q.setSuffix(f"  de {sb['n']} questões"); q.setValue(min(sb["n"], s.rec.get("scores", {}).get(sb["name"], 0))); q.valueChanged.connect(lambda _: s.sumup()); s.af.addRow(muted(f"Acertos em {sb['name']}", 12), q); s.spins[sb["name"]] = (q, sb["n"])
        else:
            s.mn = QLineEdit(s.rec.get("type", "") if not exam_type(d, s.rec.get("type", "")) else ""); s.mn.setPlaceholderText("Ex.: ENEM"); s.mh = QSpinBox(); s.mh.setRange(0, 9999); s.mh.setValue(s.rec.get("hits", 0)); s.mt = QSpinBox(); s.mt.setRange(0, 9999); s.mt.setValue(s.rec.get("total", 0))
            s.af.addRow(muted("Nome do tipo", 12), s.mn); s.af.addRow(muted("Acertos", 12), s.mh); s.af.addRow(muted("Total de questões", 12), s.mt)
        s.sumup()
    def sumup(s):
        if s.t: h = sum(q.value() for q, _ in s.spins.values()); n = sum(n for _, n in s.spins.values()); s.tot.setText(f"Total: {h} de {n} acertos" + (f"  ({h / n * 100:.0f}%)" if n else ""))
        else: s.tot.setText("")
    def values(s):
        if s.t: sc = {k: q.value() for k, (q, _) in s.spins.items()}; tt = {k: n for k, (_, n) in s.spins.items()}; hits, total, typ = sum(sc.values()), sum(tt.values()), s.t["name"]
        else: sc, tt, hits, total, typ = {}, {}, s.mh.value(), s.mt.value(), s.mn.text().strip()
        return dict(date=s.dt.date().toString(Qt.ISODate), type=typ, scores=sc, totals=tt, hits=hits, total=total, file=s.fl.text(), notes=s.nt.toPlainText().strip())

class ExamsPage(RecordsPage):
    def __init__(s, win):
        cols = [("Data", lambda r: br(r["date"])), ("Tipo", lambda r: r.get("type", "")), ("Acertos", lambda r: f"{r['hits']}/{r['total']}"), ("%", lambda r: f"{r['hits'] / r['total'] * 100:.0f}%" if r["total"] else "-"),
                ("Por matéria", lambda r: "  ·  ".join(f"{k} {v}/{r['totals'][k]}" for k, v in r.get("scores", {}).items())), ("Comentários", lambda r: r["notes"].replace("\n", " "))]
        super().__init__(win, "exams", [], cols, {}, extra=[("book", "Tipos de prova e questões por matéria", "types_dialog")])
    def types_dialog(s): ExamTypesDialog(s, s.win).exec(); s.refresh()
    def edit(s, new=False):
        r = None if new else next((x for x in s.d["exams"] if x["id"] == sel_id(s.tb)), None)
        if not new and not r: return
        dlg = ExamDialog(s, s.win, r)
        if dlg.exec():
            v = dlg.values()
            if r: r.update(v)
            else: s.d["exams"].append(dict(v, id=uid()))
            s.st.save(); s.refresh()

def make_exams(win): return ExamsPage(win)
def make_essays(win):
    f = [("date", "Data", "date"), ("theme", "Tema", "text"), ("texts", "Textos motivadores", "long"), ("grade", "Nota", "float"), ("file", "Arquivo da redação", "file"), ("notes", "Comentários do corretor", "long")]
    cols = [("Data", lambda r: br(r["date"])), ("Tema", lambda r: r["theme"]), ("Nota", lambda r: f"{r['grade']:.0f}"), ("Comentários", lambda r: r["notes"].replace("\n", " "))]
    return RecordsPage(win, "essays", f, cols)

# ───────────────────────── configurações ─────────────────────────
class Swatch(QWidget):
    picked = Signal(str)
    def __init__(s, name): super().__init__(); s.name = name; s.setFixedSize(46, 46); s.setCursor(Qt.PointingHandCursor); s.setToolTip(name); s.sel = False
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); p.setBrush(QColor(ACCENTS[s.name])); p.drawEllipse(QRectF(s.rect()).adjusted(6, 6, -6, -6))
        if s.sel: p.setBrush(Qt.NoBrush); p.setPen(QPen(QColor(T["text"]), 2.5)); p.drawEllipse(QRectF(s.rect()).adjusted(2, 2, -2, -2))
    def mousePressEvent(s, e): s.picked.emit(s.name)

class SettingsPage(Page):
    def __init__(s, win):
        super().__init__(win); lay = QVBoxLayout(s); lay.setContentsMargins(60, 26, 44, 26); lay.addWidget(heading("Configurações", 44)); sc = QScrollArea(); sc.setWidgetResizable(True); w = QWidget(); L = QVBoxLayout(w); L.setSpacing(16); L.setContentsMargins(0, 0, 10, 0); sc.setWidget(w); lay.addWidget(sc, 1)
        def card(title):
            c = Card(22); l = QVBoxLayout(c); l.setContentsMargins(24, 20, 24, 22); l.setSpacing(12); l.addWidget(heading(title, 20)); L.addWidget(c); return l
        a = card("Aparência"); a.addWidget(muted("Modo", 12)); r = QHBoxLayout(); s.bd, s.bl = pill("Escuro", True, 40), pill("Claro", True, 40); g = QButtonGroup(s); [g.addButton(b) or r.addWidget(b) for b in (s.bd, s.bl)]; r.addStretch(); a.addLayout(r)
        s.bd.clicked.connect(lambda: s.set_theme(mode="dark")); s.bl.clicked.connect(lambda: s.set_theme(mode="light")); a.addWidget(muted("Cor de destaque", 12)); r = QHBoxLayout(); s.sw = []
        for n in ACCENTS: sw = Swatch(n); sw.picked.connect(lambda n: s.set_theme(accent=n)); r.addWidget(sw); s.sw.append(sw)
        r.addStretch(); a.addLayout(r); s.pin = QCheckBox("Barra lateral sempre visível (desmarcado: aparece ao passar o mouse na borda esquerda)"); s.pin.toggled.connect(s.set_pin); a.addWidget(s.pin)
        s.full = QCheckBox("Abrir o aplicativo em tela cheia (F11 alterna a qualquer momento)"); s.full.toggled.connect(lambda v: (s.d["settings"].__setitem__("fullscreen", v), s.st.save())); a.addWidget(s.full)
        s.intro = QCheckBox("Tocar a introdução ao abrir o aplicativo"); s.intro.toggled.connect(lambda v: (s.d["settings"].__setitem__("intro", v), s.st.save())); a.addWidget(s.intro)
        tb = card("Barra lateral — abas visíveis"); tb.addWidget(muted("Desmarque as abas que você não quer ver. Configurações não pode ser ocultada.", 12, 500)); gl = QGridLayout(); gl.setHorizontalSpacing(24); s.tabcb = {}
        for i, (ic, n) in enumerate(NAV):
            cb = QCheckBox(n); cb.toggled.connect(lambda v, n=n: s.set_tab(n, v)); gl.addWidget(cb, i // 3, i % 3); s.tabcb[n] = cb
        s.tabcb["Configurações"].setEnabled(False); s.tabcb["Configurações"].setText("Configurações (sempre visível)"); tb.addLayout(gl); s.myday = QCheckBox("Mostrar o “Meu Dia” na página Tarefas"); s.myday.toggled.connect(s.set_myday); tb.addWidget(s.myday)
        o = card("Matérias e tags (nomes e cores)"); r = QHBoxLayout()
        for t, k in (("Gerenciar matérias", "subjects"), ("Gerenciar tags", "tags")): b = QPushButton(t); b.clicked.connect(lambda _, k=k, t=t: manage(s, s.st, k, t)); r.addWidget(b)
        r.addStretch(); o.addLayout(r)
        dd = card("Dados e sincronização"); s.info = QLabel(); s.info.setWordWrap(True); s.info.setStyleSheet(f"color:{T['muted']}"); dd.addWidget(s.info)
        for t, fn in [("Exportar backup (.json)", s.export), ("Importar backup", s.imp), ("Escolher pasta de sincronização (Google Drive, Dropbox, OneDrive…)", s.pick), ("Sincronizar agora", s.now), ("Remover sincronização", s.unset)]:
            b = QPushButton(t); b.clicked.connect(lambda _, fn=fn: fn()); b.setStyleSheet("text-align:left;padding-left:22px"); b.setMaximumWidth(560); dd.addWidget(b)
        dz = card("Zona de perigo"); dz.addWidget(muted("Apaga permanentemente todas as tarefas, blocos de estudo, eventos, ciclos, simulados, redações e configurações deste computador (e do arquivo sincronizado).", 12, 500))
        wb = QPushButton("Apagar todos os meus dados…"); wb.setStyleSheet(f"background:{RED};color:white"); wb.setMaximumWidth(360); wb.clicked.connect(s.wipe); dz.addWidget(wb)
        L.addWidget(muted(f"Ômega v{VERSION}", 12, 500)); L.addStretch()
    def set_tab(s, n, v):
        h = s.d["settings"]["hidden_tabs"]
        if n == "Configurações": return   # a aba de configurações nunca pode ser removida
        if v and n in h: h.remove(n)
        elif not v and n not in h: h.append(n)
        s.st.save(); s.win.apply_tabs()
    def set_myday(s, v): s.d["settings"]["hide_myday"] = not v; s.st.save()
    def wipe(s):
        name = s.d["settings"]["user"].strip(); need = name or "APAGAR"; dlg = QDialog(s); dlg.setWindowTitle("Apagar todos os dados"); dlg.setMinimumWidth(480); l = QVBoxLayout(dlg); l.setContentsMargins(24, 22, 24, 22); l.setSpacing(12)
        l.addWidget(heading("Apagar todos os dados?", 24)); m = QLabel(("Esta ação não pode ser desfeita. Para continuar, digite seu nome de usuário:" if name else "Esta ação não pode ser desfeita. Você ainda não definiu um nome de usuário; para continuar, digite APAGAR:") + f"\n\n{need}"); m.setWordWrap(True); l.addWidget(m)
        ed = QLineEdit(); ed.setPlaceholderText(need); l.addWidget(ed); r = QHBoxLayout(); r.addStretch(); cn = pill("Cancelar", False, 40); ok = QPushButton("Apagar tudo"); ok.setStyleSheet(f"background:{RED};color:white"); ok.setEnabled(False)
        cn.clicked.connect(dlg.reject); ok.clicked.connect(dlg.accept); ed.textChanged.connect(lambda t: ok.setEnabled(t.strip() == need)); r.addWidget(cn); r.addWidget(ok); l.addLayout(r)
        if dlg.exec() and ed.text().strip() == need: s.win.wipe_all(); QMessageBox.information(s, "Ômega", "Todos os dados foram apagados.")
    def set_theme(s, mode=None, accent=None):
        c = s.d["settings"]; c["mode"] = mode or c["mode"]; c["accent"] = accent or c["accent"]; s.st.save(); s.win.apply_theme(); s.refresh()
    def set_pin(s, v): s.d["settings"]["pin"] = v; s.st.save(); s.win.apply_pin()
    def refresh(s):
        c = s.d["settings"]; s.bd.setChecked(c["mode"] != "light"); s.bl.setChecked(c["mode"] == "light"); [setattr(w, "sel", w.name == c["accent"]) or w.update() for w in s.sw]
        for cb, v in ((s.pin, c["pin"]), (s.intro, c["intro"]), (s.full, c["fullscreen"])): cb.blockSignals(True); cb.setChecked(v); cb.blockSignals(False)
        for n, cb in s.tabcb.items(): cb.blockSignals(True); cb.setChecked(n not in c["hidden_tabs"] or n == "Configurações"); cb.blockSignals(False)
        s.myday.blockSignals(True); s.myday.setChecked(not c["hide_myday"]); s.myday.blockSignals(False)
        s.info.setStyleSheet(f"color:{T['muted']}"); sf = s.st.sync_file(); s.info.setStyleSheet(f"color:{T['muted']}"); s.info.setText(f"Arquivo local: {s.st.local}\nSincronização: {sf if sf else 'desativada'}\n\nTudo é salvo automaticamente. Com uma pasta de sincronização, o app grava o omega_data.json nela e confere mudanças de outros dispositivos a cada minuto.")
    def export(s):
        p, _ = QFileDialog.getSaveFileName(s, "Exportar", "omega_backup.json", "JSON (*.json)")
        if p: Path(p).write_text(json.dumps(s.d, ensure_ascii=False, indent=1), "utf-8"); QMessageBox.information(s, "Ômega", "Backup salvo.")
    def imp(s):
        p, _ = QFileDialog.getOpenFileName(s, "Importar", "", "JSON (*.json)")
        if p and confirm(s, "Isto substituirá os dados atuais. Continuar?"):
            if s.st.read(Path(p)): s.st.save(); s.win.refresh_all()
            else: QMessageBox.warning(s, "Ômega", "Arquivo inválido.")
    def pick(s):
        p = QFileDialog.getExistingDirectory(s, "Pasta de sincronização")
        if not p: return
        s.st.cfg["sync_dir"] = p; s.st.save_cfg(); f = s.st.sync_file()
        if f.exists() and confirm(s, "Já existe um omega_data.json nessa pasta. Carregar os dados dele (Sim) ou sobrescrever com os deste computador (Não)?"): s.st.pull(True)
        s.st.save(); s.win.refresh_all()
    def now(s): QMessageBox.information(s, "Ômega", "Dados atualizados." if s.st.pull(True) else "Nada a atualizar."); s.win.refresh_all()
    def unset(s): s.st.cfg["sync_dir"] = ""; s.st.save_cfg(); s.refresh()
