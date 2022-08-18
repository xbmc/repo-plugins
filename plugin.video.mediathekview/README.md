Kodi MediathekView.de Addon
===========================

* **English Version:** Please see below
* **Versione Italiana:** Il testo italiano si trova più in basso

[1]: https://forum.mediathekview.de/category/14/offizieller-client-kodi-add-on
[2]: https://forum.kodi.tv/showthread.php?tid=326799
[3]: https://github.com/mediathekview/plugin.video.mediathekview/issues
[4]: https://github.com/mediathekview/plugin.video.mediathekview

Über dieses Addon
-----------------

Und schon wieder ein Kodi-Addon für deutsche Mediatheken... Wozu das ganze?

Weil der Ansatz dieses Addons ein anderer ist, als der der bereits verfügbaren
Addons: dieses Addon benutzt die Datenbank des beliebten Projektes
"MediathekView", welche stündlich aktualisiert wird und über 200.000 Einträge
aus allen deutschen Mediatheken enthält. Dieser Ansatz hat einige entscheidende
Vorteile gegenüber den anderen Addons, die in der Regel die sich stetig
verändernden Webseiten der Mediatheken der Öffentlich Rechtlichen durchsuchen.

* Hohe Geschwindigkeit beim Durchsuchen und Navigieren
* Unabhängigkeit von allen Änderungen des Seitenlayouts der Mediatheken
* Hohe Zuverlässigkeit


Für Fragen und Anregungen zu diesem Addon steht das [deutschsprachige Forum][1]
zur Verfügung. Fehlermeldungen und Vorschläge für neue Features können auch
direkt als [GitHub Issue][3] gemeldet werden. Der Quelltext steht ebenfalls auf 
[GitHub][4] zur Verfügung.


Wichtigste Features
-------------------
* Hintergrundaktualisierung der Datenbank
* Blitzschnelle Navigation
* Herunterladen von Filmen mit automatischer Erzeugung von NFO Dateien und
  eventueller Untertitel
* Lokale interne Datenbank oder geteilte MySQL Datenbank
* Benutzeroberfläche verfügbar in Deutsch, Englisch und Italienisch


Funktionsweise
--------------

Das Addon lädt die Datenbank von MediathekView herunter und importiert diese
entweder in eine lokale SQLite Datenbank, oder wahlweise in eine lokale
oder entfernte MySQL Datenbank (zur Benutzung durch mehrere Kodi-Clients).
Während der Laufzeit von Kodi werden in einem konfigurierbaren Intervall
(Standard: 2 Stunden) die Differenzdateien von MediathekView heruntergeladen
und in die Datenbank integriert. Spätestens am nächsten Kalendertag nach
dem letzten Update wird die Aktualisierung wieder mittels des vollständigen
Updates von Mediathekview ausgeführt.


Systemvoraussetzungen
---------------------

Die Systemvoraussetzungen für das Addon unterscheiden sich je nach
Konfiguration. Nach der Installation startet das Addon im lokalen Modus:
dies bedeutet, dass eine lokale SQLite-Datenbank benutzt wird, die auch
durch das Kodi-System lokal aktualisiert wird. Dies dürfte auch das
üblichste Szenario sein.

Die Benutzung der lokalen Datenbank erfordert im Idealfall ein einigermaßen
performantes Dateisystem. Ein Raspberry mit seiner langsamen SD-Karte ist in
diesem Fall sicherlich nicht die allerbeste Wahl. Das vollständige Update der
Datenbank dauert auf einem solchen System erfahrungsgemäß um die 15-20 Minuten.
Da dies aber im Hintergrund passiert, kann man unter Umständen gut damit leben.

Das Addon wurde auf verschiedenen Plattformen unter Linux, MacOS, Windows und
LibreELEC bzw. OpenELEC getestet. Auch verschiedene Android Systeme konnten
schon erfolgreich getestet werden. Wegen der Vielzahl der Plattformen ist es
allerdings nicht möglich eine abschließende Kompatibilitätsaussage zu machen.


Funktionsweise der Aktualisierungsmethoden
------------------------------------------

Das Addon unterstützt 5 verschiedene Aktualisierungsmethoden:
* **Zeitgesteuert:** Bei dieser Methode erfolgt die Aktualisierung ein mal
pro eingestelltem Zeitintervall (Standard: 2 Stunden). Die erste
Aktualisierung eines Kalendertages ist eine vollständige Aktualisierung, alle
weiteren sind Differenz-Aktualisierungen.
* **Automatisch (Standard):** Bei dieser Methode wird die Aktualisierung der
Datenbank automatisch durchgeführt. Die Aktualisierung erfolgt ein mal pro
eingestelltem Aktualisierungsintervall (Standard: 2 Stunden). Die erste
Aktualisierung eines Kalendertages ist eine vollständige Aktualisierung, alle
weiteren sind Differenz-Aktualisierungen. Die automatische Aktualisierung
pausiert, wenn das Addon länger als 2 Stunden nicht bedient wurde, um
Bandbreite und bei mobilen Geräten Strom zu sparen.
* **Nur beim Start:** Eine Aktualisierung erfolgt nur beim Start des Addons.
Handelt es sich hierbei um die erste Aktualisierung des Kalendertages, ist
dies eine vollständige Aktualisierung, ansonsten eine differentielle. Alle
weiteren Aktualisierungen müssen manuell über das Hauptmenü vom Benutzer
ausgelöst werden.
* **Manuell:** Es erfolgt keine automatische Aktualisierung. Der Benutzer
hat die Möglichkeit Aktualisierungen über das Hauptmenü auszulösen. Handelt
es sich hierbei um die erste Aktualisierung des Kalendertages, ist dies eine
vollständige Aktualisierung, ansonsten eine differentielle.
* **Abgeschaltet:** Es erfolgt keine automatische Aktualisierung. Diese
Konfiguration ist nur dann sinnvoll, wenn das Plugin eine externe Datenbank
nutzt und diese anderweitig aktualisiert wird.


Alternativ-Konfigurationen
--------------------------

Ist das Kodi-System zu langsam um eine eigene Datenbank zu verwalten
(z.B. Raspberry PI mit sehr langsamer SD-Karte) oder soll die Datenbank mit
mehreren Kodi Systemen geteilt werden, so besteht die Möglichkeit das Addon
auch mit einem externen Datenbank-Server (MySQL oder MariaDB) zu nutzen.

Da viele Kodi-Nutzer über ein eigenes NAS-System verfügen um ihre Medien
dem Media-Center zur Verfügung zu stellen, eignet sich dieses in der Regel
auch als MySQL bzw. MariaDB Datenbank-Server da nahezu alle NAS-Betriebssysteme
die Installation eines solchen anbieten.

Ist das Addon so konfiguriert, dass eine MySQL/MariaDB Datenbank genutzt werden
soll, erzeugt dieses die Datenbank selbsttätig, falls diese auf dem
Datenbankserver noch nicht existiert. Der angegebene Datenbankbenutzer muss
dafür allerdings auch die Rechte dafür besitzen.

Die Verbindung zur Datenbank kann in den Addon-Einstellungen im Abschnitt
_"Datenbank Einstellungen"_ vorgenommen werden.

Ist mindestens eines der angeschlossenen Kodi-Systeme in der Lage das Update
der Datenbank durchzuführen, so ist für das Update gesorgt. Sollte dies nicht
der Fall sein, so besteht auch die Möglichkeit, den Update-Prozess auf einem
anderen System (z.B. das NAS, den Datenbankserver oder eine andere Maschine)
laufen zu lassen.


Standalone Datenbank Update Prozess
-----------------------------------

Um die Datenbankaktualisierung von der Kommandozeile auszuführen, muss das
Zielsystem einen python-Interpreter bereitstellen. Des weiteren müssen noch
folgende Bibliotheken zur Verfügung stehen, sowie das Entpackprogramm
'xz' (optional):

* mysql-connector

Die Installation dieser Bibliotheken unter Debian/Ubuntu erfolgt durch Eingabe folgender Befehle:

````
Python 2:
sudo apt install python-pip
pip install mysql-connector-python
Python 3:
sudo apt install python3-pip
pip3 install mysql-connector-python
````

Das Aktualisierungsprogramm heisst `mvupdate` (`mvupdate3` für Python 3) und liegt im Hauptverzeichnis
des Addons und muss auch von dort ausgeführt werden. Aus diesem Grunde muss
das Addon in einem Verzeichnis aus der ausführenden Maschine kopiert werden.

Dies kann entweder durch Herunterladen und Entpacken der Addon-ZIP-Datei
erfolgen oder durch Klonen des Addon-Quellcode-Repositories mittels `git`

````
git clone https://github.com/mediathekview/plugin.video.mediathekview.git
````

Durch Angabe des Parameters `-h` bzw. `-h` hinter dem Datenbanktyp, gibt
das Programm spezifische Hilfe aus. Beispiel:

````
leo@bookpoldo ~/plugin.video.mediathekview $ ./mvupdate mysql -h
usage: mvupdate mysql [-h] [-v] [-f | -F] [-i INTERVALL] [-H HOST] [-P PORT]
                      [-u USER] [-p PASSWORD] [-d DATABASE]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         show progress messages (default: 0)
  -f, --force           ignore the minimum interval (default: False)
  -F, --full            ignore the minimum interval and force a full update
                        (default: False)
  -i INTERVALL, --intervall INTERVALL
                        minimum interval between updates (default: 3600)
  -H HOST, --host HOST  hostname or ip address (default: localhost)
  -P PORT, --port PORT  connection port (default: 3306)
  -u USER, --user USER  connection username (default: mediathekview)
  -p PASSWORD, --password PASSWORD
                        connection password (default: None)
  -d DATABASE, --database DATABASE
                        database name (default: mediathekview)
````


English Version
===============

About this Addon
----------------

Yet another Kodi Addon for the German public service video platforms... Why?

Because the approach of this addon is different from that of the already
available addons: this addon uses the database of the popular project
_"MediathekView"_, which is updated hourly and contains more than 200,000
entries from all German public service video platforms. This approach has
some significant advantages over the other add-ons that usually scan the
ever-changing websites of the German public service video platforms:

* High speed browsing and navigation
* Independence from all changes to the page layout of the media libraries
* High reliability

If you have any questions or suggestions about this addon, please feel free
to use the [official Kodi Addon Forum topic][2] or the [German forum topic][1].
Errors and feature requests can also be reported directly as [GitHub Issue][3].
The source code is available as well on [GitHub][4].


Highlights
----------
* Background updating of the database
* Amazing fast navigation and search
* Download with subtitles and automatic NFO file generation
* Internal standalone or shared MySQL database support
* UI localised to German, English and Italian


How it Works
------------

The addon downloads the database from MediathekView and imports it either into
a local SQLite database, or alternatively into a local or remote MySQL database
(for use by multiple Kodi clients).
During the runtime of Kodi, only the differential update files are downloaded
from MediathekView in a configurable interval (default: 2 hours) and integrated
into the database. By the next calendar day after the last update at the latest,
the update will be carried out again by importing the full MediathekView
database.


System Requirements
-------------------

The system requirements for the addon vary depending on the configuration.
After installation, the addon starts in local mode: this means that a local
SQLite database is used, which is also updated locally by the Kodi system.
This is probably the most common scenario.

Ideally, using the local database requires a file system with a decent
performance. A Raspberry with a slow SD card is certainly not the very
best choice in this case but still acceptable. The full update will take
in this case about 15-20 Minutes but since this happens in the background,
you may be able to live with it.

The addon has been tested on different platforms under Linux, MacOS,
Windows and LibreELEC/OpenELEC. Various Android systems have also been
tested successfully. Due to the variety of platforms, however, it is not
possible to make a final compatibility statement.


How the update methods work
---------------------------

The addon supports 5 different update methods:
* **Continously:** This method automatically updates the database. The update
takes place once per set update interval (default: 2 hours). The first update
of a calendar day is a full update, all others are differential updates.
* **Automatic (Default):** This method automatically updates the database.
The update takes place once per set update interval (default: 2 hours). The
first update of a calendar day is a full update, all others are differential
updates. The auto-update pauses if the addon has not been used for more than
2 hours to save bandwidth and power on mobile devices.
* **On Start:** An update will only take place on the first invocation of the
addon during the Kodi runtime. If this is the first update of the day, it is a
complete update, otherwise a differential one. All further updates must be
manually initiated by the user via the main menu.
* **Manual:** There is no automatic update. The user has the possibility to
initiate updates via the main menu. If this is the first update of the day,
it is a complete update, otherwise a differential one.
* **Disabled:** There is no automatic update. This configuration only makes
sense if the plugin uses an external database and this database is updated
elsewhere.


Alternate Configurations
------------------------

If the Kodi system is too slow to manage its own database (e.g. Raspberry PI
with a very slow SD card) or you want to share the database across multiple
Kodi instances, it is also possible to use the addon with an external database
(MySQL or MariaDB).

Since many Kodi users have their own NAS system to make their media available
to the media center, this is usually also suitable as a MySQL/MariaDB database
server since almost all NAS operating systems offer the installation of MySQL.

If the addon is configured to use a MySQL/MariaDB database, the database is
created automatically if it does not yet exist on the database server. However,
the specified database user must also have sufficient user rights in order to
do this.

The connection to the database can be configured in the addon settings in
the "Database Settings" section.

If at least one of the connected Kodi systems is able to update the database,
the data is available to all Kodi systems. If this is not the case, it is
also possible to run the update process on a different system (e.g. the NAS,
the database server or another machine).

Standalone Database Update Process
----------------------------------

A python interpreter as well as the unpacker 'xz' is requirered on the
target system in order to execute the commandline update process. Additionally
the following python library is required:

* mysql-connector

The required library can be installed via pip:

````
Python 2:
sudo apt install python-pip
pip install mysql-connector-python
Python 3:
sudo apt install python3-pip
pip3 install mysql-connector-python
````

The update program is called `mvupdate` (`mvupdate3` for Python 3) and is located in the root directory
of the addon and must be executed from there. The whole addon has to be copied
to the target machine.

This can be either done by downloading and unpacking the addon archive or
by cloning the source repository with `git`

````
git clone https://github.com/mediathekview/plugin.video.mediathekview.git
````

By specifying the option `-h` itself or after the requested database type,
the application shows specific help instructions:

````
leo@bookpoldo ~/plugin.video.mediathekview $ ./mvupdate mysql -h
usage: mvupdate mysql [-h] [-H HOST] [-P PORT] [-u USER] [-p PASSWORD]
                      [-d DATABASE]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         show progress messages (default: 0)
  -f, --force           ignore the minimum interval (default: False)
  -F, --full            ignore the minimum interval and force a full update
                        (default: False)
  -i INTERVALL, --intervall INTERVALL
                        minimum interval between updates (default: 3600)
  -H HOST, --host HOST  hostname or ip address (default: localhost)
  -P PORT, --port PORT  connection port (default: 3306)
  -u USER, --user USER  connection username (default: mediathekview)
  -p PASSWORD, --password PASSWORD
                        connection password (default: None)
  -d DATABASE, --database DATABASE
                        database name (default: mediathekview)
````



Versione Italiana
=================

Un altro addon Kodi per la navigazione nelle piattaforme video operate dalle
emittenti pubbliche tedesche... Perchè?

Perché l'approccio di questo addon è diverso da quello degli altri addon
disponibili: questo addon utilizza il database del grande progetto
_"MediathekView"_, che viene aggiornato ogni ora e contiene oltre 200.000 voci
da tutte le piattaforme video tedesche. Questo approccio presenta alcuni
vantaggi significativi rispetto agli altri addon, che cercano di scansionare
i siti delle piattaforme video in tempo reale:

* Navigazione nella libreria ad alta velocità
* Indipendenza da qualsiasi modifica al layout di pagina delle librerie multimediali
* Alta affidabilità

Se avete domande o suggerimenti riguardo quest'addon, non esitate ad utilizzare
il [forum in lingua inglese][2] o [in lingua tedesca][1] tedesco. Errori e
suggerimenti per nuove funzionalità possono anche essere segnalati direttamente
come [GitHub Issue][3]. Il sorgente è disponibile in un [Repository GitHub][4].


Highlights
----------
* Attualizzazione della banca dati in background
* Navigazione e ricerca velocissima
* Scaricamento video con generazione automatica die file NFO e scaricamento
  sottotitoli
* Banca dati interna o banca dati condivisa a base MySQL
* Interfaccia disponibile in Italiano, Inglese e Tedesco


Come funziona
-------------

L'addon scarica il database da MediathekView e lo importa in un database SQLite
locale o, in alternativa, in un database MySQL locale o remoto (per l'uso da
parte di molteplici sistemi Kodi). Durante il runtime di Kodi, i file di
aggiornamento differenziali vengono scaricati da MediathekView in un intervallo
configurabile (predefinito: 2 ore) ed importati nel database. Al più tardi
entro il giorno successivo all'ultimo aggiornamento, l'aggiornamento sarà
nuovamente effettuato tramite l'aggiornamento completo di Mediathekview.

Idealmente, l'utilizzo del database locale richiede un file system con
prestazioni accettabili. Un Raspberry di prima generazione con una scheda SD
lenta non è certamente la miglior scelta ma sempre ancora accettabile. La
durata di un aggiornamento completo in questo caso sarà intorno ai 15-20
minuti. Ma poiché questo accade in background, l'impatto sarà accetabile.

L'addon è stato testato su diverse piattaforme in Linux, MacOS, Windows e
LibreELEC nonchè OpenELEC. Anche diversi sistemi Android sono stati testati
con successo. A causa della varietà delle piattaforme, tuttavia, non è
possibile fare una dichiarazione finale di compatibilità.


Come funzionano i metodi di aggiornamento
-----------------------------------------

L'addon supporta 5 diversi metodi di aggiornamento:
* **Di continuo:** Questo metodo aggiorna il database una volta per ogni
intervallo di aggiornamento impostato (impostazione predefinita: 2 ore).
Il primo aggiornamento di un giorno è un aggiornamento completo, tutti gli
altri sono aggiornamenti differenziali.
* **Automatico (Predefinito):** Questo metodo aggiorna automaticamente il
database. L'aggiornamento avviene una volta per ogni intervallo di
aggiornamento impostato (impostazione predefinita: 2 ore). Il primo
aggiornamento di un giorno è un aggiornamento completo, tutti gli altri sono
aggiornamenti differenziali. L'aggiornamento automatico si interrompe se
l'addon non è stato utilizzato per più di 2 ore al fine di salvare larghezza
di banda e corrente sui dispositivi mobili.
* **Solo all'avvio:** L'aggiornamento avviene non appena l'addon viene
invocato. Se questo è il primo aggiornamento del giorno, avverrà un
aggiornamento completo, altrimenti differenziale. Tutti gli ulteriori
aggiornamenti dovranno essere avviati manualmente dall'utente attraverso il
menu principale.
* **Manuale:** Non vi è alcun aggiornamento automatico. L'utente ha la
possibilità di avviare gli aggiornamenti tramite il menu principale. Se questo
è il primo aggiornamento del giorno, avverrà un aggiornamento completo,
altrimenti differenziale.
* **Disattivato:** Non vi è alcun aggiornamento automatico. Questa
configurazione ha senso solo se il plugin utilizza un database esterno che
viene aggiornato altrove.


Configurazioni alternative
--------------------------

Se il sistema Kodi è troppo lento per gestire il database interno (ad es.
Raspberry PI con una scheda SD molto lenta) o se si desidera condividere il
database con altri sistemi Kodi, è anche possibile utilizzare l'addon con un
server database esterno (MySQL o MariaDB).

Dal momento che molti utenti Kodi hanno il proprio sistema NAS per rendere i
loro contenuti mediali disponibili al media center, questo è di solito anche
adatto come server di database MySQL/MariaDB, dal momento che quasi tutti i
sistemi operativi NAS offrono l'installazione di un tale database.

Se l' addon è configurato per utilizzare un database MySQL/MariaDB, il database
verrà creato automaticamente se non esiste ancora sul database server.
Tuttavia, anche l'utente del database specificato deve avere i diritti
necessari alla creazione di un database.

Il collegamento al database può essere effettuato nelle impostazioni 
dell'addon nella sezione "Impostazioni Banca Dati".

Se almeno uno dei sistemi Kodi collegati è in grado di aggiornare il database,
l'addon funzionerà su tutti i sistemi Kodi. In caso contrario, è anche
possibile eseguire il processo di aggiornamento su un altro sistema (ad es. il
NAS, il server di database o un altro sistema).


Processo esterno di aggiornamento del database
----------------------------------------------

Per eseguire il processo esterno di aggiornamento del database, è necessario
che sul sistema sul quale il processo viene eseguito sia istallato un
interprete python, il programma di decompressione 'xz' e le seguenti
librerie python:

* mysql-connector

QUeste potranno essere istallate mediante il programma pip:

````
Python 2:
sudo apt install python-pip
pip install mysql-connector-python
Python 3:
sudo apt install python3-pip
pip3 install mysql-connector-python
````

Il programma di aggiornamento si chiama `mvupdate` (`mvupdate3` per Python 3) e si trova nella directory
principale dell'addon e dovrà essere lanciato da questa directory. L'intero
addon dovrà essere copiato sul sistema di destinazione.

Questo sarà possibile sia scaricando l'archivio dell'addon che dovrà essere
spacchettato in loco o mediante clonaggio dai sorgenti mediante `git`

````
git clone https://github.com/mediathekview/plugin.video.mediathekview.git
````

Specificando l'opzione `-h` a se stante o a tergo del tipo di database da
aggiornare, l'applicazione mostrerà le opzioni disponibili:

````
leo@bookpoldo ~/plugin.video.mediathekview $ ./mvupdate mysql -h
usage: mvupdate mysql [-h] [-H HOST] [-P PORT] [-u USER] [-p PASSWORD]
                      [-d DATABASE]

optional arguments:
  -h, --help            show this help message and exit
  -v, --verbose         show progress messages (default: 0)
  -f, --force           ignore the minimum interval (default: False)
  -F, --full            ignore the minimum interval and force a full update
                        (default: False)
  -i INTERVALL, --intervall INTERVALL
                        minimum interval between updates (default: 3600)
  -H HOST, --host HOST  hostname or ip address (default: localhost)
  -P PORT, --port PORT  connection port (default: 3306)
  -u USER, --user USER  connection username (default: mediathekview)
  -p PASSWORD, --password PASSWORD
                        connection password (default: None)
  -d DATABASE, --database DATABASE
                        database name (default: mediathekview)
````
