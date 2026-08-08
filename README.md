# Mark-IT ver. 0.2.4

> A Markdown-like markup format and CLI tool for fast note-taking with direct PDF export.

---

## What is Mark-IT?

Mark-IT is a lightweight markup format and CLI tool that converts `.mi` files into a single-page PDF — without going through HTML or CSS as an intermediate step.

Most Markdown-to-PDF converters work by first converting Markdown to HTML, then rendering that HTML to PDF. This made sense historically, since Markdown was originally designed for the web.

Mark-IT takes a different approach: it targets PDF directly, using a pure Python pipeline with a single external library. This unlocks layout options that HTML/CSS can't easily provide — like the continuous single-page format Mark-IT uses by default — while keeping the tool lightweight and portable.

---

## Features

- **Direct PDF generation** — no HTML/CSS intermediate step
- **Single long-page format** — the default layout is a continuous page, not paginated
- **Lightweight** — the entire PDF pipeline is written in Python and requires only one library, making it easy to run directly from a USB drive
- **Customizable** — fonts, colors, margins, and more can be configured via `style.json`

---

## Mark-IT vs Markdown

Mark-IT uses a syntax inspired by Markdown, but it is a distinct format. The differences are intentional and designed for note-taking speed.

### Headers

```
# Header 1   (or: #1 Header 1)
#2 Header 2
#3 Header 3
```

> Mark-IT ships with three header levels by default. More can be added in `style.json`.

### Inline Formatting

```
Bold:      **this text is bold**
Italic:    \\this text is italic\\
Highlight: ==This text is Highlighted==
Strikethrough: _-this text is crossed out-_
Underline: __this text is crossed out__
Inline code:   `this is inline code`
```

> Each formatting type has exactly one delimiter — no alternatives.

### Special Blockquotes

```
> Normal blockquote (default gray)
>n This is a Note (default Blue)
>t This is a Tip (default Green)
>i This is Important (default purple)
>w This is a Warning (default yellow)
>c This is a Caution  (default Red)
```

> Colors can be changed in the `Style.json`

### Images

```
!(image_path)[size]
```

### Links:

```
(Link text)^https://www.google.com/
```



### Tables

```
|row1|cell2|cell3|
|row2|cell2|cell3|
```
> Tables are Still buggy and can go outside the page if they're too long.

### Important: blank lines between elements

You **must** leave a blank line between different types of elements (paragraphs, blockquotes, lists, etc.). Without it, the content will be treated as a continuation of the previous element.

---

## Installation

### From Source (Linux, macOS, Windows)

```bash
# 1. Clone the beta branch
git clone --branch beta --single-branch https://github.com/Fr4z49/Mark-it.git
cd Mark-it

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Linux/macOS
# venv\Scripts\Activate.ps1       # Windows (PowerShell)

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run Mark-IT
python main.py
```

### Arch Linux (AUR)

```bash
yay -S markit-git
```

---

## Usage

### AUR installation

```
markit input.mi [-o output] [-s style] [-r]
```

### Portable (from the Mark-IT folder)

```bash
python3 markit.py input.mi [-o output] [-s style]
```

On Linux you can also run it directly:

```bash
./markit.py input.mi [-o output] [-s style]
```

| Flag | Description |
| :--- | :---------- |
| `-o output` | Output file path (defaults to input filename with `.pdf` extension) |
| `-n name` | Output Name of the file (defaults to input filename, you shouldn't need to touch this)|
| `-s style` | Path to a custom `style.json` file |
| `-r` | Reset configuration to defaults (AUR only) (deprecated) |

---

## Configuration

Mark-IT is configured via `style.json`. Depending on your installation:

| Installation | Config location |
| :----------- | :-------------- |
| AUR | `~/.config/mark-it/` |
| Portable | `Mark-it/markit/config/` |

Options include margins, colors, font sizes, and custom font imports. The default config file is well-commented and self-explanatory.

- **default output path**: 
If left blank it defaults to input path, otherwise you can set an absolute path (mostly used when markit is installed with aur) or a relative path leading to a directory two folders above the main script (useful when using markit in a portable way). 

---

## Feature Status

| Feature               | Status                                      |
| :-------------------- | :------------------------------------------ |
| Inline formatting     | Working (nesting not supported yet)         |
| Headers               | Working                                     |
| Blockquotes           | Working                                     |
| Multiline code blocks | Working                                     |
| Unordered lists       | Working                                     |
| Task lists            | Working                                     |
| Paragraphs            | Working                                     |
| Links                 | Working                                     |
| Horizontal separators | Working                                     |
| Images                | Partial                                     |
| Character escapes     | Partial                                     |
| Tables                | Partial                                     |
| Ordered lists         | Not implemented yet                         |
| Footnotes             | Not implemented yet                         |

