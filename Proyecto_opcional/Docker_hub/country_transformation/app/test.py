import os
import re
import hashlib
import datetime
import requests
import mariadb
import unittest

class Test(unittest.TestCase):
    def test1(self):
        # Database connection 
        MARIAHOST = "localhost"
        MARIAPORT = 3306
        MARIAUSER = "root"
        MARIAPASS = "Proyecto_opcional"
        MARIADB = "weather"
        print("Establishing connection with MariaDB")
        try:
            mariaDatabase = mariadb.connect(
                host=MARIAHOST,
                port=int(MARIAPORT),
                user=MARIAUSER, 
                password=MARIAPASS,
                database=MARIADB
            )
            cursor = mariaDatabase.cursor()
        except:
            pass
        ESENDPOINT = os.getenv('ESENDPOINT')
        ESPASSWORD = os.getenv('ESPASSWORD')
        ESINDEXDAILY = "daily"
        nameFile = "AEM00041217.dly"
        try:
            client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)
        except:
            pass
        dicFile = {
                    "fileName" : "AEM00041217.dly",
                    "data": [
                        {
                            "id": "AEM00041217",
                            "date": "01011983",
                            "element": "TMAX",
                            "value": "298",
                            "mflag": "B",
                            "qflag": "M",
                            "sflag": "A",
                            "FIPS_country_code": "AE",
                            "network_code": "M",
                            "real_station_id": "00041217",
                            "type_name": "Maximum temperature (tenths of degrees C)"
                        }
                    ]}
        dicDataList = dicFile['data']
        print("adding values")
        for i in range(0, len(dicDataList)):
            station_id = dicDataList[i]['id']
            if len(station_id) < 11:
                continue
            # agrega valores
            country_code = dicDataList[i]['FIPS_country_code']
            try:
                cursor.execute("SELECT country_name FROM countries WHERE country_acronym = ?", (country_code,))
                country_name_list = cursor.fetchall()
                dicDataList[i]['country_name'] = ""
                for country_name in country_name_list:
                    dicDataList[i]['country_name'] = country_name
                state = dicDataList[i]['state']
                cursor.execute("SELECT state_name FROM states WHERE state_acronym = ?", (state,))
                state_name_list = cursor.fetchall()
                dicDataList[i]['state_name'] = ""
                for state_name in state_name_list:
                    dicDataList[i]['state_name'] = state_name
            except:
                pass
        dicFile['data'] = dicDataList
        # Actualiza datos en Elasticsearch
        print("updating Elasticsearch")
        try:
            client.index(index = ESINDEXDAILY, id = nameFile, document = dicFile)
        except:
            pass
        # Actualiza tabla files
        print("updating database")
        try:
            cursor.execute("UPDATE files SET file_state= 'CON_PAIS'\
                                WHERE file_name = ?", (nameFile,))
            mariaDatabase.commit()
            mariaDatabase.close()
        except:
            pass

if __name__ == '__main__':
    unittest.main()              