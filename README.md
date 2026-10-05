# Chat with your EV digital twin

An AI assistant that lets simulation engineers run and analyse electric-vehicle models in plain language.

> "Run the WLTC cycle for the EV model, then plot battery state of charge."

The assistant runs the simulation in OpenModelica (inside Docker), reads the results and plots them, so engineers spend less time on tool mechanics and more time on engineering decisions.

## Why

Virtual validation means many repetitive steps: choose a model, set up a drive cycle, run the simulation, find the right signal among hundreds, plot and compare. This project explores how much of that loop an AI assistant can handle reliably, and measures how often it gets things right.

## How it works (planned)

- **Simulation:** [OpenModelica](https://openmodelica.org/) running in Docker, so the setup is identical on any machine.
- **Core library:** a small Python package to run a simulation, read results and plot signals.
- **AI interface:** the library exposed as [MCP](https://modelcontextprotocol.io/) tools, so any MCP-compatible AI assistant can use it.
- **Evaluation:** a test set of typical engineer requests, with measured accuracy and documented failure modes.

## Status

🚧 Phase 0: environment setup.

| Milestone | Scope |
|---|---|
| 1 | Docker + OpenModelica environment; core library: run a drive cycle, read results, plot |
| 2 | MCP server working with an off-the-shelf assistant; evaluation set of 30–50 requests |
| 3 | "Chat to validate": requirement files, automatic pass/fail checks, test reports |
| 4 | Fault injection (e.g. degraded battery) and AI diagnosis accuracy |
| 5 | Product write-up, demo video |

## Ground rules

- Only open-source models and publicly available parameters.
- No API keys in the code; secrets live in a local `.env` file that is never committed.
