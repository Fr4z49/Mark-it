#!/usr/bin/env python3

import argparse
import os
import shutil
from pathlib import Path
import New_Parser

def main():
    parser = argparse.ArgumentParser()

    parser.add_argument("input")
    parser.add_argument("-o", "--output")
    parser.add_argument("-s", "--style")

    args = parser.parse_args()

    if args.output is None:
        args.output = args.input + ".pdf"

    # GESTIONE AUTOMATICA DELLO STILE (PORTATILE + PACCHETTO)
    if args.style is None:
        # Trova la cartella in cui risiede fisicamente lo script markit.py
        script_dir = Path(__file__).parent
        local_style = script_dir / "Style.json"

        if local_style.exists():
            # 1. MODALITÀ PORTATILE: Se Style.json è nella cartella dello script (es. sulla chiavetta), usa quello.
            # Funziona anche se l'utente lancia il programma trovandosi in un'altra directory!
            args.style = str(local_style)
        elif os.path.exists("Style.json"):
            # 2. PRIORITÀ LOCALE: Se l'utente ha messo uno Style.json specifico nella cartella dei suoi appunti corrente
            args.style = "Style.json"
        else:
            # 3. MODALITÀ PACCHETTO ARCH: Usa ~/.config (perché in site-packages lo Style.json non c'è)
            home_config_dir = Path.home() / ".config" / "mark-it"
            home_config_style = home_config_dir / "Style.json"
            system_style = Path("/usr/share/mark-it/Style.json")

            # Se la cartella ~/.config/mark-it/ non esiste, la crea
            if not home_config_dir.exists():
                home_config_dir.mkdir(parents=True, exist_ok=True)

            # Se il file Style.json non esiste in ~/.config, lo copia da quello di sistema
            if not home_config_style.exists() and system_style.exists():
                shutil.copy(system_style, home_config_style)
                print(f"Creato file di stile predefinito in: {home_config_style}")

            args.style = str(home_config_style)

    # Controlli e correzioni delle estensioni (il tuo codice originale)
    if args.output[-4:] != ".pdf":
        args.output += ".pdf"
    if args.input[-3:] != ".mi":
        args.input += ".mi"
    if args.style[-5:] != ".json" and args.style[-5:] != ".JSON":
        args.style += ".json"

    print(f"input: {args.input}")
    print(f"output: {args.output}")
    print(f"stile: {args.style}")

    New_Parser.main(args.input, args.output, args.style)

if __name__ == "__main__":
    main()