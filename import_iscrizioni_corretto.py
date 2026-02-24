"""
UNIGEST - Import Iscrizioni CORRETTO
Usa Anno + Codice Corso invece di ID edizione
"""

import os
import sys
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import *

def import_iscrizioni_per_anno(anno_vecchio_formato):
    """
    Importa iscrizioni per un singolo anno
    """
    # Converti formato anno
    anno_nuovo_formato = anno_vecchio_formato.replace('/', '-')

    print(f"\n📝 Importazione anno {anno_vecchio_formato} -> {anno_nuovo_formato}")

    # Trova anno nel nuovo DB
    anno = AnnoAccademico.objects.filter(anno=anno_nuovo_formato).first()
    if not anno:
        print(f"   ⚠️ Anno {anno_nuovo_formato} non trovato nel nuovo DB")
        return 0

    cursor = connections['old_database'].cursor()

    # Conta iscrizioni per questo anno
    cursor.execute(f"""
        SELECT COUNT(*)
        FROM TFrequenzaCorsi
        WHERE AnnoAccademico = '{anno_vecchio_formato}'
    """)
    totale = cursor.fetchone()[0]
    print(f"   Iscrizioni nel vecchio DB: {totale}")

    if totale == 0:
        return 0

    # Prendi tutte le iscrizioni
    cursor.execute(f"""
        SELECT Corso, Matricola, Ricevuta, Data
        FROM TFrequenzaCorsi
        WHERE AnnoAccademico = '{anno_vecchio_formato}'
    """)

    importate = 0
    errori = 0
    corso_non_trovato = set()
    iscritto_non_trovato = set()
    edizione_non_trovata = set()

    for row in cursor.fetchall():
        codice_corso = row[0]
        matricola = row[1]
        ricevuta = row[2]
        data = row[3]

        try:
            # Trova iscritto
            iscritto = Iscritto.objects.filter(matricola=matricola).first()
            if not iscritto:
                iscritto_non_trovato.add(matricola)
                errori += 1
                continue

            # Trova corso
            corso = Corso.objects.filter(codice=codice_corso).first()
            if not corso:
                corso_non_trovato.add(codice_corso)
                errori += 1
                continue

            # Trova edizione per questo anno e corso
            edizione = EdizioneCorso.objects.filter(
                anno_accademico=anno,
                corso=corso
            ).first()

            if not edizione:
                edizione_non_trovata.add(f"{anno_nuovo_formato}-{codice_corso}")
                errori += 1
                continue

            # Crea iscrizione
            _, created = IscrizioneCorso.objects.get_or_create(
                anno_accademico=anno,
                edizione_corso=edizione,
                iscritto=iscritto,
                defaults={
                    'numero_ricevuta': ricevuta,
                    'data_iscrizione': data if data else anno.data_inizio
                }
            )

            if created:
                importate += 1

                # Progress ogni 100
                if importate % 100 == 0:
                    percentuale = (importate / totale) * 100
                    print(f"   Progresso: {importate}/{totale} ({percentuale:.1f}%)")

        except Exception as e:
            errori += 1
            if errori <= 3:
                print(f"   ⚠️ Errore: {e}")

    print(f"   ✅ {importate} importate, {errori} errori")

    # Mostra dettaglio errori
    if corso_non_trovato:
        print(f"   ⚠️ {len(corso_non_trovato)} corsi non trovati: {list(corso_non_trovato)[:5]}")
    if iscritto_non_trovato:
        print(f"   ⚠️ {len(iscritto_non_trovato)} iscritti non trovati")
    if edizione_non_trovata:
        print(f"   ⚠️ {len(edizione_non_trovata)} edizioni non trovate")

    return importate


def main():
    print("="*70)
    print("UNIGEST - Import Iscrizioni Corso CORRETTO")
    print("="*70)

    # Ottieni tutti gli anni dal vecchio DB
    cursor = connections['old_database'].cursor()
    cursor.execute("""
        SELECT DISTINCT AnnoAccademico
        FROM TFrequenzaCorsi
        ORDER BY AnnoAccademico DESC
    """)

    anni = [row[0] for row in cursor.fetchall() if row[0]]
    print(f"\nAnni trovati nel vecchio DB: {len(anni)}")
    for anno in anni[:5]:
        print(f"  - {anno}")

    if len(anni) > 5:
        print(f"  ... e altri {len(anni)-5}")

    risposta = input("\nVuoi importare TUTTE le iscrizioni? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's', 'yes', 'y']:
        print("❌ Annullato")
        return

    # Importa per ogni anno
    totale_importate = 0
    for anno in anni:
        importate = import_iscrizioni_per_anno(anno)
        totale_importate += importate

    # Verifica finale
    print("\n" + "="*70)
    print("VERIFICA FINALE")
    print("="*70)

    totale_db = IscrizioneCorso.objects.count()
    print(f"Iscrizioni totali nel nuovo DB: {totale_db}")

    # Verifica per anno 2023-2024
    anno_test = AnnoAccademico.objects.filter(anno='2023-2024').first()
    if anno_test:
        count_2023 = IscrizioneCorso.objects.filter(anno_accademico=anno_test).count()
        edizioni_2023 = EdizioneCorso.objects.filter(anno_accademico=anno_test).count()
        print(f"\nAnno 2023-2024:")
        print(f"  - Edizioni: {edizioni_2023}")
        print(f"  - Iscrizioni: {count_2023}")

    print("="*70)
    print(f"\n✅ Importazione completata! Totale importate: {totale_importate}")


if __name__ == '__main__':
    main()
