from PyQt5.QtSql import QSqlQueryModel, QSqlQuery, QSqlDatabase #QSqlDatabase in used only for type hints
import pandas as pd

from ..interactions.InnerMessages import ComputationsState
from .GraphsModels import PressureDataModel, TemperatureDataModel, SolvedTemperatureModel, HeatFluxesModel, WaterFluxModel, ParamsDistributionModel
from ..utils.general import databaseDateFormat, databaseDateToDatetime

class SPointCoordinator:
    """
    A concrete class to handle communication between the database and the views in the window displaying a sampling point's results.
    This class can:
        -return informations about the current sampling point
        -manage, fill and clear all models in the subwindow
        -deal with end user's actions in the subwindow. Currently, this means SPointCoordinator can insert cleaned measures in the database.
    This class does not:
        -interact with the pyheatmy module. For this purpose, see Compute.
    """
    def __init__(self, con : QSqlDatabase, studyName : str, samplingPointName : str):
        self.con = con

        spointID_query = self.build_sampling_point_id(studyName, samplingPointName)
        spointID_query.exec()
        spointID_query.next()
        self.samplingPointID = spointID_query.value(0)

        self.pointID = self.find_or_create_point_ID()

        #Create all models (empty for now)
        self.pressuremodel = PressureDataModel([])
        self.tempmodel = TemperatureDataModel([])
        self.tempmap_model = SolvedTemperatureModel([])
        self.heatfluxes_model = HeatFluxesModel([])
        self.waterflux_model = WaterFluxModel([])
        self.paramsdistr_model = ParamsDistributionModel([])

    def find_or_create_point_ID(self):
        """
        Return the Point ID corresponding to this sampling point OR if this is the first time this sampling point is opened, create the relevant entry in the Point table.
        """
        select_pointID = self.build_select_point_ID()
        select_pointID.exec()
        select_pointID.next()
        if select_pointID.value(0) is None:
            insertPoint = self.build_insert_point()
            insertPoint.bindValue(":SamplingPoint", self.samplingPointID)
            insertPoint.exec()
            return insertPoint.lastInsertId()
        return select_pointID.value(0)

    def get_pressure_model(self):
        return self.pressuremodel

    def get_temp_model(self):
        return self.tempmodel

    def get_temp_map_model(self):
        return self.tempmap_model

    def get_water_fluxes_model(self):
        return self.waterflux_model

    def get_heatfluxes_model(self):
        return self.heatfluxes_model

    def get_params_distr_model(self):
        return self.paramsdistr_model

    def get_spoint_infos(self):
        """
        Return the path to the scheme, the path to notice and a model containing the informations about the sampling point.
        """
        select_paths, select_infos = self.build_infos_queries()
        #Installation image
        select_paths.exec()
        select_paths.next()
        schemePath = select_paths.value(0)
        noticePath = select_paths.value(1)

        select_infos.exec()
        infosModel = QSqlQueryModel()
        infosModel.setQuery(select_infos)

        return schemePath, noticePath, infosModel

    def get_params_model(self, layer : float):
        """
        Given a layer (identified by its depth), return the associated best parameters.
        """
        select_params = self.build_params_query(layer)
        select_params.exec()
        self.paramsModel = QSqlQueryModel()
        self.paramsModel.setQuery(select_params)
        return self.paramsModel

    def get_table_model(self, raw_measures : bool):
        """
        Return a model with all direct information from the database.
        If raw_measures is true, the raw measures from the point are displayed, else cleaned measures are displayed
        """
        if raw_measures:
            select_query = self.build_raw_measures(full_query=True)
        else:
            select_query = self.build_cleaned_measures(full_query=True)
        select_query.exec()
        self.tableModel = QSqlQueryModel()
        self.tableModel.setQuery(select_query)
        return self.tableModel

    def all_raw_measures(self):
        """
        Return the raw measures in an iterable format. The result is a list of lists. The inner lists hold the following information in the following order:
            -date (in datetime format), Temp1, Temp2, Temp3, Temp4, TempBed, Voltage
        """
        select_data = self.build_raw_measures(full_query=True)
        select_data.exec()
        result = []
        while select_data.next():
            result.append([databaseDateToDatetime(select_data.value(0))]+ [select_data.value(i) for i in range(1,7)])
        return result

    def all_cleaned_measures(self):
        """
        Return the cleaned measures in an iterable format. The result is a list of tuple:
        -the first element is a list holding temperature readings (date, Temp1, Temp2, Temp3, Temp4)
        -the second element is a list holding pressure readings (date, pressure, temperature at the river bed)
        """
        select_data = self.build_cleaned_measures(full_query=True)
        select_data.exec()
        result = []
        while select_data.next():
            result.append(([databaseDateToDatetime(select_data.value(0))] + [select_data.value(i) for i in range(1,5)],
                           [databaseDateToDatetime(select_data.value(0)), select_data.value(6),select_data.value(5)]))
        return result

    def layers_depths(self):
        """
        Return a list with all the depths of the layers. It may be empty.
        """
        select_depths_layers = self.build_layers_query()
        select_depths_layers.exec()
        layers = []
        while select_depths_layers.next():
            layers.append(select_depths_layers.value(0))
        return layers

    def all_RMSE(self):
        """
        Return
        -the RMSE for the direct model
        -a dictionnary where the keys are the quantile and values are associated RMSE. This can be empty is the MCMC has not been computed yet.
        -a list corresponding to the RMSE of the three thermometers
        """
        select_globalRMSE = self.build_global_RMSE_query()
        select_globalRMSE.exec()
        globalRmse = {}
        directModelRMSE = None
        while select_globalRMSE.next():
            if select_globalRMSE.value(0) !=0:
                globalRmse[select_globalRMSE.value(0)] = select_globalRMSE.value(1)
            else:
                directModelRMSE = select_globalRMSE.value(1)

        select_thermRMSE = self.build_therm_RMSE()
        select_thermRMSE.exec()
        select_thermRMSE.next()

        return directModelRMSE, globalRmse, [select_thermRMSE.value(i) for i in range(3)]

    def thermo_depth(self, depth_id : int):
        """
        Given a thermometer number (1, 2, 3), return depth of associated thermometer.
        """
        select_thermo_depth = self.build_thermo_depth(depth_id)
        select_thermo_depth.exec()
        select_thermo_depth.next()
        return select_thermo_depth.value(0)

    def max_depth(self):
        """
        Return the altitude of the deepest point in the river. We can assume that this is the lenght of the shaft.
        """
        selectdepth = self.build_max_depth()
        selectdepth.exec()
        selectdepth.next()
        return selectdepth.value(0)

    def calibration_infos(self):
        """
        Return three values corresponding to the intercept, differential pressure (DuDH), and differential temperature (DuDT).
        """
        select_cal_infos = self.build_calibration_info()
        select_cal_infos.exec()
        select_cal_infos.next()
        return select_cal_infos.value(0), select_cal_infos.value(1), select_cal_infos.value(2)

    def refresh_measures_plots(self, raw_measures : bool):
        """
        Refresh the models displaying the measures in graphs.
        If raw_measures is true, then the raw measures will be displayed, else cleaned measures will be shown.
        """
        if raw_measures:
            select_pressure = self.build_raw_measures(field ="Pressure")
            select_temp = self.build_raw_measures(field ="Temp")
        else:
            select_pressure = self.build_cleaned_measures(field ="Pressure")
            select_temp = self.build_cleaned_measures(field ="Temp")

        self.pressuremodel.new_queries([select_pressure])
        self.tempmodel.new_queries([select_temp])

    def refresh_params_distr(self, layer : float):
        """
        Refresh the parameter distribution model for the given layer.
        """
        select_params = self.build_params_distribution(layer)
        self.paramsdistr_model.new_queries([select_params])

    def refresh_all_models(self, raw_measures_plot : bool, layer : float):
        """
        Refresh all models.
        If some models have their own function to be refreshed, then these functions should be called to prevent code duplication
        """
        self.refresh_measures_plots(raw_measures_plot)

        #Plot the heat fluxes
        select_heatfluxes= self.build_result_queries(result_type="2DMap",option="HeatFlows") #This is a list
        select_depths = self.build_depths()
        select_dates = self.build_dates()
        self.heatfluxes_model.new_queries([select_dates,select_depths]+select_heatfluxes)

        #Plot the water fluxes
        select_waterflux= self.build_result_queries(result_type="WaterFlux") #This is already a list
        self.waterflux_model.new_queries(select_waterflux)

        #Plot the temperatures
        select_tempmap = self.build_result_queries(result_type="2DMap",option="Temperature") #This is a list of temperatures for all quantiles
        select_depths = self.build_depths()
        select_dates = self.build_dates()
        self.tempmap_model.new_queries([select_dates,select_depths]+select_tempmap)

        #Histogramms
        self.refresh_params_distr(layer)

    def insert_cleaned_measures(self, dfCleaned : pd.DataFrame):
        """
        Insert the cleaned measures into the database.
        The cleaned measures must be in dataframe with the following structure:
            -row[1] : Date (in datetime/Timestamp format) with name Date
            -row[2] : Temperature 1 with name Temp1
            -row[3] : Temperature 2 with name Temp2
            -row[4] : Temperature 3 with name Temp3
            -row[5] : Temperature 4 with name Temp4
            -row[6] : Bed temperature with name TempBed
            -row[7] : Pressure with name Pressure
        Furthermore, they must be database friendly (ie no NaN, no empty field... Just full columns basically).
        """
        #Convert datetime objects (here Timestamp objects) into a string with correct date format.
        dfCleaned["Date"] = dfCleaned["Date"].dt.strftime(databaseDateFormat())

        query_dates = self.build_insert_date()
        query_dates.bindValue(":PointKey", self.pointID)

        query_measures = self.build_insert_cleaned_measures()
        query_measures.bindValue(":PointKey", self.pointID)

        self.con.transaction()
        for row in dfCleaned.itertuples():
            query_dates.bindValue(":Date", row[1])
            query_dates.exec()
            query_measures.bindValue(":DateID", query_dates.lastInsertId())
            query_measures.bindValue(":Temp1", row[2])
            query_measures.bindValue(":Temp2", row[3])
            query_measures.bindValue(":Temp3", row[4])
            query_measures.bindValue(":Temp4", row[5])
            query_measures.bindValue(":TempBed", row[6])
            query_measures.bindValue(":Pressure", row[7])
            query_measures.exec()
        self.con.commit()

    def delete_processed_data(self):
        """
        Delete all processed data (cleaned measures and computations). This reverts the sampling point to its original state (only raw measures)
        """
        self.delete_computations()

        #Now delete the cleaned measures and then the dates.
        dateID = QSqlQuery(self.con)
        dateID.exec(f"""SELECT Date.ID FROM DATE
                        JOIN Point
                        ON Date.PointKey = Point.ID
                        WHERE Point.ID={self.pointID}""")
        deleteTableQuery = QSqlQuery(self.con)
        deleteTableQuery.exec(f"DELETE FROM CleanedMeasures WHERE CleanedMeasures.PointKey=(SELECT ID FROM Point WHERE Point.ID={self.pointID})")
        deleteDate = QSqlQuery(self.con)

        deleteDate.prepare("DELETE FROM Date WHERE Date.ID = :Date")
        self.con.transaction()
        while dateID.next():
            deleteDate.bindValue(":Date", dateID.value(0))
            deleteDate.exec()
        self.con.commit()
        #Note: the Point has not been removed, but it doesn't matter. The find_or_create_point_ID function is here for this reason.


    def delete_computations(self):
        """
        Delete every computations made for this point. This function builds and execute the DELETE queries. Be careful, calling it will clear the database for this point!
        """
        deleteTableQuery = QSqlQuery(self.con)
        #Careful: should have joins as WaterFlow.PointKey !=Samplingpoint.name
        deleteTableQuery.exec(f'DELETE FROM WaterFlow WHERE WaterFlow.PointKey=(SELECT Point.ID FROM Point WHERE Point.ID ={self.pointID})')
        deleteTableQuery.exec(f'DELETE FROM RMSE WHERE PointKey=(SELECT Point.ID FROM Point WHERE Point.ID ={self.pointID})')
        deleteTableQuery.exec(f'DELETE FROM TemperatureAndHeatFlows WHERE PointKey=(SELECT Point.ID FROM Point WHERE Point.ID  = {self.pointID})')
        deleteTableQuery.exec(f'DELETE FROM ParametersDistribution WHERE ParametersDistribution.PointKey=(SELECT Point.ID FROM Point WHERE Point.ID = {self.pointID})')
        deleteTableQuery.exec(f'DELETE FROM BestParameters WHERE BestParameters.PointKey=(SELECT Point.ID FROM Point WHERE Point.ID = {self.pointID})')
        deleteTableQuery.exec(f'DELETE FROM Quantiles WHERE Quantiles.PointKey=(SELECT Point.ID FROM Point WHERE Point.ID = {self.pointID})')
        deleteTableQuery.exec(f'DELETE FROM Depth WHERE Depth.PointKey=(SELECT Point.ID FROM Point WHERE Point.ID = {self.pointID})')
        deleteTableQuery.exec(f'DELETE FROM Layer WHERE Layer.PointKey=(SELECT Point.ID FROM Point WHERE Point.ID = {self.pointID})')
        deleteTableQuery.exec(f'DELETE FROM Quantile WHERE Quantile.PointKey=(SELECT Point.ID FROM Point WHERE Point.ID = {self.pointID})')
        deleteTableQuery.exec(f"""UPDATE Point
                        SET IncertK = NULL,
                            IncertLambda = NULL,
                            DiscretStep = NULL,
                            IncertRho = NULL,
                            TempUncertainty = NULL,
                            IncertPressure = NULL
                        WHERE ID = {self.pointID}""")

    def computation_type(self):
        """
        Return a symbolic name (via an enumeration) representing the state of the database.
        """
        quant = QSqlQuery(self.con)
        quant.prepare(f"""SELECT COUNT(*) FROM Quantile
                JOIN Point
                ON Quantile.PointKey = Point.ID
                WHERE Point.ID = {self.pointID}""")
        quant.exec()
        quant.next()
        comp = QSqlQuery(self.con)
        comp.prepare(f"""SELECT COUNT(*) FROM CleanedMeasures
                JOIN Point
                ON CleanedMeasures.PointKey = Point.ID
                WHERE Point.ID = {self.pointID}
                """)
        comp.exec()
        comp.next()
        if quant.value(0) ==0:
            if comp.value(0) ==0:
                return ComputationsState.RAW_MEASURES
            else:
                return ComputationsState.CLEANED_MEASURES
        elif quant.value(0) ==1:
            return ComputationsState.DIRECT_MODEL
        else:
            return ComputationsState.MCMC

    def build_sampling_point_id(self, studyName : int | str, spointName : str):
        """
        Build and return a query giving the ID of the sampling point called spointName in the study with the name studyName.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""SELECT SamplingPoint.ID FROM SamplingPoint
                        JOIN Study
                        ON SamplingPoint.Study = Study.ID
                        WHERE Study.Name = '{studyName}' AND SamplingPoint.Name = '{spointName}'""")
        return query

    def build_select_point_ID(self):
        """
        Build and return a query giving the ID of the Point corresponding to the current sampling point
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT Point.ID FROM Point
            JOIN SamplingPoint
            ON Point.SamplingPoint = SamplingPoint.ID
            WHERE SamplingPoint.ID = {self.samplingPointID}
        """)
        return query

    def build_infos_queries(self):
        """
        Build and return two queries for the info tab:
        -one to get the configuration image of the sampling point and the notice. Theses are paths.
        -one to get the rest of the information of the sampling point.
        """
        paths = QSqlQuery(self.con)
        paths.prepare(f"""
            SELECT SamplingPoint.Scheme, SamplingPoint.Notice FROM SamplingPoint
            WHERE SamplingPoint.ID = {self.samplingPointID}
        """)

        infos = QSqlQuery(self.con)
        infos.prepare(f"""
            SELECT SamplingPoint.Name, SamplingPoint.Setup, SamplingPoint.LastTransfer, SamplingPoint.Offset, SamplingPoint.RiverBed FROM SamplingPoint
            WHERE SamplingPoint.ID = {self.samplingPointID}
        """)
        return paths, infos

    def build_layers_query(self):
        """
        Build and return a query giving the depths of all the layers.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT Layer.Depth FROM Layer
            JOIN Point
            ON Layer.PointKey = Point.ID
            WHERE Point.ID = {self.pointID}
            ORDER BY Layer.Depth
        """)
        return query

    def build_params_query(self, depth : float):
        """
        Build and return the parameters for the given depth.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT BestParameters.Permeability, BestParameters.ThermConduct, BestParameters.Porosity, BestParameters.Capacity FROM BestParameters
            JOIN Layer ON BestParameters.Layer = Layer.ID
            JOIN Point
            ON BestParameters.PointKey = Point.ID
            WHERE Point.ID = {self.pointID}
            AND Layer.Depth = {depth}
        """)
        return query

    def build_params_distribution(self, layer : float):
        """
        Given a layer's depth, return the distribution for the 4 types of parameters.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT Permeability, ThermConduct, Porosity, HeatCapacity FROM ParametersDistribution
            JOIN Point
            ON ParametersDistribution.PointKey = Point.ID
            JOIN Layer
            ON ParametersDistribution.Layer = Layer.ID
            WHERE Layer.Depth = {layer}
            AND Point.ID = {self.pointID}
        """)
        return query

    def build_global_RMSE_query(self):
        """
        Build and return all the quantiles as well as the associated global RMSE.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT Quantile.Quantile, RMSE.RMSETotal FROM RMSE
            JOIN Quantile
            ON RMSE.Quantile = Quantile.ID
            JOIN Point
            ON Quantile.PointKey = Point.ID
            WHERE Point.ID = {self.pointID}
            ORDER BY Quantile.Quantile
        """)
        return query

    def build_therm_RMSE(self):
        """
        Build and return the RMSE for the three thermometers.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT RMSE1, RMSE2, RMSE3 FROM RMSE
            JOIN Quantile
            ON RMSE.Quantile = Quantile.ID
            JOIN Point
            ON Quantile.PointKey = Point.ID
            WHERE Point.ID = {self.pointID}
            AND Quantile.Quantile = 0
        """)
        return query

    def build_thermo_depth(self, id : int):
        """
        Given an integer (1,2 or 3), return the associated depth of the thermometer.
        """
        if id in [1,2,3]:
            field = f"Depth{id}"
            query = QSqlQuery(self.con)
            query.prepare(f"""
                SELECT Depth.Depth FROM Depth
                JOIN RMSE
                ON Depth.ID = RMSE.{field}
                JOIN Point
                ON RMSE.PointKey = Point.ID
                WHERE Point.ID = {self.pointID}
            """)
            return query

    def build_raw_measures(self, full_query : bool = False, field : str = ""):
        """
        Build an return a query getting the raw measures:
        -if full_query is True, then extract the Date, Pressure and all Temperatures.
        -if field is not an empty string, then it MUST be either "Temp" or "Pressure". Extract the Date and the corresponding field : either all the temperatures or just the pressure.
        """
        query = QSqlQuery(self.con)
        if full_query:
            query.prepare(f"""
                SELECT RawMeasuresTemp.Date, RawMeasuresTemp.Temp1, RawMeasuresTemp.Temp2, RawMeasuresTemp.Temp3, RawMeasuresTemp.Temp4, RawMeasuresPress.TempBed, RawMeasuresPress.Voltage FROM RawMeasuresTemp, RawMeasuresPress
                JOIN SamplingPoint AS SP_press ON RawMeasuresPress.SamplingPoint = SP_press.ID
                JOIN SamplingPoint AS SP_temp ON RawMeasuresTemp.SamplingPoint = SP_temp.ID
                WHERE RawMeasuresTemp.Date = RawMeasuresPress.Date
                AND SP_press.ID = {self.samplingPointID}
                AND SP_temp.ID = {self.samplingPointID}
                ORDER BY RawMeasuresTemp.Date
            """)
            return query
        elif field =="Temp":
            query.prepare(f"""
                SELECT RawMeasuresTemp.Date, RawMeasuresTemp.Temp1, RawMeasuresTemp.Temp2, RawMeasuresTemp.Temp3, RawMeasuresTemp.Temp4, RawMeasuresPress.TempBed FROM RawMeasuresTemp, RawMeasuresPress
                JOIN SamplingPoint AS SP_press ON RawMeasuresPress.SamplingPoint = SP_press.ID
                 JOIN SamplingPoint AS SP_temp ON RawMeasuresTemp.SamplingPoint = SP_temp.ID
                 WHERE RawMeasuresTemp.Date = RawMeasuresPress.Date
                 AND SP_press.ID = {self.samplingPointID}
                AND SP_temp.ID = {self.samplingPointID}
                ORDER BY RawMeasuresTemp.Date
            """)
            return query
        elif field =="Pressure":
            query.prepare(f"""
                SELECT RawMeasuresPress.Date,RawMeasuresPress.Voltage FROM RawMeasuresPress
                JOIN SamplingPoint
                ON RawMeasuresPress.SamplingPoint = SamplingPoint.ID
                WHERE SamplingPoint.ID = {self.samplingPointID}
                ORDER BY RawMeasuresPress.Date
            """)
            return query

    def build_cleaned_measures(self, full_query : bool = False, field : str = ""):
        """
        Build an return a query getting the cleaned measures. This function behaves the same as build_raw_measures: see its docstrings for additional information.
        """
        query = QSqlQuery(self.con)
        if full_query:
                query.prepare(f"""
                    SELECT Date.Date, CleanedMeasures.Temp1, CleanedMeasures.Temp2, CleanedMeasures.Temp3, CleanedMeasures.Temp4, CleanedMeasures.TempBed, CleanedMeasures.Pressure FROM CleanedMeasures
                    JOIN Date
                    ON CleanedMeasures.Date = Date.ID
                    JOIN Point
                    ON CleanedMeasures.PointKey = Point.ID
                    WHERE Point.ID = {self.pointID}
                    ORDER BY Date.Date
                """)
                return query
        elif field =="Temp":
            query.prepare(f"""
                SELECT Date.Date, CleanedMeasures.Temp1, CleanedMeasures.Temp2, CleanedMeasures.Temp3, CleanedMeasures.Temp4, CleanedMeasures.TempBed FROM CleanedMeasures
                JOIN Date
                ON CleanedMeasures.Date = Date.ID
                JOIN Point
                ON CleanedMeasures.PointKey = Point.ID
                WHERE Point.ID = {self.pointID}
                ORDER BY Date.Date
            """)
            return query
        elif field =="Pressure":
            query.prepare(f"""
                SELECT Date.Date, CleanedMeasures.Pressure FROM CleanedMeasures
                JOIN Date
                ON CleanedMeasures.Date = Date.ID
                JOIN Point
                ON CleanedMeasures.PointKey = Point.ID
                WHERE Point.ID = {self.pointID}
                ORDER BY Date.Date
            """)
            return query

    def build_result_queries(self,result_type ="",option=""):
        """
        Return a list of queries according to the user's wish. The list will either be of length 1 (the model was not computed before), or more than one: in this case, there are as many queries as there are quantiles: the first query corresponds to the default model (quantile 0)
        """
        compute_type = self.computation_type()
        if compute_type == ComputationsState.DIRECT_MODEL:
            return [self.define_result_queries(result_type=result_type,option=option, quantile=0)]
        elif compute_type == ComputationsState.MCMC:
            #This could be enhanced by going in the database and seeing which quantiles are available. For now, these available quantiles will be hard-coded
            select_quantiles = self.build_quantiles()
            select_quantiles.exec()
            result = []
            while select_quantiles.next():
                if select_quantiles.value(0) ==0:
                    #Default model should always be the first one
                    result.insert(0,self.define_result_queries(result_type=result_type,option=option, quantile=select_quantiles.value(0)))
                else:
                    result.append(self.define_result_queries(result_type=result_type,option=option, quantile=select_quantiles.value(0)))
            return result
        else: #RAW_MEASURES or CLEANED_MEASURES
            return []

    def define_result_queries(self,result_type ="",option="",quantile = 0):
        """
        Build and return ONE AND ONLY ONE query concerning the results.
        -quantile must be a float, and is either 0 (direct result), 0.05,0.5 or 0.95
        -option can be a string (which 2D map should be displayed or a date for the umbrellas) or a float (depth required by user)
        """
        #Water Flux
        query = QSqlQuery(self.con)
        if result_type =="WaterFlux":
            query.prepare(f"""
                SELECT Date.Date, WaterFlow.WaterFlow, Quantile.Quantile FROM WaterFlow
                JOIN Date
                ON WaterFlow.Date = Date.ID
                JOIN Quantile
                ON WaterFlow.Quantile = Quantile.ID
                JOIN Point
                ON Quantile.PointKey = Point.ID
                WHERE Point.ID = {self.pointID}
                AND Quantile.Quantile = {quantile}
                ORDER BY Date.Date
            """)
            return query
        elif result_type =="2DMap":
            if option=="Temperature":
                query.prepare(f"""
                    SELECT TemperatureAndHeatFlows.Temperature, Quantile.Quantile FROM TemperatureAndHeatFlows
                    JOIN Date
                    ON TemperatureAndHeatFlows.Date = Date.ID
                    JOIN Depth
                    ON TemperatureAndHeatFlows.Depth = Depth.ID
                    JOIN Quantile
                    ON TemperatureAndHeatFlows.Quantile = Quantile.ID
                    JOIN Point
                    ON Quantile.PointKey = Point.ID
                    WHERE Point.ID = {self.pointID}
                    AND Quantile.Quantile = {quantile}
                    ORDER BY Date.Date, Depth.Depth
                """) #Column major: order by date
                return query
            elif option=="HeatFlows":
                query.prepare(f"""
                    SELECT Date.Date, TemperatureAndHeatFlows.AdvectiveFlow,TemperatureAndHeatFlows.ConductiveFlow,TemperatureAndHeatFlows.TotalFlow, TemperatureAndHeatFlows.Depth FROM TemperatureAndHeatFlows
                    JOIN Date
                    ON TemperatureAndHeatFlows.Date = Date.ID
                    JOIN Depth
                    ON TemperatureAndHeatFlows.Depth = Depth.ID
                    JOIN Quantile
                    ON TemperatureAndHeatFlows.Quantile = Quantile.ID
                    JOIN Point
                    ON Quantile.PointKey = Point.ID
                    WHERE Point.ID = {self.pointID}
                    AND Quantile.Quantile = {quantile}
                    ORDER BY Date.Date, Depth.Depth
                """)
                return query

    def build_depths(self):
        """
        Build and return all the depths values.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT Depth.Depth FROM Depth
            JOIN Point
            ON Depth.PointKey = Point.ID
            WHERE Point.ID = {self.pointID}
            ORDER BY Depth.Depth
        """)
        return query

    def build_dates(self):
        """
        Build and return all the dates for this point.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT Date.Date FROM Date
            JOIN Point
            ON Date.PointKey = Point.ID
            WHERE Point.ID = {self.pointID}
            ORDER by Date.Date
        """)
        return query

    def build_quantiles(self):
        """
        Build and return the quantiles values.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT Quantile.Quantile FROM Quantile
            JOIN Point
            ON Quantile.PointKey = Point.ID
            WHERE Point.ID = {self.pointID}
            ORDER BY Quantile.Quantile
        """)
        return query

    def build_max_depth(self):
        """
        Build and return a query giving the total depth for the sampling point with the ID samplingPointID.
        """
        shaft_depth = QSqlQuery(self.con)
        shaft_depth.prepare(f"""
            SELECT Shaft.Depth4
            FROM Shaft
            JOIN SamplingPoint
            ON Shaft.ID = SamplingPoint.Shaft
            WHERE SamplingPoint.ID = {self.samplingPointID}
            """)
        return shaft_depth

    def build_calibration_info(self):
        """
        Build and return a query giving information to calibrate the computations: the intercept, Du/DH and Du/DT for the current point.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            SELECT PressureSensor.Intercept, PressureSensor.DuDH, PressureSensor.DuDT FROM PressureSensor
            JOIN SamplingPoint
            ON PressureSensor.ID = SamplingPoint.PressureSensor
            WHERE SamplingPoint.ID = {self.samplingPointID}
        """)
        return query

    def build_insert_point(self):
        """
        Build and return a query creating a Point. For now, most fields are empty.
        """
        query = QSqlQuery(self.con)
        query.prepare(f""" INSERT INTO Point (SamplingPoint)  VALUES (:SamplingPoint)
        """)
        return query

    def build_insert_date(self):
        """
        Build and return a query to insert dates in the Date table.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            INSERT INTO Date (Date, PointKey)
            VALUES (:Date, :PointKey)
        """)
        return query

    def build_insert_cleaned_measures(self):
        """
        Build and return a query to insert cleaned measures in the database.
        """
        query = QSqlQuery(self.con)
        query.prepare(f"""
            INSERT INTO CleanedMeasures (Date, TempBed, Temp1, Temp2, Temp3, Temp4, Pressure, PointKey)
            VALUES (:DateID, :TempBed, :Temp1, :Temp2, :Temp3, :Temp4, :Pressure, :PointKey)
        """)
        return query