from flask import Flask, jsonify, render_template
import threading
import time

# Importam clasa si functia din fisierul tau hardware
from hala import DigitalTwinHala, asculta_terminal, ruleaza_sistem

app = Flask(__name__)
twin_global = None

@app.route('/')
def home():
    # Trimite fisierul index.html din folderul templates
    return render_template('index.html')

@app.route('/api/stare')
def api_stare():
    # Cand site-ul cere date, le luam direct din hala.py
    if twin_global:
        stare = twin_global.obtine_stare()
        # Adaugam si constantele de referinta pentru interfata web
        stare['tinta'] = twin_global.temp # initial ia valoarea default
        # Pentru a accesa variabile globale din alt fisier, e un truc:
        import hala
        stare['tinta'] = hala.TEMPERATURA_TINTA
        stare['toleranta'] = hala.TOLERANTA_TEMP
        
        return jsonify(stare)
    return jsonify({"error": "Sistem neinitializat"})

if __name__ == "__main__":
    print("?? Initializare Sistem Complet (Hardware + Web)...")
    
    # 1. Pornim Hardware-ul
    twin_global = DigitalTwinHala()
    
    # 2. Pornim ascultarea comenzilor din terminal (cum aveai inainte)
    t_cmd = threading.Thread(target=asculta_terminal, args=(twin_global,), daemon=True)
    t_cmd.start()
    
    # 3. Pornim bucla principala a halei in fundal (sa nu blocheze web serverul)
    t_hala = threading.Thread(target=ruleaza_sistem, args=(twin_global,), daemon=True)
    t_hala.start()
    
    # 4. Pornim serverul Web Flask
    print("\n?? SERVER WEB PORNIT!")
    print("Daca esti pe Raspberry Pi, deschide browserul la: http://localhost:5000")
    print("Pentru a te conecta de pe telefon, vezi IP-ul tau de mai jos.")
    import socket
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        print(f"?? Acces de pe telefon: http://{ip}:5000\n")
    except Exception:
        print("Nu am putut detecta IP-ul local automat. Foloseste comanda 'hostname -I' in terminal.")
        
    # Pornirea propriu-zisa a Flask-ului (pe portul 5000)
    app.run(host='0.0.0.0', port=5000, debug=False, use_reloader=False)