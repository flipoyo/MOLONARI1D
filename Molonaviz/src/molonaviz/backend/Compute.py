from PyQt5 import QtCore
from PyQt5.QtSql import QSqlQuery
from pyheatmy import *
from numpy import shape

from ..utils.general import databaseDateToDatetime, datetimeToDatabaseDate
from .SPointCoordinator import SPointCoordinator

class ColumnMCMCRunner(QtCore.QObject):
    """
    A QT runner which is meant to launch the MCMC in its own thread.
    """
    finished = QtCore.pyqtSignal()

    def __init__(self, col, nb_iter: int, all_priors: dict, nb_cells: str, quantiles: list):
        super(ColumnMCMCRunner, self).__init__()

        self.col = col
        self.nb_iter = nb_iter
        self.all_priors = all_priors
        self.nb_cells = nb_cells
        self.quantiles = quantiles

    def run(self):
        print("Launching MCMC...")
        self.col.compute_mcmc(self.nb_iter, self.all_priors, self.nb_cells, self.quantiles)
        self.finished.emit()

class ColumnDirectModelRunner(QtCore.QObject):
    """
    A QT runner which is meant to launch the Direct Model in its own thread.
    """
    finished = QtCore.pyqtSignal()

    def __init__(self, col, params : list[list], nb_cells : int):
        super(ColumnDirectModelRunner, self).__init__()
        self.col = col
        self.params = params
        self.nb_cells = nb_cells

    def run(self):
        print("Launching Direct Model...")
        layers = layersListCreator(self.params)
        self.col.compute_solve_transi(layers, self.nb_cells)
        self.finished.emit()

class Compute(QtCore.QObject):
    """
    How to use this class :
    - Initialise the compute engine by giving it the  database connection and ID of the current Point.
    - When computations are needed, create an associated Column objected. This requires cleaned measures to be in the database for this point. This can be made by calling compute.set_column()
    - Launch the computation :
        - with given parameters : compute.compute_direct_model(params: tuple, nb_cells: int, sensorDir: str)
        - with parameters inferred from MCMC : compute.compute_MCMC(nb_iter: int, priors: dict, nb_cells: str, sensorDir: str)
    """
    MCMCFinished = QtCore.pyqtSignal()
    DirectModelFinished = QtCore.pyqtSignal()

    def __init__(self, coordinator : SPointCoordinator):
        # Call constructor of parent classes
        super(Compute, self).__init__()
        self.thread = QtCore.QThread()

        self.con = coordinator.con
        self.pointID = coordinator.pointID
        self.coordinator = coordinator
        self.col = None

    def set_column(self):
        """
        Create the Column object associated to the current Point.
        """
        press = []
        temps = []
        cleaned_measures = self.coordinator.build_cleaned_measures(full_query=True)
        cleaned_measures.exec()
        while cleaned_measures.next():
            # Warning: temperatures are stored in °C. However, phyheatmy requires K to work!
            temps.append([databaseDateToDatetime(cleaned_measures.value(0)),[cleaned_measures.value(i)+273.15 for i in range(1,5)]]) #Date and 4 Temperatures
            press.append([databaseDateToDatetime(cleaned_measures.value(0)), [cleaned_measures.value(6), cleaned_measures.value(5) + 273.15]]) #Date, Pressure, Temperature

        column_infos = self.build_column_infos()
        column_infos.exec()
        column_infos.next()

        col_dict = {
	        "river_bed" : column_infos.value(0),
            "depth_sensors" : [column_infos.value(i) for i in [1,2,3,4]],
	        "offset" : column_infos.value(5),
            "dH_measures" : press,
	        "T_measures" : temps,
            "sigma_meas_P" : column_infos.value(6),
            "sigma_meas_T" : column_infos.value(7),
            "inter_mode" : "linear"
            }

        self.col = Column.from_dict(col_dict)

    def compute_direct_model(self, params : list[list],  nb_cells: int):
        """
        Launch the direct model with given parameters per layer.
        """
        if self.thread.isRunning():
            print("Please wait while for the previous computation to end")
            return

        self.save_layers_and_params(params)
        self.update_nb_cells(nb_cells)

        self.set_column() #Updates self.col
        self.direct_runner = ColumnDirectModelRunner(self.col,params,nb_cells)
        self.direct_runner.finished.connect(self.end_direct_model)
        self.direct_runner.moveToThread(self.thread)
        self.thread.started.connect(self.direct_runner.run)
        self.thread.start()

    def end_direct_model(self):
        """
        This is called when the DirectModel is over. Save the relevant information in the database
        """
        self.save_direct_model_results()

        self.thread.quit()
        print("Direct model finished.")

        self.DirectModelFinished.emit()

    def update_nb_cells(self, nb_cells):
        """
        Update entry in Point table to reflect the given number of cells.
        """
        updatePoint =  QSqlQuery(self.con)
        updatePoint.prepare(f"UPDATE Point SET DiscretStep = {nb_cells} WHERE ID = {self.pointID}")
        updatePoint.exec()

    def save_layers_and_params(self, data : list[list]):
        """
        Save the layers and the last parameters in the database.
        """
        insertlayer = QSqlQuery(self.con)
        insertlayer.prepare("INSERT INTO Layer (Name, Depth, PointKey) VALUES (:Name, :Depth, :PointKey)")
        insertlayer.bindValue(":PointKey", self.pointID)

        insertparams = QSqlQuery(self.con)
        insertparams.prepare(f"""INSERT INTO BestParameters (Permeability, ThermConduct, Porosity, Capacity, Layer, PointKey)
                           VALUES (:Permeability, :ThermConduct, :Porosity, :Capacity, :Layer, :PointKey)""")
        insertparams.bindValue(":PointKey", self.pointID)

        self.con.transaction()
        for layer, depth, perm, n, lamb, rho in data:
            insertlayer.bindValue(":Name", layer)
            insertlayer.bindValue(":Depth", depth)
            insertlayer.exec()

            insertparams.bindValue(":Permeability", perm)
            insertparams.bindValue(":ThermConduct", lamb)
            insertparams.bindValue(":Porosity", n)
            insertparams.bindValue(":Capacity", rho)
            insertparams.bindValue(":Layer", insertlayer.lastInsertId())
            insertparams.exec()
        self.con.commit()

    def save_direct_model_results(self, save_dates = True):
        """
        Query the database and save the direct model results.
        """
        #Quantile 0
        insertquantiles = QSqlQuery(self.con)
        insertquantiles.prepare(f"INSERT INTO Quantile (Quantile, PointKey) VALUES (0,{self.pointID})")

        insertquantiles.exec()
        quantileID = insertquantiles.lastInsertId()

        depths = self.col.get_depths_solve()
        #Depths
        if save_dates:
            insertDepths = QSqlQuery(self.con)
            insertDepths.prepare("INSERT INTO Depth (Depth,PointKey) VALUES (:Depth, :PointKey)")
            insertDepths.bindValue(":PointKey", self.pointID)
            self.con.transaction()
            for depth in depths:
                insertDepths.bindValue(":Depth", float(depth))
                insertDepths.exec()
            self.con.commit()

        #Temperature and heat flows
        fetchDate = QSqlQuery(self.con)
        fetchDate.prepare(f"SELECT Date.ID FROM Date WHERE Date.PointKey = :PointKey AND Date.Date = :Date ")
        fetchDate.bindValue(":PointKey", self.pointID)
        fetchDepth = QSqlQuery(self.con)
        fetchDepth.prepare(f"SELECT Depth.ID FROM Depth WHERE Depth.PointKey = :PointKey AND Depth.Depth = :Depth")
        fetchDepth.bindValue(":PointKey", self.pointID)

        solvedTemps = self.col.get_temps_solve()
        advecFlows = self.col.get_advec_flows_solve()
        conduFlows = self.col.get_conduc_flows_solve()
        times = self.col.get_times_solve()

        insertTemps = QSqlQuery(self.con)
        insertTemps.prepare("""INSERT INTO TemperatureAndHeatFlows (Date, Depth, Temperature, AdvectiveFlow, ConductiveFlow, TotalFlow, PointKey, Quantile)
            VALUES (:Date, :Depth, :Temperature, :AdvectiveFlow, :ConductiveFlow, :TotalFlow, :PointKey, :Quantile)""")
        insertTemps.bindValue(":PointKey", self.pointID)
        insertTemps.bindValue(":Quantile", quantileID)
        #We assume solvedTemps,advecFlows and conduFlows have the same shapes, and that the dates and depths are also identical, ie the first column of all three arrays corrresponds to the same fixed date.

        nb_rows,nb_cols = shape(solvedTemps)
        self.con.transaction()
        for j in range(nb_cols):
            fetchDate.bindValue(":Date", datetimeToDatabaseDate(times[j]))
            fetchDate.exec()
            fetchDate.next()
            insertTemps.bindValue(":Date", fetchDate.value(0))
            for i in range(nb_rows):
                fetchDepth.bindValue(":Depth", float(depths[i]))
                fetchDepth.exec()
                fetchDepth.next()
                insertTemps.bindValue(":Depth", fetchDepth.value(0))
                # We need to convert into float, as SQL doesn't undestand np.float32 !
                insertTemps.bindValue(":Temperature", float(solvedTemps[i,j]) -273.15) # Also convert to °C (pyheatmy returns K)
                insertTemps.bindValue(":AdvectiveFlow", float(advecFlows[i,j]))
                insertTemps.bindValue(":ConductiveFlow", float(conduFlows[i,j]))
                insertTemps.bindValue(":TotalFlow", float(advecFlows[i,j] + conduFlows[i,j]))
                insertTemps.exec()
        self.con.commit()

        #Water flows
        waterFlows = self.col.get_flows_solve(depths[0]) #Water flows at the top of the column.
        insertFlows = QSqlQuery(self.con)
        insertFlows.prepare("INSERT INTO WaterFlow (WaterFlow, Date, PointKey, Quantile) VALUES (:WaterFlow,:Date, :PointKey, :Quantile)")
        insertFlows.bindValue(":PointKey", self.pointID)
        insertFlows.bindValue(":Quantile", quantileID)
        self.con.transaction()
        for j in range(nb_cols):
            fetchDate.bindValue(":Date", datetimeToDatabaseDate(times[j]))
            fetchDate.exec()
            fetchDate.next()
            insertFlows.bindValue(":WaterFlow", float(waterFlows[j]))
            insertFlows.bindValue(":Date", fetchDate.value(0))
            insertFlows.exec()
        self.con.commit()

        #RMSE
        sensorsID = self.col.get_id_sensors()
        depthsensors = [depths[i-1] for i in sensorsID] #Python indexing starts a 0 but cells are indexed starting at 1
        computedRMSE = self.col.get_RMSE()
        insertRMSE = QSqlQuery(self.con)
        insertRMSE.prepare("""INSERT INTO RMSE (Depth1, Depth2, Depth3, RMSE1, RMSE2, RMSE3, RMSETotal, PointKey, Quantile)
                 VALUES (:Depth1, :Depth2, :Depth3, :RMSE1, :RMSE2, :RMSE3, :RMSETotal, :PointKey, :Quantile)""")
        insertRMSE.bindValue(":PointKey", self.pointID)
        insertRMSE.bindValue(":Quantile", quantileID)

        self.con.transaction()
        for i in range(1,4):
            fetchDepth.bindValue(":Depth", float(depthsensors[i-1]))
            fetchDepth.exec()
            fetchDepth.next()
            insertRMSE.bindValue(f":Depth{i}", fetchDepth.value(0))
            insertRMSE.bindValue(f":RMSE{i}", float(computedRMSE[i-1]))
        insertRMSE.bindValue(":RMSETotal", float(computedRMSE[3]))
        insertRMSE.exec()
        self.con.commit()

    def compute_MCMC(self, nb_iter: int, all_priors : list, nb_cells: str, quantiles: tuple):
        """
        Launch the MCMC computation with given parameters.
        """
        if self.thread.isRunning():
            print("Please wait while for the previous computation to end")
            return

        self.update_nb_cells(nb_cells)

        self.set_column() #Updates self.col
        self.mcmc_runner = ColumnMCMCRunner(self.col, nb_iter, all_priors, nb_cells, quantiles)
        self.mcmc_runner.finished.connect(self.end_MCMC)
        self.mcmc_runner.moveToThread(self.thread)
        self.thread.started.connect(self.mcmc_runner.run)
        self.thread.start()

    def end_MCMC(self):
        """
        This is called when the MCMC is over. Save the relevant information in the database.
        """
        self.save_MCMC_results()

        self.thread.quit()
        print("MCMC finished.")

        self.MCMCFinished.emit()

    def save_MCMC_results(self):
        """
        Query the database and save the MCMC results. This is essentially a copy of saveDirectResults, except for the function called to get the results.
        """
        #Quantiles for the MCMC
        quantiles = self.col.get_quantiles()
        depths = self.col.get_depths_mcmc() # Should be get_depths_solve?
        times = self.col.get_times_mcmc()

        sensorsID = self.col.get_id_sensors()
        depthsensors = [depths[i-1] for i in sensorsID] #Python indexing starts a 0 but cells are indexed starting at 1

        #Quantile
        insertquantiles = QSqlQuery(self.con)
        insertquantiles.prepare(f"INSERT INTO Quantile (Quantile, PointKey) VALUES (:Quantile,{self.pointID})")
        #Depths
        insertDepths = QSqlQuery(self.con)
        insertDepths.prepare("INSERT INTO Depth (Depth,PointKey) VALUES (:Depth, :PointKey)")
        insertDepths.bindValue(":PointKey", self.pointID)
        #Temperature and heat flows
        fetchDate = QSqlQuery(self.con)
        fetchDate.prepare(f"SELECT Date.ID FROM Date WHERE Date.PointKey = :PointKey AND Date.Date = :Date ")
        fetchDate.bindValue(":PointKey", self.pointID)
        fetchDepth = QSqlQuery(self.con)
        fetchDepth.prepare(f"SELECT Depth.ID FROM Depth WHERE Depth.PointKey = :PointKey AND Depth.Depth = :Depth")
        fetchDepth.bindValue(":PointKey", self.pointID)
        insertTemps = QSqlQuery(self.con)
        insertTemps.prepare("""INSERT INTO TemperatureAndHeatFlows (Date, Depth, Temperature, AdvectiveFlow, ConductiveFlow, TotalFlow, PointKey, Quantile)
            VALUES (:Date, :Depth, :Temperature, :AdvectiveFlow, :ConductiveFlow, :TotalFlow, :PointKey, :Quantile)""")
        #Water Flows
        insertTemps.bindValue(":PointKey", self.pointID)
        insertFlows = QSqlQuery(self.con)
        insertFlows.prepare("INSERT INTO WaterFlow (WaterFlow, Date, PointKey, Quantile) VALUES (:WaterFlow,:Date, :PointKey, :Quantile)")
        insertFlows.bindValue(":PointKey", self.pointID)
        #RMSE
        insertRMSE = QSqlQuery(self.con)
        insertRMSE.prepare("""INSERT INTO RMSE (Depth1, Depth2, Depth3, RMSE1, RMSE2, RMSE3, RMSETotal, PointKey, Quantile)
                 VALUES (:Depth1, :Depth2, :Depth3, :RMSE1, :RMSE2, :RMSE3, :RMSETotal, :PointKey, :Quantile)""")
        insertRMSE.bindValue(":PointKey", self.pointID)

        self.con.transaction()
        for depth in depths:
            insertDepths.bindValue(":Depth", float(depth))
            insertDepths.exec()
        self.con.commit()

        for quantile in quantiles:
            insertquantiles.bindValue(":Quantile",quantile)
            insertquantiles.exec()
            quantileID = insertquantiles.lastInsertId()

            insertTemps.bindValue(":Quantile", quantileID)
            #We assume solvedTemps,advecFlows and conduFlows have the same shapes, and that the dates and depths are also identical, ie the first column of all three arrays corrresponds to the same fixed date.
            solvedTemps = self.col.get_temps_quantile(quantile)
            nb_rows,nb_cols = shape(solvedTemps)
            self.con.transaction()
            for j in range(nb_cols):
                fetchDate.bindValue(":Date", datetimeToDatabaseDate(times[j]))
                fetchDate.exec()
                fetchDate.next()
                insertTemps.bindValue(":Date", fetchDate.value(0))
                # Note: we leave out the AdvectiveFlow, ConductiveFlow and TotalFlow. Why?
                # Well theses values are not computed per quantile: instead, there are computed for the direct model.
                # There is no need to store these values as they don't represent anything. Hence, we leave them out and they will be empty.
                # This isn't a problem as they are never used: once again, only the values for the direct model are relevant.
                for i in range(nb_rows):
                    fetchDepth.bindValue(":Depth", float(depths[i]))
                    fetchDepth.exec()
                    fetchDepth.next()
                    insertTemps.bindValue(":Depth", fetchDepth.value(0))
                    insertTemps.bindValue(":Temperature", float(solvedTemps[i,j]) - 273.15) #Need to convert into float, as SQL doesn't undestand np.float32 !
                    insertTemps.exec()
            self.con.commit()

            #Water flows
            waterFlows = self.col.get_flows_quantile(quantile)[0,:] #Water flows at the top of the column.
            insertFlows.bindValue(":Quantile", quantileID)
            self.con.transaction()
            for j in range(nb_cols):
                fetchDate.bindValue(":Date", datetimeToDatabaseDate(times[j]))
                fetchDate.exec()
                fetchDate.next()
                insertFlows.bindValue(":WaterFlow", float(waterFlows[j]))
                insertFlows.bindValue(":Date", fetchDate.value(0))
                insertFlows.exec()
            self.con.commit()

            #RMSE
            computedRMSE = self.col.get_RMSE_quantile(quantile)
            insertRMSE.bindValue(":Quantile", quantileID)

            self.con.transaction()
            for i in range(1,4):
                fetchDepth.bindValue(":Depth", float(depthsensors[i-1]))
                fetchDepth.exec()
                fetchDepth.next()
                insertRMSE.bindValue(f":Depth{i}", fetchDepth.value(0))
                insertRMSE.bindValue(f":RMSE{i}", float(computedRMSE[i-1]))
            insertRMSE.bindValue(":RMSETotal", float(computedRMSE[3]))
            insertRMSE.exec()
            self.con.commit()

        # Layers
        # Warning: the code for inserting the layers is a duplicate from save_layers_and_params.
        # We use a copy of save_layers_and_params's code just because we are lazy and don't want to
        # create all the layers THEN query one by one to get their ID THEN insert the parameters distribution. Here, we do it all at once.
        layers = self.col.get_best_layers()
        all_params = self.col.get_all_params()
        current_params_index = 0

        insertlayer = QSqlQuery(self.con)
        insertlayer.prepare("INSERT INTO Layer (Name, Depth, PointKey) VALUES (:Name, :Depth, :PointKey)")
        insertlayer.bindValue(":PointKey", self.pointID)
        insertparams = QSqlQuery(self.con)
        insertparams.prepare(f"""INSERT INTO BestParameters (Permeability, ThermConduct, Porosity, Capacity, Layer, PointKey)
                           VALUES (:Permeability, :ThermConduct, :Porosity, :Capacity, :Layer, :PointKey)""")
        insertparams.bindValue(":PointKey", self.pointID)
        insertdistribution = QSqlQuery(self.con)
        insertdistribution.prepare("""INSERT INTO ParametersDistribution (Permeability, ThermConduct, Porosity, HeatCapacity, Layer, PointKey)
                VALUES (:Permeability, :ThermConduct,  :Porosity, :HeatCapacity, :Layer, :PointKey)""")
        insertdistribution.bindValue(":PointKey", self.pointID)

        self.con.transaction()
        for elem in layers:
            name = elem.name
            zLow = elem.zLow
            perm = elem.params.moinslog10K
            poro = elem.params.n
            lambda_s = elem.params.lambda_s
            rhos_cs = elem.params.rhos_cs

            insertlayer.bindValue(":Name", name)
            insertlayer.bindValue(":Depth", zLow)
            insertlayer.exec()
            layerID = insertlayer.lastInsertId()

            insertparams.bindValue(":Permeability", perm)
            insertparams.bindValue(":ThermConduct", lambda_s)
            insertparams.bindValue(":Porosity", poro)
            insertparams.bindValue(":Capacity", rhos_cs)
            insertparams.bindValue(":Layer", layerID)
            insertparams.exec()

            all_params_layer = all_params[current_params_index]
            for params in all_params_layer:
                #Convert everything to float as the parameters are of type np.float
                insertdistribution.bindValue(":Permeability", float(params[0]))
                insertdistribution.bindValue(":ThermConduct", float(params[2]))
                insertdistribution.bindValue(":Porosity", float(params[1]))
                insertdistribution.bindValue(":HeatCapacity", float(params[3]))
                insertdistribution.bindValue(":Layer", layerID)
                insertdistribution.exec()
            current_params_index +=1
        self.con.commit()

        # Recompute direct model with best parameters.
        self.col.compute_solve_transi(layers, self.mcmc_runner.nb_cells, verbose = False)
        self.save_direct_model_results(save_dates = False)

    def build_column_infos(self):
        """
        Build and return a query giving all the necessary information for the column.
        """
        query  = QSqlQuery(self.con)
        query.prepare(f"""SELECT SamplingPoint.RiverBed, Shaft.Depth1, Shaft.Depth2, Shaft.Depth3, Shaft.Depth4, SamplingPoint.Offset, PressureSensor.Error, Thermometer.Error FROM SamplingPoint
            JOIN PressureSensor
            ON SamplingPoint.PressureSensor = PressureSensor.ID
            JOIN Shaft
            ON SamplingPoint.Shaft = Shaft.ID
            JOIN Thermometer
            ON Shaft.ThermoModel = Thermometer.ID
            JOIN Point
            ON SamplingPoint.ID = Point.SamplingPoint
            WHERE Point.ID = {self.pointID}
        """)
        return query