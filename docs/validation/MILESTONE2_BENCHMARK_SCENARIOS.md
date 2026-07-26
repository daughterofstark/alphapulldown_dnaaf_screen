# Milestone 2 Benchmark Scenarios

This document records the closed Milestone 2 benchmark scenario set used for offline configuration and future AlphaPulldown validation.

No biological sequences were retrieved, validated, modified, or generated for this benchmark definition. The 62-target universe manifests remain untouched and are not fallback sources for this benchmark.

## Files

- Scenario manifest: `data/processed/benchmarks/milestone2_scenarios.json`
- Benchmark FASTA manifest: `data/processed/benchmarks/fasta/fasta_manifest.tsv`
- Benchmark AlphaPulldown input sheet: `data/processed/benchmarks/alphapulldown_inputs/milestone2_sample_sheet.tsv`
- Example config: `config/benchmarks/milestone2_benchmark.example.yaml`
- Remote env template: `config/benchmarks/milestone2_remote.example.env`
- Input directory: `data/processed/benchmarks/alphapulldown_inputs`
- Future output directory placeholder: `results/milestone2_benchmark`
- Future provenance directory placeholder: `results/provenance/milestone2_benchmark`

The benchmark FASTA manifest is intentionally independent from
`data/processed/fasta/fasta_manifest.tsv`. It references the existing versioned
human FASTA records by path, but the Milestone 2 remote configuration reads only
the benchmark manifest and benchmark AlphaPulldown inputs.

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

The eight human scenarios are runnable from existing versioned records:

- `human_dnaaf18_ift46_negative`
- `human_dnaaf9_ift74_ift81_known`
- `human_dnaaf9_ift46_ift74_ift81_exploratory`
- `human_dnaaf9_ift80_ift172_exploratory`
- `human_dnai1_ift46_ift74_ift81_exploratory`
- `human_dnai2_ift46_ift74_ift81_exploratory`
- `human_dnai1_dnai2_ift46_ift74_ift81_exploratory`
- `human_dnai1_dnai2_ift80_ift172_exploratory`

## Explicitly Excluded IDs

These scenario IDs are prohibited:

- `human_dnaaf9_ift74`
- `human_dnaaf9_ift81`
- `ift74_ift81`
- `human_dnaaf18_ift46_ift74_ift81`

## Future CPU Commands

The commands below are for the future remote CPU feature-generation session. Do
not run them as part of offline repository review.

```bash
cp config/benchmarks/milestone2_remote.example.env config/remote/paths.env
sed -n '1,220p' config/remote/paths.env
```

```bash
export PATH="/workspace/miniforge3/bin:$PATH"
source /workspace/miniforge3/etc/profile.d/conda.sh
conda activate snake
cd /workspace/alphapulldown

bash scripts/remote/bootstrap_remote_environment.sh --dry-run
bash scripts/remote/validate_remote_environment.sh
bash scripts/remote/run_feature_generation.sh --dry-run
```

```bash
PYTHONPATH=src python -m alphapulldown_dnaaf_screen.remote_cli \
  --config config/remote/paths.env \
  check-feature-coverage \
  --screen milestone2 \
  --json
```

After the Milestone 2 feature files exist, the future GPU pod should dry-run the
benchmark prediction step before launching inference:

```bash
bash scripts/remote/run_prediction.sh --screen milestone2 --dry-run
```
