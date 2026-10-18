# -*- coding: utf-8 -*-
"""Tarefas, Edital e Calendário."""
from omega_core import *

class CheckCircle(QWidget):
    toggled = Signal()
    def __init__(s, d=44, done=False): super().__init__(); s.done = done; s.d = d; s.setFixedSize(d, d); s.setCursor(Qt.PointingHandCursor)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setPen(Qt.NoPen); c = QColor(T["accent"])
        if s.done: c.setAlpha(255)
        p.setBrush(c); p.drawEllipse(QRectF(s.rect()).adjusted(1, 1, -1, -1))
        if s.done: k = int(s.d * .62); p.drawPixmap(QPointF((s.d - k) / 2, (s.d - k) / 2), pix("check", T["on_accent"], k))
    def mousePressEvent(s, e): s.done = not s.done; s.update(); s.toggled.emit()

# ───────────────────────── tarefas ─────────────────────────
class TaskRow(Card):
    clicked = Signal(str)
    def __init__(s, t, selected, on_toggle):
        super().__init__(29, "row", selected); s.bkey = "accent"; s.tid = t["id"]; s.setFixedHeight(62); s.setCursor(Qt.PointingHandCursor)
        l = QHBoxLayout(s); l.setContentsMargins(10, 8, 18, 8); l.setSpacing(12); c = CheckCircle(44, t["done"]); c.toggled.connect(on_toggle); l.addWidget(c)
        v = QVBoxLayout(); v.setSpacing(0); v.setContentsMargins(0, 0, 0, 0); tl = QLabel(t["title"]); f = tl.font(); f.setPixelSize(16); f.setStrikeOut(t["done"]); tl.setFont(f)
        if t["done"]: tl.setStyleSheet(f"color:{T['muted']}")
        v.addWidget(tl)
        if t["due"]:
            late = t["due"] < iso(today()) and not t["done"]; dl = QLabel("Para dia " + br(t["due"])[:5]); dl.setStyleSheet(f"font-size:11px;font-weight:500;color:{RED if late else T['accent']}"); v.addWidget(dl)
        l.addLayout(v, 1)
        s.p0 = None; s.dragged = False
    def mousePressEvent(s, e): s.p0 = e.position(); s.dragged = False
    def mouseMoveEvent(s, e):
        if s.p0 is not None and e.buttons() & Qt.LeftButton and (e.position() - s.p0).manhattanLength() > 10:
            s.dragged = True; md = QMimeData(); md.setData("application/x-omega-task", s.tid.encode()); dr = QDrag(s); dr.setMimeData(md); pm = s.grab(); dr.setPixmap(pm); dr.setHotSpot(e.position().toPoint()); s.p0 = None; dr.exec(Qt.MoveAction)
    def mouseReleaseEvent(s, e):
        if not s.dragged and s.p0 is not None: s.clicked.emit(s.tid)
        s.p0 = None

class RowsHost(QWidget):
    """Contêiner das tarefas: aceita arrastar para reordenar (somente tarefas, não subtarefas)."""
    dropped = Signal(str, int)
    def __init__(s): super().__init__(); s.setAcceptDrops(True); s.ind = None
    def rows(s): return [s.layout().itemAt(i).widget() for i in range(s.layout().count()) if isinstance(s.layout().itemAt(i).widget(), TaskRow)]
    def index_at(s, y): return sum(1 for r in s.rows() if r.geometry().center().y() < y)
    def dragEnterEvent(s, e):
        if e.mimeData().hasFormat("application/x-omega-task"): e.acceptProposedAction()
    def dragMoveEvent(s, e):
        rs = s.rows(); i = s.index_at(e.position().y()); s.ind = (rs[i].geometry().top() - 6) if i < len(rs) else (rs[-1].geometry().bottom() + 6 if rs else 0); s.update(); e.acceptProposedAction()
    def dragLeaveEvent(s, e): s.ind = None; s.update()
    def dropEvent(s, e):
        i = s.index_at(e.position().y()); s.ind = None; s.update(); e.acceptProposedAction(); s.dropped.emit(bytes(e.mimeData().data("application/x-omega-task")).decode(), i)
    def paintEvent(s, e):
        if s.ind is not None: p = QPainter(s); p.setPen(QPen(QColor(T["accent"]), 3, Qt.SolidLine, Qt.RoundCap)); p.drawLine(8, int(s.ind), s.width() - 14, int(s.ind))

class Tasks(Page):
    def __init__(s, win):
        super().__init__(win); s.sel = None; s.loading = False; root = QHBoxLayout(s); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        c = QWidget(); cl = QVBoxLayout(c); cl.setContentsMargins(60, 30, 34, 20); cl.setSpacing(14)
        top = QHBoxLayout(); s.cb = QComboBox(); s.cb.setFixedHeight(58); s.cb.setStyleSheet("QComboBox{border-radius:29px;padding:4px 24px;font-size:16px}"); s.cb.currentIndexChanged.connect(lambda _: s.build())
        top.addWidget(s.cb, 1)
        for ic, tip, fn, k in [("plus", "Nova lista", s.new_list, "accent"), ("pencil", "Renomear lista", s.ren_list, "ghost"), ("trash", "Excluir lista", s.del_list, "ghost")]:
            b = IBtn(ic, 46, k, tip); b.clicked.connect(lambda _, fn=fn: fn()); top.addWidget(b)
        cl.addLayout(top); add = Card(30, "row"); add.setFixedHeight(62); al = QHBoxLayout(add); al.setContentsMargins(26, 0, 10, 0)
        s.new = QLineEdit(); s.new.setPlaceholderText("Adicionar nova tarefa"); s.new.setStyleSheet("background:transparent;font-size:16px"); s.new.returnPressed.connect(s.add)
        ab = IBtn("plus", 42); ab.clicked.connect(s.add); al.addWidget(s.new); al.addWidget(ab); cl.addWidget(add)
        sc = QScrollArea(); sc.setWidgetResizable(True); w = RowsHost(); s.rows = QVBoxLayout(w); s.rows.setContentsMargins(0, 0, 6, 0); s.rows.setSpacing(12); s.rows.addStretch(); w.dropped.connect(s.reorder); sc.setWidget(w); cl.addWidget(sc, 1); root.addWidget(c, 1)
        det = Card(0, "side"); det.setFixedWidth(350); dl = QVBoxLayout(det); dl.setContentsMargins(26, 28, 20, 14); dl.setSpacing(10)
        h = QHBoxLayout(); s.dchk = CheckCircle(42); s.dchk.toggled.connect(s.toggle_sel); s.dtitle = QLineEdit(); s.dtitle.setStyleSheet("background:transparent;font-size:26px;font-weight:700;padding:0"); s.dtitle.editingFinished.connect(s.set_title)
        s.dtrash = IBtn("trash", 40, "ghost", "Excluir tarefa"); s.dtrash.clicked.connect(s.delete); s.dup = IBtn("up", 30, "ghost", "Subir tarefa na lista", 18); s.ddn = IBtn("down", 30, "ghost", "Descer tarefa na lista", 18); s.dup.clicked.connect(lambda: s.move(-1)); s.ddn.clicked.connect(lambda: s.move(1))
        h.addWidget(s.dchk); h.addWidget(s.dtitle, 1); h.addWidget(s.dup); h.addWidget(s.ddn); h.addWidget(s.dtrash); dl.addLayout(h)
        s.dsub = QLineEdit(); s.dsub.setPlaceholderText("+ Adicionar subtarefa"); s.dsub.setStyleSheet(f"background:transparent;font-size:16px;font-weight:700;padding:2px 0"); s.dsub.returnPressed.connect(s.add_sub); dl.addWidget(s.dsub)
        s.subs = QVBoxLayout(); s.subs.setSpacing(6); dl.addLayout(s.subs)
        s.pd, s.pt, s.pf = ClickPill("Adicionar Data de Conclusão"), ClickPill("Adicionar Tag / Matéria"), ClickPill("Anexar Arquivo")
        s.pd.clicked.connect(s.set_date); s.pt.clicked.connect(s.set_tag); s.pf.clicked.connect(s.set_files)
        for b in (s.pd, s.pt, s.pf): dl.addWidget(b)
        s.ddesc = QTextEdit(); s.ddesc.setPlaceholderText("Adicionar Descrição"); s.ddesc.setStyleSheet(f"background:{T['field']};border-radius:30px;padding:18px 22px;font-size:14px"); s.ddesc.textChanged.connect(s.desc_changed); dl.addWidget(s.ddesc, 1)
        s.dcr = muted("", 11, 500); s.dcr.setAlignment(Qt.AlignCenter); dl.addWidget(s.dcr); root.addWidget(det)
        s.dsave = QTimer(s); s.dsave.setSingleShot(True); s.dsave.setInterval(600); s.dsave.timeout.connect(s.st.save)
    def retheme(s): s.ddesc.setStyleSheet(f"background:{T['field']};border-radius:30px;padding:18px 22px;font-size:14px")
    def retheme(s): s.ddesc.setStyleSheet(f"background:{T['field']};border-radius:30px;padding:18px 22px;font-size:14px")
    # dados
    def cur(s): i = s.cb.currentIndex(); return s.d["lists"][i] if 0 <= i < len(s.d["lists"]) else None
    def find(s, tid): return next((t for l in s.d["lists"] for t in iter_tasks(l["tasks"]) if t["id"] == tid), None)
    def refresh(s):
        i = max(0, s.cb.currentIndex()); s.cb.blockSignals(True); s.cb.clear(); s.cb.addItems([l["name"] for l in s.d["lists"]]); s.cb.setCurrentIndex(min(i, len(s.d["lists"]) - 1)); s.cb.blockSignals(False); s.build()
    def goto(s, tid):
        for i, l in enumerate(s.d["lists"]):
            if any(t["id"] == tid for t in iter_tasks(l["tasks"])): s.cb.setCurrentIndex(i); s.sel = tid; s.build(); return
    def build(s):
        clear_layout(s.rows, 1)
        l = s.cur()
        if l:
            for t in l["tasks"]:
                r = TaskRow(t, t["id"] == s.sel, lambda t=t: s.toggle(t)); r.clicked.connect(s.select); s.rows.insertWidget(s.rows.count() - 1, r)
        s.load_detail()
    def select(s, tid): s.sel = tid; s.build()
    def reorder(s, tid, idx):
        l = s.cur(); t = next((x for x in l["tasks"] if x["id"] == tid), None) if l else None
        if not t: return
        old = l["tasks"].index(t); l["tasks"].remove(t); l["tasks"].insert(idx - 1 if old < idx else idx, t); s.st.save(); s.build()
    def move(s, d):
        l = s.cur(); t = s.find(s.sel) if l else None
        if t and t in l["tasks"]:
            i = l["tasks"].index(t); j = i + d
            if 0 <= j < len(l["tasks"]): l["tasks"][i], l["tasks"][j] = l["tasks"][j], l["tasks"][i]; s.st.save(); s.build()
    def toggle(s, t): t["done"] = not t["done"]; s.st.save(); QTimer.singleShot(0, s.build)
    def toggle_sel(s):
        t = s.find(s.sel)
        if t: s.toggle(t)
    def load_detail(s):
        t = s.find(s.sel); s.loading = True; on = t is not None
        for w in (s.dchk, s.dtitle, s.dtrash, s.dup, s.ddn, s.dsub, s.pd, s.pt, s.pf, s.ddesc): w.setEnabled(on)
        s.dtitle.setText(t["title"] if t else ""); s.dtitle.setPlaceholderText("Selecione"); s.dchk.done = bool(t and t["done"]); s.dchk.update()
        s.pd.setv(("Concluir até " + br(t["due"])) if t and t["due"] else ""); s.pt.setv(" · ".join(x for x in (t["subject"], t["tag"]) if x) if t else "")
        s.pf.setv(f"{len(t['files'])} arquivo(s) anexado(s)" if t and t["files"] else ""); s.ddesc.setPlainText(t["desc"] if t else ""); s.dcr.setText(f"Criado em {br(t.get('created', ''))} às {t.get('created', 'T')[11:16] or '00:00'}" if t and t.get("created") else "")
        clear_layout(s.subs, 0)
        for sb in (t["subtasks"] if t else []):
            w = QWidget(); r = QHBoxLayout(w); r.setContentsMargins(2, 0, 0, 0); r.setSpacing(10); c = CheckCircle(26, sb["done"]); c.toggled.connect(lambda sb=sb: (sb.__setitem__("done", not sb["done"]), s.st.save(), QTimer.singleShot(0, s.load_detail)))
            lb = QLabel(sb["title"]); f = lb.font(); f.setPixelSize(15); f.setWeight(QFont.Bold); f.setStrikeOut(sb["done"]); lb.setFont(f)
            x = IBtn("x", 26, "ghost", "Remover subtarefa", 12); x.clicked.connect(lambda _, sb=sb: (t["subtasks"].remove(sb), s.st.save(), s.load_detail()))
            r.addWidget(c); r.addWidget(lb, 1); r.addWidget(x); s.subs.addWidget(w)
        s.loading = False
    def mk(s, title): return dict(id=uid(), title=title, subject="", tag="", due="", desc="", done=False, files=[], subtasks=[], created=dt.datetime.now().isoformat(timespec="minutes"))
    def add(s):
        l = s.cur(); n = s.new.text().strip()
        if l and n: t = s.mk(n); l["tasks"].append(t); s.new.clear(); s.sel = t["id"]; s.st.save(); s.build()
    def add_sub(s):
        t = s.find(s.sel); n = s.dsub.text().strip()
        if t and n: t["subtasks"].append(dict(id=uid(), title=n, done=False, subtasks=[], subject="", tag="", due="", desc="", files=[])); s.dsub.clear(); s.st.save(); s.load_detail()
    def set_title(s):
        t = s.find(s.sel)
        if t and s.dtitle.text().strip() and s.dtitle.text().strip() != t["title"]: t["title"] = s.dtitle.text().strip(); s.st.save(); s.build()
    def desc_changed(s):
        t = s.find(s.sel)
        if t and not s.loading: t["desc"] = s.ddesc.toPlainText(); s.dsave.start()
    def set_date(s):
        t = s.find(s.sel); v = pick_date(s, t["due"] or None, True) if t else None
        if v is not None: t["due"] = v; s.st.save(); s.build()
    def set_tag(s):
        t = s.find(s.sel)
        if not t: return
        dlg = FormDialog(s, "Tag / Matéria", [("subject", "Matéria", "combo", s.d["subjects"]), ("tag", "Tag", "combo", s.d["tags"])], t)
        if dlg.exec(): t.update(dlg.values()); s.st.save(); s.build()
    def set_files(s):
        t = s.find(s.sel)
        if not t: return
        dlg = FormDialog(s, "Arquivos", [("files", "Anexos", "files")], t)
        if dlg.exec(): t.update(dlg.values()); s.st.save(); s.build()
    def delete(s):
        l = s.cur(); t = s.find(s.sel)
        if l and t and confirm(s, "Excluir esta tarefa?"):
            def rm(ts):
                for x in ts:
                    if x["id"] == t["id"]: ts.remove(x); return True
                    if rm(x["subtasks"]): return True
            rm(l["tasks"]); s.sel = None; s.st.save(); s.build()
    def new_list(s):
        n, ok = QInputDialog.getText(s, "Nova lista", "Nome da lista:")
        if ok and n.strip(): s.d["lists"].append(dict(id=uid(), name=n.strip(), tasks=[])); s.st.save(); s.refresh(); s.cb.setCurrentIndex(len(s.d["lists"]) - 1)
    def ren_list(s):
        l = s.cur()
        if l:
            n, ok = QInputDialog.getText(s, "Renomear", "Nome:", text=l["name"])
            if ok and n.strip(): l["name"] = n.strip(); s.st.save(); s.refresh()
    def del_list(s):
        l = s.cur()
        if l and len(s.d["lists"]) > 1 and confirm(s, f"Excluir a lista '{l['name']}'?"): s.d["lists"].remove(l); s.sel = None; s.st.save(); s.refresh()

# ───────────────────────── edital ─────────────────────────
LEVELS = [("red", "Desempenho Ruim", RED), ("yellow", "Desempenho Razoável", YEL), ("green", "Desempenho Bom", GRN)]
class Dot(QWidget):
    def __init__(s, color, d=34): super().__init__(); s.c = color; s.setFixedSize(d, d)
    def paintEvent(s, e): p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(s.c)); p.setPen(Qt.NoPen); p.drawEllipse(s.rect())

class SubjectCard(Card):
    clicked = Signal(str)
    def __init__(s, name, v, selected):
        super().__init__(12, "card", selected); s.bkey = "accent"; s.name = name; s.setFixedHeight(96); s.setCursor(Qt.PointingHandCursor); l = QVBoxLayout(s); l.setContentsMargins(14, 12, 14, 14); l.setSpacing(8)
        t = QLabel(name); t.setStyleSheet("font-size:20px;font-weight:700"); l.addWidget(t); r = QHBoxLayout(); r.setSpacing(8)
        for (k, _, col) in LEVELS:
            r.addWidget(Dot(col)); n = QLabel(str(len(v[k]))); n.setStyleSheet("font-size:20px;font-weight:300"); r.addWidget(n); r.addSpacing(8)
        r.addStretch(); l.addLayout(r)
    def mousePressEvent(s, e): s.clicked.emit(s.name)

class DropList(QListWidget):
    moved = Signal(str, str, list); reordered = Signal()
    def __init__(s, lvl):
        super().__init__(); s.lvl = lvl; s.setDragDropMode(QAbstractItemView.DragDrop); s.setDefaultDropAction(Qt.MoveAction); s.setSelectionMode(QAbstractItemView.ExtendedSelection); s.setWordWrap(True)
        s.setStyleSheet("QListWidget{background:transparent;border:none;font-size:16px}QListWidget::item{padding:9px 6px}")
    def dropEvent(s, e):
        src = e.source()
        if isinstance(src, DropList) and src is not s:
            texts = [i.text() for i in src.selectedItems()]; e.setDropAction(Qt.IgnoreAction); e.accept(); QTimer.singleShot(0, lambda: s.moved.emit(src.lvl, s.lvl, texts))
        else: super().dropEvent(e); QTimer.singleShot(0, s.reordered.emit)

class Syllabus(Page):
    def __init__(s, win):
        super().__init__(win); s.cur = None; lay = QHBoxLayout(s); lay.setContentsMargins(60, 36, 36, 30); lay.setSpacing(18)
        left = Card(16, "side"); left.setFixedWidth(340); ll = QVBoxLayout(left); ll.setContentsMargins(18, 18, 18, 18); h = QHBoxLayout(); h.addWidget(heading("Matérias", 36)); pe = IBtn("pencil", 46, "accent", "Gerenciar matérias"); pe.clicked.connect(s.manage); h.addWidget(pe); h.addStretch(); ll.addLayout(h)
        sc = QScrollArea(); sc.setWidgetResizable(True); w = QWidget(); s.cards = QVBoxLayout(w); s.cards.setContentsMargins(0, 0, 4, 0); s.cards.setSpacing(10); s.cards.addStretch(); sc.setWidget(w); ll.addWidget(sc, 1); lay.addWidget(left)
        rt = QVBoxLayout(); t = heading("Assuntos", 40); t.setAlignment(Qt.AlignCenter); rt.addWidget(t); cols = QHBoxLayout(); cols.setSpacing(18); s.ls = {}; s.ins = {}
        for k, name, col in LEVELS:
            v = QVBoxLayout(); v.setSpacing(6); hd = QLabel(name); hd.setAlignment(Qt.AlignCenter); hd.setFixedHeight(56); hd.setStyleSheet(f"background:{col};color:white;border-radius:14px;font-size:15px;font-weight:700"); v.addWidget(hd)
            body = Card(14, "side"); bl = QVBoxLayout(body); bl.setContentsMargins(14, 12, 10, 10); e = QLineEdit(); e.setPlaceholderText("Adicionar novo assunto"); e.setStyleSheet("background:transparent;font-size:17px;padding:4px 0"); e.returnPressed.connect(lambda k=k: s.add(k)); bl.addWidget(e)
            l = DropList(k); l.setContextMenuPolicy(Qt.CustomContextMenu); l.customContextMenuRequested.connect(lambda pos, l=l: s.menu(l, pos)); l.moved.connect(s.on_moved); l.reordered.connect(s.sync_order); bl.addWidget(l, 1)
            v.addWidget(body, 1); cols.addLayout(v, 1); s.ls[k] = l; s.ins[k] = e
        rt.addLayout(cols, 1); b = QPushButton("Excluir Selecionados"); b.setFixedHeight(54); b.setStyleSheet("border-radius:10px;font-size:15px;font-weight:500"); b.clicked.connect(s.delete); rt.addWidget(b); lay.addLayout(rt, 1)
    def lv(s, n): return s.d["syllabus"].setdefault(n, {"red": [], "yellow": [], "green": []})
    def manage(s):
        if edit_list(s, "Matérias", s.d["subjects"]): s.st.save(); s.refresh()
    def refresh(s):
        if s.cur not in s.d["subjects"]: s.cur = s.d["subjects"][0] if s.d["subjects"] else None
        clear_layout(s.cards, 1)
        if not s.d["subjects"]: s.cards.insertWidget(0, muted("Nenhuma matéria cadastrada.\nClique no lápis para adicionar.", 13, 600))
        for n in s.d["subjects"]: c = SubjectCard(n, s.lv(n), n == s.cur); c.clicked.connect(lambda n: (setattr(s, "cur", n), s.refresh())); s.cards.insertWidget(s.cards.count() - 1, c)
        for k, l in s.ls.items():
            l.clear()
            if s.cur: l.addItems(s.lv(s.cur)[k])
            s.ins[k].setEnabled(bool(s.cur))
    def add(s, k):
        t = s.ins[k].text().strip()
        if t and s.cur: s.lv(s.cur)[k].append(t); s.ins[k].clear(); s.st.save(); s.refresh()
    def delete(s):
        if not s.cur: return
        for k, l in s.ls.items():
            for i in l.selectedItems():
                if i.text() in s.lv(s.cur)[k]: s.lv(s.cur)[k].remove(i.text())
        s.st.save(); s.refresh()
    def on_moved(s, a, b, texts):
        v = s.lv(s.cur)
        for t in texts:
            if t in v[a]: v[a].remove(t); v[b].append(t)
        s.st.save(); s.refresh()
    def sync_order(s):
        if s.cur:
            for k, l in s.ls.items(): s.lv(s.cur)[k] = [l.item(i).text() for i in range(l.count())]
            s.st.save()
    def menu(s, l, pos):
        it = l.itemAt(pos)
        if not it or not s.cur: return
        m = QMenu(s); acts = {m.addAction("Mover para: " + nm): k for k, nm, _ in LEVELS if k != l.lvl}; ren = m.addAction("Renomear"); dl = m.addAction("Excluir"); a = m.exec(l.mapToGlobal(pos)); v = s.lv(s.cur)
        if a in acts: s.on_moved(l.lvl, acts[a], [i.text() for i in l.selectedItems()])
        elif a == ren:
            t, ok = QInputDialog.getText(s, "Renomear", "Assunto:", text=it.text())
            if ok and t.strip(): v[l.lvl][v[l.lvl].index(it.text())] = t.strip(); s.st.save(); s.refresh()
        elif a == dl: s.delete()

# ───────────────────────── calendário ─────────────────────────
class Pill(QLabel):
    def __init__(s, text, bg, fg, cb, tip=""):
        super().__init__(text); s.cb = cb; s.setFixedHeight(22); s.setSizePolicy(QSizePolicy.Ignored, QSizePolicy.Fixed); s.setToolTip(tip or text); s.setCursor(Qt.PointingHandCursor)
        s.setStyleSheet(f"background:{bg};color:{fg};border-radius:11px;padding:0 9px;font-size:11px;font-weight:500")
    def mousePressEvent(s, e): s.cb()
    def mouseReleaseEvent(s, e): e.accept()

class DayCell(QWidget):
    new = Signal(str)
    def __init__(s, d, other, tod):
        super().__init__(); s.d, s.other, s.tod = d, other, tod; s.lay = QVBoxLayout(s); s.lay.setContentsMargins(5, 26, 5, 4); s.lay.setSpacing(3); s.lay.addStretch(); s.setMinimumHeight(70)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setPen(QColor(T["line"])); p.drawLine(s.width() - 1, 0, s.width() - 1, s.height()); p.drawLine(0, s.height() - 1, s.width(), s.height() - 1)
        f = p.font(); f.setPixelSize(11); f.setWeight(QFont.Bold); p.setFont(f); txt = str(s.d.day) if s.d.day != 1 else f"1 {MESES[s.d.month - 1][:3].lower()}."
        if s.tod: p.setBrush(QColor(T["accent"])); p.setPen(Qt.NoPen); p.drawRoundedRect(QRectF(s.width() / 2 - 14, 4, 28, 20), 10, 10); p.setPen(QColor(T["on_accent"]))
        else: p.setPen(QColor(T["muted"] if s.other else T["text"]))
        p.drawText(QRectF(0, 4, s.width(), 20), Qt.AlignCenter, txt)
    def mouseReleaseEvent(s, e): s.new.emit(iso(s.d))

class EventDialog(Overlay):
    def __init__(s, parent, win, ev, date):
        super().__init__(parent, 500); s.win, s.ev, s.deleted = win, ev, False; d = win.store.data; s.date = ev["date"] if ev else date; s.time = ev["time"] if ev else ""; s.files = list(ev["files"]) if ev else []
        s.title = s.head(ev["title"] if ev else "Novo Evento"); s.bd = QPushButton(br(s.date)); s.bd.setStyleSheet(f"background:transparent;color:{T['text']};font-size:28px;font-weight:300;text-align:left;padding:0"); s.bd.setCursor(Qt.PointingHandCursor); s.bd.clicked.connect(s.chg_date); s.lay.addWidget(s.bd)
        s.desc = s.ph_edit("Adicionar Descrição", 170); s.desc.setPlainText(ev["desc"] if ev else ""); s.lay.addWidget(s.desc)
        s.tp = ClickPill("Adicionar Horário"); s.tp.setv(s.time); s.tp.clicked.connect(s.chg_time); s.lay.addWidget(s.tp)
        r = QHBoxLayout(); s.sub = s.pill_combo("Adicionar Matéria", d["subjects"], ev["subject"] if ev else ""); s.tag = s.pill_combo("Adicionar Tag", d["tags"], ev["tag"] if ev else ""); r.addWidget(s.sub); r.addWidget(s.tag); s.lay.addLayout(r)
        s.fp = ClickPill("Anexar Arquivos"); s.fp.setv(f"{len(s.files)} arquivo(s)" if s.files else ""); s.fp.clicked.connect(s.chg_files); s.lay.addWidget(s.fp)
        b = QHBoxLayout()
        if ev: tr = IBtn("trash", 46, "dark", "Excluir evento"); tr.clicked.connect(lambda: (setattr(s, "deleted", True), s.accept())); b.addWidget(tr)
        b.addStretch(); sv = QPushButton("Salvar"); sv.setMinimumWidth(140); sv.clicked.connect(s.accept); b.addWidget(sv); s.lay.addLayout(b)
    def chg_date(s):
        v = pick_date(s, s.date)
        if v: s.date = v; s.bd.setText(br(v))
    def chg_time(s):
        v = pick_time(s, s.time)
        if v is not None: s.time = v; s.tp.setv(v)
    def chg_files(s):
        dlg = FormDialog(s, "Arquivos", [("files", "Anexos", "files")], {"files": s.files})
        if dlg.exec(): s.files = dlg.values()["files"]; s.fp.setv(f"{len(s.files)} arquivo(s)" if s.files else "")
    def result(s):
        return dict(title=s.title.text().strip() or "Novo Evento", date=s.date, time=s.time, subject=cbval(s.sub), tag=cbval(s.tag), desc=s.desc.toPlainText().strip(), files=s.files)

class CalendarPage(Page):
    def __init__(s, win):
        super().__init__(win); s.m = today().replace(day=1); lay = QVBoxLayout(s); lay.setContentsMargins(60, 24, 44, 26); lay.setSpacing(8); h = QHBoxLayout(); h.addWidget(heading("Calendário", 44)); h.addStretch()
        pv = IBtn("tri_l", 56, "ghost", "Mês anterior", 40); nx = IBtn("tri_r", 56, "ghost", "Próximo mês", 40); pv.clicked.connect(lambda: s.shift(-1)); nx.clicked.connect(lambda: s.shift(1)); h.addWidget(pv); h.addWidget(nx); h.addSpacing(18)
        s.lbl = QLabel(); s.lbl.setStyleSheet("font-size:42px;font-weight:300"); h.addWidget(s.lbl); lay.addLayout(h)
        s.card = Card(24); s.grid = QGridLayout(s.card); s.grid.setContentsMargins(4, 4, 4, 4); s.grid.setSpacing(0); lay.addWidget(s.card, 1)
    def shift(s, n):
        y, m = divmod(s.m.year * 12 + s.m.month - 1 + n, 12); s.m = dt.date(y, m + 1, 1); s.refresh()
    def refresh(s):
        clear_layout(s.grid, 0)
        s.lbl.setText(f"{MESES[s.m.month - 1]} {s.m.year}")
        for c in range(7): l = QLabel(DIAS_DOM[c].upper() + "."); l.setAlignment(Qt.AlignCenter); l.setFixedHeight(28); l.setStyleSheet(f"font-size:10px;font-weight:700;color:{T['text']}"); s.grid.addWidget(l, 0, c)
        start = s.m - dt.timedelta(days=(s.m.weekday() + 1) % 7); ev = {}; tk = {}
        for e in s.d["events"]: ev.setdefault(e["date"], []).append(e)
        for l in s.d["lists"]:
            for t in iter_tasks(l["tasks"]):
                if t.get("due"): tk.setdefault(t["due"], []).append(t)
        for i in range(42):
            d = start + dt.timedelta(days=i); c = DayCell(d, d.month != s.m.month, d == today()); c.new.connect(s.open_event); items = []
            for e in sorted(ev.get(iso(d), []), key=lambda e: e["time"]): items.append((e["title"], YEL, "#ffffff", lambda e=e: s.open_event(e["date"], e), (e["time"] + " " if e["time"] else "") + e["title"]))
            for t in tk.get(iso(d), []): items.append((("✓ " if t["done"] else "") + t["title"], T["accent"], T["on_accent"], lambda t=t: s.open_task(t["id"]), "Tarefa: " + t["title"]))
            for txt, bg, fg, cb, tip in items[:3]: c.lay.insertWidget(c.lay.count() - 1, Pill(txt, bg, fg, cb, tip))
            if len(items) > 3: c.lay.insertWidget(c.lay.count() - 1, muted(f"+{len(items) - 3} mais", 10))
            s.grid.addWidget(c, 1 + i // 6 * 0 + i // 7, i % 7)
        for r in range(1, 7): s.grid.setRowStretch(r, 1)
    def open_task(s, tid): s.win.go(2); s.win.items[2][2].goto(tid)
    def open_event(s, date, ev=None):
        dlg = EventDialog(s.win, s.win, ev, date)
        if dlg.exec():
            if dlg.deleted: s.d["events"][:] = [e for e in s.d["events"] if e["id"] != ev["id"]]
            elif ev: ev.update(dlg.result())
            else: s.d["events"].append(dict(dlg.result(), id=uid()))
            s.st.save(); s.refresh()
