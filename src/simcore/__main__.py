"""Command line for simcore. Examples (from the project folder):

    docker compose run --rm om python3 -m simcore info
    docker compose run --rm om python3 -m simcore run HelloEV --stop-time 300
    docker compose run --rm om python3 -m simcore run HelloEV --keep-build     (keep C code etc.)
    docker compose run --rm om python3 -m simcore run EHPTexamples.EV.MBEV
    docker compose run --rm om python3 -m simcore run EHPTexamples.EV.FirstEV --simflags "-jacobian=coloredNumerical"
"""

import argparse
import sys

from simcore import environment_info, run_simulation


def main() -> int:
    parser = argparse.ArgumentParser(prog="simcore", description="Run Modelica simulations in OpenModelica.")
    sub = parser.add_subparsers(dest="command")

    sub.add_parser("info", help="show versions of OpenModelica, Python and packages")

    p_run = sub.add_parser("run", help="run one model in its own run folder")
    p_run.add_argument("model", help='full Modelica name, e.g. "EHPTexamples.EV.MBEV" or "HelloEV"')
    p_run.add_argument("--stop-time", type=float, default=None, help="end time in seconds (default: model's own)")
    p_run.add_argument("--simflags", default=None, help='extra simulation flags, e.g. "-jacobian=coloredNumerical"')
    p_run.add_argument("--keep-build", action="store_true",
                       help="keep OpenModelica's intermediate files (C code etc.) in build/ for debugging")

    args = parser.parse_args()

    if args.command == "run":
        result = run_simulation(args.model, stop_time=args.stop_time, simflags=args.simflags,
                                keep_build=args.keep_build)
        print(result.summary())
        return 0 if result.status == "success" else 1

    # default (and "info"): print the environment
    for name, version in environment_info().items():
        print(f"{name:13s} {version}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
