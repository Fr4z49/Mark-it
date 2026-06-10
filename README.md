# Presentazione Mark-IT:

## Cos'è mark-it:
> **mark-it** è un formato di testo simile al markdown che permette di creare un pdf secondo uno stile predefinito.
## Header multilivello:

Markit supporta 3 livelli di header e si usano tramite il simbolo '#' con il numero del livello dell'header:
- "#" -> titolo /H1
- "#2" -> H2
- "#3" -> H3

gli headers sono di default **in BOLD** ma si puo cambiare nel file `Style.json`, inoltre gli headers possono essere sbarrati con due underscore.


## Paragrafi:

per markit, il testo normale è un paragrafo, ed in ognuno di essi è possibile avere delle "opzioni di formattazione:

- **BOLD**: Il grassetto si utilizza avvolgendo le frasi o parole da grassettare con due asterischi
- ~~TESTO BARRATO~~ : é possibile barrare il testo (come negli header), con avvolgendo le frasi o parole con due underscore.
- `Codice inline`: Il codice inline è utilizzato per evidenziare del codice o testo semplice. si utilizza avvolgendo le parole o frasi con un singolo backtick.

## Blockquote (Citazioni):

Le citazioni creano un blocco di testo con sfondo che puo essere utilizzato per, appunto, fare delle citazioni\n si utilizza iniziando la riga con un simbolo del maggiore.
> Questo è un esempio di citazione

## Codice multilinea:

Il codice multilinea permette di scrivere in un area riquadrata qualsiasi cosa senza formattazione markit, perfetto appunto per del codice.

```
Questo è un esempio
    Di codice Multilinea!

        wow!
        **questo non diventerà mai grassetto!**
```
codice python:
```
# Script Python: esempio con indentazione

a = 5
b = 3

if a > b:
    print("a è maggiore di b")
    print("Dentro il blocco if")
else:
    print("b è maggiore o uguale ad a")
    print("Dentro il blocco else")

print("Fuori dal blocco if/else")
```
## Pagine:

Markit ha la peculiarità di generare una singola lunga pagina al posto di un pdf di dimensione "A4" standard. in questo modo il documento (che non è pensato per la stampa) è piu ordinato senza stacchi bruschi della pagina.
La altezza della pagina minima puo essere specificata nel file di stile e viene usata quando il contenuto della pagina non supera l'altezza minima specificata, dopodichè la pagina si espande in base al contenuto.

## File di stile:

Markit usa un file con formato `JSON` per cambiare le impostazioni di stile del documento.
Questo comprende:
- impostazioni della pagina (colore sfondo, margini, altezza minima documento, larghezza documento)
- impostazioni header (colore, dimensione, stile, font, margini)
- impostazioni paragrafi (colore,font,margini, interlinea)
- impostazioni blockquote (colore sfondo, colore testo, font e dimensione font,, colore linea laterale,margini)
- impostazioni inline-code (colore sfondo, colore testo, font e dimesione font,)
- impostazioni codice multilinea (colore sfondo, colore testo, font e dimensione font, margini)


## Perchè markit?:

>Ho deciso di sviluppare Mark-it perchè avevo bisogno di qualcosa di piu pratico per prendere appunti formattati con uno stile predefinito.

>Prima di mark-it usavo dei binari di pandoc + wkhtmltopdf per generare i pdf ma cerano 4 problemi:
1. conversione da Markdown a PDF:
    >Il file markdown non viene trasformato direttamente in pdf, ma viene trasformato prima in un HTML, ad esso gli viene allegato un file di stile "css" con pandoc e poi viene trasformato in pdf con wkhtmltopdf.
    >questo perchè markdown è un formato che era stato ideato per l'uso nei siti web per creare documentazioni (come su GitHub, nei readme), non per prendere appunti e trasformarli in PDF.

2. Binari statici e librerie:
    >Pandoc e wkhtmltopdf non possono funzionare da soli, infatti dipendono da diverse librerie che non sono leggere. inoltre essendo che avevo bisogno di una soluzione portatile (che deve funzionare indipendentemente dal pc), avevo bisogno di uno script bash che dice di lanciare i due programmi con le librerie che sono sulla chiavetta, e non era per niente comodo.

3. Le interruzioni di pagina:
    > la "goccia che ha fatto traboccare il vaso" per me sono state le interruzioni di pagina.\nNon riuscivo a trovare un programma che mi lasciasse fare una singola lunga pagina che si adatta al contenuto e che fosse allo stesso tempo una soluzione portatile

4. Sicurezza e fragilià:
    >Eseguire dei programmi che non sono installati su una macchina è un pericolo per la sicurezza e generalmente non adrebbe fatto, python invece è generalmente piu "innocuo" e sicuro da usare, in piu, quasi tutte le macchine linux hanno di default un interprete python.


soluzione... Python!:

>Python è il linguaggio che stiamo imparando a scuola e il problema lo ho trasformato in una possibilità per ampliare le mie conoscienze nel linguaggio ed anche per crearmi una sfida personale.


## Usare Mark-it (Linux): 

### Modalità portatile: 
- Clona il repository:
    ```
    git clone https://www.github.com/Fr4z49/Mark-it
    cd Mark-it
    ```
- crea la virtual env:

    ```
    python -m venv venv
    ```
- Attiva la venv:

    ```
    source ./venv/bin/activate
    ```
- Installa le dipendenze con pip:

    ```
    pip install -r requirements.txt
    ```
- Avvia markit!:

    ```
    ./markit.py input.mi [-o output.pdf] [-s style.json]
    ```



