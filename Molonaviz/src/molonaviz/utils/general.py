"""
Some useful functions which can be used throughout the code.
"""
from PyQt5 import QtWidgets
import os
from datetime import datetime
import pandas as pd
import numpy as np
import matplotlib.dates as mdates
from PyQt5.QtSql import QSqlDatabase, QSqlQuery
from shutil import copy2
import glob



def displayCriticalMessage(mainMessage: str, infoMessage: str = ''):
    """
    Display a critical message (with a no entry sign). This should be used to tell the user that an important error occured and he has to actively do something.
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Critical)
    msg.setText(mainMessage)
    msg.setInformativeText(infoMessage)
    msg.exec()

def displayWarningMessage(mainMessage: str, infoMessage: str = ''):
    """
    Display a warning message. This should be used to tell the user that an error occured but it is not detrimental to the app's features.
    """
    msg = QtWidgets.QMessageBox()
    msg.setIcon(QtWidgets.QMessageBox.Warning)
    msg.setText(mainMessage)
    msg.setInformativeText(infoMessage)
    msg.exec()

def createDatabaseDirectory(directory, databaseName, sampleTextFile, sqlInitFile):
    """
    Given a directory and the name of the database, create a folder with the name databaseName and the correct structure. Also create the empty database with correct table structure based on the sqlInitFile.
    Return True if the directory was successfully created, False otherwise
    """
    databaseFolder = os.path.join(directory, databaseName)
    if os.path.isdir(databaseFolder):
        return False
    os.mkdir(databaseFolder)
    os.mkdir(os.path.join(databaseFolder, "Notices"))
    os.mkdir(os.path.join(databaseFolder, "Schemes"))
    os.mkdir(os.path.join(databaseFolder, "Scripts"))
    copy2(sampleTextFile, os.path.join(databaseFolder, "Scripts"))
    f = open(os.path.join(databaseFolder, "Molonari.sqlite"),"x")
    f.close()

    con = QSqlDatabase.addDatabase("QSQLITE")
    con.setDatabaseName(os.path.join(databaseFolder, "Molonari.sqlite"))
    con.open()
    f = open(sqlInitFile, 'r')
    sqlQueries = f.read()
    f.close()
    sqlQueries = sqlQueries.split(";")
    query = QSqlQuery(con)
    for q in sqlQueries:
        query.exec(q)
    con.close()
    return True

def checkDbFolderIntegrity(dbPath):
    """
    Given the path to a database folder, check if it has all the subfolders and the database in it.
    """
    return os.path.isfile(os.path.join(dbPath, "Molonari.sqlite")) and os.path.isdir(os.path.join(dbPath, "Notices")) and os.path.isdir(os.path.join(dbPath, "Schemes")) and os.path.isdir(os.path.join(dbPath, "Scripts"))

class InvalidFile(Exception):
    pass

def extractDetectorsDF(labDirPath):
    """
    Given the path to a laboratory directory, read all files and select the valid ones. The valid files are converted into panda dataframes that will be passed to the backend, and the invalid files should trigger error message.
    If no .csv file is found, or if the folder is not divided into the correct subfolders (currently temperature_sensors, pressure_sensors and shafts), no error message is raised, as we assume the user wishes to create an empty laboratory (or a lab missing one of these detectors).
    """
    #This function probably shouldn't exist at all. The user should enter the detectors information directly in the app, and not in a csv which is imported into the app.

    tempdir = os.path.join(labDirPath, "temperature_sensors", "*.csv")
    files = glob.glob(tempdir)
    files.sort()
    validThermometers = []
    for file in files:
        try:
            df = pd.read_csv(file, header=None)
            if df[1].isnull().sum() ==0:
                validThermometers.append(df)
            else:
                raise InvalidFile
        except Exception as e:
            print("Couldn't load thermometer ", file)

    psdir = os.path.join(labDirPath, "pressure_sensors", "*.csv")
    files = glob.glob(psdir)
    files.sort()
    validPSensors = []
    for file in files:
        try:
            df = pd.read_csv(file, header=None)
            if df[1].isnull().sum() ==0:
                validPSensors.append(df)
            else:
                raise InvalidFile
        except Exception as e:
            print("Couldn't load pressure sensor ", file)

    shaftdir = os.path.join(labDirPath, "shafts", "*.csv")
    files = glob.glob(shaftdir)
    files.sort()
    validShafts = []
    for file in files:
        try:
            df = pd.read_csv(file, header=None)
            if df[1].isnull().sum() ==0:
                validShafts.append(df)
            else:
                raise InvalidFile
        except Exception as e:
            print("Couldn't load shaft ", file)
    rejected = checkDetectorsIntegrity(validThermometers, validPSensors, validShafts)
    if len(rejected) == 0:
        return validThermometers, validPSensors, validShafts
    raise InvalidFile

def checkDetectorsIntegrity(thermos : list[pd.DataFrame], psensors : list[pd.DataFrame], shafts : list[pd.DataFrame]):
    """
    Given lists of dataframes describing sensors, make sure they have the correct number of fields.
    """
    rejected = []
    for thermo in thermos:
        if len(thermo) != 4:
            rejected.append(thermo)
    for psensor in psensors:
        if len(psensor) !=8:
            rejected.append(psensor)
    for shaft in shafts:
        if len(shaft) !=4:
            rejected.append(shaft)
    return rejected

def convertDates(df : pd.DataFrame, timesIndex = 0):
    """
    Convert dates from a list of strings by testing several different input formats
    Try all date formats already encountered in data points
    If none of them is OK, try the generic way (None)
    If the generic way doesn't work, this method fails
    (in that case, you should add the new format to the list)

    This function works directly on the giving Pandas dataframe (in place)
    This function assumes that the column timesIndex of the given Pandas dataframe
    contains the dates as characters string type

    For datetime conversion performance, see:
    See https://stackoverflow.com/questions/40881876/python-pandas-convert-datetime-to-timestamp-effectively-through-dt-accessor
    """
    formats = ("%m/%d/%y %H:%M:%S", "%m/%d/%y %I:%M:%S %p",
               "%d/%m/%y %H:%M",    "%d/%m/%y %I:%M %p",
               "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %I:%M:%S %p",
               "%d/%m/%Y %H:%M",    "%d/%m/%Y %I:%M %p",
               "%y/%m/%d %H:%M:%S", "%y/%m/%d %I:%M:%S %p",
               "%y/%m/%d %H:%M",    "%y/%m/%d %I:%M %p",
               "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %I:%M:%S %p",
               "%Y/%m/%d %H:%M",    "%Y/%m/%d %I:%M %p",
               "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %I:%M:%S %p",
               "%Y:%m:%d %H:%M:%S", "%Y:%m:%d %I:%M:%S %p",
               "%m:%d:%Y %H:%M:%S", "%m:%d:%Y %I:%M:%S %p",None)

    times = df[df.columns[timesIndex]]
    for f in formats:
        try:
            # Convert strings to datetime objects
            new_times = pd.to_datetime(times, format=f)
            # Convert datetime series to numpy array of integers (timestamps)
            new_ts = new_times.values.astype(np.int64)
            # If times are not ordered, this is not the appropriate format
            test = np.sort(new_ts) - new_ts
            if np.sum(abs(test)) != 0 :
                #print("Order is not the same")
                raise ValueError()
            # Else, the conversion is a success
            #print("Found format ", f)
            df[df.columns[0]] = new_times
            return

        except ValueError:
            #print("Format ", f, " not valid")
            continue

    # None of the known format are valid
    raise ValueError("Cannot convert dates: No known formats match your data!")

def databaseDateFormat():
    """
    Return the database date format as a string: currently, it is YYYY/MM/DD HH:MM:SS.
    """
    return "%Y/%m/%d %H:%M:%S"

def databaseDateToDatetime(date : str):
    """
    Given a date in the database format (YYYY/MM/DD HH:MM:SS), return the corresponding datetime object.
    If a list is given instead, return the list of datetime objects.
    """
    if isinstance(date, list) or isinstance(date, np.ndarray):
        return [databaseDateToDatetime(d) for d in date]
    return datetime.strptime(date, databaseDateFormat())

def datetimeToDatabaseDate(date : datetime):
    """
    Given a datetime oject, return a date (string) in the database format (YYYY/MM/DD HH:MM:SS).
    """
    return date.strftime(databaseDateFormat())

def dateToMdates(dates : list[str]):
    """
    Given a list of datetime objects, return the corresponding list of matplotlib dates.
    """
    return [mdates.date2num(date) for date in dates]

def build_picture(oneDArray : np.array, nb_cells=100):
    """
    Given a 1D numpy array, convert it into a rectangular picture. nb_cells corresponds to the number of elements per column. Used to convert data from the database into a 2D map with respect to the number of cells.
    """
    nb_elems = oneDArray.shape[0] #Total number of elements
    y = nb_cells #One hundred cells
    x = nb_elems//y
    return oneDArray.reshape(x,y).T#Now this is the color map with y-axis being the depth (number of cells) and x-axis being the time