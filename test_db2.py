from decouple import config
import pymysql

print("=== TEST CONNESSIONE DATABASE ===")
print(f"DB_NAME: {config('DB_NAME')}")
print(f"DB_USER: {config('DB_USER')}")
print(f"DB_HOST: {config('DB_HOST')}")

try:
    connection = pymysql.connect(
        host=config('DB_HOST'),
        user=config('DB_USER'),
        password=config('DB_PASSWORD'),
        database=config('DB_NAME'),
        charset='utf8mb4'
    )
    print("✅ Connessione riuscita!")
    
    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE();")
    db_name = cursor.fetchone()
    print(f"✅ Database attivo: {db_name[0]}")
    
    cursor.execute("SELECT USER();")
    user = cursor.fetchone()
    print(f"✅ Utente connesso: {user[0]}")
    
    connection.close()
    
except Exception as e:
    print(f"❌ ERRORE: {e}")
