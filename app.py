import hashlib, random, shutil
from datetime import datetime
from pathlib import Path
import pandas as pd
import streamlit as st

DATA_FILE = Path("italienisch_bibliothek.xlsx")
BACKUP_DIR = Path("backups")
SHEET_LIBRARY = "Bibliothek"
REQUIRED_COLUMNS = ["ID","Kategorie","Italienisch","Deutsch","Richtung","Rating","Richtig","Falsch","Letzte_Abfrage"]

st.set_page_config(page_title="Italienisch Lern-Tool", page_icon="🇮🇹", layout="centered", initial_sidebar_state="collapsed")

st.markdown("""
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
.notice{border:1px solid #fde68a;background:#fffbeb;color:#78350f;border-radius:13px;padding:.48rem .62rem;font-size:.72rem;line-height:1.2;margin-top:.35rem;}
@media (max-height: 760px){
  .question-card{padding:.62rem .65rem;}
  .question-text{font-size:1.25rem;min-height:2.35rem;}
  textarea{min-height:52px!important;max-height:58px!important;}
  .stButton>button{min-height:2.45rem;}
  .status-card{min-height:48px;padding:.35rem .15rem;}
  .notice{display:none;}
}
</style>
""", unsafe_allow_html=True)

def optional_password_gate():
    try: password = st.secrets.get("APP_PASSWORD", None)
    except Exception: password = None
    if not password or st.session_state.get("authenticated", False): return
    st.title("🇮🇹 Italienisch Lern-Tool")
    entered = st.text_input("Passwort", type="password")
    if st.button("Einloggen"):
        if hashlib.sha256(entered.encode()).hexdigest() == hashlib.sha256(str(password).encode()).hexdigest():
            st.session_state.authenticated=True; st.rerun()
        else: st.error("Falsches Passwort.")
    st.stop()

def normalize_library(df):
    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            df[col] = 50 if col=="Rating" else (0 if col in ["Richtig","Falsch"] else ("IT-DE" if col=="Richtung" else ""))
    df = df[REQUIRED_COLUMNS].copy()
    df["ID"] = pd.to_numeric(df["ID"], errors="coerce")
    df = df.dropna(subset=["ID"])
    df["ID"] = df["ID"].astype(int)
    for col, default in [("Rating",50),("Richtig",0),("Falsch",0)]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(default).astype(int)
    for col in ["Kategorie","Italienisch","Deutsch","Richtung","Letzte_Abfrage"]:
        df[col] = df[col].fillna("").astype(str)
    df.loc[df["Richtung"].eq(""),"Richtung"]="IT-DE"
    return df.sort_values("ID").reset_index(drop=True)

@st.cache_data(show_spinner=False)
def load_library_from_disk(mtime):
    if not DATA_FILE.exists(): return pd.DataFrame(columns=REQUIRED_COLUMNS)
    return normalize_library(pd.read_excel(DATA_FILE, sheet_name=SHEET_LIBRARY))

def load_library():
    return load_library_from_disk(DATA_FILE.stat().st_mtime if DATA_FILE.exists() else 0)

def make_backup():
    if not DATA_FILE.exists(): return None
    BACKUP_DIR.mkdir(exist_ok=True)
    path = BACKUP_DIR / f"italienisch_bibliothek_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    shutil.copy(DATA_FILE, path)
    return path

def save_library(df):
    with pd.ExcelWriter(DATA_FILE, engine="openpyxl", mode="w") as writer:
        normalize_library(df).to_excel(writer, sheet_name=SHEET_LIBRARY, index=False)
    st.cache_data.clear()

def weighted_pick(df, low_rating_chance, weighting_strength):
    if random.random() < low_rating_chance:
        low_part = df[df["Rating"] <= df["Rating"].quantile(0.35)]
        if not low_part.empty: return low_part.sample(1).iloc[0]
    weights = df["Rating"].clip(lower=1).astype(float) ** weighting_strength
    return df.sample(1, weights=weights).iloc[0]

def qa(row, mode):
    direction = random.choice(["IT-DE","DE-IT"]) if mode=="Gemischt" else mode
    return (row["Italienisch"], row["Deutsch"], "Übersetze auf Deutsch") if direction=="IT-DE" else (row["Deutsch"], row["Italienisch"], "Übersetze auf Italienisch")

def reset_card():
    st.session_state.current_id=None
    st.session_state.show_solution=False
    st.session_state.question=""
    st.session_state.answer=""
    st.session_state.task_label=""
    st.session_state.user_answer=""

optional_password_gate()

if "df" not in st.session_state: st.session_state.df = load_library()
if "current_id" not in st.session_state: reset_card()
if "show_settings" not in st.session_state: st.session_state.show_settings = False
if "show_stats" not in st.session_state: st.session_state.show_stats = False

df_all = st.session_state.df
min_id_available = int(df_all["ID"].min()) if not df_all.empty else 1
max_id_available = int(df_all["ID"].max()) if not df_all.empty else 1000

# Persistent settings in session state
defaults = {
    "id_von": min_id_available,
    "id_bis": max_id_available,
    "direction_mode": "DE-IT",
    "low_rating_chance_int": 10,
    "weighting_strength": 1.3,
    "richtig_abzug": 5,
    "mittel_abzug": 1,
    "falsch_zuschlag": 10,
    "min_rating": 1,
    "max_rating": 100,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# Clamp ID settings if new library changes range
st.session_state.id_von = max(1, min(int(st.session_state.id_von), max_id_available))
st.session_state.id_bis = max(1, min(int(st.session_state.id_bis), max_id_available))

if st.session_state.show_settings:
    st.markdown("""
    <div class="settings-box">
      <div class="settings-title">⚙ Einstellungen</div>
      <div class="settings-note">Hier steuerst du ID-Bereich, Abfragerichtung, Rating-Logik und Bibliothek.</div>
    </div>
    """, unsafe_allow_html=True)

    if st.button("← Zurück zur Abfrage"):
        st.session_state.show_settings = False
        st.rerun()

    st.subheader("Abfrage")
    c1, c2 = st.columns(2)
    with c1:
        st.number_input("ID von", min_value=1, max_value=max_id_available, step=1, key="id_von")
    with c2:
        st.number_input("ID bis", min_value=1, max_value=max_id_available, step=1, key="id_bis")

    st.selectbox("Abfragerichtung", ["DE-IT","IT-DE","Gemischt"], key="direction_mode")

    st.subheader("Wahrscheinlichkeit / Gewichtung")
    st.slider("Chance für tiefe Ratings (%)", 0, 50, 10, 1, key="low_rating_chance_int")
    st.slider("Stärke der Rating-Gewichtung", 1.0, 3.0, 1.3, 0.1, key="weighting_strength")

    st.subheader("Rating-Veränderung")
    c3, c4, c5 = st.columns(3)
    with c3:
        st.number_input("Einfach", 1, 50, 5, 1, key="richtig_abzug")
    with c4:
        st.number_input("Mittel", 0, 20, 1, 1, key="mittel_abzug")
    with c5:
        st.number_input("Falsch", 1, 50, 10, 1, key="falsch_zuschlag")

    c6, c7 = st.columns(2)
    with c6:
        st.number_input("Mindest-Rating", 1, 100, 1, 1, key="min_rating")
    with c7:
        st.number_input("Maximal-Rating", 10, 500, 100, 5, key="max_rating")

    st.subheader("Bibliothek")
    uploaded = st.file_uploader("Neue Excel-Bibliothek hochladen", type=["xlsx"])
    if uploaded is not None:
        try:
            new_df = normalize_library(pd.read_excel(uploaded, sheet_name=SHEET_LIBRARY))
            make_backup()
            save_library(new_df)
            st.session_state.df = new_df
            reset_card()
            st.success("Neue Bibliothek geladen und gespeichert.")
            st.rerun()
        except Exception as e:
            st.error(f"Upload konnte nicht verarbeitet werden: {e}")

    if DATA_FILE.exists():
        with open(DATA_FILE, "rb") as f:
            st.download_button(
                "Aktuelle Bibliothek herunterladen",
                f.read(),
                "italienisch_bibliothek_aktuell.xlsx",
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    c8, c9 = st.columns(2)
    with c8:
        if st.button("Backup erstellen"):
            make_backup()
            st.success("Backup erstellt.")
    with c9:
        if st.button("Bibliothek neu laden"):
            st.session_state.df = load_library()
            reset_card()
            st.success("Neu geladen.")
            st.rerun()

    st.stop()

id_von = int(st.session_state.id_von)
id_bis = int(st.session_state.id_bis)
direction_mode = st.session_state.direction_mode
low_rating_chance = st.session_state.low_rating_chance_int / 100
weighting_strength = float(st.session_state.weighting_strength)
richtig_abzug = int(st.session_state.richtig_abzug)
mittel_abzug = int(st.session_state.mittel_abzug)
falsch_zuschlag = int(st.session_state.falsch_zuschlag)
min_rating = int(st.session_state.min_rating)
max_rating = int(st.session_state.max_rating)

df = st.session_state.df
filtered = df[(df["ID"] >= id_von) & (df["ID"] <= id_bis)].copy()
if filtered.empty:
    st.warning("Keine Einträge im gewählten ID-Bereich.")
    if st.button("⚙ Einstellungen öffnen"):
        st.session_state.show_settings = True
        st.rerun()
    st.stop()

def next_card():
    chosen = weighted_pick(filtered, low_rating_chance, weighting_strength)
    q,a,label = qa(chosen, direction_mode)
    st.session_state.current_id = int(chosen["ID"])
    st.session_state.question = q
    st.session_state.answer = a
    st.session_state.task_label = label
    st.session_state.show_solution = False
    st.session_state.user_answer = ""

def update_card(result):
    cid = st.session_state.current_id
    idxs = st.session_state.df.index[st.session_state.df["ID"] == cid]
    if len(idxs)==0: return
    idx = idxs[0]
    old = int(st.session_state.df.at[idx, "Rating"])
    if result == "easy":
        st.session_state.df.at[idx, "Rating"] = max(min_rating, old - richtig_abzug)
        st.session_state.df.at[idx, "Richtig"] = int(st.session_state.df.at[idx, "Richtig"]) + 1
    elif result == "medium":
        st.session_state.df.at[idx, "Rating"] = max(min_rating, old - mittel_abzug)
        st.session_state.df.at[idx, "Richtig"] = int(st.session_state.df.at[idx, "Richtig"]) + 1
    else:
        st.session_state.df.at[idx, "Rating"] = min(max_rating, old + falsch_zuschlag)
        st.session_state.df.at[idx, "Falsch"] = int(st.session_state.df.at[idx, "Falsch"]) + 1
    st.session_state.df.at[idx, "Letzte_Abfrage"] = datetime.now().strftime("%Y-%m-%d %H:%M")
    save_library(st.session_state.df)
    next_card()

if st.session_state.current_id is None:
    next_card()

row = st.session_state.df[st.session_state.df["ID"] == st.session_state.current_id]
rating = int(row["Rating"].iloc[0]) if not row.empty else 0
errors = int(row["Falsch"].iloc[0]) if not row.empty else 0
progress = max(0, min(100, round(((int(st.session_state.current_id)-id_von+1)/max((id_bis-id_von+1),1))*100)))

st.markdown(f"""
<div class="app-title-row"><div class="app-title">🇮🇹 Italienisch</div><div class="tiny-pill">{len(filtered)} Karten</div></div>
<div class="status-grid">
<div class="status-card"><div class="status-label">ID</div><div class="status-value">{st.session_state.current_id}</div></div>
<div class="status-card"><div class="status-label">Rating</div><div class="status-value">{rating}</div></div>
<div class="status-card"><div class="status-label">Fehler</div><div class="status-value">{errors}</div></div>
<div class="status-card"><div class="status-label">Bereich</div><div class="status-value">{progress}%</div></div>
</div>
<div class="question-card">
<div class="question-meta">ID {st.session_state.current_id} · {st.session_state.task_label}</div>
<div class="question-text">{st.session_state.question}</div>
{("<div class='solution-card'><div class='solution-label'>Lösung</div><div class='solution-text'>"+st.session_state.answer+"</div></div>") if st.session_state.show_solution else ""}
</div>
""", unsafe_allow_html=True)

st.text_area("Deine Antwort", placeholder="Hier deine Übersetzung eingeben ...", key="user_answer")

c1, c2 = st.columns(2)
with c1:
    if st.button("💡 Auflösen"):
        st.session_state.show_solution = True
        st.rerun()
with c2:
    if st.button("▶ Nächster Satz"):
        next_card()
        st.rerun()

r1, r2, r3 = st.columns(3)
with r1:
    if st.button("✕ Falsch"):
        update_card("hard")
        st.rerun()
with r2:
    if st.button("– Mittel"):
        update_card("medium")
        st.rerun()
with r3:
    if st.button("✓ Einfach"):
        update_card("easy")
        st.rerun()

st.markdown('<div class="small-action">', unsafe_allow_html=True)
b1, b2 = st.columns(2)
with b1:
    if st.button("📊 Statistik"):
        st.session_state.show_stats = not st.session_state.get("show_stats", False)
        st.rerun()
with b2:
    if st.button("⚙ Einstellungen"):
        st.session_state.show_settings = True
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

if st.session_state.get("show_stats", False):
    with st.expander("Statistik / schwierigste Sätze", expanded=True):
        hard = filtered.sort_values(["Rating","Falsch"], ascending=False).head(20)
        st.dataframe(hard[["ID","Kategorie","Italienisch","Deutsch","Rating","Richtig","Falsch","Letzte_Abfrage"]], use_container_width=True, hide_index=True)

st.markdown('<div class="notice">Online-Hinweis: Backup/Download findest du unter ⚙ Einstellungen.</div>', unsafe_allow_html=True)
