# Changelog

## [1.1.1] - 2026-09-25

- New short command `pesvf` (the old `pre_execution_validator` name still works).
- Colored output in terminals: red verdict, cyan probes, level-colored logs. Honors `NO_COLOR` and `FORCE_COLOR`; plain text when piped.
- `--json` prints the full validation report as JSON (logs stay on stderr).
- `--help` now shows examples. `ValidationReport.summary()` takes an optional `color` flag and there is a new `ValidationReport.to_dict()`.
- Tests (pytest) run in CI. README rebuilt with a banner and a recorded terminal demo.

## [1.1.0] - 2026-09-25

- Prebuilt single-file executables for Windows, macOS (Apple Silicon and Intel) and Linux, attached to each GitHub Release. No Python needed.
- `--version`, `--help` and `--quiet` (hides the debug logging; the answer is still False).
- `pyproject.toml`, so `pipx install git+https://github.com/Mattbusel/pre_execution_validator` gives you a `pre_execution_validator` command.
- CI runs the script on Linux and Windows.

## [1.0.0]

- Initial release. The answer was False.
