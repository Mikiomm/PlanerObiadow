import os
import json
import random
import socket
from flask import Flask, render_template, jsonify

# Optional: load .env in development
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

from supabase import create_client

app = Flask(__name__)

# Read DATABASE_URL from env (Supabase provides this). If not set, fall back to in-memory list.
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DATABASE_URL')
SUPABASE_URL = os.getenv('SUPABASE_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')

# Inform developer if Supabase credentials were provided
if SUPABASE_URL and SUPABASE_KEY:
    app.logger.info('SUPABASE_URL and SUPABASE_KEY found in environment; Supabase will be used.')
elif DATABASE_URL:
    app.logger.info('DATABASE_URL found in environment; legacy DB URL will be used.')
else:
    app.logger.info('Database not configured; using in-memory fallback. Copy .env.example -> .env and set SUPABASE_URL and SUPABASE_KEY to use Supabase.')

# Default seed data (used to seed the DB on first run or used as fallback)
DEFAULT_DANIA = [
    {"nazwa": "Pierogi", "skladniki": ["mąka", "ziemniaki", "mięso", "cebula"]},
    {"nazwa": "Bigos", "skladniki": ["kapusta", "mięso", "cebula", "marchew"]},
    {"nazwa": "Żurek", "skladniki": ["mąka", "mięso", "cebula", "chleb"]},
    {"nazwa": "Kotlet schabowy", "skladniki": ["mięso", "mąka", "jajko", "bułka tarta"]},
    {"nazwa": "Placki ziemniaczane", "skladniki": ["ziemniaki", "mąka", "jajko", "cebula"]},
]

# DB helpers

def get_supabase():
    """Return a Supabase client or None if not configured."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)


def init_db():
    """Seed default dinners on first run when Supabase is available.

    Note: Creating tables (DDL) via the public Supabase client is not supported
    from the REST layer. Please create the `dinners` table in the Supabase
    dashboard or via migrations. This function will attempt to seed the table
    if it already exists.
    """
    sb = get_supabase()
    if not sb:
        app.logger.warning('Supabase credentials not set - using in-memory list')
        return

    try:
        # Try to read the table; if it doesn't exist, the API may return an error or empty data.
        res = sb.table('dinners').select('name, ingredients').execute()
        rows = res.data if hasattr(res, 'data') else res.get('data', None)
        if rows is None:
            app.logger.warning('Could not access `dinners` table. Ensure it exists in Supabase.')
            return
        if len(rows) == 0:
            for d in DEFAULT_DANIA:
                sb.table('dinners').insert({'name': d['nazwa'], 'ingredients': d['skladniki']}).execute()
    except Exception as e:
        app.logger.warning(f'Error accessing Supabase: {e}')
        return


def get_dishes():
    """Return list of dishes from Supabase or fallback to DEFAULT_DANIA."""
    sb = get_supabase()
    if not sb:
        return DEFAULT_DANIA.copy()

    try:
        res = sb.table('dinners').select('name, ingredients').execute()
        rows = res.data if hasattr(res, 'data') else res.get('data', [])
    except Exception as e:
        app.logger.warning(f'Error querying Supabase: {e}')
        return DEFAULT_DANIA.copy()

    # Convert to expected format
    results = []
    for r in rows:
        # Supabase returns keys as defined in the table
        results.append({'nazwa': r.get('name'), 'skladniki': r.get('ingredients')})
    return results


def add_dish(name, skladniki):
    sb = get_supabase()
    if not sb:
        app.logger.warning('Supabase not configured - cannot add to DB')
        return False

    try:
        sb.table('dinners').insert({'name': name, 'ingredients': skladniki}).execute()
        return True
    except Exception as e:
        app.logger.warning(f'Error inserting into Supabase: {e}')
        return False


#@app.before_first_request
def startup():
    """Initialize DB on first run."""
    init_db()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/dania', methods=['GET'])
def lista_dan():
    """Return list of available dinners from DB."""
    return jsonify({'dania': get_dishes()})


@app.route('/losuj', methods=['POST'])
def losuj():
    wyniki = []

    dania = get_dishes()
    all_skladniki = set()
    for d in dania:
        all_skladniki.update(d['skladniki'])

    streak = {s: 0 for s in all_skladniki}

    dostepne_dania = dania.copy()
    streak_copy = streak.copy()

    for dzien in range(1, 8):
        mozliwe = [d for d in dostepne_dania if not any(streak_copy.get(s, 0) >= 2 for s in d['skladniki'])]

        if not mozliwe:
            break

        wybrane = random.choice(mozliwe)
        wyniki.append(wybrane['nazwa'])

        used_today = set(wybrane['skladniki'])
        for s in all_skladniki:
            if s in used_today:
                streak_copy[s] += 1
            else:
                streak_copy[s] = 0

        dostepne_dania.remove(wybrane)

    return jsonify({'wyniki': wyniki})


if __name__ == '__main__':
    startup()
    app.run(debug=True)
