import os

templates = {
    # Continua nella prossima risposta...
}
```

Vuoi che ti crei lo script COMPLETO per generare tutti i template?

### 2. **Import e Anni Accademici**

**NO, NON devi creare manualmente gli anni accademici!**

Lo script `import_vecchio_db.py` che ti ho appena dato:
1. **IMPORTA automaticamente** tutti gli anni accademici dalla tabella `TAnnoAccademico` del vecchio DB
2. **Marca come attivo** solo l'anno più recente (se non ce n'è già uno attivo)
3. **Poi importa** tutti i dati collegati a quegli anni

### 3. **Ordine corretto**:
```
1. ✅ Crea Quadrimestri (manualmente nell'admin) - FATTO
2. ✅ Crea Categorie Corsi (manualmente nell'admin) - FATTO
3. 🚀 Esegui import_vecchio_db.py - IMPORTA TUTTO (inclusi anni accademici)
4. ✅ Verifica dati importati
5. 📝 Genera template mancanti
