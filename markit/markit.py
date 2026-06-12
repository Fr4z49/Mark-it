#!/usr/bin/env python3

import argparse
import os
import shutil
from pathlib import Path

try:
    from . import New_Parser
except ImportError:
    import New_Parser

def parse_arguments():
    """Gestisce il parsing degli argomenti comuni a entrambe le modalità."""
    parser = argparse.ArgumentParser()

    parser.add_argument("input")
    parser.add_argument("-o", "--output")
    parser.add_argument("-s", "--style")
    parser.add_argument("-r", "--reset", action="store_true", help="Ripristina gli stili predefiniti")

    args = parser.parse_args()

    # Correzione automatica delle estensioni
    if args.output is None:
        args.output = args.input + ".pdf"
    elif not args.output.lower().endswith(".pdf"):
        args.output += ".pdf"

    if not args.input.lower().endswith(".mi"):
        args.input += ".mi"

    if args.style and not args.style.lower().endswith(".json"):
        args.style += ".json"

    return args

def execute_parser(args,font_path):
    """Avvia il parser effettivo con i parametri configurati."""
    print(f"Input:  {args.input}")
    print(f"Output: {args.output}")
    print(f"Stile:  {args.style}")
    
    New_Parser.main(args.input, args.output, args.style,font_path)

def main():
    """Entry point per la versione INSTALLATA (via pyproject).
    
    Usa ~/.config/mark-it/ come cartella di lavoro principale.
    """
    args = parse_arguments()

    # Directory sorgente interna al pacchetto e destinazione in ~/.config
    script_dir = Path(__file__).parent
    internal_config_dir = script_dir / "config"
    home_config_dir = Path.home() / ".config" / "mark-it"
    home_style_default = home_config_dir / "Style.json"
    font_path = home_config_dir / "fonts"
    # Se l'utente chiede il reset O se la cartella in ~/.config non esiste ancora
    if args.reset or not home_config_dir.exists():
        if internal_config_dir.exists():
            # Copia ricorsivamente tutta la cartella 'config' (stili, font, ecc.)
            shutil.copytree(internal_config_dir, home_config_dir, dirs_exist_ok=True)
            print(f"Configurazione inizializzata/ripristinata in: {home_config_dir}")
        else:
            print("Avviso: Cartella 'config' interna al pacchetto non trovata. Impossibile copiare i file di default.")

    # Gestione dello stile
    if args.style is None:
        args.style = str(home_style_default)
    else:
        # Se viene passato solo un nome file (es. -s stile2.json) e non esiste nella cartella corrente
        if not os.path.exists(args.style) and Path(args.style).parent == Path('.'):
            potential_style = home_config_dir / args.style
            if potential_style.exists():
                args.style = str(potential_style)

    execute_parser(args,font_path)

def portable():
    """Entry point per la versione PORTABLE (lanciato come script).
    
    Legge i file direttamente dalla cartella 'config' locale al file python.
    """
    args = parse_arguments()

    # Directory config locale allo script
    script_dir = Path(__file__).parent
    local_config_dir = script_dir / "config"
    font_path = local_config_dir / "fonts"
    local_style_default = local_config_dir / "Style.json"

    # Gestione dello stile
    if args.style is None:
        args.style = str(local_style_default)
    else:
        # Se viene passato solo un nome file e non esiste nella cartella corrente
        if not os.path.exists(args.style) and Path(args.style).parent == Path('.'):
            potential_style = local_config_dir / args.style
            if potential_style.exists():
                args.style = str(potential_style)

    if args.reset:
        print("Modalità Portable: il flag --reset non ha effetto poiché si usano i file locali.")

    execute_parser(args, font_path)

if __name__ == "__main__":
    # Quando viene eseguito direttamente come script (`python nomefile.py`), parte in modalità portable
    portable()