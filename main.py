import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from PIL import Image, ImageTk
import mysql.connector
import pandas as pd
import os

# Diccionario: nombre carrera → ID
carrera_map = {
    "COMUNICACIÓN SOCIAL": "01",
    "EDUCACIÓN SOCIAL": "02",
    "EDUCACIÓN PRIMARIA": "03",
    "EDUCACIÓN SECUNDARIA": "04",
    "PSICOLOGÍA": "05",
    "PUBLICIDAD Y MULTIMEDIA": "06",
    "TEOLOGÍA": "07",
    "TRABAJO SOCIAL": "08",
    "TURISMO Y HOTELERÍA": "09",
    "ADMINISTRACIÓN DE EMPRESAS": "10",
    "CIENCIA POLÍTICA Y GOBIERNO": "11",
    "CONTABILIDAD": "12",
    "DERECHO": "13",
    "INGENIERÍA COMERCIAL": "14",
    "ARQUITECTURA": "15",
    "INGENIERÓA AGRONÓMICA Y AGRÍCOLA": "16",
    "INGENIERÍA AMBIENTAL": "17",
    "INGENIERÍA CIVIL": "18",
    "INGENIERÍA DE INDUSTRIA ALIMENTARIA": "19",
    "INGENIERÍA DE MINAS": "20",
    "INGENIERÍA DE SISTEMAS": "21",
    "INGENIERÍA ELECTRÓNICA": "22",
    "INGENIERÍA INDUSTRIAL": "23",
    "INGENIERÍA MECÁNICA": "24",
    "INGENIERÍA MECÁNICA ELÉCTRICA": "25",
    "INGENIERÍA MECATRÓNICA": "26",
    "MEDICINA VETERINARIA Y ZOOTECNIA": "27",
    "ENFERMERÍA": "28",
    "FARMACIA Y BIOQUÍMICA": "29",
    "INGENIERÍA BIOTECNOLÓGICA": "30",
    "MEDICINA HUMANA": "31",
    "OBSTRETICIA Y PUERICULTURA": "32",
    "ODONTOLOGÍA": "33",
    "TECNOLOGÍA MÉDICA": "34",
}

# Conexion a base de datos
def conectar_db():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="123456",
        database="CertiGest"
    )

# Exportar asistentes por carrera en Excel
def exportar_asistentes(evento_id, evento_nombre):
    conn = conectar_db()
    cursor = conn.cursor(dictionary=True)

    cursor.execute("""
        SELECT a.DNI, a.APELLIDOS, a.NOMBRES, c.NOMBRE AS CARRERA, a.CORREO, a.SEMESTRE
        FROM ASISTENTE a
        JOIN CARRERA c ON a.ID_CARRERA = c.ID
        JOIN ASISTENCIA s ON s.DNI = a.DNI
        WHERE s.ID_EVENTO = %s
    """, (evento_id,))
    rows = cursor.fetchall()
    df = pd.DataFrame(rows)

    if df.empty:
        messagebox.showinfo("Sin datos", "No hay asistentes para este evento.")
        return

    carpeta = f"Asistentes_{evento_nombre.replace(' ', '_')}"
    os.makedirs(carpeta, exist_ok=True)

    for carrera, grupo in df.groupby("CARRERA"):
        archivo = os.path.join(carpeta, f"{carrera}.xlsx")
        grupo.to_excel(archivo, index=False)

    messagebox.showinfo("Exportación Completa", f"Asistentes exportados en la carpeta: {carpeta}")
    conn.close()

def abrir_crear_evento():
    for widget in root.winfo_children():
        widget.destroy()

    frame = tk.Frame(root, bg="#f0f0f0")
    frame.pack(fill="both", expand=True)

    # Variables para almacenar los datos
    titulo_evento = tk.StringVar()
    imagen_path = tk.StringVar()
    excel_path = tk.StringVar()

    # Función para seleccionar imagen
    def seleccionar_imagen():
        filepath = filedialog.askopenfilename(title="Seleccionar imagen", filetypes=[("Archivos JPG", "*.jpg")])
        if filepath:
            imagen_path.set(filepath)
            lbl_imagen.config(text=f"Imagen seleccionada: {os.path.basename(filepath)}")

    # Función para seleccionar Excel
    def seleccionar_excel():
        filepath = filedialog.askopenfilename(title="Seleccionar archivo Excel", filetypes=[("Archivos Excel", "*.xlsx *.xls")])
        if filepath:
            excel_path.set(filepath)
            lbl_excel.config(text=f"Excel seleccionado: {os.path.basename(filepath)}")

    # Función para guardar el evento
    def guardar_evento():
        titulo = titulo_evento.get().strip()
        img_path = imagen_path.get()
        exc_path = excel_path.get()

        if not titulo:
            messagebox.showwarning("Campo vacío", "Ingrese un título para el evento.")
            return
        if not img_path:
            messagebox.showwarning("Imagen faltante", "Seleccione una imagen para el evento.")
            return
        if not exc_path:
            messagebox.showwarning("Excel faltante", "Seleccione un archivo Excel con los asistentes.")
            return

        # Crear el evento en la base de datos
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO EVENTO (TITULO) VALUES (%s)", (titulo,))
        conn.commit()
        evento_id = cursor.lastrowid

        # Guardar la imagen
        os.makedirs("imagenes", exist_ok=True)
        destino_img = f"imagenes/{evento_id}.jpg"
        with open(img_path, "rb") as src, open(destino_img, "wb") as dst:
            dst.write(src.read())

        # Procesar el archivo Excel (aquí puedes agregar el código para procesar los asistentes)
        try:
            df = pd.read_excel(exc_path)

            # Validar columnas esperadas
            columnas_esperadas = {"DNI", "APELLIDOS", "NOMBRES", "ESCUELA PROFESIONAL", "E-MAIL", "SEMESTRE", "ASISTIO"}
            if not columnas_esperadas.issubset(df.columns):
                raise ValueError("El archivo Excel no contiene las columnas requeridas.")

            insertados = 0
            for _, row in df.iterrows():
                dni = str(row["DNI"]).strip()
                apellidos = str(row["APELLIDOS"]).strip().upper()
                nombres = str(row["NOMBRES"]).strip().upper()
                carrera_nombre = str(row["ESCUELA PROFESIONAL"]).strip().upper()
                correo = str(row["E-MAIL"]).strip()
                semestre = str(row["SEMESTRE"])
                asistencia = str(row["ASISTIO"]).strip().upper()
                if asistencia == "SI":
                    asistencia = 1
                else:
                    asistencia = 0

                id_carrera = carrera_map.get(carrera_nombre)
                if not id_carrera:
                    continue  # Saltar si la carrera no es válida

                # Verificar si el asistente ya existe
                cursor.execute("SELECT COUNT(*) FROM ASISTENTE WHERE DNI = %s", (dni,))
                existe = cursor.fetchone()[0]

                if not existe:
                    datos_asistente =(dni, apellidos, nombres, id_carrera, correo, semestre)
                    cursor.callproc('insertar_asistente', datos_asistente)
                
                # Registrar en la tabla ASISTENCIA
                datos_asistencia =(dni, evento_id, asistencia )
                cursor.callproc('insertar_asistencia', datos_asistencia)

                insertados += 1

            conn.commit()
            messagebox.showinfo("Éxito", f"Evento creado correctamente con ID: {evento_id}\n{insertados} registros procesados del Excel.")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo procesar el archivo Excel: {str(e)}")

        
        conn.close()
        abrir_menu()

    # Interfaz para crear evento
    tk.Label(frame, text="Título del Evento:", bg="#f0f0f0", font=("Arial", 12)).pack(pady=10)
    entry_titulo = tk.Entry(frame, textvariable=titulo_evento, font=("Arial", 12), width=40)
    entry_titulo.pack(pady=5)

    # Botón para seleccionar imagen
    tk.Label(frame, text="Imagen del Evento:", bg="#f0f0f0", font=("Arial", 12)).pack(pady=10)
    tk.Button(frame, text="Seleccionar Imagen", command=seleccionar_imagen, 
              bg="#2196F3", fg="white", font=("Arial", 10, "bold")).pack(pady=5)
    lbl_imagen = tk.Label(frame, text="Ninguna imagen seleccionada", bg="#f0f0f0")
    lbl_imagen.pack(pady=5)

    # Botón para seleccionar Excel
    tk.Label(frame, text="Lista de Asistentes (Excel):", bg="#f0f0f0", font=("Arial", 12)).pack(pady=10)
    tk.Button(frame, text="Seleccionar Archivo Excel", command=seleccionar_excel, 
              bg="#4CAF50", fg="white", font=("Arial", 10, "bold")).pack(pady=5)
    lbl_excel = tk.Label(frame, text="Ningún archivo seleccionado", bg="#f0f0f0")
    lbl_excel.pack(pady=5)

    # Botones de acción
    frame_botones = tk.Frame(frame, bg="#f0f0f0")
    frame_botones.pack(pady=20)

    tk.Button(frame_botones, text="Guardar Evento", command=guardar_evento, 
              bg="#4CAF50", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)
    tk.Button(frame_botones, text="Volver al Menú", command=abrir_menu, 
              bg="#FF5722", fg="white", font=("Arial", 12, "bold")).pack(side="left", padx=10)

# Interfaz de consulta (el resto del código permanece igual)
def abrir_consultas():
    for widget in root.winfo_children():
        widget.destroy()

    frame_superior = tk.Frame(root)
    frame_superior.pack(fill="both", expand=True)

    global tree
    tree = ttk.Treeview(frame_superior, columns=("ID", "Título"), show="headings")
    tree.heading("ID", text="ID")
    tree.heading("Título", text="Título")
    tree.pack(side="left", fill="both", expand=True, pady=10, padx=10)

    scrollbar = ttk.Scrollbar(frame_superior, orient="vertical", command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    scrollbar.pack(side="right", fill="y")

    def cargar_eventos():
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute("SELECT ID, TITULO FROM EVENTO")
        eventos = cursor.fetchall()
        for ev in eventos:
            tree.insert("", "end", values=ev)
        conn.close()

    def mostrar_inscritos():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning("Seleccione un evento", "Debe seleccionar un evento.")
            return
        item = tree.item(seleccionado)
        evento_id, titulo = item['values']

        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.DNI, a.APELLIDOS, a.NOMBRES, c.NOMBRE AS CARRERA, a.CORREO, a.SEMESTRE
            FROM ASISTENTE a
            JOIN CARRERA c ON a.ID_CARRERA = c.ID
            JOIN ASISTENCIA s ON s.DNI = a.DNI
            WHERE s.ID_EVENTO = %s
        """, (evento_id,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("Sin datos", "No se encontraron registros.")
            return

        df = pd.DataFrame(rows)
        mostrar_datos(df)

    def mostrar_asistentes():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning("Seleccione un evento", "Debe seleccionar un evento.")
            return
        item = tree.item(seleccionado)
        evento_id, titulo = item['values']

        conn = conectar_db()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT a.DNI, a.APELLIDOS, a.NOMBRES, c.NOMBRE AS CARRERA, a.CORREO, a.SEMESTRE
            FROM ASISTENTE a
            JOIN CARRERA c ON a.ID_CARRERA = c.ID
            JOIN ASISTENCIA s ON s.DNI = a.DNI
            WHERE s.ID_EVENTO = %s AND ASISTIO = %s
        """, (evento_id, True,))
        rows = cursor.fetchall()
        conn.close()

        if not rows:
            messagebox.showinfo("Sin datos", "No se encontraron registros.")
            return

        df = pd.DataFrame(rows)
        mostrar_datos(df)

    def mostrar_datos(df):
        for widget in root.winfo_children():
            widget.destroy()

        frame_resultado = tk.Frame(root)
        frame_resultado.pack(fill="both", expand=True)

        txt = tk.Text(frame_resultado)
        txt.pack(expand=True, fill="both")
        txt.insert("1.0", df.to_string(index=False))

        tk.Button(frame_resultado, text="Volver", command=abrir_consultas, bg="#FF5722", fg="white", font=("Arial", 10, "bold")).pack(pady=10)

    def exportar():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning("Seleccione un evento", "Debe seleccionar un evento.")
            return
        item = tree.item(seleccionado)
        evento_id, titulo = item['values']
        exportar_asistentes(evento_id, titulo)

    def mostrar_imagen():
        seleccionado = tree.selection()
        if not seleccionado:
            messagebox.showwarning("Seleccione un evento", "Debe seleccionar un evento.")
            return
        item = tree.item(seleccionado)
        evento_id, titulo = item['values']

        imagen_path = f"imagenes/{evento_id}.jpg"
        if not os.path.exists(imagen_path):
            messagebox.showinfo("Sin imagen", "No se encontró imagen para este evento.")
            return

        img = Image.open(imagen_path)
        img = img.resize((500, 400))
        img_tk = ImageTk.PhotoImage(img)

        for widget in root.winfo_children():
            widget.destroy()

        frame_img = tk.Frame(root)
        frame_img.pack(expand=True, fill="both")

        lbl = tk.Label(frame_img, image=img_tk)
        lbl.image = img_tk
        lbl.pack(pady=20)

        tk.Button(frame_img, text="Volver", command=abrir_consultas, bg="#FF5722", fg="white").pack(pady=10)

    frame_botones = tk.Frame(root)
    frame_botones.pack(pady=10)

    estilo_boton = {"width": 20, "padx": 5, "pady": 5, "bg": "#4CAF50", "fg": "white", "font": ("Arial", 10, "bold")}

    tk.Button(frame_botones, text="Ver Inscritos", command=mostrar_inscritos, **estilo_boton).pack(side="left")
    tk.Button(frame_botones, text="Ver Asistentes", command=mostrar_asistentes, **estilo_boton).pack(side="left")
    tk.Button(frame_botones, text="Exportar por Carrera", command=exportar, **estilo_boton).pack(side="left")
    tk.Button(frame_botones, text="Ver Imagen", command=mostrar_imagen, **estilo_boton).pack(side="left")
    tk.Button(frame_botones, text="Menú Principal", command=abrir_menu, **estilo_boton).pack(side="left")

    cargar_eventos()

# Menú principal
def abrir_menu():
    for widget in root.winfo_children():
        widget.destroy()

    frame_inicio = tk.Frame(root, bg="#f0f0f0")
    frame_inicio.pack(expand=True)

    btn1 = tk.Button(frame_inicio, text="Crear Evento", width=25, bg="#2196F3", fg="white", font=("Arial", 12, "bold"), command=abrir_crear_evento)
    btn1.pack(pady=20)

    btn2 = tk.Button(frame_inicio, text="Consultas", width=25, command=abrir_consultas, bg="#4CAF50", fg="white", font=("Arial", 12, "bold"))
    btn2.pack(pady=10)

# Iniciar app
root = tk.Tk()
root.title("CertiGest")
root.geometry("900x600")
root.configure(bg="#f0f0f0")
abrir_menu()
root.mainloop()