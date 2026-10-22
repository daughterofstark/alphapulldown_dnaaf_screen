# Data Transfer Guide

## Local to Remote

Use Git for code and small tracked data:

```bash
git push
ssh <remote-host>
git clone <REPOSITORY_URL> alphapulldown
cd alphapulldown
git checkout feature/alphapulldown-implementation
```

If generated data must be refreshed independently of Git, use `rsync`:

```bash
rsync -av data/processed/fasta/ <remote-host>:/path/to/alphapulldown/data/processed/fasta/
rsync -av data/processed/alphapulldown/ <remote-host>:/path/to/alphapulldown/data/processed/alphapulldown/
rsync -av config/remote/ <remote-host>:/path/to/alphapulldown/config/remote/
```

Do not transfer:

- AlphaFold databases.
- Large MSA caches.
- Temporary directories.
- Machine-specific secrets.

## Remote to Local

On the remote host:

```bash
bash scripts/remote/collect_results.sh
```

From macOS:

```bash
rsync -av <remote-host>:/path/to/alphapulldown/results/collected/ results/remote_collected/
```

Transfer only:

- `reports/all_interfaces.csv`
- `predictions/<fold>/interfaces.csv`
- `predictions/<fold>/ranked_*.pdb`
- `predictions/<fold>/ranking_debug.json`
- `predictions/<fold>/pae_*.json`
- `predictions/<fold>/pae_plot_ranked_*.png`
- `predictions/<fold>/confidence_*.json`
- logs
- provenance
- `result_*.pkl*` only when explicitly needed

## Reproducibility Notes

Always record:

- Git commit.
- Branch.
- Dirty state.
- Remote host environment.
- AlphaPulldown/Snakemake versions.
- CUDA/GPU details.
- Input checksums.
