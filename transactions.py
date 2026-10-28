from supabase_client import supabase
import pandas as pd
import yfinance as yf

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

def verrijk_posities_met_koersen(posities_df):

    if posities_df.empty:
        return posities_df

    actuele_koersen = []
    marktwaarde = []
    winst_verlies = []
    rendement = []

    for _, row in posities_df.iterrows():

        try:

            ticker = yf.Ticker(
                row["Ticker"]
            )

            koers = float(
                ticker.fast_info["lastPrice"]
            )

        except:

            koers = 0

        actuele_koersen.append(
            round(koers, 2)
        )

        waarde = (
            koers *
            row["Aantal"]
        )

        marktwaarde.append(
            round(waarde, 2)
        )

        winst = (
            waarde -
            row["Kostbasis"]
        )

        winst_verlies.append(
            round(winst, 2)
        )

        rendement_pct = (
            winst /
            row["Kostbasis"]
            * 100
            if row["Kostbasis"] > 0
            else 0
        )

        rendement.append(
            round(
                rendement_pct,
                2
            )
        )

    posities_df["Koers"] = actuele_koersen
    posities_df["Marktwaarde"] = marktwaarde
    posities_df["Winst/Verlies"] = winst_verlies
    posities_df["Rendement %"] = rendement

    return posities_df


def verwijder_transactie(transactie_id):

    return (
        supabase.table("transactions")
        .delete()
        .eq("id", transactie_id)
        .execute()
    )
