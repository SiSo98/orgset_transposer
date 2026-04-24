from orgset_transposer.cli import transpose_orgsets
import pandas as pd


def test_transpose_orgsets_basic_join():
    df = pd.DataFrame(
        {
            "Column1": ["BKP001", "BKP001", "BKP001", "BKP002"],
            "Column3": ["$WERKS", "$WERKS", "$CONGR", "$WERKS"],
            "Column4": ["4150", "5956", "A1", "7000"],
        }
    )

    result = transpose_orgsets(
        df=df,
        orgset_col_ref="Column1",
        field_col_ref="Column3",
        value_col_ref="Column4",
        join_separator=", ",
        empty_placeholder="' '",
        sort_columns=True,
        keep_input_order=False,
    )

    assert list(result.columns) == ["Orgset", "$CONGR", "$WERKS"]
    assert result.loc[result["Orgset"] == "BKP001", "$WERKS"].iloc[0] == "4150, 5956"
    assert result.loc[result["Orgset"] == "BKP002", "$CONGR"].iloc[0] == "' '"
