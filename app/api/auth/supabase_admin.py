import httpx

from app.api.core.config import PROJECT_URL, SUPABASE_SERVICE_ROLE_KEY


class SupabaseAdminError(Exception):
    pass


async def delete_auth_user(supabase_user_id) -> None:
    """Delete a user from Supabase auth.users via the admin API.

    Idempotent only when Supabase explicitly reports the user does not exist —
    a generic 404 (e.g. wrong URL) raises so we don't silently mask config bugs.
    """
    base = PROJECT_URL.rstrip("/")
    url = f"{base}/admin/users/{supabase_user_id}"
    headers = {
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
    }

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.delete(url, headers=headers)
    except httpx.HTTPError as e:
        raise SupabaseAdminError(f"Network error contacting Supabase: {e}") from e

    if response.is_success:
        return

    if response.status_code == 404:
        try:
            body = response.json()
        except ValueError:
            body = {}
        if body.get("code") == "user_not_found":
            return

    raise SupabaseAdminError(
        f"Supabase admin delete failed ({response.status_code}): {response.text}"
    )
