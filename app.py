import hashlib
import random
import shutil
from datetime import datetime
from pathlib import Path

import pandas as pd
import streamlit as st


DATA_FILE = Path("italienisch_bibliothek.xlsx")
BACKUP_DIR = Path("backups")
SHEET_LIBRARY = "Bibliothek"

REQUIRED_COLUMNS = [
    "ID",
    "Kategorie",
    "Italienisch",
    "Deutsch",
    "Richtung",
    "Rating",
    "Richtig",
    "Falsch",
    "Letzte_Abfrage",
]

st.set_page_config(
    page_title="Italienisch Lern-Tool",
    page_icon="🇮🇹",
    layout="centered",
    initial_sidebar_state="collapsed",
)

CUSTOM_CSS = """
<style>
.block-container {
    max-width: 760px;
    padding-top: 1.2rem;
    padding-bottom: 4rem;
}
.stButton > button {
    width: 100%;
    min-height: 3.2rem;
    border-radius: 14px;
    font-size: 1.05rem;
    font-weight: 650;
}
textarea {
    font-size: 1.05rem !important;
}
.big-card {
    border: 1px solid rgba(49,51,63,.15);
    border-radius: 18px;
    padding: 1.2rem;
    margin: .6rem 0 1rem 0;
    background: rgba(250,250,250,.75);
}
.prompt-text {
    font-size: 1.45rem;
    line-height: 1.45;
    font-weight: 700;
}
.solution-text {
    font-size: 1.2rem;
    line-height: 1.45;
    font-weight: 600;
}
.small-note {
    color: #666;
    font-size: .9rem;
}
.warning-box {
    border: 1px solid #f2c94c;
    background: #fff9e6;
    border-radius: 14px;
    padding: .8rem 1rem;
    margin: .6rem 0 1rem 0;
}
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


def optional_password_gate() -> None:
    """Protect the app if APP_PASSWORD is set in Streamlit secrets."""
    password = None
    try:
        password = st.secrets.get("APP_PASSWORD", None)
    except Exception:
        password = None

    if not password:
        return

    if st.session_state.get("authenticated", False):
        return

    st.title("🇮🇹 Italienisch Lern-Tool")
    st.subheader("Login")
    entered = st.text_input("Passwort", type="password")
    if st.button("Einloggen"):
        if hashlib.sha256(entered.encode()).hexdigest() == hashlib.sha256(str(password).encode()).hexdigest():
            st.session_state.authenticated = True
            st.rerun()
        else:
            st.error("Falsches Passwort.")
    st.stop()


def normalize_library(df: pd.DataFrame) -> pd.DataFrame:
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            if col == "Rating":
                df[col] = 50
            elif col in ["Richtig", "Falsch"]:
                df[col] = 0
            elif col == "Richtung":
                df[col] = "IT-DE"
            else:
                df[col] = ""

    df = df[REQUIRED_COLUMNS].copy()
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    df = df.dropna(subset=["ID"])
    df["ID"] = df["ID"].astype(int)
    df["Rating"] = pd.to_numeric(df["Rating"], errors="coerce").fillna(50).astype(int)
    df["Richtig"] = pd.to_numeric(df["Richtig"], errors="coerce").fillna(0).astype(int)
    df["Falsch"] = pd.to_numeric(df["Falsch"], errors="coerce").fillna(0).astype(int)
    df["Kategorie"] = df["Kategorie"].fillna("").astype(str)
    df["Italienisch"] = df["Italienisch"].fillna("").astype(str)
    df["Deutsch"] = df["Deutsch"].fillna("").astype(str)
    df["Richtung"] = df["Richtung"].fillna("IT-DE").astype(str)
    df["Letzte_Abfrage"] = df["Letzte_Abfrage"].fillna("").astype(str)
    return df.sort_values("ID").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def load_library_from_disk(file_mtime: float) -> pd.DataFrame:
    if not DATA_FILE.exists():
        return pd.DataFrame(columns=REQUIRED_COLUMNS)
    df = pd.read_excel(DATA_FILE, sheet_name=SHEET_LIBRARY)
    return normalize_library(df)


def load_library() -> pd.DataFrame:
    mtime = DATA_FILE.stat().st_mtime if DATA_FILE.exists() else 0
    return load_library_from_disk(mtime)


def make_backup() -> Path | None:
    if not DATA_FILE.exists():
        return None
    BACKUP_DIR.mkdir(exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = BACKUP_DIR / f"italienisch_bibliothek_backup_{stamp}.xlsx"
    shutil.copy(DATA_FILE, backup_path)
    return backup_path


def save_library(df: pd.DataFrame, make_file_backup: bool = False) -> None:
    df = normalize_library(df)
    if make_file_backup:
        make_backup()
    with pd.ExcelWriter(DATA_FILE, engine="openpyxl", mode="w") as writer:
        df.to_excel(writer, sheet_name=SHEET_LIBRARY, index=False)
    st.cache_data.clear()


def weighted_pick(df: pd.DataFrame, low_rating_chance: float, weighting_strength: float) -> pd.Series:
    if df.empty:
        raise ValueError("Keine Einträge im gewählten Bereich.")

    # With this probability, easy cards are intentionally repeated.
    if random.random() < low_rating_chance:
        low_part = df[df["Rating"] <= df["Rating"].quantile(0.35)]
        if not low_part.empty:
            return low_part.sample(1).iloc[0]

    # Normal weighted draw. Strength > 1 makes difficult cards dominate more.
    weights = df["Rating"].clip(lower=1).astype(float) ** weighting_strength
    return df.sample(1, weights=weights).iloc[0]


def get_question_and_answer(row: pd.Series, direction_mode: str) -> tuple[str, str, str]:
    if direction_mode == "Gemischt":
        direction = random.choice(["IT-DE", "DE-IT"])
    else:
        direction = direction_mode

    if direction == "IT-DE":
        return row["Italienisch"], row["Deutsch"], "Übersetze auf Deutsch"
    return row["Deutsch"], row["Italienisch"], "Übersetze auf Italienisch"


def reset_current_card() -> None:
    st.session_state.current_id = None
    st.session_state.show_solution = False
    st.session_state.question = ""
    st.session_state.answer = ""
    st.session_state.task_label = ""


optional_password_gate()

if "df" not in st.session_state:
    st.session_state.df = load_library()
if "current_id" not in st.session_state:
    reset_current_card()

st.title("🇮🇹 Italienisch Lern-Tool")
st.caption("Spaced-Repetition mit Rating-System, ID-Bereich und mobiler Abfrageansicht.")

with st.sidebar:
    st.header("Einstellungen")

    df_all = st.session_state.df
    min_id_available = int(df_all["ID"].min()) if not df_all.empty else 1
    max_id_available = int(df_all["ID"].max()) if not df_all.empty else 1000

    id_von = st.number_input("ID von", min_value=1, value=min_id_available, step=1)
    id_bis = st.number_input("ID bis", min_value=1, value=max_id_available, step=1)
    direction_mode = st.selectbox("Abfragerichtung", ["DE-IT", "IT-DE", "Gemischt"], index=0)

    low_rating_chance = st.slider(
        "Chance für tiefe Ratings",
        min_value=0,
        max_value=50,
        value=10,
        step=1,
        help="Damit einfache Sätze ab und zu trotzdem wiederholt werden.",
    ) / 100

    weighting_strength = st.slider(
        "Stärke der Rating-Gewichtung",
        min_value=1.0,
        max_value=3.0,
        value=1.0,
        step=0.1,
        help="1.0 = linear. Höher = schwierige Karten werden aggressiver bevorzugt.",
    )

    richtig_abzug = st.number_input("Rating-Abzug bei richtig", min_value=1, max_value=50, value=5, step=1)
    falsch_zuschlag = st.number_input("Rating-Zuschlag bei falsch", min_value=1, max_value=50, value=10, step=1)
    min_rating = st.number_input("Mindest-Rating", min_value=1, max_value=100, value=1, step=1)
    max_rating = st.number_input("Maximal-Rating", min_value=10, max_value=500, value=100, step=5)

    st.divider()
    st.header("Bibliothek / Backup")

    uploaded = st.file_uploader("Neue Excel-Bibliothek hochladen", type=["xlsx"])
    if uploaded is not None:
        try:
            new_df = pd.read_excel(uploaded, sheet_name=SHEET_LIBRARY)
            new_df = normalize_library(new_df)
            make_backup()
            save_library(new_df)
            st.session_state.df = new_df
            reset_current_card()
            st.success("Bibliothek geladen und gespeichert.")
            st.rerun()
        except Exception as e:
            st.error(f"Upload konnte nicht verarbeitet werden: {e}")

    if DATA_FILE.exists():
        with open(DATA_FILE, "rb") as f:
            st.download_button(
                "Aktuelle Bibliothek herunterladen",
                data=f.read(),
                file_name="italienisch_bibliothek_aktuell.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    if st.button("Backup jetzt erstellen"):
        path = make_backup()
        if path:
            st.success(f"Backup erstellt: {path.name}")
        else:
            st.warning("Keine Bibliothek gefunden.")

    if st.button("Bibliothek von Disk neu laden"):
        st.session_state.df = load_library()
        reset_current_card()
        st.success("Neu geladen.")
        st.rerun()

df = st.session_state.df
filtered = df[(df["ID"] >= id_von) & (df["ID"] <= id_bis)].copy()

col1, col2, col3 = st.columns(3)
col1.metric("Einträge", len(filtered))
col2.metric("Ø Rating", round(filtered["Rating"].mean(), 1) if not filtered.empty else "-")
col3.metric("Fehler", int(filtered["Falsch"].sum()) if not filtered.empty else 0)

st.markdown(
    """
    <div class="warning-box">
    <strong>Online-Hinweis:</strong> Bei Streamlit Community Cloud ist der Dateispeicher nicht als dauerhafte Datenbank gedacht.
    Lade deshalb regelmässig die aktuelle Bibliothek als Backup herunter.
    </div>
    """,
    unsafe_allow_html=True,
)


def next_card():
    chosen = weighted_pick(filtered, low_rating_chance, weighting_strength)
    q, a, label = get_question_and_answer(chosen, direction_mode)
    st.session_state.current_id = int(chosen["ID"])
    st.session_state.question = q
    st.session_state.answer = a
    st.session_state.task_label = label
    st.session_state.show_solution = False


def update_card(was_correct: bool):
    current_id = st.session_state.current_id
    if current_id is None:
        return

    idx_matches = st.session_state.df.index[st.session_state.df["ID"] == current_id]
    if len(idx_matches) == 0:
        return
    idx = idx_matches[0]

    old_rating = int(st.session_state.df.at[idx, "Rating"])
    if was_correct:
        st.session_state.df.at[idx, "Rating"] = max(min_rating, old_rating - richtig_abzug)
        st.session_state.df.at[idx, "Richtig"] = int(st.session_state.df.at[idx, "Richtig"]) + 1
    else:
        st.session_state.df.at[idx, "Rating"] = min(max_rating, old_rating + falsch_zuschlag)
        st.session_state.df.at[idx, "Falsch"] = int(st.session_state.df.at[idx, "Falsch"]) + 1

    st.session_state.df.at[idx, "Letzte_Abfrage"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_library(st.session_state.df, make_file_backup=False)
    next_card()


if filtered.empty:
    st.warning("Keine Einträge im gewählten ID-Bereich. Bitte Bibliothek oder ID-Bereich prüfen.")
else:
    if st.session_state.current_id is None:
        next_card()

    st.markdown(
        f"""
        <div class="big-card">
            <div class="small-note">ID {st.session_state.current_id} · {st.session_state.task_label}</div>
            <div class="prompt-text">{st.session_state.question}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.text_area("Deine Antwort", height=120, placeholder="Hier deine Übersetzung eingeben ...", key="user_answer")

    c1, c2 = st.columns(2)
    with c1:
        if st.button("Auflösen"):
            st.session_state.show_solution = True
    with c2:
        if st.button("Nächster Satz"):
            next_card()
            st.rerun()

    if st.session_state.show_solution:
        st.markdown(
            f"""
            <div class="big-card">
                <div class="small-note">Lösung</div>
                <div class="solution-text">{st.session_state.answer}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        r1, r2 = st.columns(2)
        with r1:
            if st.button("✅ Richtig"):
                update_card(True)
                st.rerun()
        with r2:
            if st.button("❌ Falsch"):
                update_card(False)
                st.rerun()

    with st.expander("Statistik / schwierigste Sätze"):
        hard = filtered.sort_values(["Rating", "Falsch"], ascending=False).head(20)
        st.dataframe(
            hard[["ID", "Kategorie", "Italienisch", "Deutsch", "Rating", "Richtig", "Falsch", "Letzte_Abfrage"]],
            use_container_width=True,
            hide_index=True,
        )
