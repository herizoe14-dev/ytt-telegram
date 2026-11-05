"""Réglages par conversation (mode, debug), stockés dans Supabase.

Variables d'environnement (voir .env.example) :
    SUPABASE_URL              ex. https://kvslcdvandyqlalvmwkx.supabase.co
    SUPABASE_PUBLISHABLE_KEY  clé publique du projet (sb_publishable_...)
    SUPABASE_BOT_SECRET       secret du bot, vérifié côté base de données

La table `public.user_settings` n'est pas accessible directement avec la clé
publique : le bot passe par les fonctions `get_user_settings` et
`set_user_settings`, qui refusent tout appel sans le bon SUPABASE_BOT_SECRET
(la base n'en garde que l'empreinte SHA-256). Ne mets jamais ce secret dans
le dépôt.

Sans ces variables, les réglages restent en mémoire (perdus au redémarrage).
"""
import logging
import os

import httpx

log = logging.getLogger("alice.settings")

DEFAULTS = {"mode": "direct", "debug": False}


class SettingsStore:
    def __init__(self, url=None, key=None, bot_secret=None):
        url = url if url is not None else os.environ.get("SUPABASE_URL")
        key = key if key is not None else os.environ.get("SUPABASE_PUBLISHABLE_KEY")
        self._secret = bot_secret if bot_secret is not None else os.environ.get("SUPABASE_BOT_SECRET")
        self._cache: dict[int, dict] = {}
        self._client = None
        if url and key and self._secret:
            headers = {"apikey": key, "Content-Type": "application/json"}
            if not key.startswith("sb_"):  # ancienne clé « anon » (JWT)
                headers["Authorization"] = f"Bearer {key}"
            self._client = httpx.AsyncClient(
                base_url=url.rstrip("/") + "/rest/v1/rpc", headers=headers, timeout=10)

    @property
    def persistent(self):
        return self._client is not None

    async def _rpc(self, name, **params):
        r = await self._client.post(f"/{name}", json={"p_bot_secret": self._secret, **params})
        if r.is_error:
            raise httpx.HTTPStatusError(f"{name}: {r.status_code} {r.text}", request=r.request, response=r)
        return r.json() if r.content else None

    async def check(self):
        """Vérifie la connexion et le secret au démarrage (lève une erreur sinon)."""
        if self._client:
            await self._rpc("get_user_settings", p_chat_id=0)

    async def get(self, chat_id: int) -> dict:
        if chat_id in self._cache:
            return self._cache[chat_id]
        settings = dict(DEFAULTS)
        if self._client:
            try:
                row = await self._rpc("get_user_settings", p_chat_id=chat_id)
                if row:
                    settings.update({k: row[k] for k in DEFAULTS if k in row})
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
                await self._rpc("set_user_settings", p_chat_id=chat_id,
                                p_mode=settings["mode"], p_debug=settings["debug"])
            except httpx.HTTPError:
                log.exception("Écriture Supabase impossible (réglage gardé en mémoire)")
        return settings

    async def close(self):
        if self._client:
            await self._client.aclose()
