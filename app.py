import hashlib
import json
import random
from datetime import datetime, timezone

import pandas as pd
import streamlit as st
from supabase import create_client


# -----------------------------
# Konfiguration
# -----------------------------
TABLE_NAME = "cards"

REQUIRED_SUPABASE_COLUMNS = [
    "id",
    "kategorie",
    "italienisch",
    "deutsch",
    "richtung",
    "rating",
    "richtig",
    "falsch",
    "letzte_abfrage",
]

EXCEL_TO_DB_COLUMNS = {
    "ID": "id",
    "Kategorie": "kategorie",
    "Italienisch": "italienisch",
    "Deutsch": "deutsch",
    "Richtung": "richtung",
    "Rating": "rating",
    "Richtig": "richtig",
    "Falsch": "falsch",
    "Letzte_Abfrage": "letzte_abfrage",
}


st.set_page_config(
    page_title="Italienisch Lern-Tool",
    page_icon="🇮🇹",
    layout="centered",
    initial_sidebar_state="collapsed",
)

# -----------------------------
# CSS
# -----------------------------
st.markdown(
    """
<style>
html, body, [data-testid="stAppViewContainer"] { background:#f7f8fb; }
.block-container{max-width:520px;padding:.45rem .55rem .8rem .55rem;}
header[data-testid="stHeader"], [data-testid="stToolbar"]{display:none;}
div[data-testid="stSidebar"]{display:none;}
div[data-testid="stVerticalBlock"]{gap:.35rem;}
div[data-testid="stHorizontalBlock"]{gap:.45rem;}
.app-title-row{display:flex;align-items:center;justify-content:space-between;margin-bottom:.45rem;}
.app-title{font-size:1.45rem;font-weight:900;letter-spacing:-.04em;color:#111827;}
.tiny-pill{border:1px solid #e5e7eb;background:white;border-radius:999px;padding:.32rem .55rem;font-size:.76rem;color:#6b7280;}
.status-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:.32rem;margin-bottom:.45rem;}
.status-card{background:white;border:1px solid #e5e7eb;border-radius:13px;padding:.42rem .18rem;text-align:center;min-height:52px;box-shadow:0 1px 2px rgba(0,0,0,.03);}
.status-label{color:#6b7280;font-size:.6rem;line-height:1.05;margin-bottom:.17rem;}
.status-value{color:#111827;font-weight:900;font-size:1.05rem;line-height:1.05;}
.question-card{background:white;border:1px solid #e5e7eb;border-radius:18px;padding:.75rem .7rem .82rem;text-align:center;margin-bottom:.35rem;box-shadow:0 3px 12px rgba(17,24,39,.04);}
.question-meta{color:#2563eb;font-weight:700;font-size:.76rem;margin-bottom:.42rem;}
.question-text{color:#111827;font-size:clamp(1.25rem,6.4vw,2rem);font-weight:900;line-height:1.2;letter-spacing:-.025em;min-height:3rem;display:flex;align-items:center;justify-content:center;}
.solution-card{background:#eef6ff;border:1px solid #bfdbfe;border-radius:15px;padding:.62rem .75rem;margin-top:.55rem;}
.solution-label{color:#1d4ed8;font-size:.7rem;font-weight:800;margin-bottom:.2rem;}
.solution-text{color:#111827;font-size:1.12rem;font-weight:800;line-height:1.28;}
div[data-testid="stTextArea"] label{font-size:.76rem;color:#6b7280;font-weight:700;}
textarea{min-height:62px!important;max-height:74px!important;border-radius:15px!important;font-size:1rem!important;background:white!important;}
.stButton>button{width:100%;border-radius:15px;min-height:2.75rem;font-size:.94rem;font-weight:850;border:1px solid #e5e7eb;box-shadow:0 1px 3px rgba(0,0,0,.04);}
.small-action button{min-height:2.35rem!important;font-size:.82rem!important;font-weight:850!important;border-radius:13px!important;}
.settings-box{background:white;border:1px solid #e5e7eb;border-radius:18px;padding:.85rem;margin:.55rem 0;box-shadow:0 3px 12px rgba(17,24,39,.04);}
.settings-title{font-size:1.15rem;font-weight:900;margin-bottom:.4rem;color:#111827;}
.settings-note{font-size:.75rem;color:#6b7280;line-height:1.25;margin-bottom:.55rem;}
.notice{border:1px solid #bbf7d0;background:#f0fdf4;color:#166534;border-radius:13px;padding:.48rem .62rem;font-size:.72rem;line-height:1.2;margin-top:.35rem;}
.audio-wrap button{
    width:100%;
    border-radius:15px;
    min-height:2.75rem;
    font-size:.94rem;
    font-weight:850;
    border:1px solid #e5e7eb;
    box-shadow:0 1px 3px rgba(0,0,0,.04);
    background:white;
    color:#111827;
}
.audio-wrap button:active{ transform:scale(.99); }
@media (max-height: 760px){
  .question-card{padding:.62rem .65rem;}
  .question-text{font-size:1.25rem;min-height:2.35rem;}
  textarea{min-height:52px!important;max-height:58px!important;}
  .stButton>button{min-height:2.45rem;}
  .status-card{min-height:48px;padding:.35rem .15rem;}
  .notice{display:none;}
}
</style>
""",
    unsafe_allow_html=True,
)


# -----------------------------
# Supabase Verbindung
# -----------------------------
def get_supabase_client():
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
    except Exception:
        st.error(
            "Supabase Secrets fehlen. Bitte in Streamlit unter Settings → Secrets "
            "SUPABASE_URL und SUPABASE_KEY eintragen."
        )
        st.stop()

    return create_client(url, key)


supabase = get_supabase_client()


# -----------------------------
# Hilfsfunktionen
# -----------------------------
def render_audio_button(text_to_speak: str):
    """Italian pronunciation using browser speech synthesis."""
    safe_text = json.dumps(text_to_speak or "")
    function_name = "speakItalian_" + hashlib.sha1(
        (text_to_speak or "").encode("utf-8")
    ).hexdigest()[:12]

    st.html(
        f"""
        <div class="audio-wrap">
          <button type="button" onclick="window.{function_name}()">🔊 Ton</button>
        </div>
        <script>
        window.{function_name} = function() {{
            const text = {safe_text};
            if (!text || !("speechSynthesis" in window)) return;

            window.speechSynthesis.cancel();

            const utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = "it-IT";
            utterance.rate = 0.86;
            utterance.pitch = 1.0;

            const voices = window.speechSynthesis.getVoices();
            const italianVoice = voices.find(
                voice => voice.lang && voice.lang.toLowerCase().startsWith("it")
            );
            if (italianVoice) utterance.voice = italianVoice;

            window.speechSynthesis.speak(utterance);
        }};
        </script>
        """,
        unsafe_allow_javascript=True,
    )

def normalize_cards_df(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize either Excel-style columns or Supabase-style columns and remove all NaN values."""
    df = df.copy()

    # Rename Excel columns if present
    rename_map = {col: EXCEL_TO_DB_COLUMNS[col] for col in df.columns if col in EXCEL_TO_DB_COLUMNS}
    df = df.rename(columns=rename_map)

    for col in REQUIRED_SUPABASE_COLUMNS:
        if col not in df.columns:
            if col == "rating":
                df[col] = 50
            elif col in ["richtig", "falsch"]:
                df[col] = 0
            elif col == "richtung":
                df[col] = "DE-IT"
            elif col == "letzte_abfrage":
                df[col] = None
            else:
                df[col] = ""

    df = df[REQUIRED_SUPABASE_COLUMNS].copy()

    df["id"] = pd.to_numeric(df["id"], errors="coerce")
    df = df.dropna(subset=["id"])
    df["id"] = df["id"].astype(int)

    for col, default in [("rating", 50), ("richtig", 0), ("falsch", 0)]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default).astype(int)

    for col in ["kategorie", "italienisch", "deutsch", "richtung"]:
        df[col] = df[col].fillna("").astype(str)

    df.loc[df["richtung"].eq(""), "richtung"] = "DE-IT"

    # Clean timestamp column: invalid/empty values must become None, never NaN/NaT
    df["letzte_abfrage"] = pd.to_datetime(df["letzte_abfrage"], errors="coerce")
    df["letzte_abfrage"] = df["letzte_abfrage"].apply(
        lambda value: value.isoformat() if pd.notnull(value) else None
    )

    # Final JSON-safe cleanup. Supabase rejects float NaN values.
    df = df.astype(object)
    df = df.where(pd.notnull(df), None)

    return df.sort_values("id").reset_index(drop=True)

def load_cards_from_supabase() -> pd.DataFrame:
    response = supabase.table(TABLE_NAME).select("*").order("id").execute()
    data = response.data or []
    if not data:
        return pd.DataFrame(columns=REQUIRED_SUPABASE_COLUMNS)
    return normalize_cards_df(pd.DataFrame(data))


def upsert_cards_to_supabase(df: pd.DataFrame):
    df = normalize_cards_df(df)
    # Ensure no NaN survives into JSON payload
    df = df.astype(object).where(pd.notnull(df), None)
    records = df.to_dict(orient="records")

    # Supabase/PostgREST payloads should be chunked
    chunk_size = 500
    for i in range(0, len(records), chunk_size):
        chunk = records[i : i + chunk_size]
        supabase.table(TABLE_NAME).upsert(chunk, on_conflict="id").execute()


def update_card_in_supabase(card_id: int, rating: int, richtig: int, falsch: int):
    now = datetime.now(timezone.utc).isoformat()
    supabase.table(TABLE_NAME).update(
        {
            "rating": int(rating),
            "richtig": int(richtig),
            "falsch": int(falsch),
            "letzte_abfrage": now,
        }
    ).eq("id", int(card_id)).execute()


def weighted_pick(df: pd.DataFrame, low_rating_chance: float, weighting_strength: float) -> pd.Series:
    if random.random() < low_rating_chance:
        low_part = df[df["rating"] <= df["rating"].quantile(0.35)]
        if not low_part.empty:
            return low_part.sample(1).iloc[0]

    weights = df["rating"].clip(lower=1).astype(float) ** float(weighting_strength)
    return df.sample(1, weights=weights).iloc[0]


def get_question_answer(row: dict, mode: str):
    direction = random.choice(["IT-DE", "DE-IT"]) if mode == "Gemischt" else mode

    if direction == "IT-DE":
        return row["italienisch"], row["deutsch"], "Übersetze auf Deutsch", row["italienisch"]

    return row["deutsch"], row["italienisch"], "Übersetze auf Italienisch", row["italienisch"]


def default_settings(min_id: int, max_id: int):
    return {
        "id_von": min_id,
        "id_bis": max_id,
        "direction_mode": "DE-IT",
        "low_rating_chance_int": 10,
        "weighting_strength": 1.3,
        "rating_reduction_correct": 5,
        "rating_increase_wrong": 10,
        "min_rating": 1,
        "max_rating": 100,
    }


def load_settings_from_supabase(defaults: dict) -> dict:
    """Load app settings from Supabase table settings. Falls back to defaults."""
    try:
        response = supabase.table("settings").select("value").eq("key", "app_settings").execute()
        if response.data and len(response.data) > 0 and response.data[0].get("value"):
            saved = response.data[0]["value"]
            merged = defaults.copy()
            merged.update(saved)
            return merged
    except Exception:
        pass
    return defaults.copy()


def save_settings_to_supabase(settings: dict):
    """Persist app settings in Supabase."""
    clean_settings = {
        "id_von": int(settings.get("id_von", 1)),
        "id_bis": int(settings.get("id_bis", 1000)),
        "direction_mode": str(settings.get("direction_mode", "DE-IT")),
        "low_rating_chance_int": int(settings.get("low_rating_chance_int", 10)),
        "weighting_strength": float(settings.get("weighting_strength", 1.3)),
        "rating_reduction_correct": int(settings.get("rating_reduction_correct", 5)),
        "rating_increase_wrong": int(settings.get("rating_increase_wrong", 10)),
        "min_rating": int(settings.get("min_rating", 1)),
        "max_rating": int(settings.get("max_rating", 100)),
    }
    supabase.table("settings").upsert(
        {"key": "app_settings", "value": clean_settings},
        on_conflict="key",
    ).execute()


def reset_card():
    st.session_state.current_card = None
    st.session_state.show_solution = False


def refresh_cards():
    st.session_state.cards = load_cards_from_supabase()
    reset_card()


# -----------------------------
# Session State
# -----------------------------
if "cards" not in st.session_state:
    st.session_state.cards = load_cards_from_supabase()

cards = st.session_state.cards

if cards.empty:
    st.warning("Die Supabase-Tabelle ist noch leer. Lade unter ⚙ Einstellungen deine Excel-Bibliothek hoch.")
    if "show_settings" not in st.session_state:
        st.session_state.show_settings = True

if "show_settings" not in st.session_state:
    st.session_state.show_settings = False

if "show_stats" not in st.session_state:
    st.session_state.show_stats = False

if "show_solution" not in st.session_state:
    st.session_state.show_solution = False

if "current_card" not in st.session_state:
    st.session_state.current_card = None

if "settings" not in st.session_state:
    if cards.empty:
        defaults = default_settings(1, 1000)
    else:
        defaults = default_settings(int(cards["id"].min()), int(cards["id"].max()))
    st.session_state.settings = load_settings_from_supabase(defaults)


# -----------------------------
# Einstellungen-Ansicht
# -----------------------------
if st.session_state.show_settings:
    s = st.session_state.settings.copy()
    min_id_available = int(cards["id"].min()) if not cards.empty else 1
    max_id_available = int(cards["id"].max()) if not cards.empty else 1000

    st.markdown(
        """
        <div class="settings-box">
          <div class="settings-title">⚙ Einstellungen</div>
          <div class="settings-note">Supabase ist aktiv. Ratings werden dauerhaft in der Datenbank gespeichert.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if st.button("← Zurück zur Abfrage"):
        st.session_state.show_settings = False
        st.rerun()

    with st.form("settings_form", clear_on_submit=False):
        st.subheader("Abfrage")

        c1, c2 = st.columns(2)
        with c1:
            form_id_von = st.number_input(
                "ID von",
                min_value=1,
                max_value=max_id_available,
                value=max(1, min(int(s.get("id_von", min_id_available)), max_id_available)),
                step=1,
            )
        with c2:
            form_id_bis = st.number_input(
                "ID bis",
                min_value=1,
                max_value=max_id_available,
                value=max(1, min(int(s.get("id_bis", max_id_available)), max_id_available)),
                step=1,
            )

        direction_options = ["DE-IT", "IT-DE", "Gemischt"]
        form_direction = st.selectbox(
            "Abfragerichtung",
            direction_options,
            index=direction_options.index(s.get("direction_mode", "DE-IT"))
            if s.get("direction_mode", "DE-IT") in direction_options
            else 0,
        )

        st.subheader("Wahrscheinlichkeit / Gewichtung")
        form_low = st.slider("Chance für tiefe Ratings (%)", 0, 50, int(s.get("low_rating_chance_int", 10)), 1)
        form_weight = st.slider(
            "Stärke der Rating-Gewichtung",
            1.0,
            3.0,
            float(s.get("weighting_strength", 1.3)),
            0.1,
        )

        st.subheader("Rating-Logik")
        st.caption("Richtig senkt das Rating, falsch erhöht es. Hohe Ratings werden häufiger abgefragt.")
        c3, c4 = st.columns(2)
        with c3:
            form_reduce = st.number_input(
                "Rating reduzieren bei richtig",
                1,
                50,
                int(s.get("rating_reduction_correct", 5)),
                1,
            )
        with c4:
            form_increase = st.number_input(
                "Rating erhöhen bei falsch",
                1,
                50,
                int(s.get("rating_increase_wrong", 10)),
                1,
            )

        c5, c6 = st.columns(2)
        with c5:
            form_min_rating = st.number_input("Mindest-Rating", 1, 100, int(s.get("min_rating", 1)), 1)
        with c6:
            form_max_rating = st.number_input("Maximal-Rating", 10, 500, int(s.get("max_rating", 100)), 5)

        submitted = st.form_submit_button("Einstellungen speichern")

    if submitted:
        new_settings = {
            "id_von": int(form_id_von),
            "id_bis": int(form_id_bis),
            "direction_mode": form_direction,
            "low_rating_chance_int": int(form_low),
            "weighting_strength": float(form_weight),
            "rating_reduction_correct": int(form_reduce),
            "rating_increase_wrong": int(form_increase),
            "min_rating": int(form_min_rating),
            "max_rating": int(form_max_rating),
        }

        if new_settings["id_von"] > new_settings["id_bis"]:
            new_settings["id_bis"] = new_settings["id_von"]

        st.session_state.settings = new_settings
        save_settings_to_supabase(new_settings)
        reset_card()
        st.success("Einstellungen gespeichert und dauerhaft in Supabase übernommen.")

    st.subheader("Bibliothek / Supabase Import")

    uploaded = st.file_uploader("Excel-Bibliothek nach Supabase importieren", type=["xlsx"])
    if uploaded is not None:
        try:
            excel_df = pd.read_excel(uploaded, sheet_name="Bibliothek")
            normalized = normalize_cards_df(excel_df)
            upsert_cards_to_supabase(normalized)
            refresh_cards()
            st.success(f"{len(normalized)} Karten nach Supabase importiert.")
            st.rerun()
        except Exception as exc:
            st.error(f"Import fehlgeschlagen: {exc}")

    if not cards.empty:
        export_df = cards.rename(
            columns={
                "id": "ID",
                "kategorie": "Kategorie",
                "italienisch": "Italienisch",
                "deutsch": "Deutsch",
                "richtung": "Richtung",
                "rating": "Rating",
                "richtig": "Richtig",
                "falsch": "Falsch",
                "letzte_abfrage": "Letzte_Abfrage",
            }
        )

        output = pd.ExcelWriter("italienisch_bibliothek_export.xlsx", engine="openpyxl")
        export_df.to_excel(output, sheet_name="Bibliothek", index=False)
        output.close()

        with open("italienisch_bibliothek_export.xlsx", "rb") as f:
            st.download_button(
                "Aktuelle Bibliothek aus Supabase herunterladen",
                f.read(),
                "italienisch_bibliothek_supabase_export.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    if st.button("Daten aus Supabase neu laden"):
        refresh_cards()
        st.rerun()

    st.stop()


# -----------------------------
# Hauptansicht
# -----------------------------
cards = st.session_state.cards
if cards.empty:
    st.stop()

s = st.session_state.settings

id_von = int(s["id_von"])
id_bis = int(s["id_bis"])
direction_mode = s["direction_mode"]
low_rating_chance = int(s["low_rating_chance_int"]) / 100
weighting_strength = float(s["weighting_strength"])
rating_reduction_correct = int(s["rating_reduction_correct"])
rating_increase_wrong = int(s["rating_increase_wrong"])
min_rating = int(s["min_rating"])
max_rating = int(s["max_rating"])

filtered = cards[(cards["id"] >= id_von) & (cards["id"] <= id_bis)].copy()

if filtered.empty:
    st.warning("Keine Karten im gewählten ID-Bereich.")
    if st.button("⚙ Einstellungen öffnen"):
        st.session_state.show_settings = True
        st.rerun()
    st.stop()


def next_card():
    chosen = weighted_pick(filtered, low_rating_chance, weighting_strength)
    st.session_state.current_card = chosen.to_dict()
    st.session_state.show_solution = False


if st.session_state.current_card is None:
    next_card()

card = st.session_state.current_card
question, answer, label, audio_text = get_question_answer(card, direction_mode)

progress = max(0, min(100, round(((int(card["id"]) - id_von + 1) / max((id_bis - id_von + 1), 1)) * 100)))

st.markdown(
    f"""
<div class="app-title-row"><div class="app-title">🇮🇹 Italienisch</div><div class="tiny-pill">{len(filtered)} Karten</div></div>
<div class="status-grid">
<div class="status-card"><div class="status-label">ID</div><div class="status-value">{int(card["id"])}</div></div>
<div class="status-card"><div class="status-label">Rating</div><div class="status-value">{int(card["rating"])}</div></div>
<div class="status-card"><div class="status-label">Fehler</div><div class="status-value">{int(card["falsch"])}</div></div>
<div class="status-card"><div class="status-label">Bereich</div><div class="status-value">{progress}%</div></div>
</div>
<div class="question-card">
<div class="question-meta">ID {int(card["id"])} · {label}</div>
<div class="question-text">{question}</div>
{("<div class='solution-card'><div class='solution-label'>Lösung</div><div class='solution-text'>" + answer + "</div></div>") if st.session_state.show_solution else ""}
</div>
""",
    unsafe_allow_html=True,
)

st.text_area("Deine Antwort", placeholder="Hier deine Übersetzung eingeben ...", key="user_answer")

c1, c2, c3 = st.columns(3)
with c1:
    if st.button("💡 Auflösen"):
        st.session_state.show_solution = True
        st.rerun()

with c2:
    render_audio_button(audio_text)

with c3:
    if st.button("▶ Weiter"):
        next_card()
        st.rerun()

r1, r2 = st.columns(2)
with r1:
    if st.button("✕ Falsch / Schwer"):
        new_rating = min(max_rating, int(card["rating"]) + rating_increase_wrong)
        new_richtig = int(card["richtig"])
        new_falsch = int(card["falsch"]) + 1

        update_card_in_supabase(card["id"], new_rating, new_richtig, new_falsch)
        refresh_cards()
        next_card()
        st.rerun()

with r2:
    if st.button("✓ Richtig / Einfach"):
        new_rating = max(min_rating, int(card["rating"]) - rating_reduction_correct)
        new_richtig = int(card["richtig"]) + 1
        new_falsch = int(card["falsch"])

        update_card_in_supabase(card["id"], new_rating, new_richtig, new_falsch)
        refresh_cards()
        next_card()
        st.rerun()

st.markdown('<div class="small-action">', unsafe_allow_html=True)
b1, b2 = st.columns(2)
with b1:
    if st.button("📊 Statistik"):
        st.session_state.show_stats = not st.session_state.show_stats
        st.rerun()

with b2:
    if st.button("⚙ Einstellungen"):
        st.session_state.show_settings = True
        st.rerun()
st.markdown("</div>", unsafe_allow_html=True)

if st.session_state.show_stats:
    with st.expander("Statistik / schwierigste Sätze", expanded=True):
        hard = filtered.sort_values(["rating", "falsch"], ascending=False).head(20)
        st.dataframe(
            hard[["id", "kategorie", "italienisch", "deutsch", "rating", "richtig", "falsch", "letzte_abfrage"]],
            use_container_width=True,
            hide_index=True,
        )

st.markdown('<div class="notice">Supabase aktiv: Ratings und Einstellungen werden dauerhaft gespeichert.</div>', unsafe_allow_html=True)
