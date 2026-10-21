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
    def __init__(s, t, selected, on_toggle, origin=""):
        super().__init__(29, "row", selected); s.bkey = "accent"; s.tid = t["id"]; s.is_done = t["done"]; s.setFixedHeight(62); s.setCursor(Qt.PointingHandCursor)
        l = QHBoxLayout(s); l.setContentsMargins(10, 8, 18, 8); l.setSpacing(12); c = CheckCircle(44, t["done"]); c.toggled.connect(on_toggle); l.addWidget(c)
        v = QVBoxLayout(); v.setSpacing(0); v.setContentsMargins(0, 0, 0, 0); tl = QLabel(t["title"]); f = tl.font(); f.setPixelSize(16); f.setStrikeOut(t["done"]); tl.setFont(f)
        if t["done"]: tl.setStyleSheet(f"color:{T['muted']}")
        v.addWidget(tl); parts = []
        if origin: parts.append(f"<span style='color:{T['muted']}'>{origin}</span>")
        if t["due"]: late = t["due"] < iso(today()) and not t["done"]; parts.append(f"<span style='color:{RED if late else T['accent']}'>Para dia {br(t['due'])[:5]}</span>")
        if parts: dl = QLabel("  ·  ".join(parts)); dl.setStyleSheet("font-size:11px;font-weight:500"); v.addWidget(dl)
        l.addLayout(v, 1); s.p0 = None; s.dragged = False
    def mousePressEvent(s, e): s.p0 = e.position(); s.dragged = False
    def mouseMoveEvent(s, e):
        if not s.is_done and s.p0 is not None and e.buttons() & Qt.LeftButton and (e.position() - s.p0).manhattanLength() > 10:
            s.dragged = True; md = QMimeData(); md.setData("application/x-omega-task", s.tid.encode()); dr = QDrag(s); dr.setMimeData(md); dr.setPixmap(s.grab()); dr.setHotSpot(e.position().toPoint()); s.p0 = None; dr.exec(Qt.MoveAction)
    def mouseReleaseEvent(s, e):
        if not s.dragged and s.p0 is not None: s.clicked.emit(s.tid)
        s.p0 = None

class RowsHost(QWidget):
    """Contêiner das tarefas: aceita arrastar para reordenar (somente tarefas pendentes, não subtarefas)."""
    dropped = Signal(str, int)
    def __init__(s): super().__init__(); s.setAcceptDrops(True); s.ind = None
    def rows(s):
        L = s.layout(); return [w for w in (L.itemAt(i).widget() for i in range(L.count())) if isinstance(w, TaskRow) and not w.is_done]
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
        super().__init__(win); s.sel = None; s.loading = False; s.last_key = None; s.targets = []; root = QHBoxLayout(s); root.setContentsMargins(0, 0, 0, 0); root.setSpacing(0)
        c = QWidget(); cl = QVBoxLayout(c); cl.setContentsMargins(60, 30, 34, 20); cl.setSpacing(14)
        top = QHBoxLayout(); s.cb = QComboBox(); s.cb.setFixedHeight(58); s.cb.setStyleSheet("QComboBox{border-radius:29px;padding:4px 24px;font-size:16px}"); s.cb.currentIndexChanged.connect(s.on_list); top.addWidget(s.cb, 1)
        s.bnew = IBtn("plus", 46, "accent", "Nova lista"); s.bren = IBtn("pencil", 46, "ghost", "Renomear lista"); s.bdel = IBtn("trash", 46, "ghost", "Excluir lista")
        for b, fn in ((s.bnew, s.new_list), (s.bren, s.ren_list), (s.bdel, s.del_list)): b.clicked.connect(lambda _, fn=fn: fn()); top.addWidget(b)
        cl.addLayout(top); add = Card(30, "row"); add.setFixedHeight(62); al = QHBoxLayout(add); al.setContentsMargins(26, 0, 10, 0)
        s.new = QLineEdit(); s.new.setPlaceholderText("Adicionar nova tarefa"); s.new.setStyleSheet("background:transparent;font-size:16px"); s.new.returnPressed.connect(s.add)
        ab = IBtn("plus", 42); ab.clicked.connect(s.add); al.addWidget(s.new); al.addWidget(ab); cl.addWidget(add)
        sc = QScrollArea(); sc.setWidgetResizable(True); w = RowsHost(); s.rows = QVBoxLayout(w); s.rows.setContentsMargins(0, 0, 6, 0); s.rows.setSpacing(12); s.rows.addStretch(); w.dropped.connect(s.reorder); sc.setWidget(w); cl.addWidget(sc, 1); root.addWidget(c, 1)
        det = Card(0, "side"); det.setFixedWidth(360); dl = QVBoxLayout(det); dl.setContentsMargins(26, 28, 20, 14); dl.setSpacing(10)
        h = QHBoxLayout(); s.dchk = CheckCircle(42); s.dchk.toggled.connect(s.toggle_sel); s.dtitle = QLineEdit(); s.dtitle.setStyleSheet("background:transparent;font-size:26px;font-weight:700;padding:0"); s.dtitle.editingFinished.connect(s.set_title)
        s.dtrash = IBtn("trash", 40, "ghost", "Excluir tarefa"); s.dtrash.clicked.connect(s.delete); s.dup = IBtn("up", 30, "ghost", "Subir tarefa na lista", 18); s.ddn = IBtn("down", 30, "ghost", "Descer tarefa na lista", 18)
        s.dup.clicked.connect(lambda: s.move(-1)); s.ddn.clicked.connect(lambda: s.move(1)); [h.addWidget(x) for x in (s.dchk,)]; h.addWidget(s.dtitle, 1); [h.addWidget(x) for x in (s.dup, s.ddn, s.dtrash)]; dl.addLayout(h)
        s.subs = QVBoxLayout(); s.subs.setSpacing(6); dl.addLayout(s.subs)   # subtarefas existentes (nomes editáveis clicando neles)
        s.dsub = QLineEdit(); s.dsub.setPlaceholderText("+ Adicionar subtarefa"); s.dsub.setStyleSheet("background:transparent;font-size:16px;font-weight:700;padding:2px 0"); s.dsub.returnPressed.connect(s.add_sub); dl.addWidget(s.dsub)   # fica abaixo das subtarefas
        s.pd, s.pt, s.pf, s.pm = ClickPill("Adicionar Data de Conclusão"), ClickPill("Adicionar Tag / Matéria"), ClickPill("Anexar Arquivo"), ClickPill("Adicionar ao Meu Dia")
        s.pd.clicked.connect(s.set_date); s.pt.clicked.connect(s.set_tag); s.pf.clicked.connect(s.set_files); s.pm.clicked.connect(s.toggle_myday)
        for b in (s.pd, s.pt, s.pf, s.pm): dl.addWidget(b)
        s.cbm = QComboBox(); s.cbm.activated.connect(s.move_to_list); dl.addWidget(s.cbm)   # mover para outra lista (separado do Meu Dia)
        s.ddesc = LinkTextEdit(); s.ddesc.setPlaceholderText("Adicionar Descrição"); s.ddesc.textChanged.connect(s.desc_changed); dl.addWidget(s.ddesc, 1)
        s.dcr = muted("", 11, 500); s.dcr.setAlignment(Qt.AlignCenter); dl.addWidget(s.dcr); root.addWidget(det)
        s.style_fields(); s.dsave = QTimer(s); s.dsave.setSingleShot(True); s.dsave.setInterval(600); s.dsave.timeout.connect(s.st.save)
    def style_fields(s):
        s.ddesc.setStyleSheet(f"background:{T['field']};border-radius:30px;padding:18px 22px;font-size:14px")
        s.cbm.setStyleSheet(f"QComboBox{{background:{T['field']};border:none;border-radius:22px;padding:11px 20px;color:{T['text']};font-weight:500}}")
    def retheme(s): s.style_fields(); s.ddesc.retheme()
    # ── listas
    def off(s): return 0 if s.d["settings"]["hide_myday"] else 1
    def is_md(s): return s.off() == 1 and s.cb.currentIndex() == 0
    def cur(s):
        i = s.cb.currentIndex() - s.off(); return s.d["lists"][i] if 0 <= i < len(s.d["lists"]) else None
    def key(s): return "myday" if s.is_md() else (s.cur() or {}).get("id")
    def find(s, tid): return next((t for l in s.d["lists"] for t in iter_tasks(l["tasks"]) if t["id"] == tid), None)
    def owner(s, tid): return next((l for l in s.d["lists"] if any(t["id"] == tid for t in l["tasks"])), None)
    def refresh(s):
        off = s.off(); lists = s.d["lists"]; s.cb.blockSignals(True); s.cb.clear(); s.cb.addItems((["Meu Dia"] if off else []) + [l["name"] for l in lists])
        i = 0
        if s.last_key and s.last_key != "myday": i = next((k + off for k, l in enumerate(lists) if l["id"] == s.last_key), 0)
        elif s.last_key == "myday" and not off: i = 0
        s.cb.setCurrentIndex(min(i, s.cb.count() - 1)); s.cb.blockSignals(False); s.last_key = s.key(); s.update_buttons(); s.build()
    def update_buttons(s):
        md = s.is_md(); s.bren.setEnabled(not md); s.bdel.set_icon("eye_off" if md else "trash"); s.bdel.setToolTip("Ocultar Meu Dia (reative em Configurações)" if md else "Excluir lista")
    def on_list(s, _=None): s.last_key = s.key(); s.sel = None; s.update_buttons(); s.build()
    def goto(s, tid):
        l = s.owner(tid)
        if l: s.sel = tid; s.cb.blockSignals(True); s.cb.setCurrentIndex(s.d["lists"].index(l) + s.off()); s.cb.blockSignals(False); s.last_key = l["id"]; s.update_buttons(); s.build()
    def view_tasks(s):
        if s.is_md():
            names = {t["id"]: l["name"] for l in s.d["lists"] for t in l["tasks"]}; s.d["myday"][:] = [i for i in s.d["myday"] if i in names]
            return [(s.find(i), names[i]) for i in s.d["myday"]]
        l = s.cur(); return [(t, "") for t in l["tasks"]] if l else []
    def build(s):
        clear_layout(s.rows, 1); vt = s.view_tasks(); act = [x for x in vt if not x[0]["done"]]; dn = [x for x in vt if x[0]["done"]]
        def put_row(t, o): r = TaskRow(t, t["id"] == s.sel, lambda t=t: s.toggle(t), o); r.clicked.connect(s.select); s.rows.insertWidget(s.rows.count() - 1, r)
        for t, o in act: put_row(t, o)
        if dn:   # subcategoria "Concluídas": recolhida por padrão para não ocupar espaço
            k = s.key(); op = s.d["settings"]["done_open"].get(k, False); hd = flat(f"Concluídas ({len(dn)})"); hd.setFixedHeight(36); hd.setIcon(qicon("down" if op else "tri_r", T["muted"], T["muted"], 14)); hd.setIconSize(QSize(14, 14))
            hd.setStyleSheet(hd.styleSheet() + "QPushButton{font-size:14px;font-weight:700;padding-left:6px}"); hd.clicked.connect(lambda: (s.d["settings"]["done_open"].__setitem__(k, not op), s.st.save(), s.build())); s.rows.insertWidget(s.rows.count() - 1, hd)
            if op:
                for t, o in dn: put_row(t, o)
        s.load_detail()
    def select(s, tid): s.sel = tid; s.build()
    def toggle(s, t): t["done"] = not t["done"]; s.st.save(); QTimer.singleShot(0, s.build)
    def toggle_sel(s):
        t = s.find(s.sel)
        if t: s.toggle(t)
    # ── ordem (somente tarefas)
    def active_ids(s): return [t["id"] for t, _ in s.view_tasks() if not t["done"]]
    def apply_order(s, ids):
        if s.is_md(): s.d["myday"][:] = ids + [i for i in s.d["myday"] if i not in ids]
        else:
            l = s.cur(); by = {t["id"]: t for t in l["tasks"]}; l["tasks"][:] = [by[i] for i in ids] + [t for t in l["tasks"] if t["id"] not in ids]
        s.st.save(); s.build()
    def reorder(s, tid, idx):
        ids = s.active_ids()
        if tid in ids: old = ids.index(tid); ids.remove(tid); ids.insert(idx - 1 if old < idx else idx, tid); s.apply_order(ids)
    def move(s, d):
        ids = s.active_ids()
        if s.sel in ids:
            i = ids.index(s.sel); j = i + d
            if 0 <= j < len(ids): ids[i], ids[j] = ids[j], ids[i]; s.apply_order(ids)
    # ── detalhes
    def load_detail(s):
        t = s.find(s.sel); s.loading = True; on = t is not None
        for w in (s.dchk, s.dtitle, s.dtrash, s.dup, s.ddn, s.dsub, s.pd, s.pt, s.pf, s.pm, s.cbm, s.ddesc): w.setEnabled(on)
        s.dtitle.setText(t["title"] if t else ""); s.dtitle.setPlaceholderText("Selecione uma tarefa"); s.dchk.done = bool(t and t["done"]); s.dchk.update()
        s.pd.setv(("Concluir até " + br(t["due"])) if t and t["due"] else ""); s.pt.setv(" · ".join(x for x in (t["subject"], t["tag"]) if x) if t else "")
        s.pf.setv(f"{len(t['files'])} arquivo(s) anexado(s)" if t and t["files"] else ""); s.pm.setText("Remover do Meu Dia" if t and t["id"] in s.d["myday"] else "Adicionar ao Meu Dia")
        s.ddesc.setPlainText(t["desc"] if t else ""); s.dcr.setText(f"Criado em {br(t.get('created', ''))} às {t.get('created', 'T')[11:16] or '00:00'}" if t and t.get("created") else "")
        own = s.owner(s.sel) if t else None; s.targets = [l for l in s.d["lists"] if l is not own]; s.cbm.clear(); s.cbm.addItem("Mover para outra lista…"); s.cbm.addItems([l["name"] for l in s.targets])
        clear_layout(s.subs, 0)
        for sb in (t["subtasks"] if t else []):
            w = QWidget(); r = QHBoxLayout(w); r.setContentsMargins(2, 0, 0, 0); r.setSpacing(10); c = CheckCircle(26, sb["done"]); c.toggled.connect(lambda sb=sb: (sb.__setitem__("done", not sb["done"]), s.st.save(), QTimer.singleShot(0, s.load_detail)))
            le = QLineEdit(sb["title"]); le.setStyleSheet(f"background:transparent;border:none;padding:0;color:{T['muted'] if sb['done'] else T['text']}"); f = QFont(le.font()); f.setPixelSize(15); f.setWeight(QFont.Bold); f.setStrikeOut(sb["done"]); le.setFont(f)
            le.editingFinished.connect(lambda sb=sb, le=le: s.rename_sub(sb, le)); x = IBtn("x", 26, "ghost", "Remover subtarefa", 12); x.clicked.connect(lambda _, sb=sb: (t["subtasks"].remove(sb), s.st.save(), s.load_detail()))
            r.addWidget(c); r.addWidget(le, 1); r.addWidget(x); s.subs.addWidget(w)
        s.loading = False
    def rename_sub(s, sb, le):
        n = le.text().strip()
        if n and n != sb["title"]: sb["title"] = n; s.st.save()
        elif not n: le.setText(sb["title"])
    def mk(s, title): return dict(id=uid(), title=title, subject="", tag="", due="", desc="", done=False, files=[], subtasks=[], created=dt.datetime.now().isoformat(timespec="minutes"))
    def add(s):
        n = s.new.text().strip(); l = s.d["lists"][0] if s.is_md() else s.cur()   # no Meu Dia, a tarefa nasce na primeira lista
        if l and n:
            t = s.mk(n); l["tasks"].append(t)
            if s.is_md(): s.d["myday"].append(t["id"])
            s.new.clear(); s.sel = t["id"]; s.st.save(); s.build()
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
    def toggle_myday(s):
        t = s.find(s.sel)
        if not t: return
        ids = s.d["myday"]; ids.remove(t["id"]) if t["id"] in ids else ids.append(t["id"]); s.st.save(); s.build()
    def move_to_list(s, i):
        t = s.find(s.sel); src = s.owner(s.sel)
        if i <= 0 or not t or not src: return
        tgt = s.targets[i - 1]; src["tasks"].remove(t); tgt["tasks"].append(t); s.st.save()
        if not s.is_md(): s.sel = None
        s.build()
    def delete(s):
        t = s.find(s.sel); l = s.owner(s.sel)
        if l and t and confirm(s, "Excluir esta tarefa?"):
            l["tasks"].remove(t); s.d["myday"][:] = [i for i in s.d["myday"] if i != t["id"]]; s.sel = None; s.st.save(); s.build()
    def new_list(s):
        n, ok = QInputDialog.getText(s, "Nova lista", "Nome da lista:")
        if ok and n.strip(): l = dict(id=uid(), name=n.strip(), tasks=[]); s.d["lists"].append(l); s.last_key = l["id"]; s.st.save(); s.refresh()
    def ren_list(s):
        l = s.cur()
        if l:
            n, ok = QInputDialog.getText(s, "Renomear", "Nome:", text=l["name"])
            if ok and n.strip(): l["name"] = n.strip(); s.st.save(); s.refresh()
    def del_list(s):
        if s.is_md():
            if confirm(s, "Ocultar o Meu Dia? Ele não é apagado — dá para mostrar de novo em Configurações."): s.d["settings"]["hide_myday"] = True; s.last_key = None; s.st.save(); s.refresh()
            return
        l = s.cur()
        if l and len(s.d["lists"]) > 1 and confirm(s, f"Excluir a lista '{l['name']}'?"): s.d["lists"].remove(l); s.last_key = None; s.sel = None; s.st.save(); s.refresh()

# ───────────────────────── edital ─────────────────────────
LEVELS = [("red", "Desempenho Ruim", RED), ("yellow", "Desempenho Razoável", YEL), ("green", "Desempenho Bom", GRN)]
class Dot(QWidget):
    def __init__(s, color, d=34): super().__init__(); s.c = color; s.setFixedSize(d, d)
    def paintEvent(s, e): p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(s.c)); p.setPen(Qt.NoPen); p.drawEllipse(s.rect())

class SubjectCard(Card):
    clicked = Signal(str)
    def __init__(s, name, v, selected, color=""):
        super().__init__(12, "card", selected); s.bkey = "accent"; s.name = name; s.setFixedHeight(96); s.setCursor(Qt.PointingHandCursor); l = QVBoxLayout(s); l.setContentsMargins(14, 12, 14, 14); l.setSpacing(8)
        t = QLabel(name); t.setStyleSheet("font-size:20px;font-weight:700"); tr = QHBoxLayout(); tr.setSpacing(8); tr.addWidget(Dot(color or scolor(name), 12)); tr.addWidget(t, 1); l.addLayout(tr); r = QHBoxLayout(); r.setSpacing(8)
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
        if manage(s, s.st, "subjects", "Matérias"): s.refresh()
    def refresh(s):
        if s.cur not in s.d["subjects"]: s.cur = s.d["subjects"][0] if s.d["subjects"] else None
        clear_layout(s.cards, 1)
        if not s.d["subjects"]: s.cards.insertWidget(0, muted("Nenhuma matéria cadastrada.\nClique no lápis para adicionar.", 13, 600))
        for n in s.d["subjects"]: c = SubjectCard(n, s.lv(n), n == s.cur, subj_color(s.d, n)); c.clicked.connect(lambda n: (setattr(s, "cur", n), s.refresh())); s.cards.insertWidget(s.cards.count() - 1, c)
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

def ev_color(d, e): return e.get("color") or color_of(d, "subjects", e.get("subject", "")) or YEL

class EventDialog(Overlay):
    def __init__(s, parent, win, ev, date):
        super().__init__(parent, 500); s.win, s.ev, s.deleted = win, ev, False; d = win.store.data; s.date = ev["date"] if ev else date; s.time = ev["time"] if ev else ""; s.files = list(ev["files"]) if ev else []
        s.title = s.head(ev["title"] if ev else "Novo Evento"); s.bd = QPushButton(br(s.date)); s.bd.setStyleSheet(f"background:transparent;color:{T['text']};font-size:28px;font-weight:300;text-align:left;padding:0"); s.bd.setCursor(Qt.PointingHandCursor); s.bd.clicked.connect(s.chg_date); s.lay.addWidget(s.bd)
        s.desc = s.ph_edit("Adicionar Descrição", 170); s.desc.setPlainText(ev["desc"] if ev else ""); s.lay.addWidget(s.desc)
        s.tp = ClickPill("Adicionar Horário"); s.tp.setv(s.time); s.tp.clicked.connect(s.chg_time); s.lay.addWidget(s.tp)
        r = QHBoxLayout(); s.sub = s.pill_combo("Adicionar Matéria", d["subjects"], ev["subject"] if ev else ""); s.tag = s.pill_combo("Adicionar Tag", d["tags"], ev["tag"] if ev else ""); r.addWidget(s.sub); r.addWidget(s.tag); s.lay.addLayout(r)
        s.fp = ClickPill("Anexar Arquivos"); s.fp.setv(f"{len(s.files)} arquivo(s)" if s.files else ""); s.fp.clicked.connect(s.chg_files); s.lay.addWidget(s.fp)
        s.lay.addWidget(muted("Cor do evento (a primeira bolinha = automática: cor da matéria ou amarelo)", 11, 500)); s.cr = ColorRow(ev.get("color", "") if ev else ""); s.lay.addWidget(s.cr)
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
        return dict(title=s.title.text().strip() or "Novo Evento", date=s.date, time=s.time, subject=cbval(s.sub), tag=cbval(s.tag), desc=s.desc.toPlainText().strip(), files=s.files, color=s.cr.color())

class CalendarPage(Page):
    def __init__(s, win):
        super().__init__(win); s.m = today().replace(day=1); lay = QVBoxLayout(s); lay.setContentsMargins(60, 24, 44, 26); lay.setSpacing(8); h = QHBoxLayout(); h.addWidget(heading("Calendário", 44)); h.addStretch()
        pv = IBtn("tri_l", 56, "ghost", "Mês anterior", 40); nx = IBtn("tri_r", 56, "ghost", "Próximo mês", 40); pv.clicked.connect(lambda: s.shift(-1)); nx.clicked.connect(lambda: s.shift(1)); h.addWidget(pv); h.addWidget(nx); h.addSpacing(18)
        s.lbl = QLabel(); s.lbl.setStyleSheet("font-size:42px;font-weight:300"); s.lbl.setFixedWidth(450); s.lbl.setAlignment(Qt.AlignLeft | Qt.AlignVCenter); h.addWidget(s.lbl); lay.addLayout(h)
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
            for e in sorted(ev.get(iso(d), []), key=lambda e: e["time"]): col = ev_color(s.d, e); items.append((e["title"], col, on_color(col), lambda e=e: s.open_event(e["date"], e), (e["time"] + " " if e["time"] else "") + e["title"]))
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
