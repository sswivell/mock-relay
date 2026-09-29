# CLI reference

    mockrelay [--version] <command> [options]

Run `mockrelay` with no command to start a server, which is the same as
`mockrelay serve`.

## serve

    mockrelay serve
    mockrelay serve --mode replay
    mockrelay serve --latency 200

| Flag | Default | Purpose |
|---|---|---|
| `--config` | `mockrelay.yaml` | config file to read |
| `-m`, `--mode` | from config | `record`, `replay`, `passthrough`, or `hybrid` |
| `-l`, `--latency` | from config | artificial delay, in milliseconds |

## record

    mockrelay record
    mockrelay record --latency 50

Record mode only, regardless of what the config says.

## replay

    mockrelay replay
    mockrelay replay --latency 150

Replay mode only. Nothing reaches the network.

## list

    mockrelay list
    mockrelay list --upstream gh
    mockrelay list --json

| Flag | Default | Purpose |
|---|---|---|
| `--config` | `mockrelay.yaml` | config file to read |
| `-u`, `--upstream` | all | limit to one upstream |
| `--json` | off | emit machine-readable JSON |

## stats

Count what has been recorded, grouped by upstream: fixture count, bytes on
disk, the methods and statuses seen, and the recording window.

    mockrelay stats
    mockrelay stats --upstream gh
    mockrelay stats --json

An unreadable fixture is counted as a problem rather than skipped silently.

## clean

Remove fixtures older than a cutoff. The age comes from the fixture's
`recorded_at`, falling back to the file's modification time when it has
none, which is what an old hand-written fixture has.

    mockrelay clean --older-than 30
    mockrelay clean --older-than 30 --yes
    mockrelay clean --older-than 7 --upstream gh --yes

| Flag | Default | Purpose |
|---|---|---|
| `--config` | `mockrelay.yaml` | config file to read |
| `-u`, `--upstream` | all | limit to one upstream |
| `--older-than` | `30` | age in days; older fixtures are removed |
| `--yes` | off | actually delete; without it this is a preview |
| `--json` | off | emit machine-readable JSON |

Without `--yes` this prints what it would remove and deletes nothing.

## validate

Check a config file and the fixture tree beside it without starting a
server or reaching the network. Reports a setting that is wrong, a config
file that cannot be read or parsed, and each fixture that cannot be read or
does not have the shape the loader expects.

    mockrelay validate
    mockrelay validate --config path/to/mockrelay.yaml
    mockrelay validate --json

Exit code `4` means something was wrong, so a CI step can gate on it:

    mockrelay validate || exit 1

Unlike `serve`, `validate` treats a named config file that does not exist
as a failure rather than falling back to defaults.

## match

Preview how a request would be matched against the stored fixtures, without
starting a server. Every candidate is listed with a per-check breakdown of
method, path, query, and body.

    mockrelay match /v1/users
    mockrelay match /orders -m POST -b '{"total":500}'
    mockrelay match /users -q page=2 -q sort=asc
    mockrelay match /users -u gh
    mockrelay match /users --json

| Flag | Default | Purpose |
|---|---|---|
| `--config` | `mockrelay.yaml` | config file to read |
| `-m`, `--method` | `GET` | request method |
| `-u`, `--upstream` | all | limit to one upstream |
| `-q`, `--query` | none | repeatable `key=value` |
| `-b`, `--body` | none | JSON body, or a literal string |
| `--json` | off | emit machine-readable JSON |

The resolved `match_priority` order is printed above the table, and each row
shows its `prio` column so an overridden fixture is visible at a glance.

## init

    mockrelay init
    mockrelay init path/to/mockrelay.yaml
    mockrelay init --force

Writes a starter config. Refuses to overwrite an existing file unless
`--force` is given, in which case it replaces the file.

## config

    mockrelay config

Prints the effective settings and the resolved brand key. The brand key is
shown as `***`; its raw value is never printed.

## --version

    mockrelay --version

Prints `mockrelay <version>` and exits. `--version` reads the same single
version source that the installed package metadata is built from, so the
two cannot drift.

## JSON output

`list`, `stats`, `clean`, `validate`, and `match` accept `--json`. Each
prints exactly one object on stdout:

    {
      "schema": 1,
      "command": "validate",
      "ok": false,
      "problems": [
        { "problem": "is not a list", "location": "redact_headers" }
      ],
      "data": { "fixtures_checked": 12, "problems_found": 1 }
    }

`ok` is `false` when the command found a problem, and the exit code says
the same thing. `schema` is bumped if the shape changes, so a caller can
detect that rather than guess. Nothing else is written to stdout, so the
output can be piped straight into a parser.

## Exit codes

| Code | Meaning |
|---|---|
| `0` | success |
| `1` | runtime error, such as a port already in use |
| `2` | usage error, such as an unknown flag |
| `3` | the config could not be read, parsed, or accepted |
| `4` | `validate` found something wrong |
| `130` | interrupted with Ctrl-C |

A bad setting is reported rather than ignored: a command that is not
`validate` stops with code `3` and names the settings that were wrong,
instead of running on a default the user did not choose.
