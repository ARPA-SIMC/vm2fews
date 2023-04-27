# vm2fews

Scarica dati meteo da arkiweb e li salva come file XML caricabili su FEWS.

L'unico requisito è un'installazione standard di Python-3.6 o superiore, non serve altro.

Non c'è installazione, basta scaricare il file `vm2fews.py` ed eseguirlo con `python3 vm2fews.py`. Per un aiuto su tutte le opzioni, eseguire `python3 vm2fews.py --help`.

## Quick Start

Creare un file `arkiweb_url.txt` con solo l'URL da cui scaricare i dati. Esempio di URL: https://USER:PASSWORD@simc.arpae.it/services/arkiweb/data

L'unico parametro obbligatorio è il nome del dataset arkimet di cui scaricare i dati. Esempio:

```shell
$ python3 vm2fews.py simnpr > simnpr.xml
```

Questo comando scarica i dati in un file `simnpr.vm2`, lo converte in XML per FEWS e stampa il risultato su standard output. Nell'esempio l'output è rediretto su un file, ma può anche essere passato in pipe ad un altro comando, per esempio per caricarlo direttamente in FEWS.

Per default l'XML non è formattato, quindi è difficile da leggere con `less` o con un editor di base. Se si ha la necessità, si può usare il parametro `--indent`, altrimenti conviene usare un browser Web come Chrome o Firefox che mostra automaticamente la struttura del file:

```shell
$ firefox $PWD/simnpr.xml
```

Si possono usare diverse opzioni per configurare il comando. Per vederle tutte, usare:

```shell
$ python3 vm2fews.py --help
```

Così si vedono anche i rispettivi valori di default. Per esempio il default di `--hours` è il numero di ore di dati scaricati in assenza di parametri. È possibile cambiare la quantità di dati scaricati e il loro intervallo temporale, usando **un massimo di due** delle seguenti opzioni: `--hours`, `--start_date`, `--end_date`. Il periodo è configurabile con `--step`.

## FAQ

### Posso passare l'URL da linea di comando?

No, per evitare di passare utente e password da linea di comando, salvandolo così nella history della shell.

### Perché viene creato un file <dataset>.vm2 (esemio: simnpr.vm2)?

È il file originale con i dati scaricati da arkiweb. È un CSV che viene immediatamente convertito in XML per FEWS. Può essere cancellato tranquillamente. Questo per il momento non viene fatto automaticamente per rendere più semplice il debugging.