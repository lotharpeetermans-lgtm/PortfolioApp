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

    posities = []

    for ticker in df["ticker"].unique():

        subset = df[
            df["ticker"] == ticker
        ]

        gekocht = subset[
            subset["type"] == "KOOP"
        ]

        verkocht = subset[
            subset["type"] == "VERKOOP"
        ]

        totaal_gekocht = gekocht[
            "aantal"
        ].sum()

        totaal_verkocht = verkocht[
            "aantal"
        ].sum()

        open_aantal = (
            totaal_gekocht -
            totaal_verkocht
        )

        if open_aantal <= 0:
            continue

        totale_kost = (
            gekocht["aantal"]
            * gekocht["prijs"]
        ).sum()

        gemiddelde_prijs = (
            totale_kost
            / totaal_gekocht
        )

        posities.append(
            {
                "Ticker": ticker,
                "Aantal": round(
                    open_aantal,
                    2
                ),
                "Gem. aankoopprijs": round(
                    gemiddelde_prijs,
                    2
                ),
                "Kostbasis": round(
                    open_aantal *
                    gemiddelde_prijs,
                    2
                )
            }
        )

    return pd.DataFrame(
        posities
    )
