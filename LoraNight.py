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

SCORE_EDITOR_KEY = "score_editor"  # stable key for st.data_editor
MOBILE_MODE_KEY = "mobile_mode"


# ---------------- CSS (mobile-friendly taps, spacing) ----------------
st.markdown(
    """
    <style>
    .block-container { padding-top: 1rem; padding-bottom: 4rem; max-width: 1200px; }
    /* Slightly tighter tables */
    [data-testid="stDataFrame"] { font-size: 0.95rem; }
    /* Bigger tap targets on small screens */
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


# ---------------- Handle Streamlit data_editor return type ----------------
def editor_value_to_df(old_df: pd.DataFrame, widget_value):
    """
    Depending on Streamlit version, st.data_editor stores in session_state either:
      - a DataFrame
      - OR a dict like {"edited_rows": {row_idx: {col: value}}, ...}
    This function always returns a DataFrame with edits applied.
    """
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


# ---------------- Score engine (deltas stored, cumulative displayed) ----------------
def compute_cumulative_from_deltas(deltas: pd.DataFrame) -> pd.DataFrame:
    return deltas.fillna(0).cumsum(axis=0)

def deltas_complete(deltas: pd.DataFrame) -> bool:
    return deltas.notna().all().all()

def next_incomplete_row_pos(deltas: pd.DataFrame) -> int:
    """Returns first row position where any player is NA."""
    if deltas is None or deltas.empty:
        return 0
    for i in range(len(deltas)):
        if deltas.iloc[i].isna().any():
            return i
    return max(0, len(deltas) - 1)

def build_view_from_deltas(deltas: pd.DataFrame) -> pd.DataFrame:
    """
    What the user sees/edits:
    - cumulative totals as strings
    - blank where delta not entered yet
    """
    cum = compute_cumulative_from_deltas(deltas)
    view = cum.where(deltas.notna(), other=pd.NA)

    out = pd.DataFrame(index=view.index, columns=view.columns)
    for c in out.columns:
        out[c] = view[c].apply(lambda x: "" if pd.isna(x) else str(int(x)))
    return out

def apply_view_edits_to_deltas(old_view: pd.DataFrame, new_view: pd.DataFrame, deltas: pd.DataFrame) -> pd.DataFrame:
    """
    EXCEL-LIKE RULE:
    - Any integer typed is treated as ROUND DELTA.
    - Clearing clears this and all below for that player.
    """
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


# ---------------- App state ----------------
def init_state():
    st.session_state.db = load_db()

    st.session_state.view = "menu"         # menu | play | history | facts
    st.session_state.stage = "setup"       # setup | in_game | postgame

    st.session_state.player_count = 4
    st.session_state.setup_names = ["", "", "", ""]

    # Current game
    st.session_state.players_display = []
    st.session_state.players_keys = []

    # Played tracker: (p_i, g_i)->bool
    st.session_state.played = {}

    # Score table stores ROUND DELTAS (Int64); rows fixed = players * 6
    st.session_state.deltas_df = None

    st.session_state.saved_current = False
    st.session_state.last_saved_id = None

    # Editor baseline view (DataFrame of strings)
    st.session_state.score_old_view = None

    # Mobile mode toggle default
    st.session_state[MOBILE_MODE_KEY] = st.session_state.get(MOBILE_MODE_KEY, False)

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

    if SCORE_EDITOR_KEY in st.session_state:
        del st.session_state[SCORE_EDITOR_KEY]

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

    # Register for aggregation
    db = st.session_state.db
    keys = [ensure_person(db, p) for p in players]
    st.session_state.players_keys = keys
    save_db(db)
    st.session_state.db = db

    # Tracker init
    st.session_state.played = {(p_i, g_i): False for p_i in range(n) for g_i in range(len(GAMES))}

    # Fixed rows = players * 6
    rows = n * len(GAMES)
    deltas = pd.DataFrame({p: pd.Series([pd.NA] * rows, dtype="Int64") for p in players})
    deltas.index = [str(i + 1) for i in range(rows)]
    st.session_state.deltas_df = deltas

    st.session_state.saved_current = False
    st.session_state.last_saved_id = None
    st.session_state.stage = "in_game"
    st.session_state.view = "play"

    st.session_state.score_old_view = build_view_from_deltas(deltas)

    if SCORE_EDITOR_KEY in st.session_state:
        del st.session_state[SCORE_EDITOR_KEY]

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

    if SCORE_EDITOR_KEY in st.session_state:
        del st.session_state[SCORE_EDITOR_KEY]

def toggle_played(p_i: int, g_i: int) -> None:
    prev = st.session_state.played.get((p_i, g_i), False)
    st.session_state.played[(p_i, g_i)] = not prev

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


# ---------------- data_editor on_change callback ----------------
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
    st.session_state.score_old_view = build_view_from_deltas(updated)


# ---------------- Init ----------------
if "db" not in st.session_state:
    init_state()


# ---------------- Sidebar navigation (buttons) ----------------
with st.sidebar:
    st.header("Lora Nights")

    if st.button("🏠 Main menu"):
        reset_to_menu(keep_names=True)
        st.rerun()

    c1, c2, c3 = st.columns(3)
    if c1.button("🎮 Play"):
        st.session_state.view = "play" if st.session_state.deltas_df is not None else "menu"
        st.rerun()
    if c2.button("📜 History"):
        st.session_state.view = "history"
        st.rerun()
    if c3.button("📊 Facts"):
        st.session_state.view = "facts"
        st.rerun()

    st.write("---")
    st.session_state[MOBILE_MODE_KEY] = st.toggle("📱 Mobile mode", value=st.session_state.get(MOBILE_MODE_KEY, False))

    st.write("---")
    if st.button("🔁 Reset app (everything)"):
        init_state()
        st.rerun()


# ---------------- Top nav for mobile (big buttons) ----------------
st.title("🃏 Lora Nights")
if st.session_state.get(MOBILE_MODE_KEY, False):
    top1, top2, top3 = st.columns(3)
    if top1.button("🎮 Play", use_container_width=True):
        st.session_state.view = "play" if st.session_state.deltas_df is not None else "menu"
        st.rerun()
    if top2.button("📜 History", use_container_width=True):
        st.session_state.view = "history"
        st.rerun()
    if top3.button("📊 Facts", use_container_width=True):
        st.session_state.view = "facts"
        st.rerun()
    st.write("---")


# =========================
# MENU
# =========================
if st.session_state.view == "menu":
    st.subheader("Start a new game")

    st.session_state.player_count = st.number_input(
        "Number of players", min_value=2, max_value=5,
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
            f"Player {i+1} name",
            value=st.session_state.setup_names[i],
            key=f"menu_name_{i}",
            placeholder=f"Player {i+1}",
        )

    if st.button("Start ✅", type="primary"):
        start_game_from_setup()
        st.rerun()

    st.write("---")
    st.caption("Stats aggregation: 'Ivana', ' IVANA ', 'ivana' all count as the same person.")


# =========================
# PLAY
# =========================
elif st.session_state.view == "play":
    if st.session_state.deltas_df is None:
        st.info("No active game. Start one from the main menu.")
        if st.button("Go to main menu"):
            st.session_state.view = "menu"
            st.rerun()
    else:
        players = st.session_state.players_display
        n = len(players)
        deltas = st.session_state.deltas_df

        # --- Mobile: collapse tracker to reduce scrolling ---
        mobile_mode = st.session_state.get(MOBILE_MODE_KEY, False)
        tracker_expanded = not mobile_mode

        with st.expander("Played tracker", expanded=tracker_expanded):
            st.caption("Tap a box to toggle an X.")
            w = [2.0] + [0.65] * len(GAMES)
            hdr = st.columns(w)
            hdr[0].markdown("**Player**")
            for i, g in enumerate(GAMES, start=1):
                hdr[i].markdown(f"**{g['label']}**")

            for p_i, p_name in enumerate(players):
                row = st.columns(w)
                row[0].write(p_name)
                for g_i in range(len(GAMES)):
                    label = "✕" if st.session_state.played[(p_i, g_i)] else " "
                    if row[g_i + 1].button(label, key=f"played_{p_i}_{g_i}", use_container_width=True):
                        toggle_played(p_i, g_i)
                        st.rerun()

            done, total = played_progress()
            st.write(f"**Progress:** {done}/{total}")

        st.write("---")

        # --- Score sheet ---
        st.subheader("Score sheet")
        st.caption(
            f"Rows fixed: players × 6 = **{n*6}**.\n"
            "Type round changes (delta): e.g. 5 or -4.\n"
            "After Enter, the cell shows the running total."
        )

        if mobile_mode:
            # ---- Mobile-friendly round entry ----
            st.markdown("### 📱 Quick round entry")

            n_rows = len(deltas)
            current_pos = next_incomplete_row_pos(deltas)
            row_choice = st.number_input("Round", min_value=1, max_value=n_rows, value=current_pos + 1, step=1) - 1

            st.caption("Enter each player’s round change (delta).")
            round_inputs = {}
            for p in players:
                round_inputs[p] = st.text_input(
                    p,
                    value="",
                    placeholder="e.g. 5 or -4",
                    key=f"mob_{row_choice}_{p}",
                )

            if st.button("✅ Save this round", type="primary"):
                # require all players filled
                for p in players:
                    v = round_inputs[p].strip()
                    if v == "":
                        st.warning("Fill all players for this round.")
                        st.stop()
                    try:
                        deltas.iat[row_choice, deltas.columns.get_loc(p)] = int(v)
                    except ValueError:
                        st.warning(f"Invalid number for {p}.")
                        st.stop()

                st.session_state.deltas_df = deltas
                st.session_state.score_old_view = build_view_from_deltas(deltas)

                st.success("Saved round ✅")
                st.rerun()

            st.write("---")
            st.caption("Full sheet (read-only preview on mobile):")
            preview = deltas.fillna(0).astype(int).cumsum(axis=0)
            st.dataframe(preview, use_container_width=True, height=320)

        else:
            # ---- Desktop grid editor (your preferred) ----
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

        # Totals at bottom (always visible)
        cum = compute_cumulative_from_deltas(st.session_state.deltas_df)
        final = cum.iloc[-1].fillna(0).astype(int).tolist() if len(cum) else [0] * n
        tot_cols = st.columns(n)
        for i, p in enumerate(players):
            tot_cols[i].metric(label=p, value=final[i])

        # Auto-save on completion
        if (not st.session_state.saved_current) and deltas_complete(st.session_state.deltas_df):
            night_id = save_current_game_night(auto=True)
            st.session_state.saved_current = True
            st.session_state.last_saved_id = night_id
            st.session_state.stage = "postgame"
            st.rerun()

        if st.session_state.stage == "postgame":
            st.success("✅ Score sheet complete — saved automatically with date & time.")
            b1, b2, b3 = st.columns([1.2, 1.2, 3.6])
            if b1.button("🔁 Rematch", type="primary"):
                start_rematch_same_players()
                st.rerun()
            if b2.button("🏠 Main menu"):
                reset_to_menu(keep_names=True)
                st.rerun()
            b3.caption("You can exit now. The game night is saved locally.")


# =========================
# HISTORY (delete + full scoresheet)
# =========================
elif st.session_state.view == "history":
    db = st.session_state.db
    nights = list(reversed(db.get("nights", [])))

    st.subheader("History")
    st.caption("You can return to the current game anytime using Play.")

    if not nights:
        st.info("No saved game nights yet.")
    else:
        for night in nights:
            night_id = night.get("id", "")
            dt = datetime.fromisoformat(night["timestamp"]).astimezone(TZ)
            title = f"{dt.strftime('%Y-%m-%d %H:%M:%S')} — " + ", ".join(night["players_display"])

            with st.expander(title):
                del_col1, del_col2 = st.columns([1.3, 4.7])
                if del_col1.button("🗑 Delete", key=f"delete_{night_id}"):
                    delete_night_by_id(night_id)
                    st.rerun()
                del_col2.caption("Deleting removes it from History and automatically updates Facts.")

                players = night["players_display"]
                finals = night["final_totals"]
                deltas_list = night["deltas"]

                df = pd.DataFrame(deltas_list, columns=players)
                df.index = [str(i + 1) for i in range(len(df))]

                st.caption("Deltas (round changes)")
                st.dataframe(df, use_container_width=True, height=320)

                st.caption("Running totals")
                st.dataframe(df.cumsum(axis=0), use_container_width=True, height=320)

                cols = st.columns(len(players))
                for i, p in enumerate(players):
                    cols[i].metric(label=p, value=finals[i])

                tr = night.get("played_tracker", {})
                grid = tr.get("grid")
                if isinstance(grid, list):
                    st.caption("Played tracker snapshot")
                    for p_i, p_name in enumerate(players):
                        marks = []
                        for g_i, g in enumerate(GAMES):
                            if p_i < len(grid) and g_i < len(grid[p_i]) and grid[p_i][g_i]:
                                marks.append(g["label"])
                        st.write(f"- {p_name}: " + (" ".join(marks) if marks else "—"))


# =========================
# FACTS
# =========================
else:
    db = st.session_state.db
    nights = db.get("nights", [])

    st.subheader("Facts")
    st.caption("Facts update automatically when you delete nights in History.")

    if not nights:
        st.info("Save at least one complete game night to see analytics.")
    else:
        def display_for(k: str, fallback: str) -> str:
            person = db.get("people", {}).get(k)
            if isinstance(person, dict) and person.get("display"):
                return person["display"]
            return fallback

        wins: Dict[str, int] = {}
        lasts: Dict[str, int] = {}
        records: List[Tuple[datetime, str, str, int]] = []

        for night in nights:
            dt = datetime.fromisoformat(night["timestamp"]).astimezone(TZ)
            keys = night["players_keys"]
            displays = night["players_display"]
            totals = night["final_totals"]
            if not totals:
                continue

            min_score = min(totals)  # lowest = best
            max_score = max(totals)  # highest = worst

            for k, d, s in zip(keys, displays, totals):
                if not k:
                    continue
                wins[k] = wins.get(k, 0) + (1 if s == min_score else 0)
                lasts[k] = lasts.get(k, 0) + (1 if s == max_score else 0)
                records.append((dt, k, d, int(s)))

        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### 🏆 Most wins (lowest final score)")
            if wins:
                m = max(wins.values())
                top = [k for k, v in wins.items() if v == m]
                st.write(", ".join(display_for(k, k) for k in top) + f" — {m}")
            else:
                st.write("—")

        with c2:
            st.markdown("### 🧱 Most last-place finishes (highest final score)")
            if lasts:
                m = max(lasts.values())
                top = [k for k, v in lasts.items() if v == m]
                st.write(", ".join(display_for(k, k) for k in top) + f" — {m}")
            else:
                st.write("—")

        st.write("---")
        st.markdown("### 📈 Extremes")
        st.caption("Lowest = best (good). Highest = worst (bad).")

        now = datetime.now(TZ)
        week_key = now.isocalendar()[:2]
        month_key = (now.year, now.month)

        def period_records(kind: str):
            if kind == "week":
                return [r for r in records if r[0].isocalendar()[:2] == week_key]
            if kind == "month":
                return [r for r in records if (r[0].year, r[0].month) == month_key]
            return records

        def show_extremes(label: str, recs: List[Tuple[datetime, str, str, int]]):
            if not recs:
                st.info(f"No records for {label}.")
                return
            low = min(recs, key=lambda x: x[3])
            high = max(recs, key=lambda x: x[3])

            low_name = display_for(low[1], low[2])
            high_name = display_for(high[1], high[2])

            a, b = st.columns(2)
            a.metric(f"Lowest ({label}) ✅", low[3])
            a.caption(f"{low_name} — {low[0].strftime('%Y-%m-%d %H:%M')}")
            b.metric(f"Highest ({label}) ❌", high[3])
            b.caption(f"{high_name} — {high[0].strftime('%Y-%m-%d %H:%M')}")

        st.markdown("#### This week")
        show_extremes("this week", period_records("week"))

        st.markdown("#### This month")
        show_extremes("this month", period_records("month"))

        st.markdown("#### All time")
        show_extremes("all time", period_records("all"))
