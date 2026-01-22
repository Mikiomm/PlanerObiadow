from flask import Flask, render_template, jsonify
import random

app = Flask(__name__)

dania = [
    {"nazwa": "Pierogi", "skladniki": ["mąka", "ziemniaki", "mięso", "cebula"]},
    {"nazwa": "Bigos", "skladniki": ["kapusta", "mięso", "cebula", "marchew"]},
    {"nazwa": "Żurek", "skladniki": ["mąka", "mięso", "cebula", "chleb"]},
    {"nazwa": "Kotlet schabowy", "skladniki": ["mięso", "mąka", "jajko", "bułka tarta"]},
    {"nazwa": "Placki ziemniaczane", "skladniki": ["ziemniaki", "mąka", "jajko", "cebula"]},
    {"nazwa": "Barszcz czerwony", "skladniki": ["buraki", "marchew", "cebula", "mięso"]},
    {"nazwa": "Oscypek", "skladniki": ["mleko", "ser"]},
    {"nazwa": "Obwarzanek krakowski", "skladniki": ["mąka", "sól"]},
    {"nazwa": "Zapiekanka", "skladniki": ["chleb", "ser", "cebula", "mięso"]},
    {"nazwa": "Flaki", "skladniki": ["mięso", "cebula", "marchew"]},
    {"nazwa": "Pizza Margherita", "skladniki": ["mąka", "ser", "pomidory", "bazylia"]},
    {"nazwa": "Spaghetti Carbonara", "skladniki": ["makaron", "jajko", "boczek", "ser"]},
    {"nazwa": "Risotto", "skladniki": ["ryż", "bulion", "cebula", "ser"]},
    {"nazwa": "Lasagne", "skladniki": ["makaron", "mięso", "ser", "pomidory", "cebula"]},
    {"nazwa": "Osso Buco", "skladniki": ["mięso", "marchew", "cebula", "wino"]}
]

all_skladniki = set()
for d in dania:
    all_skladniki.update(d['skladniki'])

streak = {s: 0 for s in all_skladniki}

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/losuj', methods=['POST'])
def losuj():
    wyniki = []
    dostepne_dania = dania.copy()
    streak_copy = streak.copy()  # Use a copy to avoid modifying global streak
    
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