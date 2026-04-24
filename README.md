# orgset-transposer

A small local Python CLI tool that transposes SAP orgset CSV files into a wide matrix.

## Important disclosure

This project and its initial source code were generated with the help of AI and should be reviewed, tested, and approved by a human before productive use or publication.

## What the tool does

The tool reads a CSV file and converts it into this target structure:

- one **row** per orgset
- one **column** per field
- one **cell value** per orgset/field combination
- if multiple values exist for the same orgset and field, they are joined into a single cell using a separator such as `, `

Example input logic:

| Orgset | Field | Value |
|---|---|---|
| ORG_EAST | `$WERKS` | 1000 |
| ORG_EAST | `$WERKS` | 2000 |
| ORG_EAST | `$CONGR` | A1 |

Example output logic:

| Orgset | `$CONGR` | `$WERKS` |
|---|---|---|
| ORG_EAST | A1 | 1000, 2000 |

## Supported output formats

- `.csv`
- `.xlsx`

## Requirements

- Python 3.10+
- pip

## Installation

### Option 1: local run without packaging

```bash
python -m venv .venv
```

Activate the environment.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

macOS/Linux:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the tool:

```bash
python -m orgset_transposer.cli --help
```

### Option 2: install as CLI command

```bash
pip install .
orgset-transposer --help
```

## Typical usage

### CSV without header row, using columns A / C / D

```bash
python -m orgset_transposer.cli \
  --input sample_input.csv \
  --output sample_output.csv \
  --delimiter ";" \
  --no-header \
  --orgset-col A \
  --field-col C \
  --value-col D
```

### Same, but fill empty cells with `' '`

```bash
python -m orgset_transposer.cli \
  --input sample_input.csv \
  --output sample_output.xlsx \
  --delimiter ";" \
  --no-header \
  --orgset-col A \
  --field-col C \
  --value-col D \
  --empty-placeholder "' '"
```

### With logging and debug output

```bash
python -m orgset_transposer.cli \
  --input input.csv \
  --output output.csv \
  --delimiter ";" \
  --no-header \
  --orgset-col A \
  --field-col C \
  --value-col D \
  --empty-placeholder "' '" \
  --log-file run.log \
  -vv
```

## Parameter overview

| Parameter | Meaning |
|---|---|
| `-i`, `--input` | Path to the input CSV file |
| `-o`, `--output` | Path to the output file (`.csv` or `.xlsx`) |
| `--delimiter` | Input CSV delimiter. Default: `;` |
| `--encoding` | File encoding for CSV read/write. Default: `utf-8-sig` |
| `--header-row` | 0-based header row index if the input has a header |
| `--no-header` | Treat input as having no header row |
| `--orgset-col` | Orgset column reference: Excel letter, 1-based number, or header name |
| `--field-col` | Field column reference: Excel letter, 1-based number, or header name |
| `--value-col` | Value column reference: Excel letter, 1-based number, or header name |
| `--join-separator` | Separator used to join multiple values. Default: `, ` |
| `--empty-placeholder` | Placeholder for empty cells, e.g. `' '` |
| `--sort-columns` | Sort field columns alphabetically |
| `--keep-input-order` | Keep original field order if possible |
| `--quote-all-csv` | Quote all fields in CSV output |
| `--log-file` | Write log output to a file |
| `-v` | Info logging |
| `-vv` | Debug logging |

## Logging behavior

- default: warnings and errors only
- `-v`: adds informational messages
- `-vv`: adds debug messages
- `--log-file run.log`: writes logs to a file in addition to the console

## How column references work

You can reference columns in three ways:

1. Excel style: `A`, `C`, `D`
2. 1-based numeric: `1`, `3`, `4`
3. Header name: for example `OrgsetName`, `FieldName`, `Value`

## Notes for GitHub publication

Before publishing this repository, review the following:

1. Replace the placeholder in `LICENSE` and `pyproject.toml` with your own name.
2. Decide whether you want to keep the AI disclosure exactly as written.
3. The included `sample_input.csv` and `example_output.csv` are fictitious examples only.
4. Test the tool with your own files before productive use.
5. Add screenshots or CI later if you want a more polished public repository.

## Suggested repository structure

```text
orgset-transposer/
├── src/
│   └── orgset_transposer/
│       ├── __init__.py
│       └── cli.py
├── tests/
├── sample_input.csv
├── example_output.csv
├── .gitignore
├── LICENSE
├── pyproject.toml
├── README.md
└── requirements.txt
```

## Disclaimer

This tool is intended as a practical utility. It does not replace technical validation of SAP-specific downstream processing, interfaces, or import requirements.
