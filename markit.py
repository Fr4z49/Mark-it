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

    # 1. Correzione iniziale delle estensioni (fondamentale per i controlli successivi)
    if args.output[-4:] != ".pdf":
        args.output += ".pdf"
    if args.input[-3:] != ".mi":
        args.input += ".mi"
    if args.style and args.style[-5:] != ".json" and args.style[-5:] != ".JSON":
        args.style += ".json"

    # Definiamo le cartelle utili per dopo
    script_dir = Path(__file__).parent
    local_style_backup = script_dir / "Style.json"
    home_config_dir = Path.home() / ".config" / "mark-it"
    home_config_style_default = home_config_dir / "Style.json"
    system_style = Path("/usr/share/mark-it/Style.json")

    # 2. SE L'UTENTE NON HA SPECIFICATO LO STILE (Cerca quello predefinito)
    if args.style is None:
        if local_style_backup.exists():
            # Modalità Portatile
            args.style = str(local_style_backup)
        elif os.path.exists("Style.json"):
            # Priorità locale nella cartella corrente
            args.style = "Style.json"
        else:
            # Modalità Pacchetto di sistema
            if not home_config_dir.exists():
                home_config_dir.mkdir(parents=True, exist_ok=True)

            if not home_config_style_default.exists() and system_style.exists():
                shutil.copy(system_style, home_config_style_default)
                print(f"Creato file di stile predefinito in: {home_config_style_default}")

            args.style = str(home_config_style_default)

    # 3. SE L'UTENTE HA SPECIFICATO LO STILE (es. -s Style2.json)
    else:
        # Se il file specificato NON esiste nella cartella corrente, ed è solo un nome di file (senza "/" o "../")
        if not os.path.exists(args.style) and not "/" in args.style and not ".." in args.style:
            
            # Se siamo in modalità portatile, lo cerca nella cartella dello script (es. sulla chiavetta)
            if local_style_backup.exists() and (script_dir / args.style).exists():
                args.style = str(script_dir / args.style)
            
            # Altrimenti, se siamo in modalità installata, lo cerca in ~/.config/mark-it/
            elif home_config_dir.exists() and (home_config_dir / args.style).exists():
                args.style = str(home_config_dir / args.style)

    print(f"input: {args.input}")
    print(f"output: {args.output}")
    print(f"stile: {args.style}")

    New_Parser.main(args.input, args.output, args.style)

if __name__ == "__main__":
    main()