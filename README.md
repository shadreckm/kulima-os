# Kulima OS — Coordination Intelligence Infrastructure

A coordination-first digital public infrastructure that transforms real-world activity into verified demand signals for infrastructure planning.

## What it does

Kulima OS transforms aggregated, identity-free coordination signals into institution-grade demand guidance for energy and infrastructure planners. It combines environmental, telemetry, and community coordination inputs into verified patterns that are auditable, explainable, and aligned with social reserve policies.

## How it works

1. **LUMOZA** — temporal coordination intelligence
   - Processes identity-free activity signals across 7-cycle windows
   - Detects stable demand rhythms by activity, zone, and time window
   - Applies human/telemetry cross-validation and noise filtering

2. **LUNDAI** — settlement and infrastructure gap analysis
   - Analyzes zone metadata and infrastructure context
   - Identifies infrastructure mismatches and critical load gaps
   - Produces explainable gap justifications and reserve-aware guidance

3. **ZENTARI** — coordination confidence and trust evaluation
   - Scores coordination patterns based on stability, validation, and resilience
   - Produces actionable guidance only when trust thresholds are met
   - Embeds explainability fields for every pattern and recommendation

## Running locally

1. Create a Python environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Run the Streamlit app:

```bash
streamlit run streamlit_app.py
```

4. To enable pilot evidence logging and dashboard insights, set the pilot mode environment variable:

```bash
set KULIMA_PILOT_MODE=1
streamlit run streamlit_app.py
```

The structured pilot evidence log is written to `pilot_log.json` in the repository root.

5. Optional: run the demo or CLI scripts as needed.

## Deployment

- **Render**: Deploy the Streamlit app using `streamlit_app.py` and `requirements.txt`.
- **Streamlit**: The repo is ready for Streamlit deployment with a standard `requirements.txt` file.
- **Procfile**: Included for platform deployment if needed.

## WhatsApp usage

1. Configure the Twilio or WhatsApp integration settings in `whatsapp_handler.py`.
2. Use the WhatsApp API to submit identity-free coordination signals.
3. Monitor outputs through the Streamlit dashboard or prospectus generator.

## Repository structure

- `whatsapp_app.py`
- `lumoza_engine.py`
- `lumoza_integration.py`
- `lundai_engine.py`
- `zentari_engine.py`
- `coordination_accumulation.py`
- `prospectus_generator.py`
- `signal_storage.py`
- `streamlit_app.py`
- `zone_utils.py`
- `requirements.txt`
- `Procfile`
- `README.md`
- `assets/`

## Notes

- The system is designed to preserve privacy, avoid individual profiling, and maintain explainability for institutional use.
- Only aggregated coordination patterns are used for planning recommendations.
