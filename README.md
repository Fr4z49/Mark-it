# Mark-IT ver. 0.2.3

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
Strikethrough: _-this text is crossed out-_
Underline: __this text is crossed out__
Inline code:   `this is inline code`
```

> Each formatting type has exactly one delimiter — no alternatives.

### Special Blockquotes

```
>n This is a Note
>t This is a Tip
>i This is Important
>w This is a Warning
>c This is a Caution
```

### Images

```
!(image_path)[size]
```

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
| `-s style` | Path to a custom `style.json` file |
| `-r` | Reset configuration to defaults (AUR only) |

---

## Configuration

Mark-IT is configured via `style.json`. Depending on your installation:

| Installation | Config location |
| :----------- | :-------------- |
| AUR | `~/.config/mark-it/` |
| Portable | `Mark-it/markit/config/` |

Options include margins, colors, font sizes, and custom font imports. The default config file is well-commented and self-explanatory.

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
| Tables                | Work in progress                            |
| Ordered lists         | Not implemented yet                         |
| Footnotes             | Not implemented yet                         |

