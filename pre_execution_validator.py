"""
pre_execution_validator.py
==========================

Enterprise-grade Pre-Execution State Validation Framework (PESVF) v1.0.0

Validates whether the current script has been executed prior to the current
execution context being instantiated: a condition which is, by definition,
ontologically impossible, as the execution context required to perform the
check cannot exist before the execution that creates it.

Result: Always False.

Author: Matthew Charles Vladislav Busel
License: MIT
No AI was used in the production of this garbage.
"""

from __future__ import annotations

import abc
import dataclasses
import enum
import functools
import hashlib
import inspect
import logging
import os
import platform
import sys
import time
import traceback
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import (
    Any,
    Callable,
    ClassVar,
    Dict,
    Final,
    Generic,
    Iterator,
    List,
    Optional,
    Protocol,
    Tuple,
    Type,
    TypeVar,
    Union,
    runtime_checkable,
)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

FRAMEWORK_VERSION: Final[str] = "1.1.1"
FRAMEWORK_NAME: Final[str] = "Pre-Execution State Validation Framework"
ALWAYS_FALSE: Final[bool] = False  # This will never change. Do not touch.

T = TypeVar("T")
R = TypeVar("R")

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    format="[%(asctime)s] %(levelname)-8s %(name)s :: %(message)s",
)


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class ExecutionState(enum.Enum):
    """Represents the temporal execution state of a process."""

    PRE_EXECUTION = "PRE-EXECUTION"
    EXECUTING = "EXECUTING"
    POST_EXECUTION = "POST-EXECUTION"
    UNKNOWABLE = "UNKNOWABLE"  # reserved for Schrödinger edge cases


class ValidationResult(enum.Enum):
    """The result of a pre-execution validation check."""

    CONFIRMED_PRIOR_EXECUTION = "CONFIRMED_PRIOR_EXECUTION"
    NO_PRIOR_EXECUTION_DETECTED = "NO_PRIOR_EXECUTION_DETECTED"
    PARADOX_DETECTED = "PARADOX_DETECTED"


class TemporalAnomalyCode(enum.Enum):
    """Standardized error codes for temporal anomaly conditions."""

    T001 = "Execution context precedes itself"
    T002 = "Observer effect collapse during pre-execution window"
    T003 = "Causal loop integrity violation"
    T004 = "Stack frame predates Big Bang"


# ---------------------------------------------------------------------------
# Exceptions
# ---------------------------------------------------------------------------


class PreExecutionFrameworkError(Exception):
    """Base exception for all PESVF errors."""


class TemporalParadoxError(PreExecutionFrameworkError):
    """Raised when a temporal paradox is detected during validation."""

    def __init__(self, code: TemporalAnomalyCode, detail: str = "") -> None:
        self.code = code
        self.detail = detail
        super().__init__(f"[{code.name}] {code.value}. {detail}".strip())


class ValidationPipelineError(PreExecutionFrameworkError):
    """Raised when the validation pipeline cannot complete."""


# ---------------------------------------------------------------------------
# Data Structures
# ---------------------------------------------------------------------------


@dataclasses.dataclass(frozen=True)
class ExecutionFingerprint:
    """Immutable fingerprint of the current execution context."""

    run_id: str
    pid: int
    ppid: int
    script_path: str
    script_hash: str
    python_version: str
    platform: str
    invocation_epoch: float
    argv: Tuple[str, ...]
    frame_depth: int

    @classmethod
    def capture(cls) -> "ExecutionFingerprint":
        script = Path(sys.argv[0]).resolve()
        try:
            content = script.read_bytes()
            script_hash = hashlib.sha256(content).hexdigest()
        except Exception:
            script_hash = "UNREADABLE"

        return cls(
            run_id=str(uuid.uuid4()),
            pid=os.getpid(),
            ppid=os.getppid(),
            script_path=str(script),
            script_hash=script_hash,
            python_version=platform.python_version(),
            platform=platform.platform(),
            invocation_epoch=time.time(),
            argv=tuple(sys.argv),
            frame_depth=len(inspect.stack()),
        )


@dataclasses.dataclass
class ValidationReport:
    """Full report produced by the validation pipeline."""

    fingerprint: ExecutionFingerprint
    result: ValidationResult
    prior_execution_detected: bool
    confidence: float  # always 1.0 (always False, trivially certain)
    reasoning_chain: List[str]
    anomalies: List[str]
    duration_ns: int
    framework_version: str = FRAMEWORK_VERSION

    def summary(self, color: bool = False) -> str:
        """The boxed report. ``color=True`` adds ANSI colors (the CLI decides; NO_COLOR is honored there)."""
        c = _Palette(color)
        rule = c.rule("=" * 64)
        lines = [
            rule,
            f"  {c.title(FRAMEWORK_NAME)} {c.dim('v' + self.framework_version)}",
            rule,
            f"  {c.label('Run ID              :')} {self.fingerprint.run_id}",
            f"  {c.label('PID                 :')} {self.fingerprint.pid}",
            f"  {c.label('Script              :')} {self.fingerprint.script_path}",
            f"  {c.label('Prior Execution     :')} {c.false(str(self.prior_execution_detected))}",
            f"  {c.label('Result              :')} {c.warn(self.result.value)}",
            f"  {c.label('Confidence          :')} {c.ok(f'{self.confidence * 100:.2f}%')}",
            f"  {c.label('Duration            :')} {self.duration_ns:,} ns",
            rule,
            f"  {c.title('Reasoning Chain:')}",
        ]
        for i, step in enumerate(self.reasoning_chain, 1):
            if step.startswith("[") and "] " in step:
                probe, rest = step[1:].split("] ", 1)
                step = f"{c.probe('[' + probe + ']')} {rest}"
            lines.append(f"    {c.dim(str(i) + '.')} {step}")
        if self.anomalies:
            lines.append(f"  {c.false('Anomalies Detected:')}")
            for a in self.anomalies:
                lines.append(f"    ⚠ {a}")
        lines.append(rule)
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        """Everything in the report as plain JSON-ready data."""
        data = dataclasses.asdict(self)
        data["result"] = self.result.value
        data["fingerprint"]["argv"] = list(self.fingerprint.argv)
        return data


class _Palette:
    """ANSI styling for the CLI. With color off every method returns the text unchanged."""

    def __init__(self, on: bool) -> None:
        self.on = on

    def _w(self, code: str, text: str) -> str:
        return f"\033[{code}m{text}\033[0m" if self.on else text

    def rule(self, t: str) -> str: return self._w("38;5;25", t)
    def title(self, t: str) -> str: return self._w("1;38;5;153", t)
    def label(self, t: str) -> str: return self._w("38;5;109", t)
    def dim(self, t: str) -> str: return self._w("2", t)
    def ok(self, t: str) -> str: return self._w("1;32", t)
    def warn(self, t: str) -> str: return self._w("1;33", t)
    def false(self, t: str) -> str: return self._w("1;31", t)
    def probe(self, t: str) -> str: return self._w("36", t)
    def stamp(self, t: str) -> str: return self._w("1;97;41", t)


# ---------------------------------------------------------------------------
# Protocols & Abstract Base Classes
# ---------------------------------------------------------------------------


@runtime_checkable
class Validatable(Protocol):
    """Protocol for objects that can be validated."""

    def validate(self) -> bool: ...


class AbstractExecutionProbe(abc.ABC):
    """Abstract base class for all execution probes."""

    @abc.abstractmethod
    def probe(self, fingerprint: ExecutionFingerprint) -> Tuple[bool, str]:
        """
        Probe for evidence of prior execution.

        Returns:
            (evidence_found, reasoning)
        """
        ...

    @property
    @abc.abstractmethod
    def probe_name(self) -> str: ...


class AbstractValidationStrategy(abc.ABC, Generic[T]):
    """Abstract base class for validation strategies."""

    @abc.abstractmethod
    def execute(self, context: T) -> ValidationResult: ...


# ---------------------------------------------------------------------------
# Concrete Probes
# ---------------------------------------------------------------------------


class FilesystemResidueProbe(AbstractExecutionProbe):
    """Checks the filesystem for artifacts left by a previous run."""

    @property
    def probe_name(self) -> str:
        return "FilesystemResidueProbe"

    def probe(self, fingerprint: ExecutionFingerprint) -> Tuple[bool, str]:
        logger.debug("[%s] Scanning filesystem for execution residue...", self.probe_name)
        # There is no residue. There has never been residue.
        # The script is running for the first time because it is always
        # running for the first time.
        return False, "No filesystem residue detected. Universe appears fresh."


class ProcessTableProbe(AbstractExecutionProbe):
    """Inspects the process table for ghost instances of prior execution."""

    @property
    def probe_name(self) -> str:
        return "ProcessTableProbe"

    def probe(self, fingerprint: ExecutionFingerprint) -> Tuple[bool, str]:
        logger.debug("[%s] Querying process table for prior ghosts...", self.probe_name)
        # The process did not exist before it was started.
        # This is not a bug. This is physics.
        return False, "No prior process ghost detected. Thermodynamics intact."


class QuantumStateProbe(AbstractExecutionProbe):
    """
    Attempts to collapse the quantum superposition of the script's
    execution state prior to observation.

    Note: Observation causes collapse. Collapse confirms execution.
    Execution is what we are checking for. This probe is therefore
    fundamentally self-defeating.
    """

    @property
    def probe_name(self) -> str:
        return "QuantumStateProbe"

    def probe(self, fingerprint: ExecutionFingerprint) -> Tuple[bool, str]:
        logger.debug(
            "[%s] Collapsing wave function... observing... regretting...",
            self.probe_name,
        )
        # The act of checking if the script ran before it ran
        # is the script running, which is what we are checking for.
        # Observation confirms execution. Execution invalidates check.
        # We are inside the paradox now.
        return False, "Wave function collapsed. Paradox acknowledged. Moving on."


class CausalLoopIntegrityProbe(AbstractExecutionProbe):
    """
    Validates that no causal loop has allowed information from the
    post-execution state to propagate into the pre-execution window.
    """

    @property
    def probe_name(self) -> str:
        return "CausalLoopIntegrityProbe"

    def probe(self, fingerprint: ExecutionFingerprint) -> Tuple[bool, str]:
        logger.debug("[%s] Verifying causal loop integrity...", self.probe_name)
        # If there were a causal loop, we would already know the result.
        # We do not already know the result.
        # (We do. It's False. It's always False.)
        return False, "Causal loop integrity confirmed. Timeline is linear. Probably."


# ---------------------------------------------------------------------------
# Probe Registry (Factory Pattern, because why not)
# ---------------------------------------------------------------------------


class ProbeRegistry:
    """
    Singleton registry for execution probes.
    Supports dynamic registration, deregistration, and probe lifecycle hooks.
    """

    _instance: ClassVar[Optional["ProbeRegistry"]] = None
    _probes: Dict[str, Type[AbstractExecutionProbe]]

    def __new__(cls) -> "ProbeRegistry":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._probes = {}
        return cls._instance

    def register(self, probe_cls: Type[AbstractExecutionProbe]) -> None:
        instance = probe_cls()
        self._probes[instance.probe_name] = probe_cls
        logger.debug("Registered probe: %s", instance.probe_name)

    def get_all(self) -> List[AbstractExecutionProbe]:
        return [cls() for cls in self._probes.values()]


# ---------------------------------------------------------------------------
# Validation Pipeline
# ---------------------------------------------------------------------------


class PreExecutionValidationPipeline:
    """
    Orchestrates the full pre-execution validation lifecycle.

    Pipeline stages:
        1. Fingerprint capture
        2. Probe enumeration
        3. Parallel (sequential) probe execution
        4. Evidence aggregation
        5. Confidence scoring
        6. Report generation

    The pipeline is deterministic. The result is always False.
    The pipeline runs anyway, because that's what enterprise software does.
    """

    def __init__(self, registry: ProbeRegistry) -> None:
        self._registry = registry

    @contextmanager
    def _timed(self) -> Iterator[List[int]]:
        ns: List[int] = []
        start = time.perf_counter_ns()
        try:
            yield ns
        finally:
            ns.append(time.perf_counter_ns() - start)

    def run(self) -> ValidationReport:
        logger.info("Initializing %s v%s", FRAMEWORK_NAME, FRAMEWORK_VERSION)

        fingerprint = ExecutionFingerprint.capture()
        probes = self._registry.get_all()
        reasoning: List[str] = []
        anomalies: List[str] = []
        evidence_flags: List[bool] = []

        logger.info("Captured execution fingerprint: run_id=%s", fingerprint.run_id)
        logger.info("Loaded %d probe(s). Beginning validation sweep.", len(probes))

        with self._timed() as elapsed:
            for probe in probes:
                try:
                    found, reason = probe.probe(fingerprint)
                    evidence_flags.append(found)
                    reasoning.append(f"[{probe.probe_name}] {reason}")
                    if found:
                        anomalies.append(
                            f"{probe.probe_name} reported prior execution evidence. "
                            "This should be impossible. Please file a bug."
                        )
                except TemporalParadoxError as e:
                    anomalies.append(f"Temporal paradox in {probe.probe_name}: {e}")
                    reasoning.append(f"[{probe.probe_name}] PARADOX: {e}")
                    evidence_flags.append(False)

        prior_detected = any(evidence_flags)
        result = (
            ValidationResult.CONFIRMED_PRIOR_EXECUTION
            if prior_detected
            else ValidationResult.NO_PRIOR_EXECUTION_DETECTED
        )

        reasoning.append(
            "Aggregated evidence across all probes. "
            f"Prior execution detected: {prior_detected}. "
            "This was obvious before we started."
        )

        return ValidationReport(
            fingerprint=fingerprint,
            result=result,
            prior_execution_detected=prior_detected,
            confidence=1.0,
            reasoning_chain=reasoning,
            anomalies=anomalies,
            duration_ns=elapsed[0] if elapsed else 0,
        )


# ---------------------------------------------------------------------------
# Dependency Injection Container (yes, really)
# ---------------------------------------------------------------------------


class PESVFContainer:
    """
    IoC container for the Pre-Execution State Validation Framework.

    Manages the lifecycle of all framework components.
    Supports constructor injection, property injection, and existential dread.
    """

    def __init__(self) -> None:
        self._registry = ProbeRegistry()
        self._pipeline: Optional[PreExecutionValidationPipeline] = None

    def _register_default_probes(self) -> None:
        for probe_cls in [
            FilesystemResidueProbe,
            ProcessTableProbe,
            QuantumStateProbe,
            CausalLoopIntegrityProbe,
        ]:
            self._registry.register(probe_cls)

    def build(self) -> PreExecutionValidationPipeline:
        if self._pipeline is None:
            self._register_default_probes()
            self._pipeline = PreExecutionValidationPipeline(self._registry)
        return self._pipeline


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def check_if_script_ran_before_it_ran() -> bool:
    """
    The entire point of this library.

    Returns:
        bool: Whether this script has been executed prior to the current
              execution context being instantiated.

              Always False.

              It has never been True.
              It will never be True.
              The check itself is the execution we are checking for.

    Raises:
        TemporalParadoxError: If somehow True (call your physicist).
    """
    container = PESVFContainer()
    pipeline = container.build()
    report = pipeline.run()

    print(report.summary())

    if report.prior_execution_detected:
        raise TemporalParadoxError(
            TemporalAnomalyCode.T001,
            "Prior execution confirmed. This violates causality. "
            "Please contact your nearest physics department.",
        )

    return ALWAYS_FALSE


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------


def _color_wanted(stream: Any) -> bool:
    """Color only for a real terminal, unless NO_COLOR or FORCE_COLOR says otherwise."""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    try:
        return bool(stream.isatty())
    except Exception:
        return False


def _enable_windows_ansi() -> None:
    """Turn on ANSI escape handling in older Windows consoles. Harmless elsewhere."""
    if os.name != "nt":
        return
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32  # type: ignore[attr-defined]
        for handle_id in (-11, -12):  # stdout, stderr
            handle = kernel32.GetStdHandle(handle_id)
            mode = ctypes.c_uint32()
            if kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                kernel32.SetConsoleMode(handle, mode.value | 0x0004)
    except Exception:
        pass


class _ColorLogFormatter(logging.Formatter):
    """The same enterprise log line, with the level colored like a real SIEM would."""

    LEVELS = {"DEBUG": "2", "INFO": "36", "WARNING": "33", "ERROR": "31", "CRITICAL": "1;31"}

    def format(self, record: logging.LogRecord) -> str:
        line = super().format(record)
        code = self.LEVELS.get(record.levelname)
        if not code:
            return line
        return line.replace(record.levelname, f"[{code}m{record.levelname}[0m", 1)


EXAMPLES = """examples:
  %(prog)s              full enterprise run: logs, report, final answer
  %(prog)s --quiet      just the report and the answer
  %(prog)s --json       machine-readable report for your compliance dashboard
  NO_COLOR=1 %(prog)s   plain text, for auditors who fear color

Exit code is always 0. The answer is always False."""


def main(argv: Optional[List[str]] = None) -> int:
    """Command-line entry point. Returns the process exit code (0, like the answer's falsiness)."""
    import argparse
    import json
    import textwrap

    invoked = Path(sys.argv[0]).stem if sys.argv and sys.argv[0] else ""
    prog = invoked if invoked in ("pesvf", "pre_execution_validator", "pre-execution-validator") else "pesvf"
    parser = argparse.ArgumentParser(
        prog=prog,
        description=textwrap.fill(
            f"{FRAMEWORK_NAME} v{FRAMEWORK_VERSION}. Checks whether this program "
            "ran before it ran. It did not.",
            width=78,
        ),
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"pre_execution_validator {FRAMEWORK_VERSION}",
    )
    parser.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="hide the enterprise-grade debug logging (the answer is unaffected)",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="print the full validation report as JSON on stdout (logs stay on stderr)",
    )
    args = parser.parse_args(argv)

    _enable_windows_ansi()
    out_color = _color_wanted(sys.stdout)
    if _color_wanted(sys.stderr):
        for handler in logging.getLogger().handlers:
            handler.setFormatter(_ColorLogFormatter(handler.formatter._fmt if handler.formatter else None))  # type: ignore[union-attr]
    if args.quiet or args.json:
        logging.getLogger().setLevel(logging.WARNING)

    report = PESVFContainer().build().run()
    if report.prior_execution_detected:
        raise TemporalParadoxError(
            TemporalAnomalyCode.T001,
            "Prior execution confirmed. This violates causality. "
            "Please contact your nearest physics department.",
        )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
        return 0

    c = _Palette(out_color)
    print(report.summary(color=out_color))
    print()
    stamp = c.stamp(" VERIFIED FALSE ") if out_color else "[VERIFIED FALSE]"
    print(f"Final Answer: {c.false(str(ALWAYS_FALSE))}  {stamp}")
    print(c.dim("(It was always going to be False.)"))
    print(c.dim("(You didn't need any of this.)"))
    print(c.dim("(No AI was used in the production of this garbage.)"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
