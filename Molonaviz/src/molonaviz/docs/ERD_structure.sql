PRAGMA foreign_keys = off;
BEGIN TRANSACTION;

-- Table: BestParameters
CREATE TABLE BestParameters (ID INTEGER PRIMARY KEY AUTOINCREMENT, Permeability REAL, Porosity REAL, ThermConduct REAL, Capacity REAL, Layer INTEGER REFERENCES Layer (ID), PointKey INTEGER REFERENCES Point (ID));

-- Table: Parameters
CREATE TABLE Parameters (ID INTEGER PRIMARY KEY AUTOINCREMENT, Permeability REAL, Porosity REAL, ThermConduct REAL, Capacity REAL, Layer INTEGER REFERENCES Layer (ID), PointKey INTEGER REFERENCES Point (ID));

-- Table: InputMCMC
CREATE TABLE InputMCMC (ID INTEGER PRIMARY KEY AUTOINCREMENT, Niter INT, Delta INT, Nchains INT, NCR INT, C REAL, Cstar REAL, Kmin REAL, Kmax REAL, Ksigma REAL, PorosityMin REAL, PorosityMax REAL, PorositySigma REAL, TcondMin REAL, TcondMax REAL, TcondSigma REAL, TcapMin REAL, TcapMax REAL, TcapSigma REAL, Remanence REAL, tresh REAL, nb_sous_ech_iter INT, nb_sous_ech_space iNT, nb_sous_ech_time INT, Quantiles TEXT, PointKey INTEGER REFERENCES Point (ID));

-- Table: CleanedMeasures
CREATE TABLE CleanedMeasures (ID INTEGER PRIMARY KEY AUTOINCREMENT, Date INTEGER REFERENCES Date (ID), TempBed REAL NOT NULL, Temp1 REAL NOT NULL, Temp2 REAL NOT NULL, Temp3 REAL NOT NULL, Temp4 REAL NOT NULL, Pressure REAL NOT NULL, PointKey INTEGER REFERENCES Point (ID));

-- Table: Date
CREATE TABLE Date (ID INTEGER PRIMARY KEY AUTOINCREMENT, Date DATETIME, PointKey REFERENCES Point (ID));

-- Table: Depth
CREATE TABLE Depth (ID INTEGER PRIMARY KEY AUTOINCREMENT, Depth REAL, PointKey REFERENCES Point (ID));

-- Table: Labo
CREATE TABLE Labo (ID INTEGER PRIMARY KEY AUTOINCREMENT, Name VARCHAR NOT NULL UNIQUE);

-- Table: Layer
CREATE TABLE Layer (ID INTEGER PRIMARY KEY AUTOINCREMENT, Name VARCHAR, Depth REAL, PointKey REFERENCES Point (ID));

-- Table: ParametersDistribution
CREATE TABLE ParametersDistribution (ID INTEGER PRIMARY KEY AUTOINCREMENT, Permeability REAL, Porosity REAL, ThermConduct REAL, HeatCapacity REAL, Layer INTEGER REFERENCES Layer (ID), PointKey INTEGER REFERENCES Point (ID));

-- Table: Point
CREATE TABLE Point (ID INTEGER PRIMARY KEY AUTOINCREMENT, SamplingPoint INTEGER REFERENCES SamplingPoint (ID), IncertK REAL, IncertLambda REAL, DiscretStep INTEGER, IncertRho REAL, TempUncertainty REAL, IncertPressure REAL);

-- Table: PressureSensor
CREATE TABLE PressureSensor (ID INTEGER PRIMARY KEY AUTOINCREMENT, Name VARCHAR, Datalogger VARCHAR, DataloggerID INTEGER REFERENCES Datalogger (ID), Calibration DATETIME, Intercept REAL, DuDH REAL, DuDT REAL, Error REAL, ThermoModel INTEGER REFERENCES Thermometer (ID), Labo INTEGER REFERENCES Labo (ID));

-- Table: Quantile
CREATE TABLE Quantile (ID INTEGER PRIMARY KEY AUTOINCREMENT, Quantile REAL NOT NULL, PointKey REFERENCES Point (ID));

-- Table: RawMeasuresPress
CREATE TABLE RawMeasuresPress (ID INTEGER PRIMARY KEY AUTOINCREMENT, Date DATETIME NOT NULL, TempBed REAL, Voltage REAL, SamplingPoint INTEGER REFERENCES SamplingPoint (ID));

-- Table: RawMeasuresTemp
CREATE TABLE RawMeasuresTemp (ID INTEGER PRIMARY KEY AUTOINCREMENT, Date DATETIME, Temp1 REAL, Temp2 REAL, Temp3 REAL, Temp4 REAL, SamplingPoint INTEGER REFERENCES SamplingPoint (ID));

-- Table: RawMeasuresVolt
CREATE TABLE RawMeasuresVolt (ID INTEGER PRIMARY KEY AUTOINCREMENT, Date DATETIME, Volt1 REAL, Volt2 REAL, Volt3 REAL, Volt4 REAL, SamplingPoint INTEGER REFERENCES SamplingPoint (ID));

-- Table: RMSE
CREATE TABLE RMSE (ID INTEGER PRIMARY KEY AUTOINCREMENT, Depth1 INTEGER REFERENCES Depth (ID), Depth2 INTEGER REFERENCES Depth (ID), Depth3 INTEGER REFERENCES Depth (ID), RMSE1 REAL, RMSE2 REAL, RMSE3 REAL, RMSETotal REAL, PointKey INTEGER REFERENCES Point (ID), Quantile INTEGER REFERENCES Quantile (ID));

-- Table: SamplingPoint
CREATE TABLE SamplingPoint (ID INTEGER PRIMARY KEY AUTOINCREMENT, Name VARCHAR, Notice VARCHAR, Setup DATETIME, LastTransfer DATETIME, "Offset" REAL, RiverBed REAL, Shaft INTEGER REFERENCES Shaft (ID), PressureSensor INTEGER REFERENCES PressureSensor (ID), Study INTEGER REFERENCES Study (ID), Scheme VARCHAR, CleanupScript VARCHAR);

-- Table: Shaft
CREATE TABLE Shaft (ID INTEGER PRIMARY KEY AUTOINCREMENT, Name VARCHAR NOT NULL, Datalogger VARCHAR NOT NULL, DataloggerID INTEGER REFERENCES Datalogger (ID), Depth1 REAL NOT NULL, Depth2 REAL NOT NULL, Depth3 REAL NOT NULL, Depth4 REAL NOT NULL, ThermoModel INTEGER REFERENCES Thermometer (ID), Labo INTEGER REFERENCES Labo (ID));

-- Table: Study
CREATE TABLE Study (ID INTEGER PRIMARY KEY AUTOINCREMENT, Name VARCHAR NOT NULL UNIQUE, Labo INTEGER REFERENCES Labo (ID));

-- Table: TemperatureAndHeatFlows
CREATE TABLE TemperatureAndHeatFlows (
            ID              INTEGER  PRIMARY KEY AUTOINCREMENT,
            Date            INTEGER REFERENCES Date (ID),
            Depth           INTEGER REFERENCES Depth (ID),
            Temperature     REAL,
            AdvectiveFlow   REAL,
            ConductiveFlow  REAL,
            TotalFlow       REAL,
            PointKey        INTEGER REFERENCES Point (ID),
            Quantile        INTEGER REFERENCES Quantile (ID)
        );

-- Table: Thermometer
CREATE TABLE Thermometer (ID INTEGER PRIMARY KEY AUTOINCREMENT, Name VARCHAR NOT NULL, ManuName VARCHAR NOT NULL, ManuRef VARCHAR NOT NULL, Error REAL NOT NULL, Labo INTEGER REFERENCES Labo (ID));

-- Table: WaterFlow
CREATE TABLE WaterFlow (
            ID            INTEGER  PRIMARY KEY AUTOINCREMENT,
            WaterFlow           REAL,
            Date                INTEGER REFERENCES Date (ID),
            PointKey            INTEGER REFERENCES Point (ID),
            Quantile            INTEGER REFERENCES Quantile (ID)
        );

-- Table: Gateway
CREATE TABLE Gateway (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR NOT NULL UNIQUE,
    gatewayEUI VARCHAR NOT NULL UNIQUE,    -- Identifiant LoRaWAN unique de la gateway
    TLS_Cert BLOB,               -- Certificat TLS
    TLS_Key BLOB,                -- Clé privée TLS
    CA_Cert BLOB,                -- Certificat d'autorité
    Labo INTEGER REFERENCES Labo (ID)
);

-- Table: Relay
CREATE TABLE Relay (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR NOT NULL,
    RelayEUI VARCHAR NOT NULL UNIQUE,  -- Identifiant LoRaWAN unique du relay
    Gateway INTEGER NOT NULL REFERENCES Gateway (ID),  -- Lien vers la gateway parente
    Labo INTEGER REFERENCES Labo (ID),
    UNIQUE(Gateway, Name)                           -- Un nom de relay unique par gateway
    );

-- Table: Datalogger
CREATE TABLE Datalogger (
    ID INTEGER PRIMARY KEY AUTOINCREMENT,
    Name VARCHAR NOT NULL,
    DevEUI VARCHAR NOT NULL UNIQUE,     -- Ceci est l'identifiant unique (le 'datalogger EUI')
    Relay INTEGER NOT NULL REFERENCES Relay (ID),    
    Labo INTEGER REFERENCES Labo (ID),
    UNIQUE(Relay, Name)
);
COMMIT TRANSACTION;
PRAGMA foreign_keys = on;

