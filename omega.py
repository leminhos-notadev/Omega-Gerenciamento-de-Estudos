#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Ômega — gerenciamento de estudos."""
import sys
from omega_core import *
from pages_main import Home, FocusPage, MusicDialog
from pages_organize import Tasks, Syllabus, CalendarPage
from pages_plan import PlanPage, make_exams, make_essays, SettingsPage

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
        super().__init__(); s.store = store; s.zen = False; s.music = MusicPlayer(); s.setWindowTitle("Ômega"); s.resize(1366, 768); s.setMinimumSize(1100, 700)
        c = QWidget(); s.setCentralWidget(c); lay = QHBoxLayout(c); lay.setContentsMargins(0, 0, 0, 0); lay.setSpacing(0); s.pad = QWidget(); s.pad.setFixedWidth(0); lay.addWidget(s.pad); s.stack = QStackedWidget(); lay.addWidget(s.stack, 1)
        s.focus = FocusPage(s); pages = [Home(s), s.focus, Tasks(s), Syllabus(s), CalendarPage(s), PlanPage(s), make_exams(s), make_essays(s), SettingsPage(s)]
        s.items = [(ic, n, p) for (ic, n), p in zip(NAV, pages)]
        for p in pages: s.stack.addWidget(p)
        s.sidebar = Sidebar(c); s.sidebar.picked.connect(s.go); s.sidebar.raise_(); s.apply_pin(); s.focus.recover()
        QShortcut(QKeySequence("Esc"), s, activated=lambda: s.focus.set_zen(False) if s.zen else None); QShortcut(QKeySequence("Space"), s, activated=lambda: s.focus.toggle() if s.zen else None)
        [QShortcut(QKeySequence(k), s, activated=lambda n=n: s.page_shortcut(n)) for n, k in (("copy", "Ctrl+C"), ("cut", "Ctrl+X"), ("paste", "Ctrl+V"), ("delete", "Del"))]
        QShortcut(QKeySequence("F11"), s, activated=lambda: s.showNormal() if s.isFullScreen() else s.showFullScreen())
        s.pt = QTimer(s); s.pt.setInterval(60000); s.pt.timeout.connect(lambda: s.store.pull() and s.refresh_all()); s.pt.start(); s.apply_tabs(); s.go(s.first_visible())
    def streak_check(s, show=True, day=None):
        """Soma 1 ao streak quando o dia atinge STREAK_MIN minutos de foco (chamado ao terminar uma sessão)."""
        d = s.store.data; day = day or today()
        if focus_minutes_on(d, day) >= STREAK_MIN and streak_add_day(d, day):
            s.store.save()
            if s.stack.currentIndex() == 0: s.items[0][2].refresh()
            if show: s.streak_ui = StreakOverlay(s, streak_current(d))
            return True
        return False
    def page_shortcut(s, name):
        p = s.items[s.stack.currentIndex()][2]
        if hasattr(p, "on_shortcut"): p.on_shortcut(name)
    def hidden(s, n): return n in s.store.data["settings"]["hidden_tabs"] and n != "Configurações"
    def first_visible(s): return next((i for i, (_, n) in enumerate(NAV) if not s.hidden(n)), len(NAV) - 1)
    def apply_tabs(s):
        for i, b in enumerate(s.sidebar.btns): b.setVisible(not s.hidden(NAV[i][1]))
        if s.hidden(NAV[s.stack.currentIndex()][1]): s.go(s.first_visible())
    def wipe_all(s):
        """Apaga tudo (inclusive o arquivo sincronizado) e volta ao estado de primeira abertura."""
        f = s.focus; f.running = False; f.pending = False; f.elapsed = 0; f.logged = 0; f.live_id = None; f.phase = "study"; f.cycle = 1; f.blocks_done = 0; s.music.pause(); s.music.queue = []; s.music.i = -1; s.music.changed.emit()
        s.store.data = fresh(); s.store.save(); s.focus.load_cfg(); s.apply_theme(); s.apply_pin(); s.apply_tabs(); s.focus.display(); s.go(s.first_visible())
    def go(s, i): s.stack.setCurrentIndex(i); s.items[i][2].refresh(); s.sidebar.btns[i].setChecked(True)
    def refresh_all(s): s.focus.load_cfg(); s.apply_theme(); s.apply_pin(); s.apply_tabs()
    def apply_theme(s):
        c = s.store.data["settings"]; apply_theme(QApplication.instance(), c["mode"], c["accent"]); s.setWindowIcon(QApplication.windowIcon()); s.items[s.stack.currentIndex()][2].refresh()
    def apply_pin(s):
        pin = s.store.data["settings"]["pin"]; s.sidebar.pinned = pin; s.pad.setFixedWidth(Sidebar.W if pin and not s.zen else 0); s.sidebar.go(pin)
    def set_zen(s, on): s.zen = on; s.sidebar.setVisible(not on); s.pad.setFixedWidth(Sidebar.W if s.sidebar.pinned and not on else 0)
    def resizeEvent(s, e): super().resizeEvent(e); s.sidebar.place(s.centralWidget().height()); s.sidebar.raise_()
    def closeEvent(s, e): s.focus.stop(); s.store.save(); super().closeEvent(e)

class StreakOverlay(QWidget):
    """Tela que aparece ao terminar a sessão que fecha o dia no streak (chama + dias seguidos)."""
    def __init__(s, win, n):
        super().__init__(win); s.n = n; s.t = 0.0; s.setGeometry(win.rect()); s.setFocusPolicy(Qt.StrongFocus); s.raise_(); s.show(); s.setFocus()
        s.anim = QVariantAnimation(s); s.anim.setDuration(1100); s.anim.setStartValue(0.0); s.anim.setEndValue(1.0); s.anim.valueChanged.connect(lambda v: (setattr(s, "t", v), s.update())); s.anim.start(); QTimer.singleShot(7000, s.dismiss)
    def dismiss(s):
        if s.isVisible(): s.hide(); s.deleteLater()
    def mousePressEvent(s, e): s.dismiss()
    def keyPressEvent(s, e): s.dismiss()
    def paintEvent(s, e):
        p = QPainter(s); p.setRenderHints(QPainter.Antialiasing | QPainter.TextAntialiasing | QPainter.SmoothPixmapTransform); w, h = s.width(), s.height(); t = s.t; p.fillRect(s.rect(), QColor(T["bg"]))
        cl = lambda x: max(0.0, min(1.0, x)); ease = lambda x: 1 - (1 - x) ** 3; a = ease(cl(t / .45)); back = 1 + 1.9 * (cl(t / .7) - 1) ** 3 + 0.9 * (cl(t / .7) - 1) ** 2   # leve "pulo" na entrada
        size = int(min(w, h) * .34); pm = flame_pix(size, s.n); pw = pm.width() / pm.devicePixelRatio(); cx, cy = w / 2, h * .38
        p.setOpacity(a); p.save(); p.translate(cx, cy); sc = max(.2, .55 + .45 * back); p.scale(sc, sc); p.drawPixmap(QPointF(-pw / 2, -pw / 2), pm); p.restore()
        for dx, dy, k, rot in ((-.62, -.5, .09, 20), (.7, -.3, .06, -15), (-.78, .35, .05, 8), (.58, .52, .07, 30)):   # losangos decorativos
            p.save(); p.translate(cx + dx * size, cy + dy * size); p.rotate(45 + rot); r = size * k; c = QColor("#ffc27a"); c.setAlpha(int(200 * a)); p.setBrush(c); p.setPen(Qt.NoPen); p.drawRoundedRect(QRectF(-r, -r, 2 * r, 2 * r), r * .25, r * .25); p.restore()
        f = QFont("Poppins"); f.setWeight(QFont.Bold); f.setPixelSize(int(h * .05)); p.setFont(f); p.setPen(QColor(T["text"])); ty = cy + size * .62
        p.setOpacity(ease(cl((t - .25) / .4))); p.drawText(QRectF(0, ty, w, h * .09), Qt.AlignHCenter | Qt.AlignVCenter, "Dias seguidos!")
        f.setWeight(QFont.Light); f.setPixelSize(int(h * .036)); p.setFont(f); p.setOpacity(ease(cl((t - .4) / .4))); p.drawText(QRectF(0, ty + h * .09, w, h * .07), Qt.AlignHCenter | Qt.AlignVCenter, "Continue mantendo os bons hábitos")
        f.setPixelSize(int(h * .022)); p.setFont(f); p.setPen(QColor(T["muted"])); p.setOpacity(ease(cl((t - .7) / .3))); p.drawText(QRectF(0, h * .93, w, h * .05), Qt.AlignHCenter | Qt.AlignVCenter, "clique para continuar")

class Intro(QWidget):
    def __init__(s, done):
        super().__init__(None, Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint); s.done = done; s.fin = False; s.t = 0.0; s.snd = Sound(); s.snd.play(RES / "sounds" / "intro.mp3")
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
    if "--version" in sys.argv: print(f"Omega {VERSION}\nArquivos em: {Path(__file__).resolve().parent}"); return
    app = QApplication(sys.argv); app.setApplicationName("Ômega")
    for f in (RES / "fonts").glob("*.ttf"): QFontDatabase.addApplicationFont(str(f))
    app.setStyle("Fusion"); app.setFont(QFont("Poppins", 10)); store = Store(); c = store.data["settings"]; apply_theme(app, c["mode"], c["accent"]); win = Main(store)
    if "--selftest" in sys.argv: return selftest(app, win, store)
    show = (lambda: win.showFullScreen()) if c.get("fullscreen", True) else (lambda: win.show())
    if c.get("intro", True) and "--no-intro" not in sys.argv: intro = Intro(show); intro.showFullScreen()
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
        try:
            if getattr(win, "streak_ui", None) and win.streak_ui.isVisible() and not name.startswith("streak"): win.streak_ui.dismiss()
        except RuntimeError: pass
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
    tk = win.items[2][2]; win.go(2); tk.cb.setCurrentIndex(tk.off()); tk.on_list(); l = tk.cur(); l["tasks"] += [tk.mk("Terceira"), tk.mk("Quarta")]; ids = [x["id"] for x in l["tasks"]]; tk.reorder(ids[-1], 0); assert l["tasks"][0]["id"] == ids[-1]; tk.sel = ids[0]; tk.move(1); tk.build(); shot("2b_tarefas_ordem")
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
    # --- v4
    from omega_core import url_at, period_buckets
    assert url_at("veja https://exemplo.com/a?b=1, ok", 10) == "https://exemplo.com/a?b=1" and url_at("www.x.com", 2) == "https://www.x.com" and url_at("sem link", 2) is None
    for per in PERIODS:
        for off in (0, 1, 3): lab, bk, a0, b0 = period_buckets(per, off); assert bk and a0 < b0 and bk[0][1] == a0 and bk[-1][2] == b0, (per, off)
    assert [len(period_buckets(p, 0)[1]) for p in ("Dia", "Semana", "Ano", "Total")] == [24, 7, 12, 6]
    d["colors"]["subjects"].update({"Matemática": "#ff5a5f", "Português": "#4a7cff"}); d["colors"]["tags"]["Teoria"] = "#7fd957"; d["events"][0]["color"] = "#4a7cff"
    d["events"].append(dict(id="e2", title="Prova de Matemática", date=t, time="14:00", subject="Matemática", tag="", desc="veja https://exemplo.com", files=[]))
    win.go(4); shot("4b_calendario_cores"); win.go(5); shot("5d_cronograma_cores")
    sv = win.items[0][2].study; win.go(0)
    for i, per in enumerate(PERIODS): sv.cb_per.setCurrentIndex(i); sv.refresh(); shot(f"0p_{per}")
    sv.cb_per.setCurrentIndex(0); sv.refresh()
    tk = win.items[2][2]; win.go(2); l0 = d["lists"][0]; tk.refresh(); tk.cb.setCurrentIndex(1 if tk.off() else 0); tk.on_list(); act = [x for x in l0["tasks"] if not x["done"]]; tk.sel = act[0]["id"]; tk.toggle_myday(); assert act[0]["id"] in d["myday"]
    tk.cb.setCurrentIndex(0); tk.on_list(); assert tk.is_md(); tk.new.setText("Tarefa do Meu Dia"); tk.add(); assert d["myday"][-1] in [x["id"] for x in d["myday_own"]] and d["myday"][-1] not in [x["id"] for l in d["lists"] for x in l["tasks"]]; shot("2c_meudia")
    d["lists"].append(dict(id="l2", name="Outra lista", tasks=[])); tk.refresh(); tk.goto(act[0]["id"]); tk.load_detail(); tk.move_to_list(d["lists"][1]); assert act[0] in d["lists"][1]["tasks"] and act[0] not in d["lists"][0]["tasks"]
    sb = dict(id="sbx", title="sub", done=False, subtasks=[]); tk2 = d["lists"][0]["tasks"][0]; tk2["subtasks"].append(sb); le = QLineEdit("Nome novo"); tk.rename_sub(sb, le); assert sb["title"] == "Nome novo"
    tk.cb.setCurrentIndex(tk.off()); tk.on_list(); tk.sel = tk2["id"]; tk.build(); d["settings"]["done_open"][d["lists"][0]["id"]] = True; tk.build(); shot("2d_concluidas")
    d["settings"]["hide_myday"] = True; tk.refresh(); assert tk.cb.itemText(0) != "Meu Dia" and not tk.is_md(); d["settings"]["hide_myday"] = False; tk.refresh()
    f = win.focus; win.go(1); f.stop(); f.set_mode("pomodoro"); f.toggle(); f.elapsed = 30; f.logged = 130; f.set_mode("stopwatch"); f.display(); assert f.running and f.am == "pomodoro" and f.banner.isVisibleTo(f); shot("1e_bloco_outro_modo")
    f.autosave(); rec = f.live_rec(); assert rec and rec.get("live") and rec["minutes"] > 2; f.toggle(); assert f.am == "stopwatch" and f.live_id is None and not rec.get("live") and rec["minutes"] > 2 and rec in d["sessions"]
    f.stop(); d["settings"]["pomo_manual"] = True; f.set_mode("pomodoro"); f.toggle(); f.elapsed = 1e5; f.logged = 100; f.tick(); assert not f.running and f.pending and f.phase == "break"; f.display(); shot("1f_pomodoro_manual"); f.toggle(); assert f.running and not f.pending
    f.stop(); d["settings"]["pomo_manual"] = False; d["sessions"].append(dict(id="lv", start=t + "T08:00", minutes=5, mode="timer", subject="", tag="", desc="", live=True)); f.recover(); assert not any(x.get("live") for x in d["sessions"])
    f.cycle_loop(); assert win.music.loop == "one" and f.bloop.name == "repeat1"; f.cycle_loop(); assert win.music.loop == "off"; f.cycle_loop(); assert win.music.loop == "all"; win.music.set_queue([dict(id="m", title="Um título de música extremamente longo para testar as reticências no final do nome", path=str(HOME / "t.mp3"))]); f.music_ui(); shot("1g_player_longo")
    d["settings"]["hidden_tabs"] = ["Edital", "Redação"]; win.apply_tabs(); assert not win.sidebar.btns[3].isVisibleTo(win.sidebar) and win.sidebar.btns[8].isVisibleTo(win.sidebar); d["settings"]["hidden_tabs"] = []; win.apply_tabs()
    from omega_core import app_icon; assert not app_icon().isNull()
    # --- v1.2.0
    from omega_core import cycle_blocks, streak_current, exam_subject_metric; from pages_plan import ExamDialog, ExamTypesDialog, ExamsPage
    assert cycle_blocks([("a", 4, 0, 4.5), ("b", 3, 0, 4.5), ("c", 4, 0, 4.5), ("d", 4, 0, 5), ("e", 5, 0, 5), ("f", 4, 0, 5), ("g", 5, 0, 5)], 50) == [7, 5, 6, 7, 9, 7, 9]   # planilha CICLO ITA
    QInputDialog.getText = staticmethod(lambda *a, **k: ("Ciclo ITA", True)); win.go(5); pp = win.items[5][2]; d["settings"]["plan_mode"] = "cycle"; pp.refresh(); pp.creating = True; pp.load(); cv = pp.cv
    for n, vals in zip(d["subjects"], ((4, 3, 4.5), (3, 2, 4.5), (5, 5, 5), (0, 0, 0))):
        for q, v in zip(cv.spins[n], vals): q.setValue(v)
    cv.total.setValue(50); cv.recalc(); got = [cv.res[n].text() for n in d["subjects"]]; assert got[-1] == "–" and sum(int(x) for x in got[:-1]) == 50, got; shot("5e_ciclo_ita"); cv.create(); cyc = d["cycles"][-1]; assert sum(i["n"] for i in cyc["items"]) == 50 and cyc["total"] == 50
    pp.creating = False; d["settings"]["plan_mode"] = "schedule"; pp.refresh()
    # calendário: arrastar, copiar, recortar, colar
    cp = win.items[4][2]; win.go(4); ev0 = d["events"][0]; cp.select_ev(ev0["id"]); other = iso(today() + dt.timedelta(days=2)); cp.move_event(ev0["id"], other); app.processEvents(); assert ev0["date"] == other
    cp.refresh(); cp.on_shortcut("copy"); cp.hover = iso(today() + dt.timedelta(days=3)); n0 = len(d["events"]); cp.on_shortcut("paste"); assert len(d["events"]) == n0 + 1 and d["events"][-1]["date"] == cp.hover and d["events"][-1]["title"] == ev0["title"]
    cp.on_shortcut("cut"); assert len(d["events"]) == n0; cp.hover = iso(today()); cp.on_shortcut("paste"); assert d["events"][-1]["date"] == iso(today()); shot("4c_calendario_dnd")
    # cronograma: mover, copiar/colar no horário do mouse
    win.go(5); sv = win.items[5][2].sv; sv.load(d["schedules"][0]); b0 = d["schedules"][0]["blocks"][0]; sv.grid.sel = b0["id"]; sv.move_block(b0["id"], 4, 13 * 60 + 30); assert (b0["day"], b0["start"], b0["end"]) == (4, "13:30", "14:30")
    sv.on_shortcut("copy"); sv.grid.hover = (2, 8 * 60 + 15); nb = len(d["schedules"][0]["blocks"]); sv.on_shortcut("paste"); last = d["schedules"][0]["blocks"][-1]; assert len(d["schedules"][0]["blocks"]) == nb + 1 and (last["day"], last["start"], last["end"]) == (2, "08:15", "09:15"); shot("5f_cronograma_dnd")
    # simulados: tipos e nota por matéria
    d["exam_types"].append(dict(id="et1", name="Meu Simulado", subjects=[dict(name="Matemática", n=20, local=False), dict(name="Interpretação (só deste tipo)", n=10, local=True)]))
    assert "Interpretação (só deste tipo)" not in d["subjects"]; dlg = ExamDialog(win, win, None); dlg.tp.setCurrentIndex(1); dlg.spins["Matemática"][0].setValue(15); dlg.spins["Interpretação (só deste tipo)"][0].setValue(6); v = dlg.values()
    assert v["hits"] == 21 and v["total"] == 30 and v["scores"]["Matemática"] == 15 and exam_subject_metric(v, "Matemática") == 75; d["exams"].append(dict(v, id="x9")); et = ExamTypesDialog(win, win); et.show(); et.lw.setCurrentRow(0); app.processEvents(); (et.grab().save(f"{shots}/dlg_tipos_prova.png") if shots else None); et.close()
    win.go(6); win.items[6][2].refresh(); win.go(0); hm_ = win.items[0][2]; hm_.tab(1); rs = hm_.ex; rs.refresh(); rs.cb_t.setCurrentIndex(rs.cb_t.findText("Meu Simulado")); rs.refresh(); rs.cb_s.setCurrentIndex(rs.cb_s.findText("Matemática")); rs.refresh(); assert rs.legend.items and "Matemática" in rs.legend.items[-2][1] + rs.legend.items[-1][1]; shot("0e_simulados_materia"); hm_.tab(0)
    # estatísticas: Total + legenda por tag
    sv_ = hm_.study; assert [sv_.cb_per.itemText(i) for i in range(sv_.cb_per.count())] == ["Dia", "Semana", "Mês", "Ano", "Total"]; sv_.cb_per.setCurrentIndex(4); sv_.refresh(); sv_.bg.click(); shot("0f_total"); assert len(sv_.legend.items) >= 2 and sv_.legend.items[0][1].startswith("Tempo total")
    # streak
    d["streak"] = {"count": 0, "last": "", "best": 0}; d["sessions"].append(dict(id="lv2", start=iso(today() - dt.timedelta(days=1)) + "T20:00", minutes=12, mode="timer", subject="", tag="", desc="", live=True)); win.focus.recover(); assert d["streak"]["count"] == 1 and d["streak"]["last"] == iso(today() - dt.timedelta(days=1))
    win.focus.logged = 700; win.focus.log(); assert d["streak"]["count"] == 2 and streak_current(d) == 2 and win.streak_ui.isVisible(); app.processEvents(); (win.grab().save(f"{shots}/streak.png") if shots else None); win.streak_ui.anim.setCurrentTime(1100); win.streak_ui.update(); app.processEvents(); (win.grab().save(f"{shots}/streak2.png") if shots else None); win.streak_ui.dismiss()
    win.focus.logged = 700; win.focus.log(); assert d["streak"]["count"] == 2; win.go(0); shot("0g_streak_home")
    d["settings"]["hidden_tabs"] = ["Configurações", "Edital"]; from omega_core import merge as _m; assert "Configurações" not in _m(d)["settings"]["hidden_tabs"]; assert not win.hidden("Configurações")
    for mode, ac in (("light", "Amarelo"), ("dark", "Rosa"), ("dark", "Roxo")):
        d["settings"]["mode"], d["settings"]["accent"] = mode, ac; win.apply_theme()
        if mode == "light":
            for i in (0, 1, 2, 4): win.go(i); shot(f"L{i}")
    d["settings"]["pin"] = True; win.apply_pin(); app.processEvents(); shot("pinned"); d["settings"]["pin"] = False; win.apply_pin()
    it = Intro(lambda: None); it.show(); it.t = .5; it.repaint(); (it.grab().save(f"{shots}/intro.png") if shots else None); it.finish(); win.grab(); win.wipe_all(); assert store.data["subjects"] == [] and store.data["sessions"] == [] and store.data["version"] == 5 and store.data["streak"]["count"] == 0 and store.data["exam_types"] == [] and store.data["myday_own"] == []; print("SELFTEST OK")

if __name__ == "__main__":
    main()
