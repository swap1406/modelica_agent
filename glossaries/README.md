# Signal glossaries

One JSON file per model (`<ModelShortName>.json`). A glossary maps the terms engineers
use ("motor torque", "battery current") to the exact signal that answers them, with its
sign convention and the unit to show it in. The MCP tools put these signals first when
an AI searches, so it picks the right one instead of guessing among hundreds.

The glossary is optional: every model works without one. It only improves accuracy.

## Format

```json
{
  "model": "MBEV",
  "approved_by": "name, date",
  "checked_against": "run id used to check the entries",
  "entries": [
    {
      "term": "battery current",
      "synonyms": ["pack current", "discharge current"],
      "signal": "batt1.n.i",
      "unit": "A",
      "display_unit": null,
      "meaning": "Battery current: positive = discharging, negative = charging (regen).",
      "check": "+64.9 A while accelerating, -35.7 A while braking"
    }
  ]
}
```

- `display_unit`: the unit to show values in; `null` uses the default for the unit
  (see `src/simcore/units.py`, e.g. m/s → km/h, J → kWh). Needed only where the default
  isn't right, e.g. a state of charge stored as a fraction (`"1"`) shown as `"%"`.
- `meaning`: say what positive and negative values mean wherever the sign matters.
- `check`: the value range you saw in real data. Check every entry against a real run
  before approving it: names can mislead (a "torque" signal may be a request, not the
  actual torque).

## Adding a model

1. Run the model once and look at its signals (`list_signals`).
2. Pick the 10–15 signals engineers ask about; check each one's values in the data.
3. Write `<Model>.json`, have a domain expert review it, and fill in `approved_by`.
