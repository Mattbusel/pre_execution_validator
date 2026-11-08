# pre_execution_validator

A joke program that checks if it ran before it ran.

The answer is always False.

- Parodies enterprise software in one Python file.
- Runs four probes.
- Prints a full validation report.
- Returns False. Always.

## Install

```bash
pipx install git+https://github.com/Mattbusel/pre_execution_validator
```

## Use

```bash
pesvf              # 1. the full enterprise experience: logs, report, verdict
pesvf --quiet      # 2. just the report and the verdict
pesvf --json       # 3. a machine-readable report for your compliance dashboard
```

[Releases](https://github.com/Mattbusel/pre_execution_validator/releases/latest)

More: [docs/DETAILS.md](docs/DETAILS.md)

MIT licensed. No AI was used in the production of this garbage.
