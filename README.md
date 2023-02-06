# vm2fews

Questo comando permette di scaricare dati meteorologici archiviati sui server del SIMC convertendoli al volo in file XML pronti per essere caricati in FEWS.

È uno script 100% Python senza altre dipendenze, quindi può essere eseguito su qualunque sistema con Python-3.6 o superiore, senza bisogno di una installazione.

Per evitare di passare utente e password da linea di comando, la URL da cui scaricare i dati deve essere scritta in un file. Per default il nome del file è `arkiweb_url.txt` e deve essere nella stessa cartella da cui si esegue il comando. Però si può specificare un nome diverso.

Per un aiuto su tutte le opzioni, eseguire `python3 vm2fews.py --help`.
