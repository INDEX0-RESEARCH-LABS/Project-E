# Run artifacts

Each folder is one immutable run: `<UTC timestamp>_<config checksum prefix>`.

`summary.json` records the resolved mission, targets, per-architecture metrics,
config checksum, git commit, and software versions. `provenance.csv` records
where every parameter came from. `report.md` is the human-readable output.

## Which runs are current

Only runs whose config checksum matches the current config are comparable.
Earlier runs are retained as history, not deleted. In particular, runs before
`20261022T181859Z` used a model that omitted converter mass and supercapacitor
volume; their masses are 9–12 kg lower and must not be quoted.

| Run | Config | Current? |
|---|---|---|
| `20261022T181859Z_9c00c799` | baseline | yes |
| `20261022T181904Z_2300c6ab` | conservative | yes |
| `20261022T181913Z_df1cb11b` | optimistic | yes |
| earlier `20261022T18*` | baseline/scenarios, pre-fix | no |

Never overwrite a run folder. Rerunning with the same config creates a new
timestamped folder with the same checksum.
