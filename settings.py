"""Réglages par conversation (mode, debug), stockés dans Supabase.

Variables d'environnement :
    SUPABASE_URL          ex. https://kvslcdvandyqlalvmwkx.supabase.co
    SUPABASE_SECRET_KEY   clé secrète (sb_secret_... ou ancienne clé service_role)

La table `public.user_settings` a la sécurité RLS activée sans politique :
seule la clé secrète peut y accéder. Ne mets jamais cette clé dans le dépôt
ni dans une application côté client.

Sans ces variables, les réglages restent en mémoire (perdus au redémarrage).
"""
import logging
import os

import httpx

log = logging.getLogger("alice.settings")

DEFAULTS = {"mode": "pivot", "debug": False}
FIELDS = tuple(DEFAULTS)


class SettingsStore:
    def __init__(self, url=None, key=None):
        url = url or os.environ.get("SUPABASE_URL")
        key = key or os.environ.get("SUPABASE_SECRET_KEY")
        self._cache: dict[int, dict] = {}
        self._client = None
        if url and key:
            headers = {"apikey": key, "Content-Type": "application/json"}
            if not key.startswith("sb_"):  # anciennes clés JWT : aussi dans Authorization
                headers["Authorization"] = f"Bearer {key}"
            self._client = httpx.AsyncClient(
                base_url=url.rstrip("/") + "/rest/v1", headers=headers, timeout=10)

    @property
    def persistent(self):
        return self._client is not None

    async def check(self):
        """Vérifie la connexion à Supabase au démarrage (lève une erreur sinon)."""
        if self._client:
            r = await self._client.get("/user_settings", params={"select": "chat_id", "limit": "1"})
            r.raise_for_status()

    async def get(self, chat_id: int) -> dict:
        if chat_id in self._cache:
            return self._cache[chat_id]
        settings = dict(DEFAULTS)
        if self._client:
            try:
                r = await self._client.get("/user_settings", params={
                    "chat_id": f"eq.{chat_id}", "select": ",".join(FIELDS)})
                r.raise_for_status()
                if r.json():
                    settings.update(r.json()[0])
            except httpx.HTTPError:
                log.exception("Lecture Supabase impossible, réglages par défaut utilisés")
                return settings  # pas de mise en cache : on réessaiera
        self._cache[chat_id] = settings
        return settings

    async def update(self, chat_id: int, **changes) -> dict:
        settings = {**await self.get(chat_id), **changes}
        self._cache[chat_id] = settings
        if self._client:
            try:
                r = await self._client.post(
                    "/user_settings",
                    params={"on_conflict": "chat_id"},
                    headers={"Prefer": "resolution=merge-duplicates,return=minimal"},
                    json={"chat_id": chat_id, **{k: settings[k] for k in FIELDS}},
                )
                r.raise_for_status()
            except httpx.HTTPError:
                log.exception("Écriture Supabase impossible (réglage gardé en mémoire)")
        return settings

    async def close(self):
        if self._client:
            await self._client.aclose()
