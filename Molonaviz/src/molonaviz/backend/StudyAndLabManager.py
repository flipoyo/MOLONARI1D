from ast import literal_eval
import pandas as pd
from PyQt5.QtSql import QSqlQuery, QSqlDatabase
from ..utils.general import displayCriticalMessage


class StudyAndLabManager:
    """
    Gère les opérations haut niveau sur les laboratoires, études et capteurs physiques
    (thermomètres, capteurs de pression, tiges, gateways et relais).
    """

    def __init__(self, con: QSqlDatabase):
        self.con = con

    # ================================================================
    # ==================== CREATION DE LABO / ETUDE ===================
    # ================================================================
    def create_new_lab(
        self,
        labName: str,
        thermometersDF: list[pd.DataFrame],
        psensorsDF: list[pd.DataFrame],
        shaftsDF: list[pd.DataFrame],
        gatewaysDF: list[pd.DataFrame] = None,
        relaysDF: list[pd.DataFrame] = None,

    ):
        """
        Crée un nouveau laboratoire et insère ses différents capteurs et équipements.
        """
        if not self.check_integrity(labName):
            displayCriticalMessage(
                "Erreur : un laboratoire du même nom existe déjà.\n"
                "Aucun laboratoire n'a été ajouté."
            )
        else:
            labID = self.insert_new_lab(labName)
            self.insert_detectors(labID, thermometersDF, psensorsDF, shaftsDF, gatewaysDF, relaysDF)

    def create_new_study(self, studyName: str, labName: str):
        """
        Crée une nouvelle étude liée à un laboratoire existant.
        """
        selectLabID = self.build_lab_id(labName)
        if not selectLabID.exec():
            print(selectLabID.lastError())
        selectLabID.next()
        labID = selectLabID.value(0)

        insertStudy = self.build_insert_study()
        insertStudy.bindValue(":Name", studyName)
        insertStudy.bindValue(":Labo", labID)
        if not insertStudy.exec():
            print(insertStudy.lastError())
        print(f"The study '{studyName}' has been added to the database.")

    # ================================================================
    # ====================== INSERTIONS DANS LA BDD ==================
    # ================================================================
    def insert_new_lab(self, labName: str):
        insert_lab = self.build_insert_lab(labName)
        if not insert_lab.exec():
            print(insert_lab.lastError())
        print(f"The lab '{labName}' has been added to the database.")
        return insert_lab.lastInsertId()

    def insert_detectors(
        self,
        labID: int | str,
        thermometersDF: list[pd.DataFrame],
        psensorsDF: list[pd.DataFrame],
        shaftsDF: list[pd.DataFrame],
        gatewaysDF: list[pd.DataFrame] = None,
        relaysDF: list[pd.DataFrame] = None,
    ):
        """
        Insère tous les détecteurs et équipements associés à un labo.
        """

        # === Thermomètres ===
        insertThermo = self.build_insert_thermometer()
        for df in thermometersDF:
            consName = df.iloc[0].at[1]
            ref = df.iloc[1].at[1]
            name = df.iloc[2].at[1]
            sigma = float(df.iloc[3].at[1].replace(",", "."))
            insertThermo.bindValue(":Name", name)
            insertThermo.bindValue(":ManuName", consName)
            insertThermo.bindValue(":ManuRef", ref)
            insertThermo.bindValue(":Error", sigma)
            insertThermo.bindValue(":Labo", labID)
            if not insertThermo.exec():
                print(insertThermo.lastError())
        print("Thermometers added.")

        # === Pressure Sensors ===
        insertPsensor = self.build_insert_psensor()
        for df in psensorsDF:
            name = df.iloc[0].at[1]
            datalogger = df.iloc[1].at[1]
            calibrationDate = df.iloc[2].at[1]
            intercept = float(df.iloc[3].at[1].replace(",", "."))
            dudh = float(df.iloc[4].at[1].replace(",", "."))
            dudt = float(df.iloc[5].at[1].replace(",", "."))
            sigma = float(df.iloc[6].at[1].replace(",", "."))
            thermo_name = df.iloc[7].at[1]

            select_thermo = self.build_thermo_id(labID, thermo_name)
            if not select_thermo.exec():
                print(select_thermo.lastError())
            select_thermo.next()
            thermo_model = select_thermo.value(0)

            insertPsensor.bindValue(":Name", name)
            insertPsensor.bindValue(":Datalogger", datalogger)
            insertPsensor.bindValue(":Calibration", calibrationDate)
            insertPsensor.bindValue(":Intercept", intercept)
            insertPsensor.bindValue(":DuDh", dudh)
            insertPsensor.bindValue(":DuDt", dudt)
            insertPsensor.bindValue(":Error", sigma)
            insertPsensor.bindValue(":ThermoModel", thermo_model)
            insertPsensor.bindValue(":Labo", labID)
            if not insertPsensor.exec():
                print(insertPsensor.lastError())
        print("Pressure sensors added.")

        # === Shafts ===
        insertShaft = self.build_insert_shaft()
        for df in shaftsDF:
            name = df.iloc[0].at[1]
            datalogger = df.iloc[1].at[1]
            tSensorName = df.iloc[2].at[1]
            depths = literal_eval(df.iloc[3].at[1])
            select_thermo = self.build_thermo_id(labID, tSensorName)
            if not select_thermo.exec():
                print(select_thermo.lastError())
            select_thermo.next()
            thermo_model = select_thermo.value(0)

            insertShaft.bindValue(":Name", name)
            insertShaft.bindValue(":Datalogger", datalogger)
            insertShaft.bindValue(":Depth1", depths[0])
            insertShaft.bindValue(":Depth2", depths[1])
            insertShaft.bindValue(":Depth3", depths[2])
            insertShaft.bindValue(":Depth4", depths[3])
            insertShaft.bindValue(":ThermoModel", thermo_model)
            insertShaft.bindValue(":Labo", labID)
            if not insertShaft.exec():
                print(insertShaft.lastError())
        print("Shafts added.")

        # === Gateways ===
        if gatewaysDF:
            insertGateway = self.build_insert_gateway()
            for df in gatewaysDF:
                name = df.iloc[0].at[1]
                ip = df.iloc[1].at[1]
                port = int(df.iloc[2].at[1])
                insertGateway.bindValue(":Name", name)
                insertGateway.bindValue(":IP", ip)
                insertGateway.bindValue(":Port", port)
                insertGateway.bindValue(":Labo", labID)
                if not insertGateway.exec():
                    print(insertGateway.lastError())
            print("Gateways added.")

        # === Relays ===
        if relaysDF:
            insertRelay = self.build_insert_relay()
            for df in relaysDF:
                name = df.iloc[0].at[1]
                channel = int(df.iloc[1].at[1])
                gateway_name = df.iloc[2].at[1]
                select_gateway = QSqlQuery(self.con)
                select_gateway.prepare(
                    f"SELECT ID FROM Gateway WHERE Name='{gateway_name}' AND Labo='{labID}'"
                )
                select_gateway.exec()
                select_gateway.next()
                gateway_id = select_gateway.value(0)

                insertRelay.bindValue(":Name", name)
                insertRelay.bindValue(":Channel", channel)
                insertRelay.bindValue(":Gateway", gateway_id)
                insertRelay.bindValue(":Labo", labID)
                if not insertRelay.exec():
                    print(insertRelay.lastError())
            print("Relays added.")

    # ================================================================
    # =================== QUERIES DE CONSTRUCTION ====================
    # ================================================================
    def build_insert_lab(self, labName: str):
        query = QSqlQuery(self.con)
        query.prepare(f"INSERT INTO Labo (Name) VALUES ('{labName}')")
        return query

    def build_insert_thermometer(self):
        query = QSqlQuery(self.con)
        query.prepare("""
            INSERT INTO Thermometer (Name, ManuName, ManuRef, Error, Labo)
            VALUES (:Name, :ManuName, :ManuRef, :Error, :Labo)
        """)
        return query

    def build_insert_psensor(self):
        query = QSqlQuery(self.con)
        query.prepare("""
            INSERT INTO PressureSensor (Name, Datalogger, Calibration, Intercept, DuDH, DuDT, Error, ThermoModel, Labo)
            VALUES (:Name, :Datalogger, :Calibration, :Intercept, :DuDh, :DuDt, :Error, :ThermoModel, :Labo)
        """)
        return query

    def build_insert_shaft(self):
        query = QSqlQuery(self.con)
        query.prepare("""
            INSERT INTO Shaft (Name, Datalogger, Depth1, Depth2, Depth3, Depth4, ThermoModel, Labo)
            VALUES (:Name, :Datalogger, :Depth1, :Depth2, :Depth3, :Depth4, :ThermoModel, :Labo)
        """)
        return query

    def build_insert_gateway(self):
        query = QSqlQuery(self.con)
        query.prepare("""
            INSERT INTO Gateway (ID, CA_Cert, Labo, Name, TLS_Cert, TLS_Key, gatewayEUI)
            VALUES (:ID, :CA_Cert, :Labo, :Name, :TLS_Cert, :TLS_Key, :gatewayEUI)
        """)
        return query

    def build_insert_relay(self):
        query = QSqlQuery(self.con)
        query.prepare("""
            INSERT INTO Relay (ID, Gateway, Labo, Name, RelayEUI)
            VALUES (:ID, :Gateway, :Labo, :Name, :RelaiEUI)
        """)
        return query

    def build_insert_study(self):
        query = QSqlQuery(self.con)
        query.prepare("""
            INSERT INTO Study (Name, Labo)
            VALUES (:Name, :Labo)
        """)
        return query

    # ================================================================
    # ===================== SELECTS ET VERIFICATIONS =================
    # ================================================================
    def build_lab_id(self, labName: str):
        query = QSqlQuery(self.con)
        query.prepare(f"SELECT Labo.ID FROM Labo WHERE Labo.Name='{labName}'")
        return query

    def build_thermo_id(self, labID: int | str, thermoname: str):
        query = QSqlQuery(self.con)
        query.prepare(
            f"SELECT Thermometer.ID FROM Thermometer WHERE Thermometer.Name='{thermoname}' AND Thermometer.Labo='{labID}'"
        )
        return query

    def build_similar_lab(self, labName: str):
        query = QSqlQuery(self.con)
        query.prepare(f"SELECT Labo.Name FROM Labo WHERE Labo.Name='{labName}'")
        return query

    def build_select_labs(self, studyName=None):
        query = QSqlQuery(self.con)
        if studyName is None:
            query.prepare("SELECT Labo.Name FROM Labo")
        else:
            query.prepare(f"""
                SELECT Labo.Name FROM Labo
                JOIN Study ON Labo.ID = Study.Labo
                WHERE Study.Name='{studyName}'
            """)
        return query

    def build_select_studies(self):
        query = QSqlQuery(self.con)
        query.prepare("SELECT Study.Name FROM Study")
        return query

    def build_similar_studies(self, studyName: str):
        query = QSqlQuery(self.con)
        query.prepare(f"SELECT * FROM Study WHERE Study.Name='{studyName}'")
        return query

    def check_integrity(self, labName: str):
        similar_lab = self.build_similar_lab(labName)
        if not similar_lab.exec():
            print(similar_lab.lastError())
        return not similar_lab.next()

    def get_lab_names(self, studyName=None):
        query = self.build_select_labs(studyName)
        labs = []
        if not query.exec():
            print(query.lastError())
        while query.next():
            labs.append(query.value(0))
        return labs

    def get_study_names(self):
        query = self.build_select_studies()
        studies = []
        if not query.exec():
            print(query.lastError())
        while query.next():
            studies.append(query.value(0))
        return studies

    # ================================================================
    # =============== EDITION DES RELATIONS (Gateway/Relay/DL) ======
    # ================================================================
    def reassign_datalogger_to_relay(self, labID: int | str, dataloggerDevEUI: str, targetRelayName: str) -> bool:
        """
        Réaffecte un dataloggeur (identifié par son DevEUI) à un relais existant (nom + labo).

        Validation :
        - le datalogger existe dans le labo
        - le relais cible existe dans le labo
        - la réaffectation ne viole pas la contrainte UNIQUE(Relay, Name) sur Datalogger

        Retourne True si succès, False sinon.
        """
        # Récupérer le datalogger
        select_dl = QSqlQuery(self.con)
        select_dl.prepare(f"SELECT ID, Name, Relay FROM Datalogger WHERE DevEUI='{dataloggerDevEUI}' AND Labo='{labID}'")
        if not select_dl.exec():
            print(select_dl.lastError())
            return False
        if not select_dl.next():
            displayCriticalMessage(f"Datalogger '{dataloggerDevEUI}' introuvable dans le labo {labID}.")
            return False
        dl_id = select_dl.value(0)
        dl_name = select_dl.value(1)

        # Récupérer le relais cible
        select_relay = QSqlQuery(self.con)
        select_relay.prepare(f"SELECT ID FROM Relay WHERE Name='{targetRelayName}' AND Labo='{labID}'")
        if not select_relay.exec():
            print(select_relay.lastError())
            return False
        if not select_relay.next():
            displayCriticalMessage(f"Relais '{targetRelayName}' introuvable dans le labo {labID}.")
            return False
        target_relay_id = select_relay.value(0)

        # Vérifier la contrainte UNIQUE(Relay, Name) sur Datalogger
        check_conflict = QSqlQuery(self.con)
        check_conflict.prepare(f"SELECT ID FROM Datalogger WHERE Relay='{target_relay_id}' AND Name='{dl_name}'")
        if not check_conflict.exec():
            print(check_conflict.lastError())
            return False
        if check_conflict.next():
            existing_id = check_conflict.value(0)
            if existing_id != dl_id:
                displayCriticalMessage(f"Impossible de déplacer le datalogger '{dl_name}' vers le relais '{targetRelayName}' : un datalogger du même nom existe déjà sur ce relais.")
                return False

        # Effectuer la mise à jour
        update = QSqlQuery(self.con)
        update.prepare(f"UPDATE Datalogger SET Relay={target_relay_id} WHERE ID={dl_id}")
        if not update.exec():
            print(update.lastError())
            return False
        return True

    def reassign_relay_to_gateway(self, labID: int | str, relayName: str, targetGatewayName: str) -> bool:
        """
        Réaffecte un relais (par nom) vers une autre gateway existante (par nom) dans le même labo.

        Validation :
        - le relais existe dans le labo
        - la gateway cible existe dans le labo
        - la réaffectation ne viole pas UNIQUE(Gateway, Name) sur Relay

        Retourne True si succès, False sinon.
        """
        # Récupérer le relais
        select_relay = QSqlQuery(self.con)
        select_relay.prepare(f"SELECT ID, Gateway FROM Relay WHERE Name='{relayName}' AND Labo='{labID}'")
        if not select_relay.exec():
            print(select_relay.lastError())
            return False
        if not select_relay.next():
            displayCriticalMessage(f"Relais '{relayName}' introuvable dans le labo {labID}.")
            return False
        relay_id = select_relay.value(0)

        # Récupérer la gateway cible
        select_gw = QSqlQuery(self.con)
        select_gw.prepare(f"SELECT ID FROM Gateway WHERE Name='{targetGatewayName}' AND Labo='{labID}'")
        if not select_gw.exec():
            print(select_gw.lastError())
            return False
        if not select_gw.next():
            displayCriticalMessage(f"Gateway '{targetGatewayName}' introuvable dans le labo {labID}.")
            return False
        target_gw_id = select_gw.value(0)

        # Vérifier la contrainte UNIQUE(Gateway, Name) sur Relay
        check_conflict = QSqlQuery(self.con)
        check_conflict.prepare(f"SELECT ID FROM Relay WHERE Gateway='{target_gw_id}' AND Name='{relayName}'")
        if not check_conflict.exec():
            print(check_conflict.lastError())
            return False
        if check_conflict.next():
            existing_id = check_conflict.value(0)
            if existing_id != relay_id:
                displayCriticalMessage(f"Impossible de déplacer le relais '{relayName}' vers la gateway '{targetGatewayName}' : un relais du même nom existe déjà sur cette gateway.")
                return False

        # Effectuer la mise à jour
        update = QSqlQuery(self.con)
        update.prepare(f"UPDATE Relay SET Gateway={target_gw_id} WHERE ID={relay_id}")
        if not update.exec():
            print(update.lastError())
            return False
        return True
