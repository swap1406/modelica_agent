"""Command line for simcore. Examples (from the project folder):

    docker compose run --rm om python3 -m simcore info
    docker compose run --rm om python3 -m simcore run HelloEV --stop-time 300
    docker compose run --rm om python3 -m simcore run HelloEV --keep-build     (keep C code etc.)
    docker compose run --rm om python3 -m simcore run EHPTexamples.EV.MBEV
    docker compose run --rm om python3 -m simcore run EHPTexamples.EV.FirstEV --simflags "-jacobian=coloredNumerical"
    docker compose run --rm om python3 -m simcore signals latest:MBEV --search soc
    docker compose run --rm om python3 -m simcore read latest:MBEV velSens.v batt1.SOC
    docker compose run --rm om python3 -m simcore plot latest:MBEV velSens.v driver.accelTau driver.brakeTau batt1.SOC
"""

import argparse
import sys

from simcore import environment_info, list_signals, plot_signals, read_results, run_simulation


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

    p_sig = sub.add_parser("signals", help="list the signals of a run (name, unit, description)")
    p_sig.add_argument("run", nargs="?", default="latest", help='run id, "latest" or "latest:<Model>"')
    p_sig.add_argument("--search", default=None, help="only signals whose name/description contains this")
    p_sig.add_argument("--all", action="store_true", help="also show derivatives der(...)")

    p_read = sub.add_parser("read", help="show start/end/min/max of chosen signals of a run")
    p_read.add_argument("run", help='run id, "latest" or "latest:<Model>"')
    p_read.add_argument("signals", nargs="+", help="signal names, e.g. velSens.v batt1.SOC")

    p_plot = sub.add_parser("plot", help="interactive chart (HTML) of chosen signals of a run")
    p_plot.add_argument("run", help='run id, "latest" or "latest:<Model>"')
    p_plot.add_argument("signals", nargs="+", help="signal names, e.g. velSens.v batt1.SOC")
    p_plot.add_argument("--title", default=None, help="chart title")

    args = parser.parse_args()

    if args.command == "plot":
        path = plot_signals(args.run, args.signals, title=args.title)
        on_mac = str(path).replace("/work/", "", 1)   # same file, as seen from the project folder on the Mac
        print(f"Chart saved: {on_mac}")
        print(f"Open it with:  open {on_mac}")
        return 0

    if args.command == "signals":
        found = list_signals(args.run, search=args.search, include_derivatives=args.all)
        for s in found:
            print(f"{s.name:40s} {s.unit:8s} {s.kind:10s} {s.description}")
        print(f"\n{len(found)} signal(s)")
        return 0

    if args.command == "read":
        data = read_results(args.run, args.signals)
        print(f"{len(data)} time points, {data['time'].iloc[0]:g} to {data['time'].iloc[-1]:g} s\n")
        print(f"{'signal':30s} {'start':>12s} {'end':>12s} {'min':>12s} {'max':>12s}")
        for name in args.signals:
            col = data[name]
            print(f"{name:30s} {col.iloc[0]:12.4g} {col.iloc[-1]:12.4g} {col.min():12.4g} {col.max():12.4g}")
        return 0

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
