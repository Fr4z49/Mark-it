#!/usr/bin/env python3

import argparse
from  Pdf_printer import generate_pdf 

parser = argparse.ArgumentParser()

parser.add_argument("input")
parser.add_argument("-o", "--output")
parser.add_argument("-s", "--style")

args = parser.parse_args()

if args.output is None:
    args.output = args.input +".pdf"

if args.style is None:
    args.style = "Style.json"


if args.output[-4:] != ".pdf":
    args.output += ".pdf"
if args.input[-3:] != ".mi":
    args.input += ".mi"
if args.style[-5:] != ".json":
    args.style += ".json"

print(f"input: {args.input}")
print(f"output: {args.output}")
print(f"stile: {args.style}")


generate_pdf(args.input, args.output, args.style)

