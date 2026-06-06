"""Build providers from environment variables.

Only providers whose required env vars are present are activated, so you can
start with two (e.g. HubSpot + Folk) and add Apple later.
"""

from __future__ import annotations

import os

from .providers import AppleContactsProvider, FolkProvider, HubSpotProvider, Provider


def providers_from_env(env: dict | None = None) -> list[Provider]:
    env = env or dict(os.environ)
    providers: list[Provider] = []

    if env.get("HUBSPOT_TOKEN"):
        providers.append(HubSpotProvider(env["HUBSPOT_TOKEN"]))

    if env.get("FOLK_TOKEN"):
        providers.append(FolkProvider(env["FOLK_TOKEN"]))

    if env.get("APPLE_CARDDAV_URL") and env.get("APPLE_USERNAME") and env.get("APPLE_PASSWORD"):
        providers.append(
            AppleContactsProvider(
                env["APPLE_CARDDAV_URL"], env["APPLE_USERNAME"], env["APPLE_PASSWORD"]
            )
        )

    return providers
