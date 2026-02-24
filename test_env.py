from decouple import config

print("=== TEST LETTURA .ENV ===")
print(f"DB_NAME: {config('DB_NAME', default='NON TROVATO')}")
print(f"DB_USER: {config('DB_USER', default='NON TROVATO')}")
print(f"DB_PASSWORD: {config('DB_PASSWORD', default='NON TROVATO')}")
print(f"DB_HOST: {config('DB_HOST', default='NON TROVATO')}")
print(f"DB_PORT: {config('DB_PORT', default='NON TROVATO')}")
