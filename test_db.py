import pymysql  # o MySQLdb se usi mysqlclient

try:
    connection = pymysql.connect(
        host='localhost',
        user='unigest_user',  # il tuo user
        password='cultura',  # sostituisci
        database='unigest_db',
        charset='utf8mb4'
    )
    print("✅ Connessione MySQL riuscita!")
    print(f"Versione server: {connection.get_server_info()}")
    connection.close()
except Exception as e:
    print(f"❌ Errore connessione: {e}")
