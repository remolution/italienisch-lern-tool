# Italienisch Lern-Tool – Online-Version v1

Diese Version ist für das Hosting auf Streamlit Community Cloud vorbereitet.

## Enthalten

- `app.py` – Streamlit-App
- `italienisch_bibliothek.xlsx` – Bibliothek mit 1000 Sätzen
- `requirements.txt` – Python-Abhängigkeiten
- `.streamlit/secrets.toml.example` – Beispiel für Passwortschutz

## Lokal starten

```bash
cd /Pfad/zum/Ordner/italienisch_lern_tool_online_v1
python3 -m pip install -r requirements.txt
python3 -m streamlit run app.py
```

Dann im Browser öffnen:

```text
http://localhost:8501
```

## Online auf Streamlit Community Cloud deployen

1. GitHub-Konto erstellen oder verwenden.
2. Neues Repository erstellen, z. B. `italienisch-lern-tool`.
3. Diese Dateien hochladen:
   - `app.py`
   - `requirements.txt`
   - `italienisch_bibliothek.xlsx`
   - Ordner `.streamlit` optional nur mit Beispiel-Datei
4. Auf Streamlit Community Cloud einloggen.
5. Neues App-Deployment erstellen.
6. GitHub-Repository auswählen.
7. Main file path: `app.py`
8. Deploy klicken.

## Passwortschutz

In Streamlit Community Cloud unter App → Settings → Secrets eintragen:

```toml
APP_PASSWORD = "dein-passwort"
```

Wenn kein Passwort gesetzt ist, ist die App ohne Login offen.

## Wichtiger Hinweis zur Speicherung

Streamlit Community Cloud ist nicht als dauerhafte Datenbank gedacht.

Die App speichert Fortschritt zwar in `italienisch_bibliothek.xlsx`, aber bei Neustarts/Re-Deployments kann der Dateistand verloren gehen. Deshalb:

- regelmässig in der Sidebar auf **Aktuelle Bibliothek herunterladen** klicken
- die heruntergeladene Datei als Backup speichern
- bei Bedarf diese Datei wieder hochladen

Für eine wirklich robuste Online-Version brauchen wir später eine externe Datenbank, z. B. Supabase, Google Sheets oder eine kleine Server-Datenbank.

## Verbesserungen gegenüber der lokalen Version

- Passwortschutz vorbereitet
- Upload/Download der Bibliothek
- Backup-Funktion
- Rating-Gewichtung zusätzlich steuerbar
- Standardrichtung ist Deutsch → Italienisch
- 1000 Sätze bereits enthalten
