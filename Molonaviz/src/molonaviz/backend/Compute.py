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

    def __init__(
        self,
        col,
        nb_iter: int,
        all_priors: dict,
        nb_cells: str,
        quantiles: list,
        nb_chains: int,
        delta: float,
        ncr,
        c,
        cstar,
        remanence,
        n_sous_ech_iter,
        n_sous_ech_time,
        n_sous_ech_space,
        threshold
    ):
        super(ColumnMCMCRunner, self).__init__()

        self.col = col
        self.nb_iter = nb_iter
        self.all_priors = all_priors
        self.nb_cells = nb_cells
        self.quantiles = quantiles

        self.nb_chains = nb_chains
        self.delta = delta
        self.ncr = ncr
        self.c = c
        self.cstar = cstar
        self.remanence = remanence
        self.n_sous_ech_iter = n_sous_ech_iter
        self.n_sous_ech_time = n_sous_ech_time
        self.n_sous_ech_space = n_sous_ech_space
        self.threshold = threshold

    def get_last_best_params(self):
        """
        Convert best parameters (coming from pyheatmy) into direct parameters
        """
        layers = []
        depths = []
        permeability = []
        porosity = []
        thermconduct = []
        thermcap = []
        best = self.col.get_best_layers()
        for elem in best:
            layers.append(elem.name)
            depths.append(float(elem.zLow))
            permeability.append(float(elem.params.moinslog10IntrinK))
            porosity.append(float(elem.params.n))
            thermconduct.append(float(elem.params.lambda_s))
            thermcap.append(float(elem.params.rhos_cs))

        return zip(layers, depths, permeability, porosity, thermconduct, thermcap)

    def run(self):
        print("Launching MCMC...")
        self.col.compute_mcmc(
            self.nb_iter,
            self.all_priors,
            self.nb_cells,
            self.quantiles,
            self.nb_chains,
            self.delta,
            self.ncr,
            self.c,
            self.cstar,
            self.remanence,
            self.n_sous_ech_iter,
            self.n_sous_ech_time,
            self.n_sous_ech_space,
            self.threshold
        )
        
        print("Launching Direct Model wih Best Parameters...")
        params = self.get_last_best_params()
        layers = layersListCreator(params)
        self.col.compute_solve_transi(layers, self.nb_cells)
        self.finished.emit()


class ColumnDirectModelRunner(QtCore.QObject):
    """
    A QT runner which is meant to launch the Direct Model in its own thread.
    """

    finished = QtCore.pyqtSignal()

    def __init__(self, col, params: list[list], nb_cells: int):
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

    # signals which will be connected to the updateAllViews function
    MCMCFinished = QtCore.pyqtSignal()
    DirectModelFinished = QtCore.pyqtSignal()

    def __init__(self, coordinator: SPointCoordinator):
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
        temperatures = []
        cleaned_measures = self.coordinator.build_cleaned_measures(full_query=True)
        if (not cleaned_measures.exec()) : print(cleaned_measures.lastError())
        while cleaned_measures.next():
            # Warning: temperatures are stored in °C. However, phyheatmy requires K to work!
            temperatures.append(
                [
                    databaseDateToDatetime(cleaned_measures.value(0)),
                    [cleaned_measures.value(i) + 273.15 for i in range(1, 5)],
                ]
            )  # Date and 4 Temperatures
            press.append(
                [
                    databaseDateToDatetime(cleaned_measures.value(0)),
                    [cleaned_measures.value(6), cleaned_measures.value(5) + 273.15],
                ]
            )  # Date, Pressure, Temperature

        column_infos = self.build_column_infos()
        if (not column_infos.exec()) : print(column_infos.lastError())
        column_infos.next()

        col_dict = {
            "river_bed": column_infos.value(0),
            "depth_sensors": [column_infos.value(i) for i in [1, 2, 3, 4]],
            "offset": column_infos.value(5),
            "dH_measures": press,
            "T_measures": temperatures,
            "sigma_meas_P": column_infos.value(6),
            "sigma_meas_T": column_infos.value(7),
            "inter_mode": "linear",
        }

        self.col = Column.from_dict(col_dict)

    def compute_direct_model(self, params: list[list], nb_cells: int):
        """
        Launch the direct model with given parameters per layer.
        """
        if self.thread.isRunning():
            print("Please wait while for the previous computation to end")
            return

        self.thread.terminate()
        self.thread = QtCore.QThread()

        self.set_column()  # Updates self.col
        self.params = params
        self.nb_cells = nb_cells
        self.direct_runner = ColumnDirectModelRunner(self.col, params, nb_cells)

        # we connect the signal which will be emitted by the runner when it's finished to the function which will be called (end_direct_model)
        self.direct_runner.finished.connect(self.end_direct_model)
        self.direct_runner.moveToThread(self.thread)

        # we connect the signal which will be emitted by the thread when it's started to the function which will be called (run)
        self.thread.started.connect(self.direct_runner.run)

        # we start the thread, so run is called
        self.thread.start()

    def end_direct_model(self):
        """
        This is called when the DirectModel is over. Save the relevant information in the database
        """
        self.save_layers_and_params(self.params, self.nb_cells)
        self.save_direct_model_results()

        self.thread.quit()
        print("Direct model finished.")

        self.DirectModelFinished.emit()

    def get_nb_cells(self):
        """
        Return the number of cells from the database
        """
        getNbCells = QSqlQuery(self.con)
        getNbCells.prepare(
            f"SELECT DiscretStep FROM Point WHERE ID = {self.pointID}"
        )
        if (not getNbCells.exec()) : print(getNbCells.lastError())
        getNbCells.next()
        return getNbCells.value(0)

    def update_nb_cells(self, nb_cells):
        """
        Update entry in Point table to reflect the given number of cells.
        """
        updatePoint = QSqlQuery(self.con)
        updatePoint.prepare(
            f"UPDATE Point SET DiscretStep = {nb_cells} WHERE ID = {self.pointID}"
        )
        if (not updatePoint.exec()) : print(updatePoint.lastError())

    def save_layers_and_params(self, data: list[list], nb_cells : int):
        """
        Save the layers and the last parameters in the database.
        """
        self.update_nb_cells(nb_cells)

        insertlayer = QSqlQuery(self.con)
        insertlayer.prepare(
            "INSERT INTO Layer (Name, Depth, PointKey) VALUES (:Name, :Depth, :PointKey)"
        )
        insertlayer.bindValue(":PointKey", self.pointID)

        insertparams = QSqlQuery(self.con)
        insertparams.prepare(f"""INSERT INTO Parameters (Permeability, Porosity, ThermConduct, Capacity, Layer, PointKey)
                           VALUES (:Permeability, :Porosity, :ThermConduct, :Capacity, :Layer, :PointKey)""")
        insertparams.bindValue(":PointKey", self.pointID)

        self.con.transaction()
        for layer, depth, perm, n, lamb, rho in data:
            insertlayer.bindValue(":Name", layer)
            insertlayer.bindValue(":Depth", depth)
            if (not insertlayer.exec()) : print(insertlayer.lastError())

            insertparams.bindValue(":Permeability", perm) # already float => OK
            insertparams.bindValue(":Porosity", n)
            insertparams.bindValue(":ThermConduct", lamb)
            insertparams.bindValue(":Capacity", rho)
            insertparams.bindValue(":Layer", insertlayer.lastInsertId())
            if (not insertparams.exec()) : print(insertparams.lastError())

        self.con.commit()

    def save_params_MCMC(self, paramsMCMC : list[list]):
        """
        Save the parameters of MCMC inversion in the database.
        """
        self.update_nb_cells(paramsMCMC[2]) # see dialogCompute getInputMCMC

        insertparams = QSqlQuery(self.con)
        insertparams.prepare(f"""INSERT INTO InputMCMC (Niter , Delta , Nchains ,NCR, C , Cstar , Kmin , Kmax, Ksigma , PorosityMin , PorosityMax ,
                              PorositySigma , TcondMin , TcondMax , TcondSigma , TcapMin , TcapMax , TcapSigma ,  Remanence , tresh , nb_sous_ech_iter ,
                              nb_sous_ech_space , nb_sous_ech_time , Quantiles, PointKey)
                              VALUES (:Niter , :Delta , :Nchains ,:NCR, :C , :Cstar , :Kmin , :Kmax, :Ksigma , 
                              :PorosityMin , :PorosityMax , :PorositySigma , :TcondMin , :TcondMax ,
                              :TcondSigma , :TcapMin , :TcapMax , :TcapSigma ,  :Remanence , :tresh , :nb_sous_ech_iter ,
                              :nb_sous_ech_space , :nb_sous_ech_time , :Quantiles , :PointKey)""")
        insertparams.bindValue(":PointKey", self.pointID)

        self.con.transaction()
        # We really should use a dictionary!
        # Look at dialogCompute getInputMCMC
        insertparams.bindValue(":Niter",            paramsMCMC[0])

        # Each layer priors are equals
        all_priors =                                paramsMCMC[1][0][2] # Priors ([2]) of the first layer ([0])

        insertparams.bindValue(":Kmin",             all_priors["moinslog10IntrinK"][0][0])
        insertparams.bindValue(":Kmax",             all_priors["moinslog10IntrinK"][0][1])
        insertparams.bindValue(":Ksigma",           all_priors["moinslog10IntrinK"][1])
        insertparams.bindValue(":PorosityMin",      all_priors["n"][0][0])
        insertparams.bindValue(":PorosityMax",      all_priors["n"][0][1])
        insertparams.bindValue(":PorositySigma",    all_priors["n"][1])
        insertparams.bindValue(":TcondMin",         all_priors["lambda_s"][0][0])
        insertparams.bindValue(":TcondMax",         all_priors["lambda_s"][0][1])
        insertparams.bindValue(":TcondSigma",       all_priors["lambda_s"][1])
        insertparams.bindValue(":TcapMin",          all_priors["rhos_cs"][0][0])
        insertparams.bindValue(":TcapMax",          all_priors["rhos_cs"][0][1])
        insertparams.bindValue(":TcapSigma",        all_priors["rhos_cs"][1])

        #                                           paramsMCMC[2]  nb_cells

        insertparams.bindValue(":Quantiles",        paramsMCMC[3]) # Must be a string
        insertparams.bindValue(":Nchains",          paramsMCMC[4])
        insertparams.bindValue(":Delta",            paramsMCMC[5])
        insertparams.bindValue(":NCR",              paramsMCMC[6])
        insertparams.bindValue(":C",                paramsMCMC[7])
        insertparams.bindValue(":Cstar",            paramsMCMC[8])
        insertparams.bindValue(":Remanence",        paramsMCMC[9])
        insertparams.bindValue(":nb_sous_ech_iter", paramsMCMC[10])
        insertparams.bindValue(":nb_sous_ech_time", paramsMCMC[11])
        insertparams.bindValue(":nb_sous_ech_space",paramsMCMC[12])
        insertparams.bindValue(":tresh",            paramsMCMC[13])

        if (not insertparams.exec()) : print(insertparams.lastError())
        self.con.commit()

    def save_direct_model_results(self, save_dates=True):
        """
        Query the database and save the direct model results.
        """
        # Quantile 0
        insertquantiles = QSqlQuery(self.con)
        insertquantiles.prepare(
            f"INSERT INTO Quantile (Quantile, PointKey) VALUES (0,{self.pointID})"
        )
        if (not insertquantiles.exec()) : print(insertquantiles.lastError())

        quantileID = insertquantiles.lastInsertId()

        depths = self.col.get_depths_solve()
        # Depths
        if save_dates:
            insertDepths = QSqlQuery(self.con)
            insertDepths.prepare(
                "INSERT INTO Depth (Depth,PointKey) VALUES (:Depth, :PointKey)"
            )
            insertDepths.bindValue(":PointKey", self.pointID)
            self.con.transaction()
            for depth in depths:
                insertDepths.bindValue(":Depth", float(depth))
                if (not insertDepths.exec()) : print(insertDepths.lastError())
            self.con.commit()

        # Temperature and heat flows
        fetchDate = QSqlQuery(self.con)
        fetchDate.prepare(
            f"SELECT Date.ID FROM Date WHERE Date.PointKey = :PointKey AND Date.Date = :Date "
        )
        fetchDate.bindValue(":PointKey", self.pointID)
        fetchDepth = QSqlQuery(self.con)
        fetchDepth.prepare(
            f"SELECT Depth.ID FROM Depth WHERE Depth.PointKey = :PointKey AND Depth.Depth = :Depth"
        )
        fetchDepth.bindValue(":PointKey", self.pointID)

        solvedtemperatures = self.col.get_temperatures_solve()
        advecFlows = self.col.get_advec_flows_solve()
        conduFlows = self.col.get_conduc_flows_solve()
        times = self.col.get_times_solve()

        inserttemperatures = QSqlQuery(self.con)
        inserttemperatures.prepare(
            """INSERT INTO TemperatureAndHeatFlows (Date, Depth, Temperature, AdvectiveFlow, ConductiveFlow, TotalFlow, PointKey, Quantile)
            VALUES (:Date, :Depth, :Temperature, :AdvectiveFlow, :ConductiveFlow, :TotalFlow, :PointKey, :Quantile)"""
        )
        inserttemperatures.bindValue(":PointKey", self.pointID)
        inserttemperatures.bindValue(":Quantile", quantileID)
        # We assume solvedtemperatures,advecFlows and conduFlows have the same shapes, and that the dates and depths are also identical, ie the first column of all three arrays corrresponds to the same fixed date.

        nb_rows, nb_cols = shape(solvedtemperatures)
        self.con.transaction()
        for j in range(nb_cols):
            fetchDate.bindValue(":Date", datetimeToDatabaseDate(times[j]))
            if (not fetchDate.exec()) : print(fetchDate.lastError())
            fetchDate.next()
            inserttemperatures.bindValue(":Date", fetchDate.value(0))
            for i in range(nb_rows):
                fetchDepth.bindValue(":Depth", float(depths[i]))
                if (not fetchDepth.exec()) : print(fetchDepth.lastError())
                fetchDepth.next()
                inserttemperatures.bindValue(":Depth", fetchDepth.value(0))
                # We need to convert into float, as SQL doesn't undestand np.float32 !
                inserttemperatures.bindValue(
                    ":Temperature", float(solvedtemperatures[i, j]) - 273.15
                )  # Also convert to °C (pyheatmy returns K)
                inserttemperatures.bindValue(":AdvectiveFlow", float(advecFlows[i, j]))
                inserttemperatures.bindValue(":ConductiveFlow", float(conduFlows[i, j]))
                inserttemperatures.bindValue(
                    ":TotalFlow", float(advecFlows[i, j] + conduFlows[i, j])
                )
                if (not inserttemperatures.exec()) : print(inserttemperatures.lastError())
        self.con.commit()

        # Water flows
        waterFlows = self.col.get_flows_solve(
            depths[0]
        )  # Water flows at the top of the column.
        insertFlows = QSqlQuery(self.con)
        insertFlows.prepare(
            "INSERT INTO WaterFlow (WaterFlow, Date, PointKey, Quantile) VALUES (:WaterFlow,:Date, :PointKey, :Quantile)"
        )
        insertFlows.bindValue(":PointKey", self.pointID)
        insertFlows.bindValue(":Quantile", quantileID)
        self.con.transaction()
        for j in range(nb_cols):
            fetchDate.bindValue(":Date", datetimeToDatabaseDate(times[j]))
            if (not fetchDate.exec()) : print(fetchDate.lastError())
            fetchDate.next()
            insertFlows.bindValue(":WaterFlow", float(waterFlows[j]))
            insertFlows.bindValue(":Date", fetchDate.value(0))
            if (not insertFlows.exec()) : print(insertFlows.lastError())
        self.con.commit()

        # RMSE
        sensorsID = self.col.get_id_sensors()
        depthsensors = [
            depths[i - 1] for i in sensorsID
        ]  # Python indexing starts a 0 but cells are indexed starting at 1
        computedRMSE = self.col.get_RMSE()
        insertRMSE = QSqlQuery(self.con)
        insertRMSE.prepare(
            """INSERT INTO RMSE (Depth1, Depth2, Depth3, RMSE1, RMSE2, RMSE3, RMSETotal, PointKey, Quantile)
                 VALUES (:Depth1, :Depth2, :Depth3, :RMSE1, :RMSE2, :RMSE3, :RMSETotal, :PointKey, :Quantile)"""
        )
        insertRMSE.bindValue(":PointKey", self.pointID)
        insertRMSE.bindValue(":Quantile", quantileID)

        self.con.transaction()
        for i in range(1, 4):
            fetchDepth.bindValue(":Depth", float(depthsensors[i - 1]))
            if (not fetchDepth.exec()) : print(fetchDepth.lastError())
            fetchDepth.next()
            insertRMSE.bindValue(f":Depth{i}", fetchDepth.value(0))
            insertRMSE.bindValue(f":RMSE{i}", float(computedRMSE[i - 1]))
        insertRMSE.bindValue(":RMSETotal", float(computedRMSE[3]))
        if (not insertRMSE.exec()) : print(insertRMSE.lastError())
        self.con.commit()

    def compute_MCMC(
        self,
        paramsMCMC
    ):
        """
        Launch the MCMC computation with given parameters.
        """
        if self.thread.isRunning():
            print("Please wait while for the previous computation to end")
            return

        self.paramsMCMC = paramsMCMC
        self.thread.terminate()
        self.thread = QtCore.QThread()

        quantiles = paramsMCMC[3]
        quantiles = quantiles.split(",")
        quantiles = tuple(quantiles)
        quantiles = [float(quantile) for quantile in quantiles]

        self.set_column()  # Updates self.col
        # Warning: order must be the same than dialogCompute getInputMCMC(otherwise use a dictionary)
        self.mcmc_runner = ColumnMCMCRunner(
            self.col,
            paramsMCMC[0], #nb_iter,
            paramsMCMC[1], #all_priors,
            paramsMCMC[2], #nb_cells,
            quantiles    , #quantiles,
            paramsMCMC[4], #nb_chains,
            paramsMCMC[5], #delta,
            paramsMCMC[6], #ncr,
            paramsMCMC[7], #c,
            paramsMCMC[8], #cstar,
            paramsMCMC[9], #remanence,
            paramsMCMC[10], #n_sous_ech_iter,
            paramsMCMC[11], #n_sous_ech_time,
            paramsMCMC[12], #n_sous_ech_space,
            paramsMCMC[13], #threshold
        )
        self.mcmc_runner.finished.connect(self.end_MCMC)
        self.mcmc_runner.moveToThread(self.thread)
        self.thread.started.connect(self.mcmc_runner.run)
        self.thread.start()

    def end_MCMC(self):
        """
        This is called when the MCMC is over. Save the relevant information in the database.
        """
        # Firstly: direct model outputs
        params = self.mcmc_runner.get_last_best_params()
        self.save_layers_and_params(params, self.get_nb_cells())
        self.save_direct_model_results()

        # Secondly: MCMC parameters distributions
        self.save_params_MCMC(self.paramsMCMC)
        self.save_MCMC_results()

        self.thread.quit()

        print("MCMC finished.")

        self.MCMCFinished.emit()

    def save_MCMC_results(self):
        """
        Query the database and save the MCMC results (distributions and quantiles)
        Reuse Depths ID, Dates ID and Layers ID stored for direct model results.
        """
        # TODO : BestParameters table no more used. To be restored ?


        # Quantiles for the MCMC
        
        # WARNING: Quantile 0 (best parameters) is already stored by direct model
        #          Only store other quantiles
        quantiles = self.col.get_quantiles()

        depths = self.col.get_depths_mcmc() # Or get_depths_solve should be the same
        times = self.col.get_times_mcmc()

        sensorsID = self.col.get_id_sensors()
        depthsensors = [
            depths[i - 1] for i in sensorsID
        ]  # Python indexing starts at 0 but cells are indexed starting at 1

        # Quantile
        insertquantiles = QSqlQuery(self.con)
        insertquantiles.prepare(
            f"INSERT INTO Quantile (Quantile, PointKey) VALUES (:Quantile,{self.pointID})"
        )
        # Layers, Dates and Depths (already existing)
        fetchLayer = QSqlQuery(self.con)
        fetchLayer.prepare(
            f"SELECT Layer.ID FROM Layer WHERE Layer.PointKey = :PointKey AND Layer.Depth = :Depth "
        )
        fetchLayer.bindValue(":PointKey", self.pointID)
        fetchDate = QSqlQuery(self.con)
        fetchDate.prepare(
            f"SELECT Date.ID FROM Date WHERE Date.PointKey = :PointKey AND Date.Date = :Date "
        )
        fetchDate.bindValue(":PointKey", self.pointID)
        fetchDepth = QSqlQuery(self.con)
        fetchDepth.prepare(
            f"SELECT Depth.ID FROM Depth WHERE Depth.PointKey = :PointKey AND Depth.Depth = :Depth"
        )
        fetchDepth.bindValue(":PointKey", self.pointID)
        # Temperature and heat flows
        inserttemperatures = QSqlQuery(self.con)
        inserttemperatures.prepare(
            """INSERT INTO TemperatureAndHeatFlows (Date, Depth, Temperature, AdvectiveFlow, ConductiveFlow, TotalFlow, PointKey, Quantile)
            VALUES (:Date, :Depth, :Temperature, :AdvectiveFlow, :ConductiveFlow, :TotalFlow, :PointKey, :Quantile)"""
        )
        inserttemperatures.bindValue(":PointKey", self.pointID)
        # Water Flows
        insertFlows = QSqlQuery(self.con)
        insertFlows.prepare(
            "INSERT INTO WaterFlow (WaterFlow, Date, PointKey, Quantile) VALUES (:WaterFlow,:Date, :PointKey, :Quantile)"
        )
        insertFlows.bindValue(":PointKey", self.pointID)
        # RMSE
        insertRMSE = QSqlQuery(self.con)
        insertRMSE.prepare(
            """INSERT INTO RMSE (Depth1, Depth2, Depth3, RMSE1, RMSE2, RMSE3, RMSETotal, PointKey, Quantile)
                 VALUES (:Depth1, :Depth2, :Depth3, :RMSE1, :RMSE2, :RMSE3, :RMSETotal, :PointKey, :Quantile)"""
        )
        insertRMSE.bindValue(":PointKey", self.pointID)

        for quantile in quantiles:
            insertquantiles.bindValue(":Quantile", quantile)
            if (not insertquantiles.exec()) : print(insertquantiles.lastError())
            quantileID = insertquantiles.lastInsertId()

            inserttemperatures.bindValue(":Quantile", quantileID)
            # We assume solvedtemperatures,advecFlows and conduFlows have the same shapes, and that the dates and depths are also identical, ie the first column of all three arrays corresponds to the same fixed date.
            solvedtemperatures = self.col.get_temperatures_quantile(quantile)
            nb_rows, nb_cols = shape(solvedtemperatures)  #!!!!!! A VOIR !!!!!!
            self.con.transaction()
            for j in range(nb_cols):
                fetchDate.bindValue(":Date", datetimeToDatabaseDate(times[j]))
                if (not fetchDate.exec()) : print(fetchDate.lastError())
                fetchDate.next()
                inserttemperatures.bindValue(":Date", fetchDate.value(0))
                # Note: we leave out the AdvectiveFlow, ConductiveFlow and TotalFlow. Why?
                # Well theses values are not computed per quantile: instead, there are computed for the direct model.
                # There is no need to store these values as they don't represent anything. Hence, we leave them out and they will be empty.
                # This isn't a problem as they are never used: once again, only the values for the direct model are relevant.
                for i in range(nb_rows):
                    fetchDepth.bindValue(":Depth", float(depths[i]))
                    if (not fetchDepth.exec()) : print(fetchDepth.lastError())
                    fetchDepth.next()
                    inserttemperatures.bindValue(":Depth", fetchDepth.value(0))
                    inserttemperatures.bindValue(
                        ":Temperature", float(solvedtemperatures[i, j]) - 273.15
                    )  # Need to convert into float, as SQL doesn't undestand np.float32 !
                    if (not inserttemperatures.exec()) : print(inserttemperatures.lastError())
            self.con.commit()

            # Water flows
            waterFlows = self.col.get_flows_quantile(quantile)[
                0, :
            ]  # Water flows at the top of the column.
            insertFlows.bindValue(":Quantile", quantileID)
            self.con.transaction()
            for j in range(nb_cols):
                fetchDate.bindValue(":Date", datetimeToDatabaseDate(times[j]))
                if (not fetchDate.exec()) : print(fetchDate.lastError())
                fetchDate.next()
                insertFlows.bindValue(":WaterFlow", float(waterFlows[j]))
                insertFlows.bindValue(":Date", fetchDate.value(0))
                if (not insertFlows.exec()) : print(insertFlows.lastError())
            self.con.commit()

            # RMSE
            computedRMSE = self.col.get_RMSE_quantile(quantile)
            insertRMSE.bindValue(":Quantile", quantileID)

            self.con.transaction()
            for i in range(1, 4):
                fetchDepth.bindValue(":Depth", float(depthsensors[i - 1]))
                if (not fetchDepth.exec()) : print(fetchDepth.lastError())
                fetchDepth.next()
                insertRMSE.bindValue(f":Depth{i}", fetchDepth.value(0))
                insertRMSE.bindValue(f":RMSE{i}", float(computedRMSE[i - 1]))
            insertRMSE.bindValue(":RMSETotal", float(computedRMSE[3]))
            if (not insertRMSE.exec()) : print(insertRMSE.lastError())
            self.con.commit()

        # Parameter distributions

        layer_depths = self.coordinator.layers_depths()
        all_params = self.col.get_all_params()
        current_params_index = 0

        insertdistribution = QSqlQuery(self.con)
        insertdistribution.prepare(
            """INSERT INTO ParametersDistribution (Permeability, Porosity, ThermConduct, HeatCapacity, Layer, PointKey)
                VALUES (:Permeability, :Porosity, :ThermConduct, :HeatCapacity, :Layer, :PointKey)"""
        )
        insertdistribution.bindValue(":PointKey", self.pointID)

        self.con.transaction()
        for depth in layer_depths:
            fetchLayer.bindValue(":Depth", depth)
            if (not fetchLayer.exec()) : print(fetchLayer.lastError())
            fetchLayer.next()

            all_params_layer = all_params[current_params_index]
            for params in all_params_layer:
                # Convert everything to float as the parameters are of type np.float
                insertdistribution.bindValue(":Permeability", float(params[0]))
                insertdistribution.bindValue(":Porosity", float(params[1]))
                insertdistribution.bindValue(":ThermConduct", float(params[2]))
                insertdistribution.bindValue(":HeatCapacity", float(params[3]))
                insertdistribution.bindValue(":Layer", fetchLayer.value(0))
                if (not insertdistribution.exec()) : print(insertdistribution.lastError())
            current_params_index += 1
        self.con.commit()

    def build_column_infos(self):
        """
        Build and return a query giving all the necessary information for the column.
        """
        query = QSqlQuery(self.con)
        query.prepare(
            f"""SELECT SamplingPoint.RiverBed, Shaft.Depth1, Shaft.Depth2, Shaft.Depth3, Shaft.Depth4, SamplingPoint.Offset, PressureSensor.Error, Thermometer.Error FROM SamplingPoint
            JOIN PressureSensor
            ON SamplingPoint.PressureSensor = PressureSensor.ID
            JOIN Shaft
            ON SamplingPoint.Shaft = Shaft.ID
            JOIN Thermometer
            ON Shaft.ThermoModel = Thermometer.ID
            JOIN Point
            ON SamplingPoint.ID = Point.SamplingPoint
            WHERE Point.ID = {self.pointID}
        """
        )
        return query
