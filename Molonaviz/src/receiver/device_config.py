import tkinter as tk
from tkinter import messagebox
import pandas as pd
import os
from PIL import Image, ImageTk

def ouvrir_formulaire(titre, fichier_csv, champs):
    def enregistrer():
        donnees = {champ: entrees[champ].get().strip() for champ in champs}

        if any(v == "" for v in donnees.values()):
            messagebox.showwarning("Champs vides", "Merci de remplir tous les champs.")
            return

        if fichier_csv == "datalogger.csv":
            base_fields = ["Nom", "datalogger ID", "Labo", "Relay ID"]
            thermo_field = ["Thermometre ID","Thermo_Model"]
            pressure_field = ["Pressure Sensor ID", "Pressure Sensor Calibrator"]

            base_data = {k: donnees[k] for k in base_fields}
            df_datalogger = pd.DataFrame([base_data])
            if os.path.exists(fichier_csv):
                old = pd.read_csv(fichier_csv)
                df_datalogger = pd.concat([old, df_datalogger], ignore_index=True)
            df_datalogger.to_csv(fichier_csv, index=False, encoding="utf-8")

            thermo_data = {
                "ID"  : donnees[thermo_field[0]],
                "Labo": donnees["Labo"],  
                "Thermo_Model": donnees[thermo_field[1]],
                "DataloggerID": donnees["datalogger ID"],
            }
            df_thermo = pd.DataFrame([thermo_data])
            if os.path.exists("thermometre.csv"):
                old_t = pd.read_csv("thermometre.csv")
                df_thermo = pd.concat([old_t, df_thermo], ignore_index=True)
            df_thermo.to_csv("thermometre.csv", index=False, encoding="utf-8")

            pressure_data = {
                "ID" : donnees[pressure_field[0]],
                "Pressure_Sensor_Calibrator": donnees[pressure_field[1]],
                "DataloggerID"  :donnees["datalogger ID"],
                "Assoc_Datalogger": donnees["Nom"],        
                "Labo": donnees["Labo"],                  
            }
            df_pressure = pd.DataFrame([pressure_data])
            if os.path.exists("pressure_captor.csv"):
                old_p = pd.read_csv("pressure_captor.csv")
                df_pressure = pd.concat([old_p, df_pressure], ignore_index=True)
            df_pressure.to_csv("pressure_captor.csv", index=False, encoding="utf-8")

            messagebox.showinfo("Succès", "Les données ont été enregistrées dans les fichiers correspondants.")
   
        else:
            df = pd.DataFrame([donnees])
            if os.path.exists(fichier_csv):
                old = pd.read_csv(fichier_csv)
                df = pd.concat([old, df], ignore_index=True)
            df.to_csv(fichier_csv, index=False, encoding="utf-8")
            messagebox.showinfo("Succès", f"Les données ont été ajoutées à {fichier_csv}")

        for champ in champs:
            entrees[champ].delete(0, tk.END)

    fenetre = tk.Toplevel()
    fenetre.title(titre)
    fenetre.geometry("400x350")
    fenetre.configure(bg="#f0f0f0")

    entrees = {}
    frame = tk.Frame(fenetre, bg="#f0f0f0")
    frame.pack(pady=20)

    for i, champ in enumerate(champs):
        label = tk.Label(frame, text=champ + " :", bg="#f0f0f0")
        label.grid(row=i, column=0, padx=10, pady=5, sticky="e")
        entree = tk.Entry(frame, width=30)
        entree.grid(row=i, column=1, padx=10, pady=5)
        entrees[champ] = entree

    bouton = tk.Button(fenetre, text="Enregistrer", command=enregistrer, bg="#4CAF50", fg="white")
    bouton.pack(pady=10)

    try:
        image = Image.open("logo_MOLONARI.png").resize((70, 70))
        logo = ImageTk.PhotoImage(image)
        label_logo = tk.Label(fenetre, image=logo, bg="#f0f0f0")
        label_logo.image = logo
        label_logo.place(x=300, y=260)
    except Exception:
        pass

    try:
        image2 = Image.open("logo_MinesParis.png").resize((150, 55))
        logo2 = ImageTk.PhotoImage(image2)
        label_logo2 = tk.Label(fenetre, image=logo2, bg="#f0f0f0")
        label_logo2.image = logo2
        label_logo2.place(x=20, y=265)
    except Exception:
        pass


root = tk.Tk()
root.title("Gestion des équipements")
root.geometry("400x350")
root.configure(bg="#e6f0ff")

tk.Label(root, text="Ajouter un nouvel élément :", bg="#e6f0ff", font=("Arial", 14, "bold")).pack(pady=20)

tk.Button(root, text="Ajouter Gateway", width=25,
          command=lambda: ouvrir_formulaire("Nouvelle Gateway", "gateways.csv",
                                            ["ID", "CA_Cert", "Labo", "Name", "TLS_Cert", "TLS_Key", "gatewayEUI"]),
          bg="#0078D7", fg="white").pack(pady=5)

tk.Button(root, text="Ajouter Relais", width=25,
          command=lambda: ouvrir_formulaire("Nouveau Relais", "relais.csv",
                                            ["ID", "Gateway", "Labo", "Name", "RelayEUI"]),
          bg="#0078D7", fg="white").pack(pady=5)

tk.Button(root, text="Ajouter Datalogger", width=25,
          command=lambda: ouvrir_formulaire("Nouveau Datalogger", "datalogger.csv",
                                            ["Nom", "datalogger ID", "Labo", "Relay ID","Thermometre ID", "Thermo_Model","Pressure Sensor ID", "Pressure Sensor Calibrator"]),
          bg="#0078D7", fg="white").pack(pady=5)



tk.Button(root, text="Quitter", width=25, command=root.destroy, bg="#999999", fg="white").pack(pady=15)

root.mainloop()