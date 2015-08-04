import sqlite3
import logging
try:
    import config
except "No such file or directory":
    import config_sample as config
    logging.critical("Configuration file not found.")
    exit()


databasePath = config.databasePath
conn = sqlite3.connect(databasePath)

c = conn.cursor()
c.execute('''CREATE TABLE IF NOT EXISTS Requests
             (
             GitHubTitle text,
             PagureTitle text,
             GitHubID integer,
             PagureID integer
             )''')
conn.commit()
conn.close()
