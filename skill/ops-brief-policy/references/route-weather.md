# Route, Trip, and ROAD Weather Workflow

Load this reference only when a user changes travel state or the engine returns an active route-weather watch or travel action.

## Store routes

- `Routes` is the learned-route database. Use one stable `ROUTE-###` row per unordered endpoint pair.
- Match endpoints bidirectionally. A saved A → B route is the same route record as B → A.
- For a new endpoint pair, ask only for the preferred route overview if it is not already explicit. Store it in the matching direction. Do not create a second reversed route row.
- If Route B → A is blank, the policy engine reverses the A → B segment order. Store a distinct reverse overview only when the user drives it differently.
- Store average runtimes directionally. A missing reverse runtime may use the opposite runtime as a labeled fallback until the user supplies a better value.
- Explicit user route/runtime changes outrank prior records. Retire obsolete route records with `Status: Retired`; never delete them.

## Store trips and corridor watches

- `Trips` preserves planned, active, arrived, and cancelled trip history. Never delete completed rows.
- Use `Planned` when armed before departure, `Active` after the user says they left, `Arrived` on arrival, and `Cancelled` when abandoned.
- A known route plus departure can derive ETA from its directional average. Write the resulting ETA and `ETA Source`. An explicit user ETA always wins.
- For a new origin/destination pair, capture the route overview and add/update `Routes` before or with the trip.
- A road-section watch such as “I-80 across Wyoming for 12 hours” may use `Route Override` without endpoints or a destination ETA.
- `Weather Watch` is `Off`, `Active`, or `Pending Expiry`. A watch needs an explicit expiry or destination ETA; ETA is the default expiry. If neither exists, set `Pending Expiry`, ask for one immediately, and let the engine repeat the request on each ROAD brief.
- Watch expiry is exclusive. At or after it, monitoring is inactive and must not be mentioned. Set the row to `Off` on the next run.
- Default monitoring cadence is only 2:45 AM/PM Eastern. A separate faster automation requires an explicit user request and must expire with the watch.
- Record user-reported `Current Location` and `Location Time (ET)`. Never present a time-progress estimate as an observed location.

## Friday departure and Saturday checkpoint

- On the Friday 2:45 PM ROAD brief, use the engine's action to confirm the terminal destination unless a current Friday trip is already planned/active.
- Resolve any default origin, departure, usual destination, work shift, team/solo pattern, HOS constraints, and governed speed from live Travel Settings. Missing configuration produces a focused question; portable source supplies no personal route defaults.
- On the first configured checkpoint brief after departure, request a fresh current-location update for an active trip if the last observed location is missing or older than the configured freshness threshold.
- Do not equate governed speed with average speed and do not invent driver-level HOS timing. Stored route averages outrank naive distance/speed math.

## Inspect route weather

1. Scope the remaining corridor to the watch window. Use reported current location/time first; otherwise use departure, ETA, stored route, and `progress_fraction` only to identify an approximate corridor, clearly labeled as estimated.
2. Check current National Weather Service watches, warnings, advisories, forecasts, and radar/forecast discussion when useful.
3. Check each relevant official state DOT/511 source for closures, crashes, winter restrictions, chain laws, road-surface reports, flooding, high-wind restrictions, and other route impacts. Use another authoritative road source only when official 511/DOT coverage is unavailable.
4. Correlate hazard timing with when the truck is expected in that segment. Cover severe weather in every season: snow/ice/blowing snow, thunderstorms/tornadoes/hail, flash flooding, extreme wind, dust, heat, wildfire/smoke, or another material road hazard.
5. Prefer official, recent evidence. Distinguish observed closures/conditions from forecasts and uncertainty.

If clear, use one line such as `No material NWS alerts or DOT/511 restrictions along the monitored corridor through <time>.` If hazardous, lead with affected segment, expected encounter window, road impact, and the safest practical action. Do not drown the user in a general forecast.

## Render trip status

When the engine returns `trip_status`, place `TRIP STATUS` last. Include only known fields, ideally one line: `Current location — Destination — ETA`. If a current location, route overview, departure, ETA, or expiry is missing, render the corresponding engine action under `ACTION REQUIRED`; never invent it.
