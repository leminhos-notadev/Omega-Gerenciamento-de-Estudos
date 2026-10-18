#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ômega — gerenciamento de estudos."""
import sys
from omega_core import *
from pages_main import Home, FocusPage, MusicDialog
from pages_organize import Tasks, Syllabus, CalendarPage
from pages_plan import PlanPage, make_exams, make_essays, SettingsPage

NAV = [("chart", "Início"), ("timer", "Foco"), ("tasks", "Tarefas"), ("book", "Edital"), ("calendar", "Calendário"),
       ("cycle", "Cronograma / Ciclo"), ("doc", "Simulados"), ("pencil", "Redação"), ("gear", "Configurações")]

class Sidebar(QFrame):
    picked = Signal(int); W, STRIP = 104, 12
    def __init__(s, parent):
        super().__init__(parent); s.setFixedWidth(s.W); s.shown_ = False; s.pinned = False; LISTEN.add(s)
        l = QVBoxLayout(s); l.setContentsMargins(0, 22, 0, 18); l.setSpacing(12); s.logo = QLabel(); s.logo.setAlignment(Qt.AlignCenter); s.logo.setCursor(Qt.PointingHandCursor)
        s.logo.mousePressEvent = lambda e: s.picked.emit(0); l.addWidget(s.logo); l.addSpacing(6); s.btns = []; g = QButtonGroup(s); g.setExclusive(True)
        for i, (ic, name) in enumerate(NAV):
            b = IBtn(ic, 56, "dark", "", 26, True); b.navname = name; g.addButton(b); b.installEventFilter(s); b.clicked.connect(lambda _, i=i: s.picked.emit(i)); l.addWidget(b, 0, Qt.AlignHCenter); s.btns.append(b)
        l.addStretch(); s.tip = QLabel(parent); s.tip.hide(); s.anim = QPropertyAnimation(s, b"pos"); s.anim.setDuration(160); s.retheme()
    def retheme(s):
        s.logo.setPixmap(logo_pix(T["accent"], 46)); s.tip.setStyleSheet(f"background:{T['card']};color:{T['text']};border:1px solid {T['line']};border-radius:17px;padding:7px 18px;font-size:14px;font-weight:600"); s.update()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHint(QPainter.Antialiasing); p.setBrush(QColor(T["side"])); p.setPen(Qt.NoPen); p.drawRoundedRect(QRectF(-40, 0, s.width() + 40, s.height()), 26, 26)
    def eventFilter(s, o, ev):
        if ev.type() == QEvent.Enter and hasattr(o, "navname"):
            s.tip.setText(o.navname); s.tip.adjustSize(); pt = o.mapTo(s.parentWidget(), QPoint(0, 0)); s.tip.move(s.x() + s.W + 6, pt.y() + (o.height() - s.tip.height()) // 2); s.tip.show(); s.tip.raise_()
        elif ev.type() == QEvent.Leave and hasattr(o, "navname"): s.tip.hide()
        return False
    def go(s, v):
        s.shown_ = v or s.pinned; s.anim.stop(); s.anim.setEndValue(QPoint(0 if s.shown_ else -(s.W - s.STRIP), 0)); s.anim.start()
        if not s.shown_: s.tip.hide()
    def place(s, h): s.setFixedHeight(h); s.move(0 if (s.shown_ or s.pinned) else -(s.W - s.STRIP), 0)
    def enterEvent(s, e): s.go(True)
    def leaveEvent(s, e): s.go(False)

class Main(QMainWindow):
    def __init__(s, store):
        super().__init__(); s.store = store; s.zen = False; s.music = MusicPlayer(); s.setWindowTitle("Ômega"); s.setWindowIcon(QIcon(str(RES / "icon.png"))); s.resize(1366, 768); s.setMinimumSize(1100, 700)
        c = QWidget(); s.setCentralWidget(c); lay = QHBoxLayout(c); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0); s.pad = QWidget(); s.pad.setFixedWidth(0); lay.addWidget(s.pad); s.stack = QStackedWidget(); lay.addWidget(s.stack, 1)
        s.focus = FocusPage(s); pages = [Home(s), s.focus, Tasks(s), Syllabus(s), CalendarPage(s), PlanPage(s), make_exams(s), make_essays(s), SettingsPage(s)]
        s.items = [(ic, n, p) for (ic, n), p in zip(NAV, pages)]
        for p in pages: s.stack.addWidget(p)
        s.sidebar = Sidebar(c); s.sidebar.picked.connect(s.go); s.sidebar.raise_(); s.apply_pin()
        QShortcut(QKeySequence("Esc"), s, activated=lambda: s.focus.set_zen(False) if s.zen else None); QShortcut(QKeySequence("Space"), s, activated=lambda: s.focus.toggle() if s.zen else None)
        QShortcut(QKeySequence("F11"), s, activated=lambda: s.showNormal() if s.isFullScreen() else s.showFullScreen())
        s.pt = QTimer(s); s.pt.setInterval(60000); s.pt.timeout.connect(lambda: s.store.pull() and s.refresh_all()); s.pt.start(); s.go(0)
    def go(s, i): s.stack.setCurrentIndex(i); s.items[i][2].refresh(); s.sidebar.btns[i].setChecked(True)
    def refresh_all(s): s.focus.load_cfg(); s.apply_theme(); s.apply_pin()
    def apply_theme(s):
        c = s.store.data["settings"]; apply_theme(QApplication.instance(), c["mode"], c["accent"]); s.items[s.stack.currentIndex()][2].refresh()
    def apply_pin(s):
        pin = s.store.data["settings"]["pin"]; s.sidebar.pinned = pin; s.pad.setFixedWidth(Sidebar.W if pin and not s.zen else 0); s.sidebar.go(pin)
    def set_zen(s, on): s.zen = on; s.sidebar.setVisible(not on); s.pad.setFixedWidth(Sidebar.W if s.sidebar.pinned and not on else 0)
    def resizeEvent(s, e): super().resizeEvent(e); s.sidebar.place(s.centralWidget().height()); s.sidebar.raise_()
    def closeEvent(s, e): s.focus.stop(); s.store.save(); super().closeEvent(e)

class Intro(QWidget):
    def __init__(s, done):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint); s.done = done; s.fin = False; s.t = 0.0; s.setFixedSize(1000, 563); s.setWindowIcon(QIcon(str(RES / "icon.png")))
        g = s.screen().availableGeometry(); s.move(g.center() - QPoint(500, 281)); s.snd = Sound(); s.snd.play(RES / "sounds" / "intro.mp3")
        s.anim = QVariantAnimation(s); s.anim.setDuration(7000); s.anim.setStartValue(0.0); s.anim.setEndValue(1.0); s.anim.valueChanged.connect(lambda v: (setattr(s, "t", v), s.update())); s.anim.finished.connect(s.finish); s.anim.start()
    def finish(s):
        if s.fin: return
        s.fin = True; s.anim.stop(); s.snd.stop(); s.close(); s.done()
    def mousePressEvent(s, e): s.finish()
    def keyPressEvent(s, e): s.finish()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform); w, h = s.width(), s.height(); t = s.t; p.fillRect(s.rect(), QColor(T["bg"]))
        cl = lambda x: max(0.0, min(1.0, x)); ease = lambda x: 1 - (1 - x) ** 3; fade = cl((1 - t) / .14)
        a1 = ease(cl(t / .2)) * fade; lh = int(h * .40); lg = logo_pix(T["accent"], lh); lw = lg.width() / lg.devicePixelRatio(); sc = .92 + .08 * ease(cl(t / .3))
        p.save(); p.translate(w / 2, h * .38); p.scale(sc, sc); p.setOpacity(a1); p.drawPixmap(QPointF(-lw / 2, -lh / 2), lg); p.restore()
        a2 = ease(cl((t - .12) / .2)) * fade; f = QFont("Poppins"); f.setWeight(QFont.Bold); f.setPixelSize(int(h * .09)); p.setFont(f); p.setOpacity(a2); p.setPen(QColor(T["text"]))
        p.drawText(QRectF(0, h * .66 + 14 * (1 - a2), w, h * .12), Qt.AlignCenter, "OMEGA")
        a3 = ease(cl((t - .24) / .2)) * fade; f.setPixelSize(int(h * .045)); p.setFont(f); p.setOpacity(a3); p.setPen(QColor(T["muted"])); p.drawText(QRectF(0, h * .79 + 10 * (1 - a3), w, h * .08), Qt.AlignCenter, "Gerenciamento de Estudos")

def main():
    app = QApplication(sys.argv); app.setApplicationName("Ômega"); app.setWindowIcon(QIcon(str(RES / "icon.png")))
    for f in (RES / "fonts").glob("*.ttf"): QFontDatabase.addApplicationFont(str(f))
    app.setStyle("Fusion"); app.setFont(QFont("Poppins", 10)); store = Store(); c = store.data["settings"]; apply_theme(app, c["mode"], c["accent"]); win = Main(store)
    if "--selftest" in sys.argv: return selftest(app, win, store)
    show = (lambda: win.showFullScreen()) if c.get("fullscreen", True) else (lambda: win.show())
    if c.get("intro", True) and "--no-intro" not in sys.argv: intro = Intro(show); intro.show()
    else: show()
    sys.exit(app.exec())

def selftest(app, win, store):
    from pages_organize import EventDialog; from pages_plan import BlockDialog
    d = store.data; t = iso(today()); shots = os.environ.get("OMEGA_SHOTS")
    assert d["subjects"] == [] and d["tags"] == [], "deve iniciar sem matérias/tags"
    d["subjects"] += ["Matemática", "Português", "Inglês", "Física"]; d["tags"] += ["Teoria", "Revisão"]
    for i in range(14): d["sessions"].append(dict(id=f"s{i}", start=iso(today() - dt.timedelta(days=i)) + "T10:00", minutes=30 + i * 9, mode="timer", subject=["Matemática", "Português", "Física"][i % 3], tag="Teoria", desc="x"))
    d["lists"][0]["tasks"] += [dict(id="t1", title="Resolver lista de funções", subject="Matemática", tag="", due=t, desc="", done=True, files=[], subtasks=[dict(id="u1", title="Subtarefa 1", done=False, subtasks=[], subject="", tag="", due="", desc="", files=[])], created=t + "T10:00"),
                               dict(id="t2", title="Revisar redação", subject="", tag="", due="", desc="", done=False, files=[], subtasks=[], created=t + "T10:00")]
    d["events"].append(dict(id="e", title="Novo Evento", date=t, time="09:00", subject="", tag="", desc="", files=[])); d["exams"] += [dict(id="x1", date=t, type="ENEM", hits=60, total=90, file="", notes="ok"), dict(id="x2", date="2026-09-01", type="ENEM", hits=50, total=90, file="", notes="")]
    d["essays"].append(dict(id="y", date=t, theme="Tema", texts="", grade=840.0, file="", notes="bom")); d["syllabus"]["Matemática"] = {"red": ["Funções"], "yellow": [], "green": ["Geometria", "Álgebra"]}
    d["schedules"][0]["blocks"] += [dict(id="b1", title="Novo Bloco", day=1, start="09:00", end="10:00", subject="Matemática", tag="", desc=""), dict(id="b2", title="Redação", day=3, start="14:00", end="16:00", subject="", tag="", desc="")]
    items = [dict(subject=n, dif=a, cont=b, peso=c, n=max(1, round(a * b * c / 125 * 40))) for n, a, b, c in (("Matemática", 4, 4, 5), ("Português", 3, 3, 3), ("Inglês", 2, 2, 2))]
    d["cycles"].append(dict(id="c1", name="Ciclo", number=1, items=items, marks={i["subject"]: [j < 3 for j in range(i["n"])] for i in items}, history=[]))
    snd = HOME / "t.mp3"; snd.write_bytes((RES / "sounds" / "alarm.mp3").read_bytes()); d["library"] += [dict(id="m1", title="Tek It", path=str(snd))]; d["playlists"].append(dict(id="p1", name="Foco", tracks=["m1"]))
    win.show(); app.processEvents()
    def shot(name):
        app.processEvents()
        if shots: Path(shots).mkdir(exist_ok=True); win.grab().save(f"{shots}/{name}.png")
    win.music.set_queue(d["library"]); win.focus.music_ui()
    d["settings"]["plan_mode"] = "schedule"
    for i, (_, n, _) in enumerate(win.items): win.go(i); shot(f"{i}_{n.split()[0]}")
    # --- v3: ciclo (sequência, marcação sem rebuild, conclusão), tarefas (ordem), playlist (ordem/aleatório), pomodoro sem pausa longa
    from omega_core import cycle_order, mark_session, cycle_complete
    cy = d["cycles"][0]; seq = cycle_order(cy); assert seq and seq[0] != seq[1], seq[:4]
    d["settings"]["plan_mode"] = "cycle"; win.go(5); pp = win.items[5][2]; cv = pp.cv; cards_before = [cv.cards.itemAt(i).widget() for i in range(cv.cards.count())]
    cv.grids["Matemática"].marks[5] = True; cv.grids["Matemática"].changed.emit(); assert [cv.cards.itemAt(i).widget() for i in range(cv.cards.count())] == cards_before, "cartões foram recriados"
    cv.do_next(); shot("5b_ciclo")
    for n in list(cy["marks"]): cy["marks"][n] = [True] * len(cy["marks"][n])
    cy["marks"]["Inglês"][-1] = False; d["settings"]["active_cycle"] = cy["id"]; f0 = win.focus; f0.cb_sub.setCurrentText("Inglês"); f0.logged = 120; f0.log(); assert cy["number"] == 2 and not cycle_complete(cy), "hook do ciclo"
    tk = win.items[2][2]; win.go(2); l = tk.cur(); l["tasks"] += [tk.mk("Terceira"), tk.mk("Quarta")]; ids = [x["id"] for x in l["tasks"]]; tk.reorder(ids[-1], 0); assert l["tasks"][0]["id"] == ids[-1]; tk.sel = ids[0]; tk.move(1); tk.build(); shot("2b_tarefas_ordem")
    pl = d["playlists"][0]; d["library"] += [dict(id="m2", title="Outra", path=str(HOME / "t.mp3")), dict(id="m3", title="Terceira", path=str(HOME / "t.mp3"))]; pl["tracks"] = ["m1", "m2", "m3"]
    from pages_main import PlaylistDialog, play_shuffled, VolumePopup; pd = PlaylistDialog(win, win, pl); pd.show(); pd.lw.setCurrentRow(2); pd.lw.item(2).setSelected(True); pd.move(-1); assert pl["tracks"] == ["m1", "m3", "m2"]; pd.play(True); pd.play(False); app.processEvents(); (pd.grab().save(f"{shots}/dlg_playlist.png") if shots else None); pd.close()
    win.go(1); win.focus.on_progress(65000, 200000); vp = VolumePopup(win); vp.popup(win.focus.bvol); vp.sl.setValue(0); assert win.focus.bvol.name == "mute"; vp.sl.setValue(40); vp.hide(); vp.sl.setValue(0)
    f = win.focus; f.chk_long.setChecked(False); f.set_mode("pomodoro"); d["settings"]["pomo_total"] = 2; f.toggle(); f.cycle = 2; f.elapsed = 1e5; f.tick(); assert f.phase == "break", f.phase; f.elapsed = 1e5; f.tick(); f.elapsed = 1e5; f.tick(); assert not f.running and f.blocks_done == 0
    f.chk_long.setChecked(True); d["settings"]["pomo_total"] = 0; f.set_mode("timer"); shot("1d_player"); f.stop()
    d["settings"]["plan_mode"] = "cycle"; win.go(5); shot("5b_ciclo"); win.items[5][2].creating = True; win.items[5][2].load(); shot("5c_ciclo_criar"); win.items[5][2].creating = False; d["settings"]["plan_mode"] = "schedule"
    win.go(0); win.items[0][2].tab(1); shot("0b_simulados"); win.items[0][2].tab(2); win.items[0][2].tab(0); win.items[0][2].study.bl.click(); win.items[0][2].study.stack.setCurrentIndex(1); shot("0c_blocos")
    win.go(1); f = win.focus; f.set_mode("pomodoro"); f.toggle(); f.elapsed = 1e4; f.tick(); f.set_mode("stopwatch"); f.set_mode("timer"); shot("1b_foco_rodando"); f.set_zen(True); shot("1c_zen"); f.set_zen(False); f.stop()
    EventDialog(win, win, d["events"][0], t).result(); BlockDialog(win, win, d["schedules"][0]["blocks"][0], 0, 0).result(); md = MusicDialog(win, win); md.show(); md.play_pl(md.pls.item(0)); md.play_track(md.lib.item(0)); win.music.toggle(); win.music.next(1)
    ed = EventDialog(win, win, None, t); ed.show(); app.processEvents(); (ed.grab().save(f"{shots}/dlg_evento.png") if shots else None); bd = BlockDialog(win, win, None, 2, 9); bd.show(); app.processEvents(); (bd.grab().save(f"{shots}/dlg_bloco.png") if shots else None); (md.grab().save(f"{shots}/dlg_musica.png") if shots else None)
    ed.close(); bd.close(); md.close()
    for mode, ac in (("light", "Amarelo"), ("dark", "Rosa"), ("dark", "Roxo")):
        d["settings"]["mode"], d["settings"]["accent"] = mode, ac; win.apply_theme()
        if mode == "light":
            for i in (0, 1, 2, 4): win.go(i); shot(f"L{i}")
    d["settings"]["pin"] = True; win.apply_pin(); app.processEvents(); shot("pinned"); d["settings"]["pin"] = False; win.apply_pin()
    it = Intro(lambda: None); it.show(); it.t = .5; it.repaint(); (it.grab().save(f"{shots}/intro.png") if shots else None); it.finish(); win.grab(); print("SELFTEST OK")

if __name__ == "__main__":
    main()
