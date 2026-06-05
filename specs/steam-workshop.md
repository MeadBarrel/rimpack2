# Steam Workshop Spec

## Scope

`rimpack.steamworks` wraps the Steamworks Python client and resolves RimWorld Workshop IDs into local mod folders.

## Workshop ID Coercion

`coerce_workshop_item_id(value)` accepts:

- positive integers
- numeric strings
- Steam sharedfiles URLs like `https://steamcommunity.com/sharedfiles/filedetails/?id=...`

It rejects empty, non-numeric, and non-positive values with `ValueError`.

## Steamworks Availability

`is_steamworks_available()` returns whether the Steamworks module can be imported and prepared.

Client creation:

- imports `steamworks`, or installs a shim from `steamworkspy`
- ensures native DLL search paths on Windows
- verifies required native files on Windows
- creates a temporary `steam_appid.txt` for RimWorld when absent
- calls `initialize` or `Initialize` on the client

Expected failures raise `SteamworksUnavailableError`.

## Subscriptions

`Steamworks.subscribe(workshop_id)` delegates to a Workshop subscribe operation.

`Steamworks.unsubscribe(workshop_id)` delegates to a Workshop unsubscribe operation.

Supported client method layouts include:

- direct methods such as `Workshop_SubscribeItem`
- `client.Workshop.SubscribeItem`
- fallback snake_case method names

If Steamworks returns `False`, raise `SteamworksSubscriptionError`.

## Resolving A Mod

`resolve_rimworld_workshop_mod_by_id(steamworks, workshop_root, workshop_id, unsubscribe=False)`:

- coerces the Workshop ID
- checks `<workshop_root>/<id>` first
- returns immediately if a valid mod folder already exists
- subscribes through Steamworks when the mod is not already present
- waits up to `WORKSHOP_RESOLVE_TIMEOUT_SECONDS`
- polls every `WORKSHOP_RESOLVE_POLL_INTERVAL_SECONDS`
- returns a loaded `ModFolder` once `About/About.xml` exists and parses
- raises `SteamworksError` if the deadline expires
- unsubscribes only when `unsubscribe=True` and the mod did not pre-exist

Tests should fake the Steamworks object and write fixture files into a temporary workshop root.
