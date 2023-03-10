import os
import re
import pika
import json
import mariadb
from elasticsearch import Elasticsearch
import unittest

class test(unittest.TestCase):
    def test1(self):
        # getFile
        print("Test get files from Elasticsearch")
        ESENDPOINT = os.getenv('ESENDPOINT')
        ESPASSWORD = os.getenv('ESPASSWORD')
        ESINDEXFILES = "files"
        fileName = "file"
        try:
            print("Connecting to Elastcisearch")
            client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)
            file = client.get(index = ESINDEXFILES, id=fileName)
            print(file['_source']["contents"])
            rawData = str(file['_source']["contents"])[2:]
            parse = rawData.split('\\n')
            temp = []
            for i in parse:
                fileContent = {
                    'id': i[0:11],
                    # month + year
                    "date": i[15:17] + i[11:15],
                    "element": i[17:21],
                    "value": i[21:26],
                    "mflag": i[26:27],
                    "qflag": i[27:28],
                    "sflag": i[28:29]
                }
                temp.append(fileContent)
            return temp
        except:
            print("Archivo no encontrado: ", fileName)
        print("End of test get files from Elasticsearch")

    def test2(self):
        # elasticFiles
        print("Test with Elasticsearch connection")
        ESENDPOINT = "os.getenv('ESENDPOINT')"
        ESPASSWORD = "os.getenv('ESPASSWORD')"
        ESINDEXDAILY = "daily"
        ESINDEXFILES = "files"
        print("Connecting to Elastcisearch")
        try:
            client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)
        except:
            pass
        fileName = "file"
        parsed = []
        doc = {
            "fileName": fileName,
            "data": parsed
        }
        try: # try to create the index ESINDEXDAILY
            client.indices.create(index=ESINDEXDAILY, mappings=doc)
        except: # ignore if exists
            pass
        # Remove the index of files and add the index daily in Elasticsearch
        print("Remove the index of files and add the index daily in Elasticsearch")
        try:
            client.index(index=ESINDEXDAILY, id= fileName, document= doc)
            client.delete(index=ESINDEXFILES, id= fileName)
        except:
            pass
        print("End of test with Elasticsearch connection")

    def test3(self):
        # mariaFiles
        print("Test with MariaDB connection")
        fileName = "file"
        mariaDatabase = mariadb.connect(
            host="localhost",
            port=int("3306"),
            user="Leemxch", 
            password="Leemxch12345",
            database="weather"
        )
        connection = mariaDatabase.cursor()
        # Update the table weather.files
        try:
            connection.execute("UPDATE files \
                        SET file_state= 'PARSEADO'\
                        WHERE file_name = ?", (fileName,))
        except:
            print("No se ha encontrado el archivo")
        # Close connection
        mariaDatabase.commit()
        mariaDatabase.close()
        print("End of test with MariaDB connection")

if __name__ == '__main__':
    unittest.main()    