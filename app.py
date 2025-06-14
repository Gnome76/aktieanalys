def init_db():
    # ...

def uppgradera_databas_med_datum():
    conn = sqlite3.connect("bolag.db")
    c = conn.cursor()
    c.execute("PRAGMA table_info(bolag)")
    kolumner = [rad[1] for rad in c.fetchall()]
    if "datum_inlagd" not in kolumner:
        c.execute("ALTER TABLE bolag ADD COLUMN datum_inlagd TEXT")

    from datetime import date
    idag = date.today().isoformat()
    c.execute("""
        UPDATE bolag
        SET datum_inlagd = ?
        WHERE datum_inlagd IS NULL OR datum_inlagd = ''
    """, (idag,))
    conn.commit()
    conn.close()

def main():
    st.title("Aktieinnehav – Spara och analysera")
    
    init_db()
    uppgradera_databas_med_datum()  # ← Körs en gång

    # ...resten av appen...
