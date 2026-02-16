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
    # Eliminamos el inventario_inicial fijo para pedirlo por formulario
    
    if request.method == "POST":
        # PASO 1: Procesar archivo Y capturar el Inventario Inicial
        if 'file' in request.files and 'inicial' in request.form:
            file = request.files['file']
            # Capturamos el conteo inicial que puso el usuario
            inv_inicial = int(request.form.get('inicial', 0))
            
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

                # Enviamos 'ventas' e 'inicial' al Paso 2
                return render_template("index.html", ventas=ventas, inicial=inv_inicial, paso=2)

        # PASO 2: Recibir conteo físico y calcular el cuadre final
        elif 'fisico' in request.form:
            ventas = int(request.form.get('ventas_previa'))
            inv_inicial = int(request.form.get('inicial_previa')) # Recuperamos el inicial del paso anterior
            fisico = int(request.form.get('fisico'))
            
            # Lógica de cuadre
            deberia = inv_inicial - ventas
            dif = fisico - deberia
            
            res = {
                "inicial": inv_inicial, 
                "ventas": ventas, 
                "deberia": deberia, 
                "fisico": fisico, 
                "dif": dif
            }
            return render_template("index.html", res=res, paso=3)

    return render_template("index.html", paso=1)

@app.route("/reset")
def reset():
    return redirect(url_for('index'))

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
    
