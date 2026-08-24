# Vehicle profiles

Place immutable, reviewed system-identification outputs here as `<vehicle_id>-<version>.json`.
Generate them with `scripts/identify_vehicle_parameters.py`; parameters that cannot be identified from
the provided channels remain `null` with a false validity flag. Do not hand-fill missing fitted values.

Unity's `VehicleProfileLoader` applies only parameters whose validity flag is true. Review and sign a
profile before assigning it to a wet-test build.
