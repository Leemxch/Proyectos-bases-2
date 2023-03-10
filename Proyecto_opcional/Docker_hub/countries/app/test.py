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
        countryName = "ghcnd-countries.txt"
        stateName = "ghcnd-states.txt"

        urlCountry = url + countryName
        urlState = url + stateName

        hitCountry = 1
        hitStates = 1

        # Get the countries from the NOAA wensite data
        requestCountries = requests.get(urlCountry)
        requestCountriesData = str(requestCountries.content)
        md5Countries = hashlib.md5(requestCountriesData.encode())
        countriesData = requestCountriesData[2:len(requestCountriesData)]
        countries = countriesData.split('\\n')

        countriesRows = []
        for i in countries:
            rowData = i.split(' ', 1)
            if (len(rowData) == 2):
                countriesRows += [rowData]
        print("Total countries: ", len(countriesRows))
        countryCheck = ['ZI','Zimbabwe ']
        print("Country to check: ", countryCheck)
        print("Checking if the last country is in the list...")
        self.assertIn(countryCheck, countriesRows)

        # Get the states from the NOAA website data
        requestStates = requests.get(urlState)
        requestStatesData = str(requestStates.content)
        md5States = hashlib.md5(requestStatesData.encode())
        statesData = requestStatesData[2:len(requestStatesData)-3]
        states = statesData.split('\\n')

        statesRows = []
        for i in states:
            rowData = i.split(' ', 1)
            if (len(rowData) == 2):
                statesRows += [rowData]
        print("Total states: ", len(statesRows))
        stateCheck = ['YT','YUKON TERRITORY']
        print("State to check: ", stateCheck)
        print("Checking if the last state is in the list...")
        self.assertIn(stateCheck, statesRows)

        # Database connection 
        MARIAHOST = os.getenv('MARIAHOST')
        MARIAPORT = os.getenv('MARIAPORT')
        MARIAUSER = os.getenv('MARIAUSER')
        MARIAPASS = os.getenv('MARIAPASS')
        MARIADB = os.getenv('MARIADB')

        print("Create conection with MariaDB")
        # Conexion al servicio de la base de datos Mariadb
        mariaDatabase = mariadb.connect(
            # MARIAHOST
            host="localhost",   
            # MARIAPORT
            port=int("3306"),           
            # MARIAUSER
            user="Leemxch",               
            # MARIAPASS 
            password="Leemxch12345",        
            # MARIADB   
            database="weather"      
        )

        # Create conection for the db
        connection = mariaDatabase.cursor()

        print("Creating tables")
        # Create tables if not exists
        connection.execute("CREATE TABLE IF NOT EXISTS countries(\
                        country_id int auto_increment,\
                        country_name varchar(255) not null,\
                        country_acronym varchar(255) not null,\
                        primary key(country_id)\
        )")

        connection.execute("CREATE TABLE IF NOT EXISTS states(\
                        state_id int auto_increment,\
                        state_name varchar(255) not null,\
                        state_acronym varchar(255) not null,\
                        primary key(state_id)\
        )")

        connection.execute("CREATE TABLE IF NOT EXISTS files(\
                        file_id int auto_increment,\
                        file_name varchar(255) not null,\
                        file_url varchar(255) not null,\
                        file_date varchar(255) not null,\
                        file_state varchar(255) not null,\
                        file_md5 varchar(255) not null,\
                        primary key(file_id)\
        )")

        print("Checking both md5's")
        # Check if theres a row with the same md5 
        connection.execute("SELECT file_md5 from files WHERE file_md5 = ?", (str(md5Countries.hexdigest()),))
        for i in connection:
            hitCountry = 0

        connection.execute("SELECT file_md5 from files WHERE file_md5 = ?", (str(md5States.hexdigest()),))
        for i in connection:
            hitStates = 0

        print("Inserting data rows")
        # If table dont have the exact md5, adds a new row
        if hitCountry:
            print("found change in country file")
            connection.execute("INSERT INTO files (file_name, file_url, file_date, file_state, file_md5) \
                        VALUES (?,?,?,?,?)", (countryName, urlCountry, date, 'En espera', str(md5Countries.hexdigest())))
            for i in countriesRows:
                connection.execute("INSERT INTO countries(country_name,country_acronym) \
                                    SELECT * FROM (SELECT ? as country_name,? as country_acronym) AS tmp\
                                    WHERE NOT EXISTS (SELECT country_acronym FROM countries WHERE country_acronym = ?)\
                                    LIMIT 1",(i[1], i[0], i[0]))

        if hitStates:
            print("found change in state file")
            connection.execute("INSERT INTO files (file_name, file_url, file_date, file_state, file_md5) \
                        VALUES (?,?,?,?,?)", (stateName, urlState, date, 'En espera', str(md5States.hexdigest())))
            for i in statesRows:
                connection.execute("INSERT INTO states(state_name,state_acronym) \
                                    SELECT * FROM (SELECT ? as state_name,? as state_acronym) AS tmp\
                                    WHERE NOT EXISTS (SELECT state_acronym FROM states WHERE state_acronym = ?)\
                                    LIMIT 1",(i[1], i[0], i[0]))

        print("Commiting")
        # Close connection
        mariaDatabase.commit()
        mariaDatabase.close()
        print("End of test1")

if __name__ == '__main__':
    unittest.main()              