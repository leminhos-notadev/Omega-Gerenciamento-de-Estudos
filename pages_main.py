# -*- coding: utf-8 -*-
"""Início (estatísticas) e Foco (temporizador / pomodoro / cronômetro + player de música)."""
from omega_core import *

# ───────────────────────── estatísticas ─────────────────────────
class StudyStats(QWidget):
    def __init__(s, win):
        super().__init__(); s.win = win; s.off = 0; L = QVBoxLayout(s); L.setContentsMargins(20, 16, 20, 16); L.setSpacing(10)
        r = QHBoxLayout(); r.setSpacing(8)
        s.cb_per = QComboBox(); s.cb_per.addItems(["Dia", "Semana", "Mês", "Ano"]); s.cb_chart = QComboBox(); s.cb_chart.addItems(["Tempo por período", "Por matéria", "Por tag"])
        s.cb_sub = QComboBox(); s.cb_tag = QComboBox()
        for w in (s.cb_per, s.cb_chart, s.cb_sub, s.cb_tag): w.setFixedHeight(38); w.setStyleSheet("padding:2px 14px"); w.currentIndexChanged.connect(lambda _: s.refresh()); r.addWidget(w)
        pv = IBtn("tri_l", 36, "ghost"); nx = IBtn("tri_r", 36, "ghost"); pv.clicked.connect(lambda: (setattr(s, "off", s.off + 1), s.refresh())); nx.clicked.connect(lambda: (setattr(s, "off", max(0, s.off - 1)), s.refresh()))
        r.addWidget(pv); r.addWidget(nx); r.addStretch()
        s.bg = pill("Gráfico", True, 36); s.bl = pill("Blocos", True, 36); g = QButtonGroup(s); g.addButton(s.bg); g.addButton(s.bl); s.bg.setChecked(True)
        s.bg.clicked.connect(lambda: s.stack.setCurrentIndex(0)); s.bl.clicked.connect(lambda: s.stack.setCurrentIndex(1)); r.addWidget(s.bg); r.addWidget(s.bl); L.addLayout(r)
        s.lbl = muted("", 12); L.addWidget(s.lbl); s.stack = QStackedWidget(); L.addWidget(s.stack, 1)
        s.chart = BarChart(fmt_min); s.stack.addWidget(s.chart)
        w = QWidget(); wl = QVBoxLayout(w); wl.setContentsMargins(0, 0, 0, 0); s.tb = mk_table(["Data / hora", "Duração", "Modo", "Matéria", "Tag", "Descrição"]); s.tb.doubleClicked.connect(lambda _: s.edit()); wl.addWidget(s.tb, 1)
        br_ = QHBoxLayout(); br_.addStretch()
        for ic, tip, fn in [("plus", "Adicionar bloco não contado", lambda: s.edit(True)), ("pencil", "Editar bloco", lambda: s.edit()), ("trash", "Apagar bloco", s.delete)]:
            b = IBtn(ic, 40, "accent" if ic == "plus" else "dark", tip); b.clicked.connect(lambda _, fn=fn: fn()); br_.addWidget(b)
        wl.addLayout(br_); s.stack.addWidget(w)
    @property
    def d(s): return s.win.store.data
    def refresh(s):
        d = s.d; fill(s.cb_sub, d["subjects"], "Todas as matérias"); fill(s.cb_tag, d["tags"], "Todas as tags")
        sub, tag = cbval(s.cb_sub), cbval(s.cb_tag); per = s.cb_per.currentText(); n = {"Dia": 14, "Semana": 12, "Mês": 12, "Ano": 6}[per]
        bk = buckets(per, n, s.off); s.lbl.setText(f"{bk[0][1].strftime('%d/%m/%Y')}  →  {(bk[-1][2] - dt.timedelta(days=1)).strftime('%d/%m/%Y')}")
        mode = s.cb_chart.currentIndex()
        if mode == 0: data = [(l, minutes_between(d, a, b, sub, tag)) for l, a, b in bk]
        else:
            key = "subject" if mode == 1 else "tag"; g = {}
            for x in d["sessions"]:
                dd = dt.date.fromisoformat(x["start"][:10])
                if bk[0][1] <= dd < bk[-1][2] and (not sub or x.get("subject") == sub) and (not tag or x.get("tag") == tag):
                    k = x.get(key) or "(nenhuma)"; g[k] = g.get(k, 0) + x["minutes"]
            data = sorted(g.items(), key=lambda kv: -kv[1])
        s.chart.set_data(data, fmt_min)
        ss = sorted([x for x in d["sessions"] if (not sub or x.get("subject") == sub) and (not tag or x.get("tag") == tag)], key=lambda x: x["start"], reverse=True)
        s.tb.setRowCount(len(ss))
        for i, x in enumerate(ss):
            put(s.tb, i, 0, x["start"].replace("T", " ")[:16], x["id"]); put(s.tb, i, 1, fmt_min(x["minutes"])); put(s.tb, i, 2, MODE_NAMES.get(x["mode"], x["mode"]))
            put(s.tb, i, 3, x.get("subject", "")); put(s.tb, i, 4, x.get("tag", "")); put(s.tb, i, 5, x.get("desc", ""))
        s.tb.resizeColumnsToContents(); s.tb.horizontalHeader().setStretchLastSection(True)
    def edit(s, new=False):
        x = None
        if not new:
            x = next((y for y in s.d["sessions"] if y["id"] == sel_id(s.tb)), None)
            if not x: return
        v = {} if new else dict(x, date=x["start"][:10], time=x["start"][11:16], minutes=int(round(x["minutes"])))
        dlg = FormDialog(s, "Novo bloco" if new else "Editar bloco", [("date", "Data", "date"), ("time", "Hora", "time"), ("minutes", "Duração (min)", "int"),
                         ("subject", "Matéria", "combo", s.d["subjects"]), ("tag", "Tag", "combo", s.d["tags"]), ("desc", "Descrição", "text")], v)
        if dlg.exec():
            r = dlg.values()
            if r["minutes"] <= 0: return
            rec = dict(start=f"{r['date']}T{r['time']}", minutes=r["minutes"], subject=r["subject"], tag=r["tag"], desc=r["desc"])
            if new: s.d["sessions"].append(dict(rec, id=uid(), mode="manual"))
            else: x.update(rec)
            s.win.store.save(); s.refresh()
    def delete(s):
        sid = sel_id(s.tb)
        if sid and confirm(s, "Apagar este bloco?"): s.d["sessions"][:] = [x for x in s.d["sessions"] if x["id"] != sid]; s.win.store.save(); s.refresh()

class RecordStats(QWidget):
    def __init__(s, win, key):
        super().__init__(); s.win, s.key, s.cfg = win, key, RECORDS[key]; L = QVBoxLayout(s); L.setContentsMargins(20, 16, 20, 16); L.setSpacing(10)
        r = QHBoxLayout(); s.cb_t = QComboBox(); s.cb_p = QComboBox(); s.cb_p.addItems(["Cada registro", "Por mês", "Por ano"])
        for w in (s.cb_t, s.cb_p): w.setFixedHeight(38); w.setStyleSheet("padding:2px 14px"); w.currentIndexChanged.connect(lambda _: s.refresh()); r.addWidget(w)
        s.cb_t.setVisible(bool(s.cfg["typekey"])); r.addStretch(); L.addLayout(r); s.sum = muted("", 13); L.addWidget(s.sum); s.chart = BarChart(s.cfg["fmt"]); L.addWidget(s.chart, 1)
    def refresh(s):
        d = s.win.store.data[s.key]; tk = s.cfg["typekey"]
        if tk: fill(s.cb_t, sorted({r.get(tk, "") for r in d if r.get(tk)}), "Todos os tipos")
        t = cbval(s.cb_t) if tk else ""; rs = sorted([r for r in d if not t or r.get(tk) == t], key=lambda r: r["date"]); m = s.cfg["metric"]
        s.chart.set_data(record_series(rs, m, s.cb_p.currentIndex()), s.cfg["fmt"]); vs = [m(r) for r in rs if m(r) is not None]; f = s.cfg["fmt"]
        s.sum.setText(f"Registros: {len(rs)}" + (f"     Média: {f(sum(vs) / len(vs))}     Melhor: {f(max(vs))}     Último: {f(vs[-1])}" if vs else "     Adicione registros na página correspondente para ver a evolução."))

class Home(Page):
    def __init__(s, win):
        super().__init__(win); lay = QVBoxLayout(s); lay.setContentsMargins(60, 26, 44, 30); lay.setSpacing(16)
        s.hello = QLabel(); s.hello.setCursor(Qt.PointingHandCursor); s.hello.setToolTip("Clique para trocar o nome"); s.hello.mousePressEvent = lambda e: s.rename(); lay.addWidget(s.hello)
        card = Card(26); cl = QVBoxLayout(card); cl.setContentsMargins(22, 20, 22, 22); cl.setSpacing(16); tabs = QHBoxLayout(); tabs.setSpacing(24); g = QButtonGroup(s); s.tb = []
        for i, n in enumerate(["Tempo de Estudo", "Simulados", "Redações"]):
            b = pill(n, True, 54); b.setStyleSheet("font-size:17px;font-weight:700;border-radius:18px"); g.addButton(b); b.clicked.connect(lambda _, i=i: s.tab(i)); tabs.addWidget(b, 1); s.tb.append(b)
        cl.addLayout(tabs); inner = Card(20, "bg"); il = QVBoxLayout(inner); il.setContentsMargins(0, 0, 0, 0); s.views = QStackedWidget(); il.addWidget(s.views)
        s.study = StudyStats(win); s.ex = RecordStats(win, "exams"); s.es = RecordStats(win, "essays")
        for v in (s.study, s.ex, s.es): s.views.addWidget(v)
        cl.addWidget(inner, 1); lay.addWidget(card, 1); s.tb[0].setChecked(True)
    def tab(s, i): s.views.setCurrentIndex(i); s.views.currentWidget().refresh()
    def rename(s):
        n, ok = QInputDialog.getText(s, "Seu nome", "Como devemos te chamar?", text=s.d["settings"]["user"])
        if ok: s.d["settings"]["user"] = n.strip(); s.st.save(); s.refresh()
    def refresh(s):
        u = s.d["settings"]["user"] or "usuário"
        s.hello.setText(f"<span style='font-size:46px;font-weight:300'>Bem-vindo, <span style='color:{T['accent']}'>{u}</span></span>"); s.views.currentWidget().refresh()

# ───────────────────────── foco ─────────────────────────
class Clock(QWidget):
    dbl = Signal()
    def __init__(s): super().__init__(); s.frac = 1.0; s.text = "25:00"; s.sub = ""; s.bell = True; s.dim = False; s.setMinimumSize(260, 260)
    def mouseDoubleClickEvent(s, e): s.dbl.emit()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); w, h = s.width(), s.height(); side = min(w, h) - 10; r = QRectF((w - side) / 2, (h - side) / 2, side, side)
        ring = r.adjusted(7, 7, -7, -7)
        if s.dim: c = QColor(T["bg"]); c.setAlpha(225); p.setPen(Qt.NoPen); p.setBrush(c); p.drawEllipse(ring)
        tr = QColor(T["accent"]); tr.setAlpha(55); p.setBrush(Qt.NoBrush); p.setPen(QPen(tr, 13)); p.drawEllipse(ring)
        p.setPen(QPen(QColor(T["accent"]), 13, Qt.SolidLine, Qt.RoundCap))
        if s.frac >= .999: p.drawEllipse(ring)
        elif s.frac > 0: p.drawArc(ring, 90 * 16, -int(s.frac * 360 * 16))
        p.setPen(QColor(T["text"])); f = QFont(s.font()); f.setWeight(QFont.Bold); f.setPixelSize(int(side / 6.4)); p.setFont(f)
        p.drawText(QRectF(r.x(), r.y(), side, side * .94), Qt.AlignCenter, s.text)
        f.setPixelSize(max(11, int(side / 15))); p.setFont(f); fm = p.fontMetrics(); tw = fm.horizontalAdvance(s.sub); ic = int(side / 14) if s.bell else 0
        x0 = r.center().x() - (tw + ic + (6 if ic else 0)) / 2; y = r.center().y() + side / 8.5; p.setPen(QColor(T["muted"]))
        if ic: p.drawPixmap(QPointF(x0, y + (fm.height() - ic) / 2), pix("bell", T["muted"], ic))
        p.drawText(QRectF(x0 + ic + (6 if ic else 0), y, tw + 4, fm.height()), Qt.AlignLeft | Qt.AlignVCenter, s.sub)

def choose_tracks(parent, lib, sel):
    dlg = QDialog(parent); dlg.setWindowTitle("Escolher músicas"); dlg.setMinimumSize(380, 420); l = QVBoxLayout(dlg); l.setContentsMargins(22, 20, 22, 20); l.addWidget(heading("Escolher músicas", 22)); lw = QListWidget()
    for t in lib:
        it = QListWidgetItem(t["title"]); it.setFlags(it.flags() | Qt.ItemIsUserCheckable); it.setCheckState(Qt.Checked if t["id"] in sel else Qt.Unchecked); it.setData(Qt.UserRole, t["id"]); lw.addItem(it)
    l.addWidget(lw); bb = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel); bb.accepted.connect(dlg.accept); bb.rejected.connect(dlg.reject); l.addWidget(bb)
    if dlg.exec(): return [lw.item(i).data(Qt.UserRole) for i in range(lw.count()) if lw.item(i).checkState() == Qt.Checked]
    return None

def play_shuffled(win, pl):
    import random
    tr = {t["id"]: t for t in win.store.data["library"]}; q = [tr[i] for i in pl["tracks"] if i in tr]; random.shuffle(q); win.music.set_queue(q)

class PlaylistDialog(Overlay):
    """Reordena as músicas arrastando (ou pelas setas), adiciona/remove e toca em ordem ou aleatório."""
    def __init__(s, parent, win, pl):
        super().__init__(parent, 540); s.win, s.pl = win, pl; s.setFixedHeight(640); r = QHBoxLayout(); r.addWidget(heading(pl["name"], 28), 1); x = IBtn("x", 46); x.clicked.connect(s.accept); r.addWidget(x); s.lay.addLayout(r)
        s.lay.addWidget(muted("Arraste as músicas para cima ou para baixo (ou use as setas) para mudar a ordem.", 12, 500))
        s.lw = QListWidget(); s.lw.setDragDropMode(QAbstractItemView.InternalMove); s.lw.setDefaultDropAction(Qt.MoveAction); s.lw.setSelectionMode(QAbstractItemView.ExtendedSelection); s.lay.addWidget(s.lw, 1)
        s.lw.model().rowsMoved.connect(lambda *_: s.sync()); s.fill(); b = QHBoxLayout(); b.setSpacing(8)
        for ic, tip, fn, k in [("up", "Mover para cima", lambda: s.move(-1), "dark"), ("down", "Mover para baixo", lambda: s.move(1), "dark"), ("plus", "Adicionar músicas", s.add, "accent"), ("trash", "Remover da playlist", s.remove, "dark")]:
            bt = IBtn(ic, 42, k, tip); bt.clicked.connect(lambda _, fn=fn: fn()); b.addWidget(bt)
        b.addStretch(); po = pill("Em ordem", False, 42); po.clicked.connect(lambda: s.play(False)); ps = QPushButton("Aleatório"); ps.setIcon(qicon("shuffle", T["on_accent"], T["on_accent"], 20)); ps.setFixedHeight(42); ps.clicked.connect(lambda: s.play(True))
        b.addWidget(po); b.addWidget(ps); s.lay.addLayout(b)
    def tracks(s): return {t["id"]: t for t in s.win.store.data["library"]}
    def fill(s):
        s.lw.clear(); tr = s.tracks()
        for i in s.pl["tracks"]:
            if i in tr: it = QListWidgetItem(tr[i]["title"]); it.setData(Qt.UserRole, i); s.lw.addItem(it)
    def sync(s): s.pl["tracks"] = [s.lw.item(i).data(Qt.UserRole) for i in range(s.lw.count())]; s.win.store.save()
    def move(s, d):
        rows = sorted(s.lw.row(i) for i in s.lw.selectedItems())
        if not rows or (d < 0 and rows[0] == 0) or (d > 0 and rows[-1] == s.lw.count() - 1): return
        for r in (rows if d < 0 else reversed(rows)): it = s.lw.takeItem(r); s.lw.insertItem(r + d, it); it.setSelected(True)
        s.sync()
    def add(s):
        ids = choose_tracks(s, s.win.store.data["library"], s.pl["tracks"])
        if ids is not None: s.pl["tracks"] = [i for i in s.pl["tracks"] if i in ids] + [i for i in ids if i not in s.pl["tracks"]]; s.win.store.save(); s.fill()
    def remove(s):
        for i in s.lw.selectedItems(): s.lw.takeItem(s.lw.row(i))
        s.sync()
    def play(s, shuffle):
        s.sync()
        if shuffle: play_shuffled(s.win, s.pl)
        else: tr = s.tracks(); s.win.music.set_queue([tr[i] for i in s.pl["tracks"] if i in tr])

class MusicDialog(Overlay):
    def __init__(s, parent, win):
        super().__init__(parent, 560); s.win = win; s.setFixedHeight(680); s.lay.setSpacing(8)
        def sec(title, fn, extra=()):
            r = QHBoxLayout(); r.addWidget(heading(title, 30)); b = IBtn("plus", 38, "accent", "Adicionar"); b.clicked.connect(fn); r.addWidget(b)
            for ic, tip, f2 in extra: e = IBtn(ic, 38, "dark", tip); e.clicked.connect(lambda _, f2=f2: f2()); r.addWidget(e)
            r.addStretch(); s.lay.addLayout(r)
            q = QLineEdit(); q.setPlaceholderText("Buscar…"); q.addAction(QIcon(pix("search", T["text"], 22)), QLineEdit.TrailingPosition); q.setFixedHeight(46); q.textChanged.connect(lambda _: s.fill()); s.lay.addWidget(q)
            lw = QListWidget(); lw.setContextMenuPolicy(Qt.CustomContextMenu); s.lay.addWidget(lw, 1); return q, lw
        s.q1, s.lib = sec("Minhas Músicas", s.import_music); s.q2, s.pls = sec("Minhas Playlists", s.new_playlist, [("pencil", "Editar ordem e músicas da playlist selecionada", s.edit_sel), ("shuffle", "Tocar a playlist selecionada em ordem aleatória", s.shuffle_sel)])
        x = IBtn("x", 44); x.clicked.connect(s.accept); x.setParent(s); x.move(560 - 44 - 22, 18); x.raise_()
        s.lib.itemDoubleClicked.connect(s.play_track); s.pls.itemDoubleClicked.connect(s.play_pl)
        s.lib.customContextMenuRequested.connect(s.lib_menu); s.pls.customContextMenuRequested.connect(s.pl_menu); s.fill()
    @property
    def d(s): return s.win.store.data
    def tracks(s): return {t["id"]: t for t in s.d["library"]}
    def fill(s):
        s.lib.clear(); f = s.q1.text().lower(); s.shown = [t for t in s.d["library"] if f in t["title"].lower()]
        for t in s.shown: it = QListWidgetItem(t["title"]); it.setData(Qt.UserRole, t["id"]); s.lib.addItem(it)
        s.pls.clear(); f = s.q2.text().lower()
        for p in s.d["playlists"]:
            if f in p["name"].lower(): it = QListWidgetItem(f"{p['name']}   ({len(p['tracks'])})"); it.setData(Qt.UserRole, p["id"]); s.pls.addItem(it)
    def import_music(s):
        ps, _ = QFileDialog.getOpenFileNames(s, "Importar músicas", "", "Áudio (*.mp3 *.wav *.ogg *.m4a *.flac *.aac)"); have = {t["path"] for t in s.d["library"]}
        for p in ps:
            if p not in have: s.d["library"].append(dict(id=uid(), title=Path(p).stem, path=p))
        s.win.store.save(); s.fill()
    def play_track(s, it):
        i = s.lib.row(it); s.win.music.set_queue(s.shown, i)
    def play_pl(s, it):
        p = next(x for x in s.d["playlists"] if x["id"] == it.data(Qt.UserRole)); tr = s.tracks(); s.win.music.set_queue([tr[i] for i in p["tracks"] if i in tr])
    def new_playlist(s):
        n, ok = QInputDialog.getText(s, "Nova playlist", "Nome da playlist:")
        if ok and n.strip():
            ids = choose_tracks(s, s.d["library"], [])
            if ids is not None: s.d["playlists"].append(dict(id=uid(), name=n.strip(), tracks=ids)); s.win.store.save(); s.fill()
    def lib_menu(s, pos):
        it = s.lib.itemAt(pos)
        if not it: return
        m = QMenu(s); sub = m.addMenu("Adicionar à playlist"); acts = {sub.addAction(p["name"]): p for p in s.d["playlists"]}; rm = m.addAction("Remover da biblioteca"); a = m.exec(s.lib.mapToGlobal(pos)); tid = it.data(Qt.UserRole)
        if a in acts and tid not in acts[a]["tracks"]: acts[a]["tracks"].append(tid)
        elif a == rm:
            s.d["library"][:] = [t for t in s.d["library"] if t["id"] != tid]
            for p in s.d["playlists"]: p["tracks"] = [i for i in p["tracks"] if i != tid]
        s.win.store.save(); s.fill()
    def cur_pl(s):
        it = s.pls.currentItem(); return next((x for x in s.d["playlists"] if it and x["id"] == it.data(Qt.UserRole)), None)
    def edit_sel(s):
        p = s.cur_pl()
        if p: PlaylistDialog(s, s.win, p).exec(); s.fill()
    def shuffle_sel(s):
        p = s.cur_pl()
        if p: play_shuffled(s.win, p)
    def pl_menu(s, pos):
        it = s.pls.itemAt(pos)
        if not it: return
        p = next(x for x in s.d["playlists"] if x["id"] == it.data(Qt.UserRole)); m = QMenu(s); ed = m.addAction("Editar ordem e músicas"); sh = m.addAction("Tocar em ordem aleatória"); rn = m.addAction("Renomear"); dl = m.addAction("Excluir"); a = m.exec(s.pls.mapToGlobal(pos))
        if a == ed: PlaylistDialog(s, s.win, p).exec()
        elif a == sh: play_shuffled(s.win, p)
        elif a == rn:
            n, ok = QInputDialog.getText(s, "Renomear", "Nome:", text=p["name"])
            if ok and n.strip(): p["name"] = n.strip()
        elif a == dl: s.d["playlists"].remove(p)
        s.win.store.save(); s.fill()

def mmss_ms(ms): ms = max(0, int(ms)) // 1000; return f"{ms // 60}:{ms % 60:02d}"

class VolumePopup(QFrame):
    def __init__(s, win):
        super().__init__(None, Qt.Popup | Qt.FramelessWindowHint); s.win = win; s.setAttribute(Qt.WA_TranslucentBackground); s.setFixedSize(76, 210)
        l = QVBoxLayout(s); l.setContentsMargins(10, 14, 10, 12); l.setSpacing(8); s.lab = QLabel("60%"); s.lab.setAlignment(Qt.AlignCenter); s.lab.setStyleSheet("font-weight:600"); l.addWidget(s.lab)
        s.sl = QSlider(Qt.Vertical); s.sl.setRange(0, 100); l.addWidget(s.sl, 1, Qt.AlignHCenter); s.mu = IBtn("mute", 34, "dark", "Silenciar", 18); l.addWidget(s.mu, 0, Qt.AlignHCenter)
        s.sl.valueChanged.connect(s.changed); s.mu.clicked.connect(s.toggle_mute)
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(T["card"])); p.setPen(QPen(QColor(T["line"]), 1.5)); p.drawRoundedRect(QRectF(s.rect()).adjusted(1, 1, -1, -1), 18, 18)
    def changed(s, v):
        c = s.win.store.data["settings"]; c["vol"] = v; s.lab.setText(f"{v}%"); mp = s.win.music
        if v > 0 and mp.muted: mp.mute(False)
        mp.volume(v); s.win.focus.vol_icon()
    def toggle_mute(s): s.win.music.mute(not s.win.music.muted); s.win.focus.vol_icon()
    def hideEvent(s, e): s.win.store.save(); super().hideEvent(e)
    def popup(s, btn):
        s.sl.blockSignals(True); s.sl.setValue(s.win.store.data["settings"]["vol"]); s.sl.blockSignals(False); s.lab.setText(f"{s.sl.value()}%")
        s.move(btn.mapToGlobal(QPoint(btn.width() // 2 - s.width() // 2, -s.height() - 8))); s.show()

class FocusPage(Page):
    def __init__(s, win):
        super().__init__(win); s.mode = "timer"; s.running = False; s.elapsed = 0.0; s.logged = 0.0; s.phase = "study"; s.cycle = 1; s.blocks_done = 0; s.last = 0; s.zen = False; s.pix = None
        s.mp = win.music; s.alarm = Sound()
        s.video = None; s.vp = None
        root = QVBoxLayout(s); root.setContentsMargins(60, 24, 44, 22); root.setSpacing(10)
        s.top = QWidget(); tl = QHBoxLayout(s.top); tl.setContentsMargins(0, 0, 0, 0); tl.addStretch(); bar = Card(30); bl = QHBoxLayout(bar); bl.setContentsMargins(14, 10, 14, 10); bl.setSpacing(10); g = QButtonGroup(s); s.mb = {}
        for k, n in [("timer", "Temporizador"), ("pomodoro", "Pomodoro"), ("stopwatch", "Cronômetro")]:
            b = pill(n, True, 44); b.setMinimumWidth(170); b.setStyleSheet("font-size:14px;border-radius:22px"); g.addButton(b); b.clicked.connect(lambda _, k=k: s.set_mode(k)); bl.addWidget(b); s.mb[k] = b
        pe = IBtn("pencil", 48, "dark", "Personalizar (matéria, tags, durações, alarmes, fundo)"); pe.clicked.connect(s.open_cfg); bl.addWidget(pe); tl.addWidget(bar); tl.addStretch(); root.addWidget(s.top)
        s.clock = Clock(); s.clock.dbl.connect(lambda: s.set_zen(not s.zen)); root.addWidget(s.clock, 1)
        s.ctl = QWidget(); cl = QHBoxLayout(s.ctl); cl.setContentsMargins(0, 0, 0, 0); cl.setSpacing(34); cl.addStretch()
        s.bp = IBtn("play", 64, "accent", "Iniciar / pausar", 28); s.bs = IBtn("stop", 64, "accent", "Finalizar e salvar o bloco", 26); s.bz = IBtn("eye", 64, "dark", "Esconder interface (só o relógio)", 28)
        for b, fn in [(s.bp, s.toggle), (s.bs, s.stop), (s.bz, lambda: s.set_zen(True))]: b.clicked.connect(lambda _, fn=fn: fn()); cl.addWidget(b)
        cl.addStretch(); root.addWidget(s.ctl); s.info = muted("", 13, 500); s.info.setAlignment(Qt.AlignCenter); root.addWidget(s.info)
        s.player = Card(34); s.player.setFixedHeight(96); s.player.setMaximumWidth(820); pv = QVBoxLayout(s.player); pv.setContentsMargins(28, 10, 16, 12); pv.setSpacing(2); pl = QHBoxLayout(); pl.setSpacing(6); pv.addLayout(pl)
        s.song = QLabel(); s.song.setStyleSheet("font-size:18px;font-weight:300"); mu = IBtn("music", 40, "ghost", "Minhas músicas e playlists", 26); mu.clicked.connect(s.open_music)
        pl.addWidget(s.song); pl.addWidget(mu); pl.addStretch(); s.bprev = IBtn("prev", 40, "ghost", "Anterior", 20); s.bpp = IBtn("pause", 46, "dark", "Tocar / pausar música", 22); s.bnext = IBtn("next", 40, "ghost", "Próxima", 20)
        s.bvol = IBtn("volume", 40, "ghost", "Volume", 22); s.bvol.clicked.connect(s.open_volume)
        s.bprev.clicked.connect(lambda: s.mp.next(-1)); s.bnext.clicked.connect(lambda: s.mp.next(1)); s.bpp.clicked.connect(s.mp.toggle)
        sk = QHBoxLayout(); sk.setSpacing(10); s.tcur = muted("0:00", 11, 500); s.tdur = muted("0:00", 11, 500); s.seek = QSlider(Qt.Horizontal); s.seek.setRange(0, 1); s.seek.setCursor(Qt.PointingHandCursor); s.seeking = False
        s.seek.sliderPressed.connect(lambda: setattr(s, "seeking", True)); s.seek.sliderReleased.connect(lambda: (setattr(s, "seeking", False), s.mp.seek(s.seek.value()))); s.seek.valueChanged.connect(lambda v: s.tcur.setText(mmss_ms(v)) if s.seeking else None)
        sk.addWidget(s.tcur); sk.addWidget(s.seek, 1); sk.addWidget(s.tdur); pv.addLayout(sk); s.mp.progress.connect(s.on_progress)
        for b in (s.bprev, s.bpp, s.bnext, s.bvol): pl.addWidget(b)
        pw = QHBoxLayout(); pw.addStretch(); pw.addWidget(s.player, 1); pw.addStretch(); s.pw = QWidget(); s.pw.setLayout(pw); pw.setContentsMargins(0, 0, 0, 0); root.addWidget(s.pw)
        s.hint = muted("Duplo clique no relógio ou Esc: sair   •   Espaço: iniciar/pausar   •   F11: tela cheia", 12, 500); s.hint.setAlignment(Qt.AlignCenter); s.hint.hide(); root.addWidget(s.hint)
        s.build_cfg(); s.load_cfg(); s.mp.changed.connect(s.music_ui); s.music_ui()
        s.t = QTimer(s); s.t.setInterval(200); s.t.timeout.connect(s.tick); s.t.start(); s.set_mode("timer")
    # ── personalizar
    def build_cfg(s):
        dlg = Overlay(s.win, 560); s.cfgdlg = dlg; te = dlg.head("Personalizar"); te.setReadOnly(True); f = QFormLayout(); f.setSpacing(10); f.setLabelAlignment(Qt.AlignRight); s.form = f
        s.cb_sub = QComboBox(); s.cb_tag = QComboBox(); s.ed = QLineEdit(); s.ed.setPlaceholderText("Descrição (opcional)")
        for cb in (s.cb_sub, s.cb_tag): cb.setStyleSheet(f"QComboBox{{border:none;background:{T['field']};padding:8px 16px}}"); cb.currentIndexChanged.connect(lambda _: s.info_txt())
        def spin(a, b): w = QSpinBox(); w.setRange(a, b); w.setStyleSheet("padding:6px 14px"); return w
        s.sp_timer, s.sp_study, s.sp_break, s.sp_long, s.sp_cyc = spin(1, 720), spin(1, 240), spin(1, 120), spin(1, 120), spin(1, 12)
        s.ed.textChanged.connect(lambda _: s.info_txt())
        aud = "Áudio (*.mp3 *.wav *.ogg *.m4a *.flac)"; test = lambda p: s.play_alarm(p)
        s.pk_at, s.pk_as, s.pk_ab = PickRow(aud, test), PickRow(aud, test), PickRow(aud, test); s.pk_bg = PickRow("Imagem/Vídeo (*.png *.jpg *.jpeg *.webp *.bmp *.gif *.mp4 *.mkv *.webm *.mov *.avi)")
        s.chk_long = QCheckBox("Usar descanso longo"); s.sp_total = spin(0, 99); s.sp_total.setSpecialValueText("sem limite")
        for lab, w in [("Matéria", s.cb_sub), ("Tag", s.cb_tag), ("Descrição", s.ed), ("Minutos", s.sp_timer), ("Estudo (min)", s.sp_study), ("Descanso (min)", s.sp_break), ("Descanso longo (min)", s.sp_long),
                       ("", s.chk_long), ("Blocos antes do descanso longo", s.sp_cyc), ("Parar após (blocos)", s.sp_total), ("Alarme do temporizador", s.pk_at), ("Alarme fim do estudo", s.pk_as), ("Alarme fim do descanso", s.pk_ab), ("Fundo (imagem/vídeo)", s.pk_bg)]:
            f.addRow(muted(lab, 12), w)
        dlg.lay.addLayout(f); mg = QPushButton("Gerenciar matérias e tags"); mg.clicked.connect(s.manage); dlg.lay.addWidget(mg)
        for w in (s.sp_timer, s.sp_study, s.sp_break, s.sp_long, s.sp_cyc, s.sp_total): w.valueChanged.connect(s.store_cfg)
        s.chk_long.toggled.connect(lambda _: (s.store_cfg(), s.update_rows()))
        for pk, k in [(s.pk_at, "alarm_timer"), (s.pk_as, "alarm_study"), (s.pk_ab, "alarm_break"), (s.pk_bg, "bg")]:
            pk.changed.connect(lambda p, k=k: (s.d["settings"].__setitem__(k, p), s.st.save(), s.apply_bg() if k == "bg" else None))
    def retheme(s):
        if hasattr(s, 'cfgdlg'): s.cfgdlg.deleteLater(); s.build_cfg(); s.load_cfg(); s.set_mode(s.mode); s.refresh()
    def retheme(s):
        if hasattr(s, "cfgdlg"): s.cfgdlg.deleteLater(); s.build_cfg(); s.load_cfg(); s.refresh(); s.set_mode(s.mode)
    def open_cfg(s): s.cfgdlg.exec(); s.display()
    def load_cfg(s):
        c = s.d["settings"]
        for w, k in [(s.sp_timer, "timer_min"), (s.sp_study, "pomo_study"), (s.sp_break, "pomo_break"), (s.sp_long, "pomo_long"), (s.sp_cyc, "pomo_cycles"), (s.sp_total, "pomo_total")]:
            w.blockSignals(True); w.setValue(c[k]); w.blockSignals(False)
        s.chk_long.blockSignals(True); s.chk_long.setChecked(c["pomo_use_long"]); s.chk_long.blockSignals(False)
        for pk, k in [(s.pk_at, "alarm_timer"), (s.pk_as, "alarm_study"), (s.pk_ab, "alarm_break"), (s.pk_bg, "bg")]: pk.set(c[k], False)
        s.mp.volume(c["vol"]); s.vol_icon(); s.apply_bg()
    def store_cfg(s):
        c = s.d["settings"]; c.update(timer_min=s.sp_timer.value(), pomo_study=s.sp_study.value(), pomo_break=s.sp_break.value(), pomo_long=s.sp_long.value(), pomo_cycles=s.sp_cyc.value(), pomo_total=s.sp_total.value(), pomo_use_long=s.chk_long.isChecked())
        s.st.save()
        if not s.running and s.elapsed == 0: s.display()
    def manage(s):
        if edit_list(s, "Matérias", s.d["subjects"]) | edit_list(s, "Tags", s.d["tags"]): s.st.save(); s.refresh()
    def refresh(s):
        fill(s.cb_sub, s.d["subjects"], "— nenhuma —"); fill(s.cb_tag, s.d["tags"], "— nenhuma —"); s.display(); s.info_txt()
    def info_txt(s):
        a = [x for x in (cbval(s.cb_sub), cbval(s.cb_tag), s.ed.text().strip()) if x]; s.info.setText("  ·  ".join(a) if a else "Escolha matéria e tag no ícone do lápis")
    def open_music(s): MusicDialog(s.win, s.win).exec(); s.win.store.save()
    def music_ui(s):
        s.song.setText(s.mp.title or "Nenhuma música"); s.bpp.set_icon("pause" if s.mp.playing else "play"); s.vol_icon()
    def on_progress(s, pos, dur):
        s.seek.blockSignals(True); s.seek.setRange(0, max(1, dur))
        if not s.seeking: s.seek.setValue(pos); s.tcur.setText(mmss_ms(pos))
        s.seek.blockSignals(False); s.tdur.setText(mmss_ms(dur))
    def vol_icon(s): s.bvol.set_icon("mute" if (s.mp.muted or s.d["settings"]["vol"] == 0) else "volume")
    def open_volume(s):
        if not hasattr(s, "volpop"): s.volpop = VolumePopup(s.win)
        s.volpop.popup(s.bvol)
    # ── fundo
    def apply_bg(s):
        p = s.d["settings"]["bg"]; s.pix = None
        if s.vp: s.vp.stop()
        if s.video: s.video.hide()
        if p and Path(p).exists():
            if Path(p).suffix.lower() in IMG_EXT: s.pix = QPixmap(p)
            elif not NOAUDIO:
                if not s.video:
                    from PySide6.QtMultimediaWidgets import QVideoWidget
                    s.video = QVideoWidget(s); s.video.setAspectRatioMode(Qt.KeepAspectRatioByExpanding); s.vp = QMediaPlayer(); s.vp.setVideoOutput(s.video); s.vp.setLoops(-1)
                s.vp.setSource(QUrl.fromLocalFile(p)); s.video.setGeometry(s.rect()); s.video.show(); s.video.lower(); s.vp.play()
        s.clock.dim = bool(s.pix) or bool(s.video and s.video.isVisible()); s.update()
    def resizeEvent(s, e):
        if s.video: s.video.setGeometry(s.rect())
    def paintEvent(s, e):
        p = QPainter(s); p.fillRect(s.rect(), QColor(T["bg"]))
        if s.pix and not s.pix.isNull():
            sc = s.pix.scaled(s.size(), Qt.KeepAspectRatioByExpanding, Qt.SmoothTransformation); p.drawPixmap((s.width() - sc.width()) // 2, (s.height() - sc.height()) // 2, sc); p.fillRect(s.rect(), QColor(0, 0, 0, 90))
    def hideEvent(s, e):
        if s.video and s.video.isVisible() and s.vp: s.vp.pause()
    def showEvent(s, e):
        if s.video and s.video.isVisible() and s.vp: s.vp.play()
    # ── modos / relógio
    def set_mode(s, k):
        if k != s.mode and (s.running or s.elapsed): s.stop()
        s.mode = k; s.mb[k].setChecked(True)
        s.update_rows(); s.display()
    def update_rows(s):
        k = s.mode; lg = s.chk_long.isChecked()
        vis = {"timer": [s.sp_timer, s.pk_at], "pomodoro": [s.sp_study, s.sp_break, s.chk_long, s.sp_total, s.pk_as, s.pk_ab] + ([s.sp_long, s.sp_cyc] if lg else []), "stopwatch": []}
        for w in (s.sp_timer, s.sp_study, s.sp_break, s.sp_long, s.sp_cyc, s.chk_long, s.sp_total, s.pk_at, s.pk_as, s.pk_ab): s.form.setRowVisible(w, w in vis[k])
    def phase_len(s):
        c = s.d["settings"]
        if s.mode == "timer": return c["timer_min"] * 60
        if s.mode == "pomodoro": return {"study": c["pomo_study"], "break": c["pomo_break"], "long": c["pomo_long"]}[s.phase] * 60
        return 0
    def counts(s): return s.mode != "pomodoro" or s.phase == "study"
    def tick(s):
        if not s.running: return
        n = time.monotonic(); dd = n - s.last; s.last = n; s.elapsed += dd
        if s.counts(): s.logged += dd
        L = s.phase_len()
        if L and s.elapsed >= L: s.finish()
        s.display()
    def play_alarm(s, path): s.alarm.play(path if path and Path(path).exists() else RES / "sounds" / "alarm.mp3")
    def finish(s):
        c = s.d["settings"]
        if s.mode == "timer": s.running = False; s.log(); s.elapsed = 0; s.mp.pause(); s.bp.set_icon("play"); s.play_alarm(c["alarm_timer"])
        else:
            if s.phase == "study":
                s.log(); s.blocks_done += 1; tot = c["pomo_total"]
                if tot and s.blocks_done >= tot:   # terminou todos os blocos pedidos
                    s.running = False; s.play_alarm(c["alarm_study"]); s.mp.pause(); s.phase = "study"; s.cycle = 1; s.blocks_done = 0; s.elapsed = 0; s.bp.set_icon("play"); return
                s.play_alarm(c["alarm_study"]); s.mp.pause(); s.phase = "long" if (c["pomo_use_long"] and s.cycle % c["pomo_cycles"] == 0) else "break"
            else: s.play_alarm(c["alarm_break"]); s.cycle = 1 if s.phase == "long" else s.cycle + 1; s.phase = "study"; s.mp.resume()
            s.elapsed = 0
    def toggle(s):
        s.alarm.stop()
        if s.running: s.running = False; s.mp.pause()
        else:
            if s.mode == "timer" and s.elapsed >= s.phase_len(): s.elapsed = 0
            s.running = True; s.last = time.monotonic()
            if s.counts(): s.mp.resume()
        s.bp.set_icon("pause" if s.running else "play"); s.display()
    def stop(s):
        s.running = False; s.log(); s.elapsed = 0; s.phase = "study"; s.cycle = 1; s.blocks_done = 0; s.mp.pause(); s.alarm.stop(); s.bp.set_icon("play"); s.display()
    def log(s):
        if s.logged >= 30:
            start = dt.datetime.now() - dt.timedelta(seconds=s.logged)
            s.d["sessions"].append(dict(id=uid(), start=start.isoformat(timespec="minutes"), minutes=round(s.logged / 60, 2), mode=s.mode, subject=cbval(s.cb_sub), tag=cbval(s.cb_tag), desc=s.ed.text().strip()))
            s.cycle_hook(cbval(s.cb_sub)); s.st.save()
        s.logged = 0
    def cycle_hook(s, subject):
        """Cada bloco de foco salvo conta como uma sessão da matéria no ciclo ativo (se a opção do ciclo estiver ligada)."""
        cy = next((c for c in s.d["cycles"] if c["id"] == s.d["settings"].get("active_cycle")), None)
        if cy and cy.get("auto", True) and subject in cy["marks"] and mark_session(cy, subject) and cycle_complete(cy): advance_cycle(cy)
    def display(s):
        mmss = lambda v: f"{int(v) // 60:02d}:{int(v) % 60:02d}"
        if s.mode == "stopwatch":
            e = int(s.elapsed); h, r = divmod(e, 3600); m, sec = divmod(r, 60); txt = f"{h}:{m:02d}:{sec:02d}" if h else f"{m:02d}:{sec:02d}"
            frac = 1 if e == 0 else (s.elapsed % 60) / 60; sub = "cronômetro"; bell = False
        else:
            L = s.phase_len(); r = math.ceil(max(0, L - s.elapsed)); txt = mmss(r); frac = max(0, L - s.elapsed) / L; bell = True; sub = mmss(L)
            if s.mode == "pomodoro":
                c = s.d["settings"]; st = f"Estudo {s.blocks_done + 1}/{c['pomo_total']}" if c["pomo_total"] else (f"Estudo {s.cycle}/{c['pomo_cycles']}" if c["pomo_use_long"] else f"Estudo {s.cycle}")
                sub = {"study": st + "  ·  ", "break": "Descanso  ·  ", "long": "Descanso longo  ·  "}[s.phase] + sub
        s.clock.text, s.clock.frac, s.clock.sub, s.clock.bell = txt, frac, sub, bell; s.clock.update(); s.win.setWindowTitle(f"{txt} · Ômega" if s.running else "Ômega")
    def set_zen(s, on):
        s.zen = on
        for w in (s.top, s.ctl, s.info, s.pw): w.setVisible(not on)
        s.hint.setVisible(on); s.win.set_zen(on)
