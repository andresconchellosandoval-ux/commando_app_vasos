from flask import Flask, render_template, request, redirect, url_for
import pandas as pd
import os
import re

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = "uploads"
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

@app.route("/", methods=["GET", "POST"])
def index():
    inventario_inicial = 1508
    
    if request.method == "POST":
        # PASO 1: Procesar el archivo y contar ventas
        if 'file' in request.files:
            file = request.files['file']
            if file.filename != '':
                path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(path)
                
                # Lectura de archivo
                df = pd.read_excel(path) if file.filename.endswith(('.xlsx', '.xls')) else pd.read_csv(path, encoding="latin1")
                df.columns = [str(c).strip().lower() for c in df.columns]
                c_prod = next((c for c in df.columns if any(p in c for p in ["prod", "item", "nombre"])), df.columns[0])
                c_cant = next((c for c in df.columns if any(p in c for p in ["qty", "cant", "total"])), None)

                # Filtro de Shakes
                shakes = ["amino juice", "banana boost", "berry mango", "berry oat", "blue lemonade", "caramel", "cha cha matcha", "chai chai", "dark acai", "double berry", "fresas y machos", "hazzelino", "manito", "la manita", "mr reeses", "original", "simple", "canelita", "mango coco", "silvestre", "quaker", "vital vainilla latte"]
                def limpiar(t): return re.sub(r'[^a-z0-9]', '', str(t).lower())
                sk_limpios = [limpiar(s) for s in shakes]

                df[c_cant] = pd.to_numeric(df[c_cant].astype(str).str.replace('[^0-9.]', '', regex=True), errors='coerce').fillna(0)
                mask = df[c_prod].apply(lambda x: any(s in limpiar(x) for s in sk_limpios))
                ventas = int(df[mask][c_cant].sum())

                # Pasamos al paso 2 enviando el número de ventas
                return render_template("index.html", ventas=ventas, paso=2)

        # PASO 2: Recibir conteo físico y calcular resta
        elif 'fisico' in request.form:
            ventas = int(request.form.get('ventas_previa'))
            fisico = int(request.form.get('fisico'))
            deberia = inventario_inicial - ventas
            dif = fisico - deberia
            
            res = {"inicial": inventario_inicial, "ventas": ventas, "deberia": deberia, "fisico": fisico, "dif": dif}
            return render_template("index.html", res=res, paso=3)

    return render_template("index.html", paso=1)

@app.route("/reset")
def reset():
    return redirect(url_for('index'))

if __name__ == "__main__":
    app.run(port=8080, debug=True)
    