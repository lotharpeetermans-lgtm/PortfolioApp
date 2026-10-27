import bcrypt

from supabase_client import supabase


def hash_password(password):

    return bcrypt.hashpw(
        password.encode(),
        bcrypt.gensalt()
    ).decode()


def verify_password(
    password,
    hashed
):

    return bcrypt.checkpw(
        password.encode(),
        hashed.encode()
    )


def registreer_gebruiker(
    naam,
    email,
    wachtwoord
):

    password_hash = hash_password(
        wachtwoord
    )

    return (
        supabase
        .table("users")
        .insert(
            {
                "naam": naam,
                "email": email,
                "password_hash": password_hash
            }
        )
        .execute()
    )


def login_user(
    email,
    wachtwoord
):

    response = (
        supabase
        .table("users")
        .select("*")
        .eq("email", email)
        .execute()
    )

    if not response.data:
        return None

    gebruiker = response.data[0]

    if verify_password(
        wachtwoord,
        gebruiker["password_hash"]
    ):
        return gebruiker

    return None
