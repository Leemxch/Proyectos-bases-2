import requests
from bs4 import BeautifulSoup
import mariadb
import unittest

class test(unittest.TestCase):
    def test1(self):
        print("Test to get files from url and sort them into a list.")
        url = ("https://www.ncei.noaa.gov/pub/data/ghcn/daily/all")
        requestFiles = requests.get(url)
        filesSoup = BeautifulSoup(requestFiles.text, 'html.parser')
        files = filesSoup.findAll('a')
        newList = []
        fileCount = 0
        maxFiles = 5000
        for file in files:
            fileCount = fileCount + 1
            if file.text.find('.dly') != -1:
                newList = newList + [file.text]
                # with open('test.txt', 'a') as f:
                # f.write(file.text + '  ')
            if fileCount == maxFiles:
                files = newList
        print("End of: Test to get files from url and sort them into a list...")


    def test2(self):
        # mariaFiles
        print("Test with MariaDB connection, add or update files.")
        mariaDatabase = mariadb.connect(
            host="localhost",
            port=int('3306'),
            user="root",
            password="gmlsdrhn2",
            database="weather"
        )
        files = ('ACW00011604.dly','ACW00011647.dly','AE000041196.dly')
        connection = mariaDatabase.cursor()
        for file in files:
            hitFile = 1
            url = 'https://www.ncei.noaa.gov/pub/data/ghcn/daily/all'
            urlFile = url + '/' + file
            connection.execute("SELECT file_name from files WHERE file_name=?", (file,))
            if connection.rowcount != 0 and connection.rowcount != -1:
                    connection.execute("UPDATE files SET file_date=now() WHERE file_name=?", (file,))
                    hitFile = 0
            # NO existe coincidencia = ingresa a la base de datos
            if hitFile:
                connection.execute(
                    "INSERT INTO files(file_name, file_url, file_date, file_state, file_md5) VALUES(?, ?, now(), 'LISTADO', 'null')",
                    (file, urlFile))
        # Close connection
        mariaDatabase.commit()
        mariaDatabase.close()
        print("End of test with MariaDB connection")

if __name__ == '__main__':
    unittest.main()