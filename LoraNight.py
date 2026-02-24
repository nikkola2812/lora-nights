# LoraNight.py
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pandas as pd
import streamlit as st
from zoneinfo import ZoneInfo

# ---------------- Config ----------------
st.set_page_config(page_title="Lora Nights", page_icon="🃏", layout="wide")

TZ = ZoneInfo("Europe/Podgorica")
DATA_FILE = Path(__file__).with_name("lora_nights_data.json")

# 6 games (S added)
GAMES = [
    {"key": "hearts", "label": "♥",  "name": "Hearts"},
    {"key": "khearts", "label": "K♥", "name": "King of Hearts"},
    {"key": "plus", "label": "+",    "name": "Plus"},
    {"key": "minus", "label": "−",   "name": "Minus"},
    {"key": "queens", "label": "Qs", "name": "Queens"},
    {"key": "s", "label": "S",       "name": "Slagalica"},
]
S_GAME_INDEX = next(i for i, g in enumerate(GAMES) if g["key"] == "s")

SCORE_EDITOR_KEY = "score_editor"
MOBILE_MODE_KEY = "mobile_mode"
TRACKER_EDITOR_KEY = "tracker_editor"
LANG_KEY = "lang"

# ---------------- i18n ----------------
TR = {
    "en":{
        "app_title": "🃏 Lora Nights",
        "sidebar_title": "Lora Nights",
        "main_menu": "🏠 Main menu",
        "play": "🎮 Play",
        "history": "📜 History",
        "facts": "📊 Facts",
        "mobile_mode": "📱 Mobile mode",
        "reset_all": "🔁 Reset app (everything)",
        "start_new_game": "Start a new game",
        "classic_game": "🎴 Classic game",
        "number_players": "Number of players",
        "player_name": "Player {i} name",
        "player_placeholder": "Player {i}",
        "start": "Start ✅",
        "stats_aggregation_hint": "Stats aggregation: 'Ivana', ' IVANA ', 'ivana' all count as the same person.",
        "no_active_game": "No active game. Start one from the main menu.",
        "go_to_main_menu": "Go to main menu",
        "played_tracker": "Played tracker",
        "tap_mark_played": "Tap to mark played games.",
        "tap_mark_played_mobile": "Tap to mark played games (mobile layout).",
        "progress": "Progress:",
        "slagalica_mode": "Slagalica mode (dots)",
        "slagalica_caption": "Tap a player to add a dot. Dots will be added automatically to the scores you enter for row {row}.",
        "score_sheet": "Score sheet",
        "score_sheet_caption": "Rows fixed: players × 6 = {rows}. Enter round change (delta): e.g. 5 or -4. Desktop grid shows running total; mobile uses quick entry.",
        "quick_round_entry": "📱 Quick round entry",
        "round": "Round",
        "slagalica_active_row": "Slagalica is active for row {row}.",
        "enter_each_delta": "Enter each player’s delta for this round:",
        "save_round": "✅ Save this round",
        "fill_all_warning": "Fill all players for this round.",
        "invalid_number_for": "Invalid number for {p}.",
        "saved_ok": "Saved ✅",
        "full_sheet_preview": "Full sheet (preview):",
        "complete_saved": "✅ Score sheet complete — saved automatically with date & time.",
        "rematch": "🔁 Rematch",
        "exit_caption": "You can exit now. The game night is saved locally.",
        "history_title": "History",
        "history_caption": "Delete removes it from History and Facts.",
        "no_saved_nights": "No saved game nights yet.",
        "delete": "🗑 Delete",
        "delete_caption": "This also updates Facts automatically.",
        "running_totals": "Running totals",
        "facts_title": "Facts",
        "facts_need_one": "Save at least one complete game night to see analytics.",
        "not_enough_data": "Not enough valid data yet.",
        "wins_leaderboards": "Wins leaderboards",
        "leaderboard_mode": "Leaderboard view",
        "leaderboard_all_time": "All time",
        "leaderboard_pick_month": "Pick month",
        "no_wins_this_period": "No wins recorded for this period yet.",
        "podium_title": "Podium",
        "player_stats_all_time": "Player stats (all time)",
        "extremes": "Extremes",
        "extremes_caption": "Lowest = best (good). Highest = worst (bad).",
        "this_week": "This week",
        "this_month": "This month",
        "all_time": "All time",
        "no_records_for": "No records for {label}.",
        "lowest_label": "Lowest ({label}) ✅",
        "highest_label": "Highest ({label}) ❌",
        "language": "🌐 Language",
        "lang_en": "🇬🇧🇺🇸",
        "lang_me": "🇲🇪🇷🇸",
        "months_won": "Months won",
        "wins_word": "wins",
    },

    "me": {
        "app_title": "🃏 Lora Nights",
        "sidebar_title": "Lora Nights",
        "main_menu": "🏠 Glavni meni",
        "play": "🎮 Igra",
        "history": "📜 Istorija",
        "facts": "📊 Statistika",
        "mobile_mode": "📱 Mobilni režim",
        "reset_all": "🔁 Resetuj aplikaciju (sve)",
        "start_new_game": "Započni novu igru",
        "classic_game": "🎴 Klasična igra",
        "number_players": "Broj igrača",
        "player_name": "Ime igrača {i}",
        "player_placeholder": "Igrač {i}",
        "start": "Start ✅",
        "stats_aggregation_hint": "Statistika: 'Ivana', ' IVANA ', 'ivana' se računaju kao ista osoba.",
        "no_active_game": "Nema aktivne igre. Pokreni je iz glavnog menija.",
        "go_to_main_menu": "Idi na glavni meni",
        "played_tracker": "Evidencija odigranih igara",
        "tap_mark_played": "Klikni da označiš odigrano.",
        "tap_mark_played_mobile": "Klikni da označiš odigrano (mobilni prikaz).",
        "progress": "Napredak:",
        "slagalica_mode": "Slagalica režim (tačkice)",
        "slagalica_caption": "Klikni igrača da dodaš tačkicu. Tačkice će se automatski dodati u rezultate koje uneseš za red {row}.",
        "score_sheet": "Tabela rezultata",
        "score_sheet_caption": "Broj redova: igrači × 6 = {rows}. Unesi promjenu po rundi (delta): npr. 5 ili -4. Desktop prikazuje ukupno, mobilni ima brzi unos.",
        "quick_round_entry": "📱 Brzi unos runde",
        "round": "Runda",
        "slagalica_active_row": "Slagalica je aktivna za red {row}.",
        "enter_each_delta": "Unesi delta za svakog igrača u ovoj rundi:",
        "save_round": "✅ Sačuvaj ovu rundu",
        "fill_all_warning": "Popuni sve igrače za ovu rundu.",
        "invalid_number_for": "Neispravan broj za {p}.",
        "saved_ok": "Sačuvano ✅",
        "full_sheet_preview": "Pregled kompletne tabele:",
        "complete_saved": "✅ Tabela je kompletna — automatski sačuvano sa datumom i vremenom.",
        "rematch": "🔁 Revanš",
        "exit_caption": "Možeš izaći. Igra je sačuvana lokalno.",
        "history_title": "Istorija",
        "history_caption": "Brisanje uklanja iz Istorije i Statistike.",
        "no_saved_nights": "Još nema sačuvanih večeri.",
        "delete": "🗑 Obriši",
        "delete_caption": "Ovo automatski ažurira Statistiku.",
        "running_totals": "Ukupni zbir (kumulativno)",
        "facts_title": "Statistika",
        "facts_need_one": "Sačuvaj makar jednu kompletnu igru da vidiš statistiku.",
        "not_enough_data": "Nema dovoljno validnih podataka.",
        "wins_leaderboards": "Rang lista pobjeda",
        "leaderboard_mode": "Prikaz rang liste",
        "leaderboard_all_time": "Sveukupno",
        "leaderboard_pick_month": "Izaberi mjesec",
        "no_wins_this_period": "Nema zabilježenih pobjeda za ovaj period.",
        "podium_title": "Postolje",
        "player_stats_all_time": "Statistika igrača (sveukupno)",
        "extremes": "Ekstremi",
        "extremes_caption": "Najniže = najbolje. Najviše = najgore.",
        "this_week": "Ove nedjelje",
        "this_month": "Ovog mjeseca",
        "all_time": "Sveukupno",
        "no_records_for": "Nema zapisa za {label}.",
        "lowest_label": "Najniže ({label}) ✅",
        "highest_label": "Najviše ({label}) ❌",
        "language": "🌐 Jezik",
        "lang_en": "🇬🇧🇺🇸",
        "lang_me": "🇲🇪🇷🇸",
        "months_won": "Mjeseci osvojeni",
        "wins_word": "pobjeda",
    }
}

def t(key: str, **kwargs) -> str:
    lang = st.session_state.get(LANG_KEY, "en")
    s = TR.get(lang, TR["en"]).get(key, TR["en"].get(key, key))
    try:
        return s.format(**kwargs)
    except Exception:
        return s

# ---------------- CSS ----------------
st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 4rem; max-width: 1200px; }
    [data-testid="stDataFrame"] { font-size: 0.95rem; }

    /* Podium styles */
    .podium-card {
        border-radius: 18px;
        padding: 14px 14px 12px 14px;
        border: 1px solid rgba(255,255,255,0.10);
        background: rgba(20,20,20,0.35);
        backdrop-filter: blur(6px);
        box-shadow: 0 6px 18px rgba(0,0,0,0.25);
        position: relative;
        overflow: hidden;
        min-height: 110px;
    }
    .podium-rank { font-size: 0.95rem; opacity: 0.85; margin-bottom: 6px; }
    .podium-name { font-size: 1.15rem; font-weight: 700; margin-bottom: 2px; }
    .podium-wins { font-size: 1.05rem; font-weight: 650; }

    .shine::before{
        content:"";
        position:absolute;
        inset:-60%;
        background: conic-gradient(from 180deg, rgba(255,255,255,0.0), rgba(255,255,255,0.18), rgba(255,255,255,0.0));
        animation: spin 3.2s linear infinite;
    }
    .shine::after{
        content:"";
        position:absolute;
        inset:0;
        background: radial-gradient(circle at 20% 15%, rgba(255,255,255,0.10), rgba(255,255,255,0.0) 55%);
        pointer-events:none;
    }
    @keyframes spin { to { transform: rotate(360deg);} }

    .gold { border-color: rgba(255,215,0,0.25); }
    .gold .podium-wins { color: rgba(255,215,0,0.95); }
    .gold.shine::before { background: conic-gradient(from 180deg, rgba(255,215,0,0.0), rgba(255,215,0,0.30), rgba(255,215,0,0.0)); }

    .silver { border-color: rgba(192,192,192,0.22); }
    .silver .podium-wins { color: rgba(220,220,220,0.95); }
    .silver.shine::before { background: conic-gradient(from 180deg, rgba(192,192,192,0.0), rgba(192,192,192,0.28), rgba(192,192,192,0.0)); }

    .bronze { border-color: rgba(205,127,50,0.22); }
    .bronze .podium-wins { color: rgba(205,127,50,0.95); }
    .bronze.shine::before { background: conic-gradient(from 180deg, rgba(205,127,50,0.0), rgba(205,127,50,0.28), rgba(205,127,50,0.0)); }

    @media (max-width: 768px) {
      button[kind="secondary"], button[kind="primary"] {
        font-size: 1.05rem !important;
        padding: 0.65rem 0.95rem !important;
      }
      .block-container { padding-left: 0.9rem; padding-right: 0.9rem; }
    }
    </style>
    """,
    unsafe_allow_html=True
)

# ---------------- Persistence ----------------
def norm_name(name: str) -> str:
    return " ".join(name.strip().lower().split())

def now_iso() -> str:
    return datetime.now(TZ).isoformat(timespec="seconds")

def load_db() -> Dict[str, Any]:
    if not DATA_FILE.exists():
        return {"people": {}, "nights": []}
    try:
        return json.loads(DATA_FILE.read_text(encoding="utf-8"))
    except Exception:
        return {"people": {}, "nights": []}

def save_db(db: Dict[str, Any]) -> None:
    DATA_FILE.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")

def ensure_person(db: Dict[str, Any], display_name: str) -> str:
    key = norm_name(display_name)
    if key == "":
        return ""
    if key not in db["people"]:
        db["people"][key] = {"display": display_name.strip() or "Unknown"}
    return key

# ---------------- data_editor compatibility ----------------
def editor_value_to_df(old_df: pd.DataFrame, widget_value):
    if isinstance(widget_value, pd.DataFrame):
        return widget_value
    if isinstance(widget_value, dict):
        df = old_df.copy()
        edited_rows = widget_value.get("edited_rows", {}) or {}
        for row_idx, changes in edited_rows.items():
            for col, val in changes.items():
                df.iat[int(row_idx), df.columns.get_loc(col)] = "" if val is None else str(val)
        return df
    return old_df.copy()

# ---------------- Score logic ----------------
def compute_cumulative_from_deltas(deltas: pd.DataFrame) -> pd.DataFrame:
    return deltas.fillna(0).cumsum(axis=0)

def deltas_complete(deltas: pd.DataFrame) -> bool:
    return deltas.notna().all().all()

def next_incomplete_row_pos(deltas: pd.DataFrame) -> int:
    if deltas is None or deltas.empty:
        return 0
    for i in range(len(deltas)):
        if deltas.iloc[i].isna().any():
            return i
    return max(0, len(deltas) - 1)

def build_view_from_deltas(deltas: pd.DataFrame) -> pd.DataFrame:
    cum = compute_cumulative_from_deltas(deltas)
    view = cum.where(deltas.notna(), other=pd.NA)

    out = pd.DataFrame(index=view.index, columns=view.columns)
    for c in out.columns:
        out[c] = view[c].apply(lambda x: "" if pd.isna(x) else str(int(x)))
    return out

def apply_view_edits_to_deltas(old_view: pd.DataFrame, new_view: pd.DataFrame, deltas: pd.DataFrame) -> pd.DataFrame:
    cols = list(deltas.columns)
    idx = list(deltas.index)

    for r_i, r in enumerate(idx):
        for col in cols:
            old = "" if pd.isna(old_view.at[r, col]) else str(old_view.at[r, col]).strip()
            new = "" if pd.isna(new_view.at[r, col]) else str(new_view.at[r, col]).strip()
            if old == new:
                continue

            if new == "":
                deltas.loc[idx[r_i]:, col] = pd.NA
                continue

            try:
                delta_val = int(new)
            except ValueError:
                continue

            deltas.at[r, col] = int(delta_val)

    return deltas

# ---------------- Slagalica behavior ----------------
def ensure_slagalica_state(players: List[str]):
    if "slagalica_active" not in st.session_state:
        st.session_state.slagalica_active = False
    if "slagalica_row_pos" not in st.session_state:
        st.session_state.slagalica_row_pos = 0
    if "s_dots" not in st.session_state or not isinstance(st.session_state.s_dots, dict):
        st.session_state.s_dots = {p: 0 for p in players}
    else:
        for p in players:
            st.session_state.s_dots.setdefault(p, 0)
        for k in list(st.session_state.s_dots.keys()):
            if k not in players:
                del st.session_state.s_dots[k]

def activate_slagalica_for_next_row():
    if st.session_state.deltas_df is None:
        return
    st.session_state.slagalica_active = True
    st.session_state.slagalica_row_pos = next_incomplete_row_pos(st.session_state.deltas_df)

def slagalica_apply_bonus_for_row(row_pos: int):
    if not st.session_state.get("slagalica_active", False):
        return
    if row_pos != int(st.session_state.get("slagalica_row_pos", 0)):
        return

    deltas = st.session_state.deltas_df
    players = st.session_state.players_display
    ensure_slagalica_state(players)

    for p in players:
        if pd.isna(deltas.iat[row_pos, deltas.columns.get_loc(p)]):
            continue
        bonus = int(st.session_state.s_dots.get(p, 0))
        if bonus != 0:
            deltas.iat[row_pos, deltas.columns.get_loc(p)] = int(deltas.iat[row_pos, deltas.columns.get_loc(p)]) + bonus
            st.session_state.s_dots[p] = 0

    st.session_state.deltas_df = deltas

    if not deltas.iloc[row_pos].isna().any():
        st.session_state.slagalica_active = False
        for p in players:
            st.session_state.s_dots[p] = 0

# ---------------- App state ----------------
def init_state():
    st.session_state.db = load_db()

    st.session_state.view = "menu"   # menu | play | history | facts
    st.session_state.stage = "setup" # setup | in_game | postgame

    st.session_state.player_count = 4
    st.session_state.setup_names = ["", "", "", ""]

    st.session_state.players_display = []
    st.session_state.players_keys = []
    st.session_state.played = {}      # (p_i,g_i)->bool
    st.session_state.deltas_df = None # Int64
    st.session_state.saved_current = False
    st.session_state.last_saved_id = None
    st.session_state.score_old_view = None
    st.session_state[MOBILE_MODE_KEY] = st.session_state.get(MOBILE_MODE_KEY, False)

    st.session_state.slagalica_active = False
    st.session_state.slagalica_row_pos = 0
    st.session_state.s_dots = {}

    if LANG_KEY not in st.session_state:
        st.session_state[LANG_KEY] = "me"

def reset_to_menu(keep_names=True):
    st.session_state.view = "menu"
    st.session_state.stage = "setup"
    st.session_state.players_display = []
    st.session_state.players_keys = []
    st.session_state.played = {}
    st.session_state.deltas_df = None
    st.session_state.saved_current = False
    st.session_state.last_saved_id = None
    st.session_state.score_old_view = None

    st.session_state.slagalica_active = False
    st.session_state.slagalica_row_pos = 0
    st.session_state.s_dots = {}

    for k in [SCORE_EDITOR_KEY, TRACKER_EDITOR_KEY]:
        if k in st.session_state:
            del st.session_state[k]

    if not keep_names:
        st.session_state.player_count = 4
        st.session_state.setup_names = ["", "", "", ""]

def played_progress() -> Tuple[int, int]:
    done = sum(1 for v in st.session_state.played.values() if v)
    total = len(st.session_state.players_display) * len(GAMES)
    return done, total

def start_game_from_setup():
    n = int(st.session_state.player_count)
    names = st.session_state.setup_names[:n]
    players = [(x.strip() if x.strip() else f"Player {i+1}") for i, x in enumerate(names)]
    st.session_state.players_display = players

    db = st.session_state.db
    keys = [ensure_person(db, p) for p in players]
    st.session_state.players_keys = keys
    save_db(db)
    st.session_state.db = db

    st.session_state.played = {(p_i, g_i): False for p_i in range(n) for g_i in range(len(GAMES))}

    rows = n * len(GAMES)
    deltas = pd.DataFrame({p: pd.Series([pd.NA] * rows, dtype="Int64") for p in players})
    deltas.index = [str(i + 1) for i in range(rows)]
    st.session_state.deltas_df = deltas

    st.session_state.saved_current = False
    st.session_state.last_saved_id = None
    st.session_state.stage = "in_game"
    st.session_state.view = "play"
    st.session_state.score_old_view = build_view_from_deltas(deltas)

    ensure_slagalica_state(players)
    st.session_state.slagalica_active = False
    st.session_state.slagalica_row_pos = next_incomplete_row_pos(deltas)

    for k in [SCORE_EDITOR_KEY, TRACKER_EDITOR_KEY]:
        if k in st.session_state:
            del st.session_state[k]

def start_rematch_same_players():
    players = st.session_state.players_display
    n = len(players)
    st.session_state.played = {(p_i, g_i): False for p_i in range(n) for g_i in range(len(GAMES))}

    rows = n * len(GAMES)
    deltas = pd.DataFrame({p: pd.Series([pd.NA] * rows, dtype="Int64") for p in players})
    deltas.index = [str(i + 1) for i in range(rows)]
    st.session_state.deltas_df = deltas

    st.session_state.saved_current = False
    st.session_state.last_saved_id = None
    st.session_state.stage = "in_game"
    st.session_state.view = "play"
    st.session_state.score_old_view = build_view_from_deltas(deltas)

    ensure_slagalica_state(players)
    st.session_state.slagalica_active = False
    st.session_state.slagalica_row_pos = next_incomplete_row_pos(deltas)

    for k in [SCORE_EDITOR_KEY, TRACKER_EDITOR_KEY]:
        if k in st.session_state:
            del st.session_state[k]

def delete_night_by_id(night_id: str) -> int:
    db = st.session_state.db
    before = len(db.get("nights", []))
    db["nights"] = [n for n in db.get("nights", []) if n.get("id") != night_id]
    after = len(db["nights"])
    save_db(db)
    st.session_state.db = db
    return before - after

def save_current_game_night(auto: bool = True) -> str:
    db = st.session_state.db
    ts = now_iso()

    players = st.session_state.players_display
    keys = st.session_state.players_keys

    deltas_df = st.session_state.deltas_df.copy()
    deltas_int = deltas_df.fillna(0).astype(int)
    deltas_list = deltas_int.values.tolist()

    running = deltas_int.cumsum(axis=0)
    final_totals = running.iloc[-1].astype(int).tolist() if len(running) else [0] * len(players)

    done, total = played_progress()
    n_players = len(players)
    played_grid = [[bool(st.session_state.played[(p_i, g_i)]) for g_i in range(len(GAMES))] for p_i in range(n_players)]

    night_id = f"night_{ts}"
    night = {
        "id": night_id,
        "timestamp": ts,
        "players_display": players,
        "players_keys": keys,
        "rows": len(deltas_int),
        "deltas": deltas_list,
        "final_totals": final_totals,
        "played_tracker": {"done": done, "total": total, "grid": played_grid},
        "auto_saved": bool(auto),
    }
    db["nights"].append(night)
    save_db(db)
    st.session_state.db = db
    return night_id

# ---------------- Callbacks ----------------
def on_score_change():
    if st.session_state.deltas_df is None:
        return

    if st.session_state.score_old_view is None:
        st.session_state.score_old_view = build_view_from_deltas(st.session_state.deltas_df)

    old_view = st.session_state.score_old_view
    widget_value = st.session_state.get(SCORE_EDITOR_KEY)
    if widget_value is None:
        return

    new_view = editor_value_to_df(old_view, widget_value)
    new_view = new_view.reindex(index=old_view.index, columns=old_view.columns)

    updated = apply_view_edits_to_deltas(old_view, new_view, st.session_state.deltas_df.copy())
    for c in updated.columns:
        updated[c] = updated[c].astype("Int64")

    st.session_state.deltas_df = updated
    slagalica_apply_bonus_for_row(int(st.session_state.get("slagalica_row_pos", 0)))
    st.session_state.score_old_view = build_view_from_deltas(st.session_state.deltas_df)

# ---------------- Init ----------------
if "db" not in st.session_state:
    init_state()

# ---------------- Sidebar ----------------
with st.sidebar:
    st.header(t("sidebar_title"))

    st.session_state[LANG_KEY] = st.selectbox(
        t("language"),
        options=["en", "me"],
        format_func=lambda x: t("lang_en") if x == "en" else t("lang_me"),
        index=0 if st.session_state.get(LANG_KEY, "en") == "en" else 1
    )

    if st.button(t("main_menu")):
        reset_to_menu(keep_names=True)
        st.rerun()

    c1, c2, c3 = st.columns(3)
    if c1.button(t("play")):
        st.session_state.view = "play" if st.session_state.deltas_df is not None else "menu"
        st.rerun()
    if c2.button(t("history")):
        st.session_state.view = "history"
        st.rerun()
    if c3.button(t("facts")):
        st.session_state.view = "facts"
        st.rerun()

    st.write("---")
    st.session_state[MOBILE_MODE_KEY] = st.toggle(t("mobile_mode"), value=st.session_state.get(MOBILE_MODE_KEY, False))

    st.write("---")
    if st.button(t("reset_all")):
        init_state()
        st.rerun()

# ---------------- Top nav (mobile) ----------------
st.title(t("app_title"))
if st.session_state.get(MOBILE_MODE_KEY, False):
    top1, top2, top3 = st.columns(3)
    if top1.button(t("play"), use_container_width=True):
        st.session_state.view = "play" if st.session_state.deltas_df is not None else "menu"
        st.rerun()
    if top2.button(t("history"), use_container_width=True):
        st.session_state.view = "history"
        st.rerun()
    if top3.button(t("facts"), use_container_width=True):
        st.session_state.view = "facts"
        st.rerun()
    st.write("---")

# =========================
# MENU
# =========================
if st.session_state.view == "menu":
    st.subheader(t("start_new_game"))

    if st.button(t("classic_game"), use_container_width=True):
        st.session_state.player_count = 3
        st.session_state.setup_names = ["Sara", "Dajana", "Ivana"]
        start_game_from_setup()
        st.rerun()

    st.write("---")

    st.session_state.player_count = st.number_input(
        t("number_players"), min_value=2, max_value=5,
        value=int(st.session_state.player_count), step=1
    )
    n = int(st.session_state.player_count)

    cur = st.session_state.setup_names
    if len(cur) < n:
        st.session_state.setup_names = cur + [""] * (n - len(cur))
    elif len(cur) > n:
        st.session_state.setup_names = cur[:n]

    for i in range(n):
        st.session_state.setup_names[i] = st.text_input(
            t("player_name", i=i + 1),
            value=st.session_state.setup_names[i],
            key=f"menu_name_{i}",
            placeholder=t("player_placeholder", i=i + 1),
        )

    if st.button(t("start"), type="primary"):
        start_game_from_setup()
        st.rerun()

    st.write("---")
    st.caption(t("stats_aggregation_hint"))

# =========================
# PLAY
# =========================
elif st.session_state.view == "play":
    if st.session_state.deltas_df is None:
        st.info(t("no_active_game"))
        if st.button(t("go_to_main_menu")):
            st.session_state.view = "menu"
            st.rerun()
    else:
        players = st.session_state.players_display
        n = len(players)
        deltas = st.session_state.deltas_df
        mobile_mode = st.session_state.get(MOBILE_MODE_KEY, False)

        ensure_slagalica_state(players)

        tracker_expanded = not mobile_mode
        with st.expander(t("played_tracker"), expanded=tracker_expanded):
            st.caption(t("tap_mark_played"))

            if mobile_mode:
                st.caption(t("tap_mark_played_mobile"))

                for p_i, p_name in enumerate(players):
                    st.markdown(f"### {p_name}")
                    prev_s = bool(st.session_state.played.get((p_i, S_GAME_INDEX), False))

                    for g_i, g in enumerate(GAMES):
                        left, right = st.columns([1.2, 0.8], vertical_alignment="center")
                        left.markdown(f"**{g['label']}**")
                        new_val = right.checkbox(
                            " ",
                            value=bool(st.session_state.played.get((p_i, g_i), False)),
                            key=f"mob_chk_{p_i}_{g_i}",
                            label_visibility="collapsed",
                        )
                        st.session_state.played[(p_i, g_i)] = bool(new_val)

                    new_s = bool(st.session_state.played.get((p_i, S_GAME_INDEX), False))
                    if (not prev_s) and new_s:
                        activate_slagalica_for_next_row()

                    st.divider()
            else:
                w = [2.0] + [0.65] * len(GAMES)
                hdr = st.columns(w)
                hdr[0].markdown("**Player**")
                for i, g in enumerate(GAMES, start=1):
                    hdr[i].markdown(f"**{g['label']}**")

                for p_i, p_name in enumerate(players):
                    row = st.columns(w)
                    row[0].write(p_name)
                    for g_i in range(len(GAMES)):
                        prev = st.session_state.played.get((p_i, g_i), False)
                        label = "✕" if prev else " "
                        if row[g_i + 1].button(label, key=f"played_{p_i}_{g_i}", use_container_width=True):
                            st.session_state.played[(p_i, g_i)] = not prev
                            if g_i == S_GAME_INDEX and (not prev) and st.session_state.played[(p_i, g_i)]:
                                activate_slagalica_for_next_row()
                            st.rerun()

            done, total = played_progress()
            st.write(f"**{t('progress')}** {done}/{total}")

        if st.session_state.get("slagalica_active", False):
            st.write("---")
            rpos = int(st.session_state.get("slagalica_row_pos", 0))
            row_label = deltas.index[rpos]
            st.subheader(t("slagalica_mode"))
            st.caption(t("slagalica_caption", row=row_label))

            cols = st.columns(n)
            for i, p in enumerate(players):
                dots = int(st.session_state.s_dots.get(p, 0))
                if cols[i].button(f"{p} • {dots}", key=f"dot_{p}", use_container_width=True):
                    st.session_state.s_dots[p] = dots + 1
                    st.rerun()

        st.write("---")
        st.subheader(t("score_sheet"))
        st.caption(t("score_sheet_caption", rows=n * 6))

        if mobile_mode:
            st.markdown(f"### {t('quick_round_entry')}")

            n_rows = len(deltas)
            current_pos = next_incomplete_row_pos(deltas)
            row_choice = st.number_input(t("round"), min_value=1, max_value=n_rows, value=current_pos + 1, step=1) - 1

            if st.session_state.get("slagalica_active", False):
                st.caption(t("slagalica_active_row", row=deltas.index[int(st.session_state.slagalica_row_pos)]))

            st.caption(t("enter_each_delta"))
            round_inputs = {}
            for p in players:
                round_inputs[p] = st.text_input(
                    p,
                    value="",
                    placeholder="e.g. 5 or -4",
                    key=f"mob_{row_choice}_{p}",
                )

            if st.button(t("save_round"), type="primary"):
                for p in players:
                    v = round_inputs[p].strip()
                    if v == "":
                        st.warning(t("fill_all_warning"))
                        st.stop()
                    try:
                        deltas.iat[row_choice, deltas.columns.get_loc(p)] = int(v)
                    except ValueError:
                        st.warning(t("invalid_number_for", p=p))
                        st.stop()

                st.session_state.deltas_df = deltas
                slagalica_apply_bonus_for_row(int(row_choice))
                st.session_state.score_old_view = build_view_from_deltas(st.session_state.deltas_df)

                st.success(t("saved_ok"))
                st.rerun()

            st.write("---")
            st.caption(t("full_sheet_preview"))

            cum = deltas.fillna(0).astype(int).cumsum(axis=0)
            preview = cum.where(deltas.notna(), other=pd.NA)
            preview_display = preview.astype("Int64").astype(str).replace("<NA>", "")
            st.dataframe(preview_display, use_container_width=True, height=320)

        else:
            if st.session_state.score_old_view is None:
                st.session_state.score_old_view = build_view_from_deltas(deltas)

            view_df = st.session_state.score_old_view

            st.data_editor(
                view_df,
                key=SCORE_EDITOR_KEY,
                on_change=on_score_change,
                use_container_width=True,
                num_rows="fixed",
                height=520,
                column_config={p: st.column_config.TextColumn(width="small") for p in players},
            )

        cum = compute_cumulative_from_deltas(st.session_state.deltas_df)
        final = cum.iloc[-1].fillna(0).astype(int).tolist() if len(cum) else [0] * n
        tot_cols = st.columns(n)
        for i, p in enumerate(players):
            tot_cols[i].metric(label=p, value=final[i])

        if (not st.session_state.saved_current) and deltas_complete(st.session_state.deltas_df):
            night_id = save_current_game_night(auto=True)
            st.session_state.saved_current = True
            st.session_state.last_saved_id = night_id
            st.session_state.stage = "postgame"
            st.rerun()

        if st.session_state.stage == "postgame":
            st.success(t("complete_saved"))
            b1, b2, b3 = st.columns([1.2, 1.2, 3.6])
            if b1.button(t("rematch"), type="primary"):
                start_rematch_same_players()
                st.rerun()
            if b2.button(t("main_menu")):
                reset_to_menu(keep_names=True)
                st.rerun()
            b3.caption(t("exit_caption"))

# =========================
# HISTORY
# =========================
elif st.session_state.view == "history":
    db = st.session_state.db
    nights = list(reversed(db.get("nights", [])))

    st.subheader(t("history_title"))
    st.caption(t("history_caption"))

    if not nights:
        st.info(t("no_saved_nights"))
    else:
        for night in nights:
            night_id = night.get("id", "")
            dt = datetime.fromisoformat(night["timestamp"]).astimezone(TZ)
            title = f"{dt.strftime('%Y-%m-%d %H:%M:%S')} — " + ", ".join(night["players_display"])

            with st.expander(title):
                del_col1, del_col2 = st.columns([1.3, 4.7])
                if del_col1.button(t("delete"), key=f"delete_{night_id}"):
                    delete_night_by_id(night_id)
                    st.rerun()
                del_col2.caption(t("delete_caption"))

                players = night["players_display"]
                finals = night["final_totals"]
                deltas_list = night["deltas"]

                df0 = pd.DataFrame(deltas_list, columns=players)
                df0.index = [str(i + 1) for i in range(len(df0))]

                st.caption(t("running_totals"))
                st.dataframe(df0.cumsum(axis=0), use_container_width=True, height=320)

                cols = st.columns(len(players))
                for i, p in enumerate(players):
                    cols[i].metric(label=p, value=finals[i])

# =========================
# FACTS
# =========================
else:
    db = st.session_state.db
    nights = db.get("nights", [])

    st.subheader(t("facts_title"))
    if not nights:
        st.info(t("facts_need_one"))
    else:
        def display_for(k: str, fallback: str) -> str:
            person = db.get("people", {}).get(k)
            if isinstance(person, dict) and person.get("display"):
                return person["display"]
            return fallback

        # Build per-night player rows
        rows = []
        records = []  # (dt, key, display, score)

        for night in nights:
            dt = datetime.fromisoformat(night["timestamp"]).astimezone(TZ)
            month_key = (dt.year, dt.month)

            keys = night.get("players_keys", [])
            displays = night.get("players_display", [])
            totals = night.get("final_totals", [])
            if not totals or not keys:
                continue

            # dense ranking by score (lower is better)
            unique_sorted = sorted(set(int(x) for x in totals))
            score_to_rank = {s: (i + 1) for i, s in enumerate(unique_sorted)}  # ranks start at 1
            max_rank = max(score_to_rank.values())

            for k, d, s in zip(keys, displays, totals):
                if not k:
                    continue
                s = int(s)
                r = score_to_rank[s]
                rows.append({
                    "dt": dt,
                    "month_key": month_key,
                    "player_key": k,
                    "player_display": display_for(k, d),
                    "score": s,
                    "rank": r,
                    "is_win": (r == 1),
                    "is_second": (r == 2),
                    "is_last": (r == max_rank),
                })
                records.append((dt, k, d, s))

        df = pd.DataFrame(rows)
        if df.empty:
            st.info(t("not_enough_data"))
            st.stop()

        # Months list for interactive selection
        months = sorted(df["month_key"].unique().tolist())
        month_labels = [f"{y}-{m:02d}" for (y, m) in months]

        view_mode = st.radio(
            t("leaderboard_mode"),
            options=["month", "all"],
            format_func=lambda x: t("leaderboard_pick_month") if x == "month" else t("leaderboard_all_time"),
            horizontal=True
        )

        chosen_month_key = None
        if view_mode == "month":
            now = datetime.now(TZ)
            current_key = (now.year, now.month)
            current_label = f"{current_key[0]}-{current_key[1]:02d}"
            default_idx = month_labels.index(current_label) if current_label in month_labels else (len(month_labels) - 1)
            chosen_label = st.selectbox(t("leaderboard_pick_month"), options=month_labels, index=default_idx)
            y, m = chosen_label.split("-")
            chosen_month_key = (int(y), int(m))

        def podium(cards: List[Tuple[str, int]]):
            styles = [("🥇 1st", "gold"), ("🥈 2nd", "silver"), ("🥉 3rd", "bronze")]
            cols = st.columns(3)
            for i in range(3):
                if i < len(cards):
                    name, wins = cards[i]
                    rank_txt, cls = styles[i]
                    html = f"""
                    <div class="podium-card {cls} shine">
                      <div class="podium-rank">{rank_txt}</div>
                      <div class="podium-name">{name}</div>
                      <div class="podium-wins">{wins} {t('wins_word')}</div>
                    </div>
                    """
                    cols[i].markdown(html, unsafe_allow_html=True)
                else:
                    cols[i].markdown("<div class='podium-card' style='opacity:0.35'></div>", unsafe_allow_html=True)

        base = df if view_mode == "all" else df[df["month_key"] == chosen_month_key]

        wins_tbl = (
            base.groupby(["player_key", "player_display"])["is_win"]
            .sum()
            .reset_index(name="wins")
            .sort_values(["wins", "player_display"], ascending=[False, True])
        )

        # Hide 0 wins
        wins_tbl = wins_tbl[wins_tbl["wins"] > 0].copy()

        st.write("---")
        st.markdown(f"### {t('podium_title')}")

        if wins_tbl.empty:
            st.info(t("no_wins_this_period"))
        else:
            top3 = wins_tbl.head(3)
            cards = list(zip(top3["player_display"].tolist(), top3["wins"].astype(int).tolist()))
            podium(cards)

            with st.expander(t("wins_leaderboards"), expanded=False):
                wins_tbl = wins_tbl.reset_index(drop=True)
                wins_tbl.index = wins_tbl.index + 1  # rank starts at 1
                show = wins_tbl[["player_display", "wins"]].rename(columns={"player_display": "Player", "wins": "Wins"})
                st.dataframe(show, use_container_width=True, height=320)

        # --------------------
        # Player stats table (all time) + which months they won monthly leaderboard
        # --------------------
        st.write("---")
        st.markdown(f"### 📋 {t('player_stats_all_time')}")

        # monthly winners list: only for FINISHED months (not the current month)
        months_won_map: Dict[str, List[str]] = {}

        now = datetime.now(TZ)
        current_month_key = (now.year, now.month)

        for mk in months:
            # mk is (year, month)
            # Only count months that are fully finished (strictly before the current month)
            if mk >= current_month_key:
                continue

            mdf = df[df["month_key"] == mk]
            w = (
                mdf.groupby(["player_key", "player_display"])["is_win"]
                .sum()
                .reset_index(name="wins")
            )

            # if nobody won any games that month, skip
            w = w[w["wins"] > 0]
            if w.empty:
                continue

            top = int(w["wins"].max())
            winners = w[w["wins"] == top]["player_key"].tolist()

            label = f"{mk[0]}-{mk[1]:02d}"
            for pk in winners:
                months_won_map.setdefault(pk, []).append(label)

        games_played = df.groupby(["player_key", "player_display"])["dt"].count().reset_index(name="games")
        firsts = df.groupby(["player_key", "player_display"])["is_win"].sum().reset_index(name="first_place")
        seconds = df.groupby(["player_key", "player_display"])["is_second"].sum().reset_index(name="second_place")
        lasts = df.groupby(["player_key", "player_display"])["is_last"].sum().reset_index(name="last_place")
        best = df.groupby(["player_key", "player_display"])["score"].min().reset_index(name="best_score")
        worst = df.groupby(["player_key", "player_display"])["score"].max().reset_index(name="worst_score")
        avg = df.groupby(["player_key", "player_display"])["score"].mean().reset_index(name="avg_score")

        stats = (
            games_played.merge(firsts, on=["player_key", "player_display"], how="left")
            .merge(seconds, on=["player_key", "player_display"], how="left")
            .merge(lasts, on=["player_key", "player_display"], how="left")
            .merge(best, on=["player_key", "player_display"], how="left")
            .merge(worst, on=["player_key", "player_display"], how="left")
            .merge(avg, on=["player_key", "player_display"], how="left")
        )

        stats["win_pct"] = (stats["first_place"] / stats["games"] * 100.0).round(1)
        stats["avg_score"] = stats["avg_score"].round(2)
        stats[t("months_won")] = stats["player_key"].apply(lambda k: ", ".join(months_won_map.get(k, [])))

        stats = stats.sort_values(
            ["first_place", "win_pct", "avg_score", "player_display"],
            ascending=[False, False, True, True]
        )

        stats_display = stats.rename(columns={
            "player_display": "Player",
            "games": "Games",
            "first_place": "1st",
            "second_place": "2nd",
            "last_place": "Last",
            "best_score": "Best (lowest)",
            "worst_score": "Worst (highest)",
            "avg_score": "Avg score",
            "win_pct": "Win %"
        })[
            ["Player", "Games", "1st", "2nd", "Last", "Best (lowest)", "Worst (highest)", "Avg score", "Win %", t("months_won")]
        ]

        st.dataframe(stats_display, use_container_width=True, height=440)

        # --------------------
        # Extremes (week/month/all-time)
        # --------------------
        st.write("---")
        st.markdown(f"### 📈 {t('extremes')}")
        st.caption(t("extremes_caption"))

        now = datetime.now(TZ)
        week_key = now.isocalendar()[:2]
        month_key = (now.year, now.month)

        def period_records(kind: str):
            if kind == "week":
                return [r for r in records if r[0].isocalendar()[:2] == week_key]
            if kind == "month":
                return [r for r in records if (r[0].year, r[0].month) == month_key]
            return records

        def show_extremes(label: str, recs):
            if not recs:
                st.info(t("no_records_for", label=label))
                return

            low = min(recs, key=lambda x: x[3])
            high = max(recs, key=lambda x: x[3])

            low_name = display_for(low[1], low[2])
            high_name = display_for(high[1], high[2])

            a, b = st.columns(2)
            a.metric(t("lowest_label", label=label), low[3])
            a.caption(f"{low_name} — {low[0].strftime('%Y-%m-%d %H:%M')}")
            b.metric(t("highest_label", label=label), high[3])
            b.caption(f"{high_name} — {high[0].strftime('%Y-%m-%d %H:%M')}")

        st.markdown(f"#### {t('this_week')}")
        show_extremes(t("this_week").lower(), period_records("week"))

        st.markdown(f"#### {t('this_month')}")
        show_extremes(t("this_month").lower(), period_records("month"))

        st.markdown(f"#### {t('all_time')}")
        show_extremes(t("all_time").lower(), period_records("all"))
