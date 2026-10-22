# Milestone 2 Benchmark Scenarios

This document records the closed Milestone 2 benchmark scenario set used for AlphaPulldown validation.

No biological sequences were retrieved, validated, modified, or generated for this benchmark definition. The 62-target universe manifests remain untouched and are not fallback sources for this benchmark.

## Files

- Scenario manifest: `data/processed/benchmarks/milestone2_scenarios.json`
- Benchmark FASTA manifest: `data/processed/benchmarks/fasta/fasta_manifest.tsv`
- Benchmark AlphaPulldown input sheet: `data/processed/benchmarks/alphapulldown_inputs/milestone2_sample_sheet.tsv`
- Example config: `config/benchmarks/milestone2_benchmark.example.yaml`
- AWS runtime template: `config/benchmarks/milestone2_aws.example.env`
- Input directory: `data/processed/benchmarks/alphapulldown_inputs`
- Output directory: `results/milestone2_benchmark`
- Provenance directory: `results/provenance/milestone2_benchmark`

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

The Chlamydomonas positive benchmark is retained as a design reference. It is marked `blocked_until_external_sequence_records_are_versioned` because no Chlamydomonas sequence target records are versioned in this repository. It must not fall back to human targets.

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

## Reproduction Commands

The following commands document the validated AWS workflow. They require the
versioned Docker image, AlphaFold parameters, and an appropriately provisioned
Linux host; they are not intended for local macOS execution.

```bash
bash scripts/aws/configure_milestone2_runtime.sh
bash scripts/aws/run_milestone2_stage.sh --stage features --dry-run
bash scripts/aws/run_milestone2_stage.sh --stage features
```

```bash
REMOTE_EXECUTION_STAGE="gpu" \
  bash scripts/aws/run_milestone2_stage.sh \
    --stage predict \
    --scenario human_dnaaf18_ift46_negative \
    --dry-run
```

The scoped AWS wrapper rejects the 62-target manifest, AlphaFold3 selectors,
the blocked Chlamydomonas scenario, and unsupported analysis modes.
