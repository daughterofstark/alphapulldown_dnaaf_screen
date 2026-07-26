# Milestone 2 Benchmark Scenarios

This document records the closed Milestone 2 benchmark scenario set used for offline configuration and future AlphaPulldown validation.

No biological sequences were retrieved, validated, modified, or generated for this benchmark definition. The 62-target universe manifests remain untouched and are not fallback sources for this benchmark.

## Files

- Scenario manifest: `data/processed/benchmarks/milestone2_scenarios.json`
- Example config: `config/benchmarks/milestone2_benchmark.example.yaml`
- Future input directory placeholder: `data/processed/benchmarks/alphapulldown_inputs`
- Future output directory placeholder: `results/milestone2_benchmark`
- Future provenance directory placeholder: `results/provenance/milestone2_benchmark`

## Scenario IDs

- `chlamy_dnaaf18_ift46_positive`
- `human_dnaaf18_ift46_negative`
- `human_dnaaf9_ift74_ift81_known`
- `human_dnaaf9_ift46_ift74_ift81_exploratory`
- `human_dnaaf9_ift80_ift172_exploratory`
- `human_dnai1_ift46_ift74_ift81_exploratory`
- `human_dnai2_ift46_ift74_ift81_exploratory`
- `human_dnai1_dnai2_ift46_ift74_ift81_exploratory`
- `human_dnai1_dnai2_ift80_ift172_exploratory`

The Chlamydomonas positive benchmark is retained as a scenario because the project already contains versioned internal benchmark records for it. It is marked `blocked_until_external_sequence_records_are_versioned` because no Chlamydomonas sequence target records are versioned in this repository. It must not fall back to human targets.

## Explicitly Excluded IDs

These scenario IDs are prohibited:

- `human_dnaaf9_ift74`
- `human_dnaaf9_ift81`
- `ift74_ift81`
- `human_dnaaf18_ift46_ift74_ift81`

## Placeholder Commands Only

The commands below are placeholders for a future execution phase. Do not run them as part of this offline configuration change.

```bash
# Placeholder only: generate Milestone 2 AlphaPulldown inputs after explicit approval.
python -m alphapulldown_dnaaf_screen.cli prepare-milestone2-benchmark \
  --config config/benchmarks/milestone2_benchmark.example.yaml
```

```bash
# Placeholder only: dry-run future feature generation after inputs are generated.
bash scripts/remote/run_feature_generation.sh --dry-run
```

```bash
# Placeholder only: dry-run future controls/benchmark prediction after feature coverage exists.
bash scripts/remote/run_prediction.sh --screen milestone2 --dry-run
```
