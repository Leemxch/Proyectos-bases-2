import os
import re
import requests
import mariadb

# Get the countries from the NOAA wensite data
requestCountries = requests.get("https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-countries.txt")
requestCountriesData = str(requestCountries.content)
countriesData = requestCountriesData[2:len(requestCountriesData)]
countries = countriesData.split('\\n')

countriesRows = []
for i in countries:
    if (len(i) == 2):
        rowData = i.split(' ', 1)
        countriesRows += [rowData]
        print(rowData)

# Get the states from the NOAA website data
requestStates = requests.get("https://www.ncei.noaa.gov/pub/data/ghcn/daily/ghcnd-states.txt")
requestStatesData = str(requestStates.content)
statesData = requestStatesData[2:len(requestStatesData)-3]
states = statesData.split('\\n')

statesRows = []
for i in states:
    if (len(i) == 2):
        rowData = i.split(' ', 1)
        statesRows += [rowData]
        print(rowData)
'''
# Database connection 
MARIAHOST = os.getenv('MARIAHOST')
MARIAPORT = os.getenv('MARIAPORT')
MARIAUSER = os.getenv('MARIAUSER')
MARIAPASS = os.getenv('MARIAPASS')
MARIADB = os.getenv('MARIADB')

# Conexion al servicio de la base de datos Mariadb

mariaDatabase = mariadb.connect(
    host=MARIAHOST,
    port=int(MARIAPORT),
    user=MARIAUSER, 
    password=MARIAPASS,
    database=MARIADB
)

mariaDatabase = mariadb.connect(
    host="127.0.0.1",
    port=3305,
    user="user", 
    password="user",
    database="my_database"
)
'''
mariaDatabase = mariadb.connect(
    host="localhost",
    port=3306,
    user="Leemxch", 
    password="Leemxch12345",
    database="weather"
)
connection = mariaDatabase.cursor()

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
                   file_dia varchar(255) not null,\
                   file_estado varchar(255) not null,\
                   primary key(file_id)\
)")

# Crear request para insertar el pais y estado
for i in countriesRows:
    connection.execute("INSERT INTO countries(country_name,country_acronym) \
                        SELECT * FROM (SELECT ? as country_name,? as country_acronym) AS tmp\
                        WHERE NOT EXISTS (SELECT country_acronym FROM countries WHERE country_acronym = ?)\
                        LIMIT 1",(i[1], i[0], i[0]))

for i in statesRows:
    connection.execute("INSERT INTO states(state_name,state_acronym) \
                        SELECT * FROM (SELECT ? as state_name,? as state_acronym) AS tmp\
                        WHERE NOT EXISTS (SELECT state_acronym FROM states WHERE state_acronym = ?)\
                        LIMIT 1",(i[1], i[0], i[0]))

mariaDatabase.commit()
mariaDatabase.close()