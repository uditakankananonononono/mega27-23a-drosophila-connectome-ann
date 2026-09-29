# stage-c-data
Connectome graph exports for the Stage C grid (22MB, gitignored on main).
Workflow fetches via: git fetch origin stage-c-data --depth 1 && git checkout FETCH_HEAD -- exports/
Regenerate with code/stage_c/make_exports.py from the FlyWire v783 raw data (see DATA_INVENTORY.md on main).
