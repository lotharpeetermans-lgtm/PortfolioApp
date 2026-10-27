from supabase_client import supabase


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
