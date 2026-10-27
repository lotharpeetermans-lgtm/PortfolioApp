from supabase_client import supabase
import pandas as pd

def voeg_transactie_toe(
    user_id,
    datum,
    ticker,
    transactie_type,
    aantal,
    prijs,
    kosten
):

    return (
        supabase
        .table("transactions")
        .insert(
            {
                "user_id": user_id,
                "datum": datum,
                "ticker": ticker,
                "type": transactie_type,
                "aantal": aantal,
                "prijs": prijs,
                "kosten": kosten
            }
        )
        .execute()
    )


def haal_transacties_op(user_id):

    return (
        supabase
        .table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

def bereken_posities(user_id):

    response = (
        supabase
        .table("transactions")
        .select("*")
        .eq("user_id", user_id)
        .execute()
    )

    if not response.data:
        return pd.DataFrame()

    df = pd.DataFrame(response.data)

    df["signed_aantal"] = df.apply(
        lambda row:
        row["aantal"]
        if row["type"] == "KOOP"
        else -row["aantal"],
        axis=1
    )

    posities = (
        df.groupby("ticker")
        ["signed_aantal"]
        .sum()
        .reset_index()
    )

    posities = posities[
        posities["signed_aantal"] > 0
    ]

    posities.columns = [
        "Ticker",
        "Aantal"
    ]

    return posities
