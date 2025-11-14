from logging import config
import tkinter as tk
from tkinter import messagebox, ttk
import pandas as pd
import os
from PIL import Image, ImageTk
from PyQt5.QtSql import QSqlQuery, QSqlDatabase
import json

# Get the information from the configuration file

RECEIVER_PATH = './src/receiver/'
SETTINGS_PATH = RECEIVER_PATH + 'settings/'
LAB_FOLDER = './src/molonaviz/backend/virtual-lab/'

with open(SETTINGS_PATH + 'config.json', 'r') as config_file:
    config = json.load(config_file)

SQLINITFILE = config['database']['ERD_structure']
DB_PATH = LAB_FOLDER + 'tmp.sqlite'


def get_db():
    if not hasattr(get_db, "db"):
        db = QSqlDatabase.addDatabase("QSQLITE")
        db.setDatabaseName(DB_PATH)
        db.open()
        get_db.db = db
    return get_db.db

def get_id_name_map(db, table, id_col, name_col):
    query = QSqlQuery(db)
    query.exec(f"SELECT {id_col}, {name_col} FROM {table}")
    result = {}
    while query.next():
        result[query.value(1)] = query.value(0)
    return result

def insert_and_get_id(table, data):
    db = get_db()
    columns = ', '.join(data.keys())
    placeholders = ', '.join([f':{k}' for k in data.keys()])
    query = QSqlQuery(db)
    query.prepare(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")
    for k, v in data.items():
        query.bindValue(f":{k}", v)
    
    if not query.exec():
        messagebox.showerror("Erreur SQL", query.lastError().text())
        return None
    return query.lastInsertId()

def save_to_csv(table, row):
    csv_file = f"{LAB_FOLDER}{table}.csv"
    df = pd.DataFrame([row])
    if os.path.exists(csv_file):
        old = pd.read_csv(csv_file)
        df = pd.concat([old, df], ignore_index=True)
    df.to_csv(csv_file, index=False, encoding="utf-8")

def ouvrir_formulaire(db, titre, table, fields, fk_fields):
    def ajouter():
        donnees = {}
        for champ in fields:
            # Map DataloggerType to Datalogger for DB insert
            if champ == "DataloggerType":
                donnees["Datalogger"] = entrees[champ].get().strip()
            elif champ in fk_fields:
                selected_name = entrees[champ].get()
                id_map = fk_fields[champ]["id_map"]
                donnees[champ] = id_map.get(selected_name)
            else:
                donnees[champ] = entrees[champ].get().strip()
        if any(v in ("", None) for v in donnees.values()):
            messagebox.showwarning("Champs vides", "Merci de remplir tous les champs.")
            return
        new_id = insert_and_get_id(table, donnees)
        if new_id is None:
            return
        donnees_with_id = {**donnees, "ID": new_id}
        save_to_csv(table, donnees_with_id)
        messagebox.showinfo("Succès", f"L'entrée a été ajoutée à la base et à {table}.csv")
        fenetre.destroy()  # Close the popup after saving
    fenetre = tk.Toplevel()
    fenetre.title(titre)
    fenetre.geometry("400x450")
    fenetre.configure(bg="#f0f0f0")
    entrees = {}
    frame = tk.Frame(fenetre, bg="#f0f0f0")
    frame.pack(pady=20)
    for i, champ in enumerate(fields):
        label_text = "Datalogger type" if champ == "DataloggerType" else champ
        label = tk.Label(frame, text=label_text + " :", bg="#f0f0f0")
        label.grid(row=i, column=0, padx=10, pady=5, sticky="e")
        if champ in fk_fields:
            id_map = get_id_name_map(db, fk_fields[champ]["table"], fk_fields[champ]["id_col"], fk_fields[champ]["name_col"])
            fk_fields[champ]["id_map"] = id_map
            combo = ttk.Combobox(frame, values=list(id_map.keys()), width=27, state="readonly")
            combo.grid(row=i, column=1, padx=10, pady=5)
            entrees[champ] = combo
        else:
            entree = tk.Entry(frame, width=30)
            entree.grid(row=i, column=1, padx=10, pady=5)
            entrees[champ] = entree
    bouton = tk.Button(fenetre, text="Ajouter", command=ajouter, bg="#4CAF50", fg="white")
    bouton.pack(pady=10)
    try:
        image = Image.open("logo_MOLONARI.png").resize((70, 70))
        logo = ImageTk.PhotoImage(image)
        label_logo = tk.Label(fenetre, image=logo, bg="#f0f0f0")
        label_logo.image = logo
        label_logo.place(x=300, y=320)
    except Exception:
        pass
    try:
        image2 = Image.open("logo_MinesParis.png").resize((150, 55))
        logo2 = ImageTk.PhotoImage(image2)
        label_logo2 = tk.Label(fenetre, image=logo2, bg="#f0f0f0")
        label_logo2.image = logo2
        label_logo2.place(x=20, y=325)
    except Exception:
        pass

def tout_supprimer():
    db = get_db()
    if not messagebox.askyesno("Confirmation", "Êtes-vous sûr de vouloir supprimer TOUTES les données de la base et des CSV ? Cette action est irréversible."):
        return
    tables = [
        "SamplingPoint", "Shaft", "PressureSensor", "Thermometer", "Datalogger", "Relay", "Gateway", "Study", "Labo"
    ]
    for table in tables:
        query = QSqlQuery(db)
        query.exec(f"DELETE FROM {table}")
    for table in tables:
        csv_file = f"{LAB_FOLDER}{table}.csv"
        if os.path.exists(csv_file):
            os.remove(csv_file)
    messagebox.showinfo("Suppression", "Toutes les données ont été supprimées.")

def initialize_local_database():
    # Delete the table if it exists
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    db = QSqlDatabase.addDatabase("QSQLITE")
    db.setDatabaseName(DB_PATH)
    db.open()
    get_db.db = db

    with open(SQLINITFILE, 'r') as f:
        sqlQueries = f.read().split(';')
    for q in sqlQueries:
        if q.strip():
            QSqlQuery(db).exec(q)

    # Now fill from CSVs in dependency order to avoid FK errors
    import_order = [
        "Labo", "Study", "Gateway", "Relay", "Datalogger", "Thermometer", "PressureSensor", "Shaft", "SamplingPoint"
    ]
    for table_name in import_order:
        csv_file = os.path.join(LAB_FOLDER, f"{table_name}.csv")
        if not os.path.exists(csv_file):
            continue
        df = pd.read_csv(csv_file)
        if not df.empty:
            for _, row in df.iterrows():
                data = row.to_dict()
                insert_and_get_id(table_name, data)
        

def cleanup_and_exit():
    db = get_db()
    db.close()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    root.destroy()

root = tk.Tk()
root.title("Gestion de la base MOLONARI")
root.geometry("475x550")
root.configure(bg="#e6f0ff")

# Disclaimer
order_text = (
    "Veuillez ajouter les éléments dans l'ordre proposé pour une configuration propre")
tk.Label(root, text=order_text, bg="#e6f0ff", fg="#b22222", font=("Arial", 10, "italic"), justify="left").pack(pady=10)

tk.Label(root, text="Ajouter un nouvel élément :", bg="#e6f0ff", font=("Arial", 14, "bold")).pack(pady=20)

# Labo
fields_labo = ["Name"]
fk_labo = {}
tk.Button(root, text="Ajouter Labo", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouveau Labo", "Labo", fields_labo, fk_labo),
          bg="#0078D7", fg="white").pack(pady=5)
# Study
fields_study = ["Name", "Labo"]
fk_study = {"Labo": {"table": "Labo", "id_col": "ID", "name_col": "Name"}}
tk.Button(root, text="Ajouter Study", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouvelle Study", "Study", fields_study, fk_study),
          bg="#0078D7", fg="white").pack(pady=5)
# Gateway
fields_gateway = ["Name", "gatewayEUI", "TLS_Cert", "TLS_Key", "CA_Cert", "Labo"]
fk_gateway = {"Labo": {"table": "Labo", "id_col": "ID", "name_col": "Name"}}
tk.Button(root, text="Ajouter Gateway", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouvelle Gateway", "Gateway", fields_gateway, fk_gateway),
          bg="#0078D7", fg="white").pack(pady=5)
# Relay
fields_relay = ["Name", "RelayEUI", "Gateway", "Labo"]
fk_relay = {"Gateway": {"table": "Gateway", "id_col": "ID", "name_col": "Name"}, "Labo": {"table": "Labo", "id_col": "ID", "name_col": "Name"}}
tk.Button(root, text="Ajouter Relay", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouveau Relay", "Relay", fields_relay, fk_relay),
          bg="#0078D7", fg="white").pack(pady=5)
# Datalogger
fields_datalogger = ["Name", "DevEUI", "Relay", "Labo"]
fk_datalogger = {"Relay": {"table": "Relay", "id_col": "ID", "name_col": "Name"}, "Labo": {"table": "Labo", "id_col": "ID", "name_col": "Name"}}
tk.Button(root, text="Ajouter Datalogger", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouveau Datalogger", "Datalogger", fields_datalogger, fk_datalogger),
          bg="#0078D7", fg="white").pack(pady=5)
# Thermometer
fields_thermo = fields_thermo = ["Name", "ManuName", "ManuRef", "Error", "Beta", "V", "Labo"]
fk_thermo = {"Labo": {"table": "Labo", "id_col": "ID", "name_col": "Name"}}
tk.Button(root, text="Ajouter Thermometer", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouveau Thermometer", "Thermometer", fields_thermo, fk_thermo),
          bg="#0078D7", fg="white").pack(pady=5)
# PressureSensor
fields_psensor = ["Name", "DataloggerType", "DataloggerID", "Calibration", "Intercept", "DuDH", "DuDT", "Error", "ThermoModel", "Labo"]
fk_psensor = {"ThermoModel": {"table": "Thermometer", "id_col": "ID", "name_col": "Name"}, "Labo": {"table": "Labo", "id_col": "ID", "name_col": "Name"}, "DataloggerID": {"table": "Datalogger", "id_col": "ID", "name_col": "Name"}}
tk.Button(root, text="Ajouter PressureSensor", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouveau PressureSensor", "PressureSensor", fields_psensor, fk_psensor),
          bg="#0078D7", fg="white").pack(pady=5)
# Shaft
fields_shaft = ["Name", "DataloggerType", "DataloggerID", "Depth1", "Depth2", "Depth3", "Depth4", "ThermoModel", "Labo"]
fk_shaft = {"ThermoModel": {"table": "Thermometer", "id_col": "ID", "name_col": "Name"}, "Labo": {"table": "Labo", "id_col": "ID", "name_col": "Name"}, "DataloggerID": {"table": "Datalogger", "id_col": "ID", "name_col": "Name"}}
tk.Button(root, text="Ajouter Shaft", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouveau Shaft", "Shaft", fields_shaft, fk_shaft),
          bg="#0078D7", fg="white").pack(pady=5)
# SamplingPoint
fields_spoint = ["Name", "Notice", "Setup", "LastTransfer", "Offset", "RiverBed", "Shaft", "PressureSensor", "Study", "Scheme", "CleanupScript"]
fk_spoint = {"Shaft": {"table": "Shaft", "id_col": "ID", "name_col": "Name"}, "PressureSensor": {"table": "PressureSensor", "id_col": "ID", "name_col": "Name"}, "Study": {"table": "Study", "id_col": "ID", "name_col": "Name"}}
tk.Button(root, text="Ajouter SamplingPoint", width=25,
          command=lambda: ouvrir_formulaire(get_db(), "Nouveau SamplingPoint", "SamplingPoint", fields_spoint, fk_spoint),
          bg="#0078D7", fg="white").pack(pady=5)

tk.Button(root, text="Quitter", width=25, command=cleanup_and_exit, bg="#999999", fg="white").pack(pady=15)
tk.Button(root, text="Tout supprimer", width=25, command=tout_supprimer, bg="#d32f2f", fg="white").pack(pady=5)

if __name__ == "__main__":
    initialize_local_database()
    root.protocol("WM_DELETE_WINDOW", cleanup_and_exit)
    root.mainloop()