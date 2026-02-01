import os
import json
import random
from flask import Flask, render_template, jsonify

# Optional: load .env in development
try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

import psycopg2
import psycopg2.extras

app = Flask(__name__)

# Read DATABASE_URL from env (Supabase provides this). If not set, fall back to in-memory list.
DATABASE_URL = os.getenv('DATABASE_URL') or os.getenv('SUPABASE_DATABASE_URL')

# Inform developer if DATABASE_URL was provided (useful during development)
if DATABASE_URL:
    app.logger.info('DATABASE_URL found in environment; DB will be used.')
else:
    app.logger.info('DATABASE_URL not set; using in-memory fallback. Copy .env.example -> .env and set DATABASE_URL to use Supabase.')

# Default seed data (used to seed the DB on first run or used as fallback)
DEFAULT_DANIA = [
    {"nazwa": "Pierogi", "skladniki": ["mąka", "ziemniaki", "mięso", "cebula"]},
    {"nazwa": "Bigos", "skladniki": ["kapusta", "mięso", "cebula", "marchew"]},
    {"nazwa": "Żurek", "skladniki": ["mąka", "mięso", "cebula", "chleb"]},
    {"nazwa": "Kotlet schabowy", "skladniki": ["mięso", "mąka", "jajko", "bułka tarta"]},
    {"nazwa": "Placki ziemniaczane", "skladniki": ["ziemniaki", "mąka", "jajko", "cebula"]},
]

# DB helpers

def get_conn():
    if not DATABASE_URL:
        return None
    # Force SSL (Supabase Postgres requires it)
    return psycopg2.connect(DATABASE_URL, sslmode='require')


def init_db():
    """Create table if missing and seed default dinners on first run."""
    conn = get_conn()
    if not conn:
        app.logger.warning('DATABASE_URL not set - using in-memory list')
        return

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS dinners (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    ingredients JSONB NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT now()
                );
                """
            )
            # Check if table empty
            cur.execute('SELECT count(*) FROM dinners;')
            count = cur.fetchone()[0]
            if count == 0:
                # Seed default dinners
                insert_sql = 'INSERT INTO dinners (name, ingredients) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING;'
                for d in DEFAULT_DANIA:
                    cur.execute(insert_sql, (d['nazwa'], json.dumps(d['skladniki'])))
    conn.close()


def get_dishes():
    """Return list of dishes from DB or fallback to DEFAULT_DANIA."""
    conn = get_conn()
    if not conn:
        return DEFAULT_DANIA.copy()

    with conn:
        with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:
            cur.execute('SELECT name, ingredients FROM dinners ORDER BY id;')
            rows = cur.fetchall()
    conn.close()

    # Convert to expected format
    results = []
    for r in rows:
        results.append({'nazwa': r['name'], 'skladniki': r['ingredients']})
    return results


def add_dish(name, skladniki):
    conn = get_conn()
    if not conn:
        app.logger.warning('DATABASE_URL not set - cannot add to DB')
        return False

    with conn:
        with conn.cursor() as cur:
            cur.execute(
                'INSERT INTO dinners (name, ingredients) VALUES (%s, %s) ON CONFLICT (name) DO NOTHING;',
                (name, json.dumps(skladniki))
            )
    conn.close()
    return True


@app.before_first_request
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
    app.run(debug=True)
