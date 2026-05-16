
# Italienisch Lern-Tool – Supabase Version v2

Diese Version speichert Ratings, Richtig/Falsch und letzte Abfrage dauerhaft in Supabase.

## GitHub

Bitte in deinem Repository ersetzen:

- `app.py`
- `requirements.txt`

## Streamlit Secrets

In Streamlit → App → Settings → Secrets muss stehen:

```toml
SUPABASE_URL = "https://dein-projekt.supabase.co"
SUPABASE_KEY = "dein-publishable-key"
```

## Supabase Tabelle

Die Tabelle `cards` muss vorhanden sein:

```sql
create table if not exists cards (
  id integer primary key,
  kategorie text,
  italienisch text not null,
  deutsch text not null,
  richtung text default 'DE-IT',
  rating integer default 50,
  richtig integer default 0,
  falsch integer default 0,
  letzte_abfrage timestamp
);
```

## Import

Nach Deployment:
1. App öffnen
2. ⚙ Einstellungen
3. Excel-Bibliothek hochladen
4. App importiert die Karten nach Supabase
