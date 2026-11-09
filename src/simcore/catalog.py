"""Model catalogue: a short, curated description of every model simcore can run.

Model files only carry one-line descriptions ("Simulates a very basic Electric
Vehicle"), which isn't enough for an engineer or an AI assistant to pick the
right model. Each entry here says what the model is, what it drives through,
how long a standard run is, its most useful signals and any known quirks.

Reviewed by a human: change deliberately, like a requirements document.
"""

MODELS = {
    "MBEV": {
        "model": "EHPTexamples.EV.MBEV",
        "description": (
            "Simple map-based battery electric vehicle (open-source EHPT library, "
            "Prof. M. Ceraolo): 1300 kg, single fixed gear, electric drive limited to "
            "150 N.m and 25 kW electrical power drawn from the battery (about 22 kW at "
            "the motor shaft after losses), battery starting at 70 % SOC. Drives the NEDC; "
            "a standard run is exactly one NEDC (1180 s). Runs longer than 1180 s repeat the cycle."
        ),
        "drive_cycle": "NEDC (one cycle = 1180 s; repeats if run longer)",
        "default_stop_time_s": 1180,
        "simflags": None,
        "key_signals": {
            "velSens.v": "vehicle speed",
            "batt1.SOC": "battery state of charge",
            "enBatDel": "battery energy used",
            "mass.s": "distance travelled",
        },
        "notes": "Use the signal glossary (list_signals) for engineering terms such as motor torque or battery current.",
        "known_messages": {
            "structural singular": "Known and harmless: OpenModelica repairs this start-up problem automatically; results are valid.",
        },
    },
    "FirstEV": {
        "model": "EHPTexamples.EV.FirstEV",
        "description": (
            "Very basic introductory electric vehicle (open-source EHPT library): a "
            "1300 kg car driven by an ideal torque source through a fixed gear "
            "(ratio 4), following the start of the NEDC drive cycle. No battery model. "
            "A standard run is 200 s."
        ),
        "drive_cycle": "NEDC (first 200 s)",
        "default_stop_time_s": 200,
        "simflags": "-jacobian=coloredNumerical",
        "key_signals": {
            "velSens.v": "vehicle speed [m/s]",
        },
        "notes": "Needs the solver flag -jacobian=coloredNumerical on OpenModelica 1.27.1 (applied automatically).",
        "known_messages": {},
    },
    "HelloEV": {
        "model": "HelloEV",
        "description": (
            "Minimal 1-D test vehicle written for this project: a constant 600 N drive "
            "force accelerates a 1600 kg car from rest against rolling resistance and "
            "aerodynamic drag. No battery and no drive cycle; speed approaches about "
            "121 km/h. Used to check the toolchain works. A standard run is 300 s."
        ),
        "drive_cycle": None,
        "default_stop_time_s": 300,
        "simflags": None,
        "key_signals": {
            "v": "vehicle speed [m/s]",
            "v_kph": "vehicle speed [km/h]",
            "x": "distance travelled [m]",
        },
        "notes": None,
        "known_messages": {},
    },
}


def get_model(name: str) -> dict:
    """Look up a catalogue entry by short name ("MBEV") or full name ("EHPTexamples.EV.MBEV")."""
    for short, entry in MODELS.items():
        if name.lower() in (short.lower(), entry["model"].lower()):
            return {"name": short, **entry}
    raise KeyError(f"Unknown model '{name}'. Available models: {', '.join(MODELS)}.")


# ── Running a catalogue model ─────────────────────────────────────────────────

MAX_STOP_TIME_S = 20000   # guardrail: no runaway simulations started by mistake


def run_model(name: str, stop_time: float | None = None):
    """Run a catalogue model by its short name, with its standard settings.

    Uses the catalogue's standard run length (unless stop_time is given) and any
    known solver flags, so callers never need full Modelica names or flags.
    Returns (RunResult, summary of the key signals or None, catalogue entry).
    """
    from simcore.results import summarize_signals
    from simcore.run import run_simulation

    entry = get_model(name)
    if stop_time is None:
        stop_time = entry["default_stop_time_s"]
    if not (0 < stop_time <= MAX_STOP_TIME_S):
        raise ValueError(f"stop_time must be between 0 and {MAX_STOP_TIME_S} s (got {stop_time}). "
                         f"The standard run for {entry['name']} is {entry['default_stop_time_s']} s.")

    result = run_simulation(entry["model"], stop_time=stop_time, simflags=entry["simflags"])
    summary = None
    if result.status == "success" and entry["key_signals"]:
        try:
            summary = summarize_signals(result, list(entry["key_signals"]))
        except (KeyError, ValueError):
            summary = None   # a key signal is missing: the run still counts, just no summary
    return result, summary, entry


def classify_messages(entry: dict, errors: list[str]) -> tuple[list[str], list[dict]]:
    """Split error messages into real errors and known, harmless ones (with an explanation)."""
    real, known = [], []
    for e in errors:
        label = next((why for pattern, why in entry.get("known_messages", {}).items()
                      if pattern.lower() in e.lower()), None)
        if label:
            known.append({"message": e.splitlines()[0][:200], "explanation": label})
        else:
            real.append(e)
    return real, known
