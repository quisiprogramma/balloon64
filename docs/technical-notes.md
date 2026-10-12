# Balloon 64 — Sky Run

Gioco infinito per Commodore 64, scritto in assembly 6502/6510.
Il PRG contiene un loader BASIC `SYS 2062` e tutto il gioco; non servono file aggiuntivi a runtime.

## Avvio

In VICE, modello C64 PAL: **File → Autostart disk/tape image**, selezionare `balloon64.prg`.
In alternativa: `x64sc -autostart balloon64.prg`.
Se il programma viene soltanto caricato, digitare `RUN`.
La tastiera deve avere il focus dell'emulatore. Disattivare un eventuale joystick emulato che intercetti la barra spaziatrice.

## Comandi

- **S**: START; **C**: CREDITS; **O**: OPTIONS.
- **SPAZIO**: spinta immediata, crescente tenendo premuto. Dopo 18 aggiornamenti (~0,36 s) la spinta termina: rilasciare per riarmarla. Non basta tenerlo premuto indefinitamente.
- **M**: menu, anche durante una partita o dopo GAME OVER.
- Options: **1/2** diminuiscono/aumentano la musica; **3/4** gli effetti.
- Options: **5/6** scelgono il colore della mongolfiera tra i 16 colori C64 (0–F), con anteprima su fondo bianco/nero. La selezione è ciclica e resta attiva nelle partite successive fino al riavvio.
- Livelli volume: **0–F**, ossia 0–15 in esadecimale. Zero silenzia la relativa voce; F è il massimo. Le impostazioni restano valide fino al riavvio.

Passare nei varchi senza toccare gli ostacoli, il limite superiore o il terreno. Ogni ostacolo superato vale un punto. Il contatore ha quattro cifre e torna a 0000 dopo 9999. Dopo una sconfitta: M, poi S.

## Ricompilazione

Requisiti: Java e [Kick Assembler](https://theweb.dk/KickAssembler/) (compilazione verificata con v5.25).
Estrarre `KickAss.jar` dal download e copiarlo in `tools/`, quindi da PowerShell:

```powershell
./build.ps1
```

Oppure specificarne il percorso:

```powershell
./build.ps1 -KickAssJar 'C:/percorso/KickAss.jar'
```

Da altri sistemi, dalla cartella del progetto:

```sh
java -jar /percorso/KickAss.jar src/main.asm -o "$PWD/balloon64.prg" -symbolfile
```

L'assemblatore non è incluso. Il PRG già compilato è pronto all'uso.

## Organizzazione e scelte

- `src/main.asm`: inizializzazione, dispatcher schermate, input, rendering, fisica, collisioni, punteggio, audio e sprite; sezioni commentate in ordine di esecuzione.
- `src/assets/title-*.bin`: schermata iniziale in bitmap multicolore nativo VIC-II, con lettere arrotondate, ombra, riflessi e nuvola dorata.
- `tools/make_title.py`: generatore della grafica e del font pixel dei comandi, senza immagini o font esterni. Richiede Python 3 e Pillow; i file binari già inclusi bastano per compilare.
- `title-preview.png`: anteprima decodificata dai valori pixel/colori della schermata C64, ingrandita senza sfocatura; non è una cattura da VICE.
- `src/main.sym`: indirizzi simbolici generati dall'assemblatore.
- `tools/test_game.py`: regressioni eseguite direttamente sulle istruzioni 6502 del PRG tramite py65.
- `build.ps1`: compilazione ripetibile.

Schermo a $0400; il menu usa bitmap multicolore a $2000 (160×200 pixel, quattro colori per cella incluso lo sfondo condiviso). Gioco, Credits e Options ripristinano il modo testo con font ROM. Sprite monocromatico 24×21 a $3FC0, fuori dal bitmap: usa esattamente i 63 byte forniti dall'utente nelle righe DATA 200–240, più un byte di allineamento. Programma da $0801, dati colore del menu da $4000. Puntatore temporaneo $FB/$FC. Il gioco assume l'avvio dall'ambiente BASIC/KERNAL standard e prende il controllo degli interrupt mascherabili; usare il reset dell'emulatore per tornare al BASIC.

I Credits riportano, in maiuscolo per il font C64: «Gioco per Commodore 64 creato con l'intelligenza artificiale con l'intento di innervosire il giocatore».

Per rigenerare la schermata dopo una modifica grafica:

```sh
python -m pip install Pillow
python tools/make_title.py
```

Ricompilare quindi il PRG con le istruzioni precedenti.

La posizione verticale usa 1/16 di pixel e velocità con segno. Gli ostacoli avanzano di una colonna ogni cinque aggiornamenti, con un varco di sette righe determinato da un LFSR. Un ostacolo alla volta viene riciclato senza termine. Le collisioni usano un rettangolo 24×21, quindi includono anche gli angoli trasparenti dello sprite. Il movimento degli ostacoli è volutamente a passi di 8 pixel.

La spinta è stata attenuata del 30% rispetto alla prima versione: ogni valore della curva originale è moltiplicato per 0,70 e arrotondato a 1/16 di pixel. Il primo frame applica -1,375 pixel/frame e il massimo è -2,625 pixel/frame. La durata resta di 18 aggiornamenti.

Aggiornamento PAL a circa 50 Hz; NTSC salta un aggiornamento ogni sei frame usando il flag video del KERNAL. SID: melodia sulla voce 1, percussioni sulla voce 2, effetti sulla voce 3. I volumi separati agiscono sul sustain delle voci, mentre il volume master resta a 15. Timbro e livelli effettivi possono variare tra SID 6581 e 8580.

## Musica dal MIDI

Il brano incluso in `music/source.mid` è il file fornito dall'utente: 120 BPM, durata 8 secondi, 32 note di melodia (programma MIDI 82, Calliope Lead) e 32 colpi di cassa/battimani. Tutte le altezze, le ripetizioni e i colpi sono mantenuti, senza trasposizioni o eliminazione di note. La musica si ripete in ciclo e continua durante i cambi di schermata.

`src/audio.asm` riproduce il brano con un timbro a onda quadra simile a un organetto, cassa triangolare con discesa di frequenza e battimani con brevi impulsi di rumore. Sono ricostruzioni SID: il MIDI non contiene registrazioni degli strumenti e i timbri non possono coincidere con quelli di un sintetizzatore General MIDI. Le note melodiche hanno una breve interruzione di 20 ms per riarticolare anche le note ripetute. Gli eventi note-on/note-off simultanei sulla stessa altezza sono interpretati come note consecutive.

Ogni ottavo dura alternativamente 13 e 12 aggiornamenti: il ciclo totalizza 400 aggiornamenti, circa 8 secondi, senza errore di arrotondamento cumulativo. La precisione locale è di 20 ms e il tempo effettivo segue la frequenza video reale. Le tabelle di intonazione sono distinte per PAL e NTSC. Il controllo MUSIC regola insieme melodia e percussioni; SFX continua a regolare solo gli effetti.

Per rigenerare le tabelle `src/song.asm` dal MIDI incluso:

```sh
python -m pip install mido==1.3.3
python tools/convert_midi.py
```

Ricompilare quindi il PRG. Il convertitore verifica questo specifico arrangiamento e rifiuta formati musicali diversi invece di scartare silenziosamente note. I dati già generati sono inclusi: Java e Kick Assembler bastano per ricompilare il gioco.

Riferimento hardware: [Commodore 64 Programmer's Reference Guide — sprite](https://www.devili.iki.fi/Computers/Commodore/C64/Programmers_Reference/Chapter_3/page_134.html).

## Verifiche

Compilazione riuscita con Kick Assembler 5.25. Superate verifiche CPU per schermate, copia dei dati bitmap/colore, ripristino del modo testo, spinta crescente, riarmo, collisioni, varco libero, incremento e riporto del punteggio, riciclo ostacoli e mute audio. Anteprima grafica decodificata e controllata visivamente.

Per ripeterle dopo la compilazione (Python 3):

```sh
python -m pip install py65==1.2.0 mido==1.3.3
python tools/test_game.py
```

Non è stato eseguito un collaudo interattivo in VICE in questo ambiente. Le verifiche CPU non emulano VIC-II, SID o KERNAL; resa video, audio e controllo reale della tastiera richiedono il collaudo nell'emulatore.

Il test della musica confronta un ciclo completo del codice macchina con le note e le percussioni del MIDI sorgente, verifica il riavvio al frame 400, l'intonazione PAL/NTSC e la contemporaneità degli effetti sulla terza voce.
