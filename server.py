from flask import Flask, jsonify, render_template, request
import threading
import time

from hala import DigitalTwinHala, asculta_terminal, ruleaza_sistem

app = Flask(__name__)
twin_global = None

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/stare')
def api_stare():
    if twin_global:
        # Acum tinta vine direct din starea obiectului
        return jsonify(twin_global.obtine_stare())
    return jsonify({"error": "Sistem neinitializat"})

@app.route('/api/comanda', methods=['POST'])
def api_comanda():
    if not twin_global:
        return jsonify({"status": "error"}), 400
        
    date_primite = request.json
    
    # Comenzi de Mod
    if 'mod' in date_primite:
        twin_global.mod_auto = (date_primite['mod'] == 'AUTO')
        
    # NOU: Schimbarea Temperaturii Tinta
    if 'tinta' in date_primite:
        twin_global.temperatura_tinta = float(date_primite['tinta'])
        
    # Comenzi Manuale
    if 'vent' in date_primite:
        twin_global.manual_vent = float(date_primite['vent']) / 100.0 
    if 'geam' in date_primite:
        twin_global.manual_geam = bool(date_primite['geam'])
    if 'inc' in date_primite:
        twin_global.manual_inc = bool(date_primite['inc'])
        
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    print("Initializare Sistem Complet (Hardware + Web)...")
    twin_global = DigitalTwinHala()
    
    t_cmd = threading.Thread(target=asculta_terminal, args=(twin_global,), daemon=True)
    t_cmd.start()
    
    t_hala = threading.Thread(target=ruleaza_sistem, args=(twin_global,), daemon=True)
    t_hala.start()
    
    print("\nSERVER WEB PORNIT! Ruleaza pe portul 5000.")
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)