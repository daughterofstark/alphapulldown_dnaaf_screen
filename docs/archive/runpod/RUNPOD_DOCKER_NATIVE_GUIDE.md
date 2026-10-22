# RunPod Docker-Native Runtime

## Purpose

RunPod launches the AlphaPulldown runtime image as the Pod itself. The project
does not launch a second container from inside the Pod.

The production image is built from
`deployment/runpod/Dockerfile`, pinned to the immutable amd64 digest recorded in
`deployment/runpod/image-lock.json`. The repository does not build or publish
that image automatically.

## Commands

Validate the configuration embedded in the checked-out repository:

```bash
python -m alphapulldown_dnaaf_screen.native_cli \
  --config config/remote/paths.env \
  validate
```

Run a host/runtime preflight:

```bash
python -m alphapulldown_dnaaf_screen.native_cli \
  --config config/remote/paths.env \
  preflight
```

Render feature commands without executing them:

```bash
bash scripts/remote/run_native_stage.sh \
  --stage features \
  --env-file config/remote/paths.env \
  --dry-run
```

Render prediction commands without executing them:

```bash
bash scripts/remote/run_native_stage.sh \
  --stage predict \
  --env-file config/remote/paths.env \
  --dry-run
```

Removing `--dry-run` directly invokes the AlphaPulldown CLI for that stage.
This requires separate approval and is not part of repository setup.

## Runtime guarantees

The native runner:

- accepts only `CONTAINER_RUNTIME=docker-native`;
- permits feature generation only with `REMOTE_EXECUTION_STAGE=cpu`;
- permits prediction only with `REMOTE_EXECUTION_STAGE=gpu`;
- requires AF2/MMseqs2 compressed `*.pkl.xz` features;
- reads only the independent Milestone 2 manifests and inputs;
- rejects the blocked Chlamydomonas scenario and excluded scenarios;
- rejects the 62-target FASTA manifest;
- does not invoke Snakemake, Docker, Apptainer, Singularity, or AlphaJudge;
- requires every feature before constructing prediction commands;
- records image, AlphaPulldown, Git, command, input checksum, and path
  provenance.

## Image identity

`ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST=UNBUILT` is an intentional placeholder.
Configuration validation and dry-run planning can use it, but scientific
execution and runtime preflight reject it. Replace it only with the immutable
digest reported by the registry after the derived image is built and pushed.

The expected AlphaPulldown source revision is also pending the direct-image
proof of concept. Record and pin it before feature generation.

## Historical runtime

The Snakemake/Apptainer implementation remains versioned for non-RunPod
environments and provenance. It is retired for RunPod and is never selected by
the Docker-native configuration.
