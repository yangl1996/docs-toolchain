import sqlite3
import logging
try:
    import config
except ImportError:
    import config_sample as config
    logging.critical("Configuration file not found.")
    exit()


conn = sqlite3.connect(config.issueDatabasePath)

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
