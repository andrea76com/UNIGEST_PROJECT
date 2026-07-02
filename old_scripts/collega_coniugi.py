"""
UNIGEST - Collega Coniugi
Collega il campo coniuge per tutti gli iscritti
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.db import connections
from core.models import Iscritto

def collega_coniugi():
    print("="*70)
    print("UNIGEST - Collega Coniugi")
    print("="*70)

    cursor = connections['old_database'].cursor()

    # 1. Quanti hanno moglie/marito nel vecchio DB?
    cursor.execute("""
        SELECT COUNT(*)
        FROM TAnagrafe
        WHERE Moglie IS NOT NULL
        AND Moglie != 0
    """)
    totale_vecchio = cursor.fetchone()[0]
    print(f"\n1. Iscritti con coniuge nel vecchio DB: {totale_vecchio}")

    # 2. Quanti nel nuovo DB?
    gia_collegati = Iscritto.objects.filter(coniuge__isnull=False).count()
    print(f"2. Già collegati nel nuovo DB: {gia_collegati}")
    print(f"   Da collegare: {totale_vecchio - gia_collegati}")

    if gia_collegati >= totale_vecchio:
        print("\n✅ Tutti i coniugi sono già collegati!")
        return

    risposta = input(f"\nVuoi collegare i coniugi mancanti? (si/no): ")
    if risposta.lower() not in ['si', 'sì', 's']:
        return

    print("\n3. Collegamento coniugi...")

    # Prendi tutti con Moglie != NULL
    cursor.execute("""
        SELECT Matr, Moglie
        FROM TAnagrafe
        WHERE Moglie IS NOT NULL
        AND Moglie != 0
    """)

    collegati = 0
    non_trovati = 0

    for row in cursor.fetchall():
        matricola = row[0]
        matricola_coniuge = row[1]

        try:
            # Trova iscritto
            iscritto = Iscritto.objects.filter(matricola=matricola).first()
            if not iscritto:
                non_trovati += 1
                continue

            # Trova coniuge
            coniuge = Iscritto.objects.filter(matricola=matricola_coniuge).first()
            if not coniuge:
                non_trovati += 1
                continue

            # Collega (solo se non già collegato)
            if not iscritto.coniuge:
                iscritto.coniuge = coniuge
                iscritto.save()
                collegati += 1

                if collegati % 10 == 0:
                    print(f"   Collegati: {collegati}")

        except Exception as e:
            if non_trovati == 0:
                print(f"   ⚠️ Errore: {e}")

    print("\n" + "="*70)
    print("RISULTATO")
    print("="*70)
    print(f"✅ Coniugi collegati: {collegati}")
    print(f"⚠️  Non trovati: {non_trovati}")
    print(f"\n📊 Totale con coniuge: {Iscritto.objects.filter(coniuge__isnull=False).count()}")
    print("="*70)


if __name__ == '__main__':
    collega_coniugi()
