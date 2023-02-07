# vm2fews

Scarica dati meteo da arkiweb e li salva come file XML caricabili su FEWS.

L'unico requisito è un'installazione standard di Python-3.6 o superiore, non serve altro.

Non c'è installazione, basta scaricare il file `vm2fews.py` ed eseguirlo con `python3 vm2fews.py`. Per un aiuto su tutte le opzioni, eseguire `python3 vm2fews.py --help`.

## Quick Start

Creare un file `arkiweb_url.txt` con solo l'URL da cui scaricare i dati. Esempio di URL: https://USER:PASSWORD@simc.arpae.it/services/arkiweb/data

L'unico parametro obbligatorio è il nome del dataset di cui scaricare i dati. Esempio:

```shell
$ python3 vm2fews.py simnpr > simnpr.xml
$ firefox $PWD/simnpr.xml
```

## FAQ

### Posso passare l'URL da linea di comando?

No, per evitare di passare utente e password da linea di comando, salvandolo così nella history della shell.
