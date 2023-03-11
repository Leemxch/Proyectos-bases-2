# Proyecto opcional: WindyUI

> Integrantes:
>* Max Richard Lee Chung - 2019185076 
>* Miguel Ku Liang - 2019061913
>* Adriel Araya Vargas -2019312845
>* André Araya Vargas - 2020142856

## Guía de instalación

El programa necesita de la aplicación "Docker" y habilitar el servicio de "Kubernetes" para tener un clúster inicial y básico, llamado "docker-desktop". La aplicación para supervisar el comportamiento del clúster de Docker se denomina "Lens". Además, se utilizarán dos herramientas con sus respectivas carpetas dentro del proyecto para los servicios automatizados tales como Helm_charts (servicios predeterminados) y Docker_images (servicios programados). Finalmente, se está utilizando la herramienta RabbitMQ que maneja el servicio de envío de mensajes entre pods programados dentro del clúster, MariaDB para la base de datos del proyecto, y Elasticsearch como servicio para subir y analizar información.

### Instalación de helm charts

Primeramente se debe de gestionar las dependencias de los helm charts de databases y elastic que serán necesarias durante toda la ejecución del proyecto. Dentro del archivo Chart.yaml en /databases dentro de /Helm_chart, se encuentran declarados la versión, enlace del repositorio y nombre para poder extraer y descargar como un archivo comprimido los recursos de cada uno en la carpeta Charts dentro del mismo directorio. Los repositorios se deben buscar en Google buscando, como por ejemplo, el repositorio de Bitnami o Elasticsearch. Al conocer el enlace del repositorio, se añade a la librería de helm charts y buscar el nombre del recurso al que se quiera utilizar y actualizar como se muestra en el siguiente bloque de código.

```
helm add repo <enlace proporcionado>    # Agregar a la librería de helm charts
helm update repo <enlace proporcionado> # Actualizar el repositorio
helm search repo <recurso a buscar>     # Buscar la información del recurso
```

Para el funcionamiento del proyecto se van a implementar dos helm charts iniciales que se dedican a correr los servicios de la base de datos, (databases y elastic) y uno para las aplicaciones implementadas en Docker (applications). Dentro del helm chart databases, se utilizó la base de datos de MariaDB y ElasticSearch, y el sistema de mensajería RabbitMQ:

```
#Helm_chart/databases/chart.yalm
dependencies:
- name: rabbitmq
  version: "11.9.0"
  repository: "https://charts.bitnami.com/bitnami"
  condition: enableRabbitMQ
- name: mariadb
  version: "11.4.6"
  repository: "https://charts.bitnami.com/bitnami"
  condition: enableMariaDB
- name: eck-operator
  version: "2.6.1"
  repository: "https://helm.elastic.co"
  condition: enableOperator
```

Es importante recordar que las 3 dependencias necesitan de un usuario y una contraseña fija para instalar y desinstalar. Estas las declararemos en values.yaml dentro de /databases, así podrán ser referenciadas y obtenidas por otros pods. 

```
#Helm_chart/databases/values.yalm
rabbitmq:
    auth:
      # Se agrega un password fija para installar/desinstalar
      password: "rabbitmqpass"
      
  # --------------------------------------------------------------------
  mariadb:
    auth:
      # Se agrega un password fija para installar/desinstalar
      rootPassword: "mariadbpass"
      username: "user"
      password: "user"
      database: "weather"

  elasticsearch:
    auth:
      username: "user"
      password: "user"
```

También, es necesario correr los siguientes comandos en la terminal para tener localmente las imágenes a utilizar del clúster y la instancia para la visualización de Kibana.
```
docker pull docker.elastic.co/elasticsearch/elasticsearch:8.6.1
docker pull docker.elastic.co/kibana/kibana:8.6.1
```
Una vez que ya tenemos nuestras dependencias podemos empezar a instalar los Helm_charts. Esta será la manera de poner nuestros pods a trabajar para realizar sus respectivas tareas. 

Empezaremos instalando databases de primero para los pods de ECK operator, MariaDB y RabbitMQ.

```
Proyecto_opcional\Helm_chart\> helm install databases databases
```

De segundo se instala Elastic para traer las instancias de Elasticsearch y Kibana.

```
Proyecto_opcional\Helm_chart\> helm install elastic elastic
```

Una vez hayamos hecho estas instalaciones podremos revisar tanto Lens como Docker para revisar que los pods estén ejecutándose de manera correcta. Lens proporciona una mayor cantidad de herramientas como logs de los pods para encontrar errores y monitorear su funcionamiento. Si todo está en verde y “Running” dentro de la sección “Pods” en Lens, podremos continuar.

### Instalación de docker images.

Para esta sección, es necesario crear una cuenta en Docker Hub para poder guardar las imágenes de las aplicaciones desarrolladas para el proyecto, el cual se usarán para todas las aplicaciones del proyecto, utilizando lenguaje Python para otorgarles la lógica de recibir mensajes de la cola de RabbitMQ y procesarlas.

Luego de tener la cuenta habilitada, dentro de la carpeta general, se crearon -siete- carpetas para las aplicaciones respectivas, en donde cada uno tiene otra carpeta con los datos únicos de configuración de la aplicación de Python y un archivo de configuración "Dockerfile" para poder publicarlo al Docker Hub.

Este Dockerfile contiene la versión de Python a utilizar dentro de las aplicaciones (buster). Además, se siguieron las recomendaciones dadas por el profesor con la configuración necesaria para poder ejecutar la aplicación.

```
FROM python:3.6-buster

RUN apt-get update && apt-get -yy install libmariadb-dev

WORKDIR /app

COPY app/. .

RUN pip install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py"]
```

Dentro de cada aplicación y carpeta de app existe un archivo de texto (requirements.txt) con las librerías necesarias para instalarlas de forma automática luego de publicar la aplicación a Docker Hub. Dicha librerías utilizadas son pika, elasticsearch, mariadb y requests. También es utilizada bs4 para la recuperación de archivos del url.

Luego de crear el archivo de texto, es necesario definir el código fuente de Python para poder conectarlo con la cola de RabbitMQ por medio de variables de entorno, al igual que con su conexión con Elasticsearch y MariaDB. También, define el comportamiento lógico para procesar la información. A continuación se muestra un ejemplo de las variables de entorno del trabajador "processor".

```
hostname = os.getenv('HOSTNAME')
RABBIT_MQ=os.getenv('RABBITMQ')
RABBIT_MQ_PASSWORD=os.getenv('RABBITPASS')
OUTPUT_QUEUE=os.getenv('OUTPUT_QUEUE')
INPUT_QUEUE=os.getenv('INPUT_QUEUE')

ESENDPOINT = os.getenv('ESENDPOINT')
ESPASSWORD = os.getenv('ESPASSWORD')

MARIAHOST = os.getenv('MARIAHOST')
MARIAPORT = os.getenv('MARIAPORT')
MARIAUSER = os.getenv('MARIAUSER')
MARIAPASS = os.getenv('MARIAPASS')
MARIADB = os.getenv('MARIADB')
```

En carpeta de application, es necesario crear modelos o “templates” predefinidos de las aplicaciones con sus respectivas variables de entorno y sus contraseñas (adquiridas por referencias a los secrets). Las variables de entorno es información guardada en variables que son visibles en todo momento y almacenadas en el sistema. Ejemplo:

```
#processor.yalm
apiVersion: apps/v1
kind: Deployment
metadata:
  name: processor
  labels:
    app: processor
spec:
  replicas: 10
  selector:
    matchLabels:
      app: processor
  template:
    metadata:
      labels:
        app: processor
    spec:
      containers:
      - name: processor
        image: basesdedatos2/processor
        env:
          - name: RABBITMQ
            value: "databases-rabbitmq"
          - name: INPUT_QUEUE
            value: {{ .Values.config.processor.input_queue }}
          - name: OUTPUT_QUEUE
            value: {{ .Values.config.processor.output_queue }}
          - name: RABBITPASS
            valueFrom:
              secretKeyRef:
                name: databases-rabbitmq
                key: rabbitmq-password
                optional: false
          - name: MARIAHOST
            value: "databases-mariadb"
          - name: MARIAPORT
            value: "3306"
          - name: MARIAUSER
            value: "user"
          - name: MARIADB
            value: "weather"
          - name: MARIAPASS
            valueFrom:
              secretKeyRef:
                name: databases-mariadb
                key: mariadb-password
                optional: false
          - name: ESENDPOINT
            value: elastic-es-default
          - name: ESPASSWORD
            valueFrom:
              secretKeyRef:
                name: elastic-es-elastic-user
                key: elastic
                optional: false
          - name: ESINDEXDAILY
            value: daily
```

Recordar que aquí es donde se define la naturaleza del objeto. Es decir, el processor es un deployment, mientras orchestrator es un CronJob. Estos son templates recuperados de documentación de Kubernets.

Por último, luego de tener los archivos listos para poder publicarlos a la nube, se siguen los siguientes comandos para poder realizarlo desde la terminal, en la carpeta de ubicación del dockerfile donde el user es el nombre de usuario de Docker. Ejemplo con imagen stations:

```
docker login
docker build -t <user>/stations .
docker images
docker push <user>/stations
```

Luego de hacer el push de las imágenes podremos correr el helm install con las aplicaciones.

```
Proyecto_opcional\Helm_chart>helm install applications applications
```
#### MariaDB
Todos los componentes se comunican directamente con MariaDB para hacer solicitudes, modificar o añadir información a la base de datos del proyecto. El siguiente código demuestra la inicialización de la conexión en python. 
```
mariaDatabase = mariadb.connect(
    host=MARIAHOST,
    port=int(MARIAPORT),
    user=MARIAUSER,
    password=MARIAPASS,
    database=MARIADB
)
connection = mariaDatabase.cursor()
```
La conexión ahora nos permite ejecutar diferentes consultas directamente de MariaDB, tales como CREATE, SELECT o INSERT.
```
connection.execute(‘SQL QUERY’)
```
Para cerrar la conexión con la base de datos al finalizar su uso, se incluyen las siguientes dos líneas.
```
mariaDatabase.commit()
mariaDatabase.close()
```

#### Elasticsearch
La mayoría de las componentes crean una conexión directa con el cliente de ElasticSearch para la creación de índices y adición de nuevos archivos. Este útiliza las variables de entorno con el usuario ESENDPOINT y contraseña o token ESPASSWORD. El puerto más común para esta conexión es el 9200. Aquí se muestra la conexión al cliente de Elasticsearch:
```
clientES = Elasticsearch("https://" + ESENDPOINT + ":9200", basic_auth = ("elastic", ESPASSWORD), verify_certs = False)
```
Para añadir documentos a Elasticsearch es necesario crear un índice donde estos se van a guardar. Ahora, es necesario definir los espacios dentro del documento según la información que va a contener. A esto se le denomina mapeo. Por ejemplo:
```
doc = {                                             #Mapeo
        'filename': fileName,
        'contents': fileData,
    }
clientES.indices.create(index="files", mappings=doc) #Se crea el índice
```
Con está información establecida ahora es posible indexar en ElasticSearch con los requerimientos correspondientes. También se usa la función para eliminar índices bastante durante el desarrollo.
```
clientES.index(index='files', id=fileName, document=doc) # Se añade el documento al índice
clientES.delete(index='files', id= fileName) #Se elimina el índice
```

#### RabbitMQ
RabbitMQ es una herramienta para el manejo de las colas y su información. Es necesario el uso de la librería pika para el uso de Rabbit MQ. Este pasa metódos callback que quieran ser invocados cuando cierto evento se completa. Esté divide sus procesos en dos, uno para manejar las entradas de las colas y otro para las sálidas. Para las entradas, primero se introducen credenciales y parametros para conectar con RabbitMQ. Cuando la conexión está hecha se establece un canal de comunicación. En este canal se declara la entrada de la cola a recibir con .queu_declare y se establece un .basic_consume para saber como manejar la entrada.
```
credentials_input = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_input = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_input)
connection_input = pika.BlockingConnection(parameters_input)
channel_input = connection_input.channel()
channel_input.queue_declare(queue=INPUT_QUEUE)
channel_input.basic_consume(queue=INPUT_QUEUE, on_message_callback=callback, auto_ack=True) 
```
Para el proceso de las salidas de las colas es similar. Primero se establece la conexión, un canal de comunicación y se declara donde va ahora en la cola.
```
credentials_output = pika.PlainCredentials('user', RABBIT_MQ_PASSWORD)
parameters_output = pika.ConnectionParameters(host=RABBIT_MQ, credentials=credentials_output)
connection_output = pika.BlockingConnection(parameters_output)
channel_output = connection_output.channel()
channel_output.queue_declare(queue=OUTPUT_QUEUE)
```
Con el siguiente comando el canal empieza a consumir de las colas y pasar información.
```
channel_input.start_consuming()
```
### Pruebas unitarias
Las pruebas unitarias se realizaron con la librería “unittest” para poder probar las componentes, el cual se le agregaron otras líneas de código al Dockerfile para poder utilizarlas al tener el visto bueno (sin errores).
```
FROM python:3.6-buster

RUN apt-get update && apt-get -yy install libmariadb-dev

WORKDIR /app

COPY app/. .

RUN pip install --upgrade pip
RUN pip3 install --no-cache-dir -r requirements.txt

CMD [ "python", "-u", "./app.py"]
```

#### CronJobs
##### Countries/states
La prueba unitaria del CronJob countries/states se realizará de forma local, dado que no ocupa muchas dependencias del clúster y la mayor parte de su proceso está dentro de la base de datos de MariaDB junto con la extracción de datos de la página NOAA. 

Primeramente, es necesario la inserción correcta de la dirección URL de NOAA para recolectar la información de los “countries” y “states”, ya que si se le otorgan datos incorrectos, el procesamiento de datos tendrá errores lógicos por la separación entre líneas y columnas. 

Luego de procesar la información, se verifica la conexión directa a la base de datos para poder llenar las tablas con sus debidos espacios. Además, se verifica que las tablas se encuentren ya existentes para evitar problemas a la hora de ingresar las debidas filas de las tablas. 

Por último, para verificar que los datos se encuentren bien y correctos, se puede ingresar a la base de datos de forma manual para observar la inserción correcta de las tablas. De esta manera, se pueden realizar cambios en su comportamiento si es necesario. 

###### Resultado
Durante esta prueba unitaria, se verificó si en la lista procesada con los datos del URL de NOAA se encuentra o no el último dato relevante para validar el funcionamiento apropiado del mismo. Luego, siguiendo el flujo lógico, verifica si los datos de prueba de una base de datos local funciona de manera correcta para finalizar con su propósito.  
![Resultado](countriesResult.PNG)

##### Stations
Las pruebas del CronJob Stations se realizarán de forma local, ya que los procesos requeridos se pueden ejecutar de esta manera.

Por medio de un url, se recolecta la información de “stations”. Luego, se conecta a la base de datos para poder crear la tabla stations. También, se necesita de las tablas files, country y state, estas dos últimas se ocupan para generar las relaciones con los stations. La información recolectada se procesa y se asignan las relaciones con country y state. Por último, podemos observar los cambios en la base de datos.

###### Resultado
![Resultado](stationsResult.PNG)

##### Orchestrator

La prueba unitaria del CronJob Orchestrator se realizará de forma local, dado que no ocupa muchas dependencias del clúster y la mayor parte de su proceso está dentro de la base de datos de MariaDB junto con la extracción de datos de la página NOAA. 

El orchestrator trae todos los archivos de https://www.ncei.noaa.gov/pub/data/ghcn/daily/all y utilizamos Beutiful Soup como herramienta de web scraping para parsear el código HTML y convertirlo en árboles dentro de python. Dentro de estas listas hacemos búsqueda de la etiqueta ‘a’ para encontrar todos los nombres.

Se corre una función para acomodar todos los nombres de los archivos en una lista regular de python.

Luego nos conectamos a la base de datos y corremos un ciclo for que se dedicara a ingresar ingresar el nombre, url, fecha, estado y MD5 en nulo (será procesado más tarde) solo si no existe el registro dentro de la base de datos. De ser que ya exista sólo actualizará la fecha a la actual.

Finalmente iniciará una instancia de RabbitMQ donde enviará el nombre de cada uno de los archivos en su respectivo formato hacia processor.

###### Resultado

![Resultado](orchestratorResult.PNG)


#### Deployments

##### Processor.
La prueba unitaria se realizó de forma local. Se encontraron problemas a la hora de realizar las pruebas ya que el software no se tiene instalado aparte del clúster.

Con respecto a la ejecución del componente, el sistema espera que le llegué el mensaje en la cola designada de RabbitMQ del componente Orquestrator. Luego de esto, recibe el nombre del archivo, lo descarga, y compara si es igual el MD5 en la base de datos con la función checkMD5. Sí este es igual se añade a un índice de Elasticsearch llamado files. En cualquiera de los dos casos también cambia el estado en la base de datos de estos archivos, descargado o procesado.. Esto se hace en la función addElastic. Luego de esto processor envía el nombre del archivo a la cola.

#####Resultado.
Dentro de la prueba, se agregaron try-except para poder ejecutar el archivo sin errores, ya que, como se mencionó anteriormente, el software de Elasticsearch no se encontraba disponible de forma local. Sin embargo, fuera de esto, las demás funciones no tuvieron problemas.
![Resultado](processorResult.PNG)


##### Parser
La prueba unitaria se realizó de forma local, sin embargo, se encontraron problemas a la hora de realizar las pruebas ya que el software no se tiene instalado aparte del clúster. 

Con respecto a la ejecución del componente, el sistema espera a que le llegue un mensaje en la cola designada de RabbitMQ del componente processor. De esta forma, extrae la información del mensaje que es el nombre del archivo para ubicar en el índice de Elasticsearch. 

Luego, se llama a la función "getFile" para poder extraer la información almacenada del contenido URL del respectivo archivo y procesarlo en una lista. Por consiguiente, la información procesada se manda a la función "elasticFiles" para poder agregar la información a un nuevo índice "daily" y el archivo del índice procesado. Por último, se actualiza el estado del archivo en la base de datos MariaDB. 

###### Resultado
Dentro de la prueba, se agregaron try-except para poder ejecutar el archivo sin errores, ya que, como se mencionó anteriormente, el software de Elasticsearch no se encontraba disponible de forma local. Sin embargo, fuera de esto, las demás funciones no tuvieron problemas. 
![Resultado](parserResult.PNG)

##### Elements_transformation
La prueba unitaria se realizó de forma local, sin embargo, se encontraron problemas a la hora de realizar las pruebas ya que el software no se tiene instalado aparte del clúster. 

Este se conecta a la base de datos y a Elasticsearch. Luego, se procesa un archivo como ejemplo, en este caso tiene los valores siguientes:
 dicFile={
“fileName”: “AEM00041217.dly", 
“data”: [
	{
		"id": "AEM00041217",
		"date": "01011983",
		"element": "TMAX",
		"value": "298",
		"mflag": "B",
		"qflag": "M",
		"sflag": "A"

}
]
}
Se agregan los valores correspondientes para luego actualizar el archivo en el índice daily de Elasticsearch

###### Resultado
Dentro de la prueba, se agregaron try-except para poder ejecutar el archivo sin errores, ya que, como se mencionó anteriormente, el software de Elasticsearch no se encontraba disponible de forma local. Sin embargo, fuera de esto, las demás funciones no tuvieron problemas. 
![Resultado](elements_transformationResult.PNG)

##### Stations_transformation
La prueba unitaria se realizó de forma local, sin embargo, se encontraron problemas a la hora de realizar las pruebas ya que el software no se tiene instalado aparte del clúster. 

Este componente recibe el mensaje enviado por Elements_transformation y verifica su existencia dentro de Elasticsearch. Si se encuentra dentro se hará una conexión con MariaDB para poder extraer información necesaria de la tabla station, que será añadida a cada respectivo objeto en elasticsearch. Es decir traeremos los valores de latitude, longitude, elevation, state, name, gsn_flag, hcn_flag y wmo_id y asegurarnos asignar esos valores en cada elemento respectivo de MariaDB.

Mediante la actualización del index con parametros index, id y document se actualiza elasticsearch, y MariaDB mediante un UPDATE query. 

Finalmente RabbitMQ envía un mensaje a la siguiente cola

###### Resultado
Dentro de la prueba, se agregaron try-except para poder ejecutar el archivo sin errores, ya que, como se mencionó anteriormente, el software de Elasticsearch no se encontraba disponible de forma local. Sin embargo, fuera de esto, las demás funciones no tuvieron problemas. 
![Resultado](stations_transformationResult.PNG)

##### Countries_transformation
La prueba unitaria se realizó de forma local, sin embargo, se encontraron problemas a la hora de realizar las pruebas ya que el software no se tiene instalado aparte del clúster.

Este se conecta a la base de datos y a Elasticsearch. Luego, se procesa un archivo como ejemplo, en este caso tiene los valores siguientes:
 dicFile={
“fileName”: “AEM00041217.dly", 
“data”: [
	{
		"id": "AEM00041217",
		"date": "01011983",
		"element": "TMAX",
		"value": "298",
		"mflag": "B",
		"qflag": "M",
		"sflag": "A"
		"FIPS_country_code": "AE",
		"network_code": "M",
		"real_station_id": "00041217",
		"type_name": "Maximum temperature (tenths of degrees C)"

}
]
}
Se agregan los valores correspondientes para luego actualizar el archivo en el índice daily de Elasticsearch

###### Resultado
Dentro de la prueba, se agregaron try-except para poder ejecutar el archivo sin errores, ya que, como se mencionó anteriormente, el software de Elasticsearch no se encontraba disponible de forma local. Sin embargo, fuera de esto, las demás funciones no tuvieron problemas. 
![Resultado](country_transformationResult.PNG)

##### Publisher
El componente extrae información del índice daily de Elasticsearch para poder procesar la información a un nuevo índice weather data. Sin embargo, se generaron problemas a la hora de ubicar el archivo del índice daily por lo que no se pudo terminar su desarrollo.

## Conclusiones
* Docker como herramienta es sumamente efectiva para empacar aplicaciones de software. Esto al proveer de un ambiente aislado del sistema operativo para correr las aplicaciones y simplificar el proceso de despliegue.
* La implementación de diferentes contenedores permitió una mayor modularidad del software, lo que facilitó la incorporación de nuevas funcionalidades y la integración de nuevos componentes.
* La implementación de colas es buena para equilibrar la carga de trabajo entre el grupo y útil cuando se debe distribuir un mensaje a varios consumidores.
* Elasticsearch es altamente flexible y puede adaptarse a una variedad de casos de uso, desde la búsqueda de texto completo hasta la analítica de datos y la indexación de documentos.
* Kubernetes automatiza gran parte del proceso de implementación, lo que reduce los errores humanos y aumenta la eficiencia del equipo.
* Kubernetes, junto a Lens, permite una gestión centralizada de las aplicaciones y servicios, lo que facilita la administración y el monitoreo de la infraestructura.
* Helm simplifica la gestión de aplicaciones en Kubernetes al permitir a los definir aplicaciones y servicios en paquetes que pueden ser fácilmente instalados, actualizados y eliminados
*El monitoreo efectivo y el registro de información (logs) son esenciales para mantener la salud y rendimiento del sistema, así como para identificar problemas durante la operación y el traspaso de datos de las colas.
*El uso de las pruebas unitarias proporciona una facilidad para revisar la integridad de muchas de nuestras funciones.

## Recomendaciones
* Usar un entorno de desarrollo integrado versátil tanto para el código como para kubernetes para facilitar la visualización y trabajo de todos los diferentes tipos de archivos y procesos.
* Es mejor escribir los archivos de configuración de Kubernets en Yalm que en JSON a pesar de ser intercambiables. Estos tipos de archivos suelen ser más sencillos de manejar.
* No especificar valores innecesarios o dejar valores predeterminados en los archivos de configuración de Kubernetes. Es mejor mantenerlo lo más simple posible para disminuir errores.
* Es mejor no crear muchas réplicas de un despliegue para pruebas para mantener la RAM disponible y no alentar los procesos.
* Es necesario estar al tanto de todas las librerías y dependencias necesarias antes de empezar el proceso de programación.
* Al obtener información de páginas web es importante estar al tanto del estado de estas. Podría estar caída o con un volumen alto de visitas que afecté la aplicación de forma externa.
* Es recomendable utilizar una librería o herramienta de web scraping para obtener información directamente de una página web de forma específica.
* Es recomendable usar la interfaz que RabbitMQ ofrece por medio de puertos para poder revisar el funcionamiento de las colas.
* La documentación clara es esencial para asegurar que otros miembros del equipo puedan comprender y trabajar con el código del proyecto. 
* Se recomienda tener a mano la documentación, o los comandos más usados, de Docker y Helm debido a la cantidad de veces que se utilizan. Además de tener familiaridad al trabajar en terminal y los shortcuts y opciones que este posee.



## Referencias
* [Repositorio del proyecto](https://github.com/Leemxch/Proyectos-bases-2/tree/main/Proyecto_opcional)
* Bitnami - MariaDB (2022) Github. Recuperdo de [MariaDB](https://github.com/bitnami/charts/tree/master/bitnami/mariadb/)
* Bitnami - RabbitMQ (2022) Github. Recuperado de [RabbitMQ](https://github.com/bitnami/charts/tree/master/bitnami/rabbitmq/)
* Elasticsearch(2023). Recuperado de [Elasticsearch](https://www.elastic.co/guide/en/elastic-stack/current/overview.html)
* MariaDB (2023). Install MariaDB Connector/Python. Recuperado de [MariaDB](https://mariadb.com/docs/skysql/connect/programming-languages/python/install/#TOP)
* Stefano (2020). docker build failed at 'Downloading mariadb'. Recuperado de [StackOverflow](https://stackoverflow.com/questions/64521556/docker-build-failed-at-downloading-mariadb)
* Regolith (2021). How do I disable the SSL requirement in MySQL Workbench? Answer. Recuperado de [StackOverflow](https://stackoverflow.com/questions/69769563/how-do-i-disable-the-ssl-requirement-in-mysql-workbench
)
* Server, David (2019). How can I do 'insert if not exists' in MySQL? Solution. Recuperado de [StackOverflow](https://stackoverflow.com/questions/1361340/how-can-i-do-insert-if-not-exists-in-mysql)
* Geeksforgeeks (2023). MD5 hash in Python. Recuperado de [Geeksforgeeks](https://www.geeksforgeeks.org/md5-hash-python/)
* Castillo, D. (2022). How to Use Elasticsearch in Python. Recuperado de [Dylan Castillo](https://dylancastillo.co/elasticsearch-python/)
* TechOPverflow (2023). How to create ElasticSearch index if it doesn’t already exist in Python. Recuperado de [TechOverflow](https://techoverflow.net/2021/08/04/how-to-create-elasticsearch-index-if-it-doesnt-already-exist-in-python/)
* W3Schools (2023). Python JSON. Recuperado de [W3Schools](https://www.w3schools.com/python/python_json.asp)
