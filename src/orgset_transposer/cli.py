from __future__ import annotations

import argparse
import csv
import logging
import sys
from pathlib import Path
from typing import Iterable, Optional

import pandas as pd

LOGGER = logging.getLogger("orgset_transposer")


def build_parser() -> argparse.ArgumentParser:
    description = (
        "Transpose a CSV file that contains orgsets into a wide matrix. "
        "One row is created per orgset, one column per field, and multiple values "
        "for the same orgset/field are joined into a single cell."
    )

    epilog = (
        "Examples:\n"
        "  python -m orgset_transposer.cli -i input.csv -o output.csv \\\n"
        "    --orgset-col A --field-col C --value-col D --delimiter ';' --no-header\n\n"
        "  python -m orgset_transposer.cli -i input.csv -o output.xlsx \\\n"
        "    --orgset-col 1 --field-col 3 --value-col 4 --empty-placeholder \"' '\" -vv\n\n"
        "Column references may be provided as Excel letters (A, C, D), 1-based numbers (1, 3, 4),\n"
        "or header names when the input file contains a header row."
    )

    parser = argparse.ArgumentParser(
        prog="orgset-transposer",
        description=description,
        formatter_class=argparse.RawTextHelpFormatter,
        epilog=epilog,
    )

    parser.add_argument("-i", "--input", required=True, help="Path to the input CSV file.")
    parser.add_argument(
        "-o",
        "--output",
        required=True,
        help="Path to the output file. Supported extensions: .csv, .xlsx",
    )
    parser.add_argument(
        "--delimiter",
        default=";",
        help="CSV delimiter used in the input file. Default: ';'",
    )
    parser.add_argument(
        "--encoding",
        default="utf-8-sig",
        help="Input/output text encoding for CSV files. Default: utf-8-sig",
    )
    parser.add_argument(
        "--header-row",
        type=int,
        default=None,
        help=(
            "0-based row index of the header row in the input CSV. "
            "If omitted, the file is treated as having no header."
        ),
    )
    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Explicitly treat the file as having no header row. This is the default behavior.",
    )
    parser.add_argument(
        "--orgset-col",
        default="A",
        help="Column for the orgset name. Accepts A / 1 / header_name. Default: A",
    )
    parser.add_argument(
        "--field-col",
        default="C",
        help="Column for the field name. Accepts C / 3 / header_name. Default: C",
    )
    parser.add_argument(
        "--value-col",
        default="D",
        help="Column for the field value. Accepts D / 4 / header_name. Default: D",
    )
    parser.add_argument(
        "--join-separator",
        default=", ",
        help="Separator used when multiple values are joined into one cell. Default: ', '",
    )
    parser.add_argument(
        "--empty-placeholder",
        default=None,
        help="Optional placeholder used for empty output cells, for example: \"' '\"",
    )
    parser.add_argument(
        "--sort-columns",
        action="store_true",
        help="Sort output columns alphabetically after the orgset column.",
    )
    parser.add_argument(
        "--keep-input-order",
        action="store_true",
        help="Keep the input order of orgsets and fields where possible.",
    )
    parser.add_argument(
        "--quote-all-csv",
        action="store_true",
        help="When writing CSV output, quote all fields instead of using minimal quoting.",
    )
    parser.add_argument(
        "--log-file",
        help="Optional path to a log file. Useful for batch runs or troubleshooting.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="count",
        default=0,
        help="Increase logging verbosity (-v = INFO, -vv = DEBUG).",
    )

    return parser


def configure_logging(verbose: int, log_file: Optional[str] = None) -> None:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG

    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    if log_file:
        handlers.append(logging.FileHandler(log_file, encoding="utf-8"))

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=handlers,
    )


def excel_letters_to_index(value: str) -> int:
    result = 0
    for char in value.upper():
        if not ("A" <= char <= "Z"):
            raise ValueError(f"Invalid Excel column reference: {value!r}")
        result = result * 26 + (ord(char) - ord("A") + 1)
    return result - 1


def resolve_column_reference(reference: str, columns: Iterable[str]) -> str:
    columns_list = list(columns)
    if reference in columns_list:
        return reference

    ref = str(reference).strip()
    if ref.isdigit():
        idx = int(ref) - 1
        if idx < 0 or idx >= len(columns_list):
            raise ValueError(
                f"Column number {reference!r} is out of range. Available columns: 1-{len(columns_list)}"
            )
        return columns_list[idx]

    if ref.isalpha():
        idx = excel_letters_to_index(ref)
        if idx < 0 or idx >= len(columns_list):
            raise ValueError(
                f"Column letter {reference!r} is out of range. Available columns: A-{index_to_excel_letters(len(columns_list)-1)}"
            )
        return columns_list[idx]

    raise ValueError(
        f"Could not resolve column reference {reference!r}. Use a header name, a 1-based number, or Excel letters."
    )


def index_to_excel_letters(index: int) -> str:
    if index < 0:
        raise ValueError("Index must be >= 0")
    result = []
    n = index + 1
    while n > 0:
        n, remainder = divmod(n - 1, 26)
        result.append(chr(ord("A") + remainder))
    return "".join(reversed(result))


def read_input_csv(path: Path, delimiter: str, encoding: str, header_row: Optional[int]) -> pd.DataFrame:
    LOGGER.info("Reading input file: %s", path)
    header = header_row if header_row is not None else None
    df = pd.read_csv(
        path,
        sep=delimiter,
        encoding=encoding,
        header=header,
        dtype=str,
        keep_default_na=False,
    )

    if header is None:
        df.columns = [f"Column{idx+1}" for idx in range(len(df.columns))]

    LOGGER.debug("Input shape: %s", df.shape)
    LOGGER.debug("Input columns: %s", list(df.columns))
    return df


def transpose_orgsets(
    df: pd.DataFrame,
    orgset_col_ref: str,
    field_col_ref: str,
    value_col_ref: str,
    join_separator: str,
    empty_placeholder: Optional[str],
    sort_columns: bool,
    keep_input_order: bool,
) -> pd.DataFrame:
    orgset_col = resolve_column_reference(orgset_col_ref, df.columns)
    field_col = resolve_column_reference(field_col_ref, df.columns)
    value_col = resolve_column_reference(value_col_ref, df.columns)

    LOGGER.info(
        "Using columns -> orgset: %s | field: %s | value: %s",
        orgset_col,
        field_col,
        value_col,
    )

    work = df[[orgset_col, field_col, value_col]].copy()
    work.columns = ["Orgset", "Field", "Value"]

    initial_rows = len(work)
    work = work[
        (work["Orgset"].astype(str).str.strip() != "")
        & (work["Field"].astype(str).str.strip() != "")
    ].copy()
    removed_rows = initial_rows - len(work)
    if removed_rows:
        LOGGER.warning("Removed %s rows with empty orgset or field values.", removed_rows)

    if keep_input_order:
        grouped = (
            work.groupby(["Orgset", "Field"], sort=False, dropna=False)["Value"]
            .apply(lambda s: join_separator.join(v for v in s.astype(str)))
            .reset_index()
        )
        field_order = pd.unique(grouped["Field"])
        result = grouped.pivot(index="Orgset", columns="Field", values="Value")
        result = result.reindex(columns=field_order)
    else:
        grouped = (
            work.groupby(["Orgset", "Field"], dropna=False)["Value"]
            .apply(lambda s: join_separator.join(v for v in s.astype(str)))
            .reset_index()
        )
        result = grouped.pivot(index="Orgset", columns="Field", values="Value")

    result = result.reset_index()
    result.columns.name = None

    if sort_columns:
        fixed = ["Orgset"]
        other_cols = sorted(col for col in result.columns if col != "Orgset")
        result = result[fixed + other_cols]

    if empty_placeholder is not None:
        result = result.fillna(empty_placeholder)

    LOGGER.info("Output shape: %s", result.shape)
    return result


def write_output(df: pd.DataFrame, output_path: Path, encoding: str, quote_all_csv: bool) -> None:
    LOGGER.info("Writing output file: %s", output_path)
    suffix = output_path.suffix.lower()

    if suffix == ".csv":
        quoting = csv.QUOTE_ALL if quote_all_csv else csv.QUOTE_MINIMAL
        df.to_csv(output_path, index=False, encoding=encoding, quoting=quoting)
    elif suffix == ".xlsx":
        df.to_excel(output_path, index=False)
    else:
        raise ValueError("Unsupported output format. Use .csv or .xlsx")


def validate_args(args: argparse.Namespace) -> None:
    input_path = Path(args.input)
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    if input_path.is_dir():
        raise IsADirectoryError(f"Input path points to a directory, not a file: {input_path}")

    output_path = Path(args.output)
    if output_path.suffix.lower() not in {".csv", ".xlsx"}:
        raise ValueError("Output file must end with .csv or .xlsx")

    if args.header_row is not None and args.header_row < 0:
        raise ValueError("--header-row must be >= 0")

    if args.header_row is not None and args.no_header:
        raise ValueError("Use either --header-row or --no-header, not both.")


def main(argv: Optional[list[str]] = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        validate_args(args)
        configure_logging(args.verbose, args.log_file)

        input_path = Path(args.input)
        output_path = Path(args.output)

        header_row = args.header_row
        if args.no_header:
            header_row = None

        df = read_input_csv(
            path=input_path,
            delimiter=args.delimiter,
            encoding=args.encoding,
            header_row=header_row,
        )

        result = transpose_orgsets(
            df=df,
            orgset_col_ref=args.orgset_col,
            field_col_ref=args.field_col,
            value_col_ref=args.value_col,
            join_separator=args.join_separator,
            empty_placeholder=args.empty_placeholder,
            sort_columns=args.sort_columns,
            keep_input_order=args.keep_input_order,
        )

        write_output(
            df=result,
            output_path=output_path,
            encoding=args.encoding,
            quote_all_csv=args.quote_all_csv,
        )

        LOGGER.warning("Done. Wrote %s rows and %s columns to %s", len(result), len(result.columns), output_path)
        return 0
    except Exception as exc:  # pragma: no cover - CLI surface
        if args.verbose >= 2:
            LOGGER.exception("Processing failed: %s", exc)
        else:
            logging.getLogger("orgset_transposer").error("Processing failed: %s", exc)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
