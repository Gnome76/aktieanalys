import sqlite3
import os

# Radera databasen om den finns
if os.path.exists("aktier.db"):
    os.remove("aktier.db")

# Skapa anslutning
conn = sqlite3.connect("aktier.db")
c = conn.cursor()

# Skapa tabellen på nytt med exakt 14 kolumner
c.execute('''
CREATE TABLE bolag (
    bolag TEXT PRIMARY KEY,
    nuvarande_kurs REAL,
    pe1 REAL, pe2 REAL, pe3 REAL, pe4 REAL,
    ps1 REAL, ps2 REAL, ps3 REAL, ps4 REAL,
    vinst_ar REAL, vinst_nasta_ar REAL,
    oms_i_ar REAL, oms_nasta_ar REAL
)
''')

# Data med exakt 14 värden
data = (
    "Testbolag",
    100.0,
    10.5, 11.0, 10.0, 9.5,
    2.5, 2.6, 2.7, 2.8,
    5.0, 5.5,
    3.0, 3.5
)

# Infoga data
c.execute('INSERT INTO bolag VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)', data)

conn.commit()

# Hämta och skriv ut för att verifiera
c.execute('SELECT * FROM bolag')
rows = c.fetchall()
print("Innehåll i tabell bolag:")
for row in rows:
    print(row)

conn.close()
