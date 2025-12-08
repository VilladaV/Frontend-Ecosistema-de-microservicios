from flask import Flask, render_template, jsonify
import requests
import threading
import time
import mysql.connector
import os

app = Flask(__name__)

# --- CONFIGURACIÓN DE BASE DE DATOS (Variables de Entorno) ---
# Esto se tiene que conectar con el contenedor
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_USER = os.getenv('DB_USER', 'usuario_seguro')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'password_segura')
DB_NAME = os.getenv('DB_NAME', 'mi_base_datos')

# --- LÓGICA DEL BOTÓN 1: API EXTERNA CON CONCURRENCIA ---
# REQUISITO: Usar Concurrencia (Threads) porque es I/O Bound.
# JUSTIFICACIÓN: Al consultar una API externa, el procesador (CPU) pasa la mayor parte
# del tiempo "esperando" la respuesta de la red. Usar un hilo permite delegar esa espera
# sin bloquear el servidor principal.

def consultar_api_externa(result_container):
    """Función que ejecutará el hilo secundario"""
    try:
        # API pública de prueba 
        response = requests.get('https://jsonplaceholder.typicode.com/users/1')
        data = response.json()
        # Simula un proceso ligero
        result_container['data'] = f"Usuario obtenido: {data['name']} (Email: {data['email']})"
        result_container['status'] = 'success'
    except Exception as e:
        result_container['status'] = 'error'
        result_container['message'] = str(e)

@app.route('/boton1', methods=['POST'])
def boton_1():
    resultado = {}
    # Creamos un hilo para no bloquear el Main Thread
    hilo = threading.Thread(target=consultar_api_externa, args=(resultado,))
    hilo.start()
    hilo.join()  # Esperamos a que el hilo termine (en un caso real async, esto sería await)
    
    return jsonify(resultado)

# --- LÓGICA DEL BOTÓN 2: CONSULTA A LA NUBE ---
# REQUISITO: Consultar la BD en la nube a través de la red Docker.

@app.route('/boton2', methods=['POST'])
def boton_2():
    try:
        # Conexión a la BD gestionada
        connection = mysql.connector.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        port=3306
        )

        cursor = connection.cursor()
        cursor.execute("SELECT * FROM productos LIMIT 5") #  según esquema real
        resultados = cursor.fetchall()
        connection.close()
        
        return jsonify({'status': 'success', 'data': resultados})
    except Exception as e:
        return jsonify({'status': 'error', 'message': f"Error conectando a BD Nube: {str(e)}"})

# --- RUTA PRINCIPAL (FRONTEND) ---
@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    # Ejecutamos en todas las interfaces (0.0.0.0) para que Docker lo exponga
    app.run(host='0.0.0.0', port=5000)