import os
import re
import hashlib
import datetime
import requests
import mariadb
import unittest

class Test(unittest.TestCase):
    def test1(self):
        date = str(datetime.date.today())
        url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/"
        stationName = "ghcnd-stations.txt"

        urlStation = url + stationName

        hitStation = 1

        # Get the stations from the NOAA website data
        requestStations = requests.get(urlStation)
        requestStationsData = requestStations.text
        md5Stations = hashlib.md5(requestStationsData.encode())

        # Database connection 
        MARIAHOST = "localhost"
        MARIAPORT = int('3306')
        MARIAUSER = "root"
        MARIAPASS = "Proyecto_opcional"
        MARIADB = "weather"

        print("Establishing connection with MariaDB")
        try:
            mariaDatabase = mariadb.connect(
                host="localhost",
                port=int('3306'),
                user="root",
                password="Proyecto_opcional",
                database="weather"
            )
            connection = mariaDatabase.cursor()
        except:
            pass

        # Create tables if not exists
        print("Creating table stations")
        try:
            connection.execute("CREATE TABLE IF NOT EXISTS stations(\
                            station_id varchar(16) not null,\
                            latitude float,\
                            longitude float,\
                            elevation float,\
                            state varchar(4) not null,\
                            name varchar(64) not null,\
                            gsn_flag varchar(4) not null,\
                            hcn_flag varchar(4) not null,\
                            wmo_id varchar(8) not null,\
                            country_id int,\
                            state_id int,\
                            primary key(station_id),\
                            foreign key (country_id) references countries (country_id),\
                            foreign key (state_id) references states (state_id)\
            )")
        except:
            pass

        # Check if theres a row with the same md5 
        print("Checking md5")
        try:
            connection.execute("SELECT file_md5 from files WHERE file_md5 = ?", (str(md5Stations.hexdigest()),))
            for i in connection:
                hitStation = 0
        except:
            pass

        # If table dont have the exact md5, adds a new row
        if hitStation:
            print("found change in station file")
            stationsList = requestStationsData.split('\n')
            stationsRows = []
            for i in range(0, len(stationsList) - 1):
                station = stationsList[i]
                id = station[0:11]
                latitude = station[12:20]
                longitude = station[21:30]
                elevation = station[31:37]
                state = station[38:40]
                name = station[41:71]
                gsn_flag = station[72:75]
                hcn_flag = station[76:79]
                wmo_id = station[80:85]
                stationsRows += [[id, latitude, longitude, elevation, state, name, gsn_flag, hcn_flag, wmo_id]]
            print("Total stations: ", len(stationsRows))
            stationCheck = ['AE000041196', ' 25.3330', '  55.5170', '  34.0', '  ', 'SHARJAH INTER. AIRP           ', 'GSN', '   ', '41196']
            print("Station to check: ", stationCheck)
            print("Checking if the station is in the list...")
            self.assertIn(stationCheck, stationsRows)
            print("inserting file in table files")
            try:
                connection.execute("INSERT INTO files (file_name, file_url, file_date, file_state, file_md5) \
                            VALUES (?,?,?,?,?)", (stationName, urlStation, date, 'En espera', str(md5Stations.hexdigest())))
                connection.execute("SELECT country_id, country_acronym FROM countries")
                countries = connection.fetchall()
                connection.execute("SELECT state_id, state_acronym FROM states")
                states = connection.fetchall()
            except:
                pass
            print("inserting stations")
            try:
                for i in stationsRows:
                    connection.execute("INSERT INTO stations(station_id, latitude, longitude, elevation, state, name, gsn_flag, hcn_flag, wmo_id) \
                                        SELECT * FROM (SELECT ? as station_id,? as latitude,? as longitude,? as elevation,? as state,? as name,? as gsn_flag,? as hcn_flag,? as wmo_id) AS tmp\
                                        WHERE NOT EXISTS (SELECT station_id FROM stations WHERE station_id = ?)\
                                        LIMIT 1",(i[0], i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8], i[0]))
            except:
                pass
            # Assign new foreign key values
            print("assigning foreign key values")
            try:
                for country in countries:
                    connection.execute("UPDATE stations SET country_id = ? \
                    WHERE substring(station_id, 1, 2) = ?", (str(country[0]), country[1]))
                for state in states:
                    connection.execute("UPDATE stations SET state_id = ? \
                    WHERE substring(station_id, 1, 2) = ?", (str(state[0]), state[1]))
            except:
                pass
        else:
            print("station file not changed")

        print("Closing connection")
        # Close connection
        try:
            mariaDatabase.commit()
            mariaDatabase.close()
        except:
            pass
        

if __name__ == '__main__':
    unittest.main()              