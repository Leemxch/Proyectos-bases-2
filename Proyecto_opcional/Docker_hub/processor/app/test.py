import requests
import mariadb
import os
import hashlib
from elasticsearch import Elasticsearch
import unittest

class test(unittest.TestCase):
    def test1(self):
        # elasticFiles
        print("Test with Elasticsearch and MariaDB to check MD5.")
        ESENDPOINT = os.getenv('ESENDPOINT')
        ESPASSWORD = os.getenv('ESPASSWORD')
        print("Connecting to Elastcisearch")
        try:
            client = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth=("elastic", ESPASSWORD),
                                   verify_certs=False)
        except:
            pass

        print('Checking MD5...')
        url = "https://www.ncei.noaa.gov/pub/data/ghcn/daily/all/"
        fileName = 'ACW00011604.dly'
        urlFile = url + fileName
        hitFile = 1
        requestFile = requests.get(urlFile)
        fileData = str(requestFile.content)
        md5File = hashlib.md5(fileData.encode())

        # Conexion al servicio de la base de datos Mariadb
        mariaDatabase = mariadb.connect(
            host="localhost",
            port=int('3306'),
            user="root",
            password="gmlsdrhn2",
            database="weather"
        )

        connection = mariaDatabase.cursor()

        connection.execute("SELECT file_md5 from files WHERE file_md5 = ? AND file_name = ?",
                           (str(md5File.hexdigest()), fileName))

        # Verificar si el md5 es diferente o igual.
        for i in connection:
            hitFile = 0

        if hitFile:
            doc = {
                'filename': fileName,
                'contents': fileData,
            }
            try:
                client.indices.create(index="files", mappings=doc)
            except:
                pass


            connection.execute("UPDATE files SET file_state = 'DESCARGADO', file_md5 = ? WHERE file_name= ?",
                           (str(md5File.hexdigest()), fileName))
            print("Descargado")
        else:
            connection.execute("UPDATE files SET file_state = 'PROCESADO' WHERE file_md5 = ?",
                               (str(md5File.hexdigest()),))
            print('Procesado')

        # Close connection
        mariaDatabase.commit()
        mariaDatabase.close()

        return


if __name__ == '__main__':
    unittest.main()