# RunPod Docker-Native Image Re-audit

**Date:** 2026-07-30
**Status:** blocked pending a reproducible image build and smoke-test evidence
**Scope:** runtime packaging only; no sequence work, feature generation, or inference

## Decision

Do not use `kosinskilab/alphafold2:2.5.0` directly and do not use it as the
base of the project image.

A real RunPod Pod started with that image did not expose the runtime contract
required by this repository:

- `python --version` returned Python 3.12.3;
- `alphapulldown` package metadata was absent;
- `create_individual_features.py` and `run_structure_prediction.py` were absent;
- JAX was absent.

The Docker Hub metadata currently claims a different filesystem contract, but
registry metadata is not a substitute for execution. The observed Pod result
therefore invalidates the direct-image design.

No other official, pinned, ready-to-run AlphaPulldown 2.5.0 amd64 image was
identified in the release source or documentation. The replacement must be a
project-controlled image built from immutable upstream artifacts.

## Pinned upstream evidence

### AlphaPulldown source

- tag object: `f838dce8351465a2dac7e7c0cdb151a61f7c9ca3`
- tag `2.5.0` commit:
  `1c99b15ce3fef42374c24a5bd83ce8241117d5f6`
- AlphaFold submodule:
  `5bf5b9f57dcd0e4919f4ff368788780f30be5d5e`
- ColabFold submodule:
  `2dca1083d6351944a32aff4f66290a961da744b0`
- AlphaLink2 submodule:
  `44f4bf2aa6b60a8f88ae05fdae12d46d967d5648`
- AlphaFold3 submodule:
  `86b9ea3feacc8934e6e2a581c49eb4c37a2a3d20`
- af2plots submodule:
  `768f35d002ab4380e6ca6ccc6953170b675c7da1`

Files inspected at that commit:

- `docker/alphafold2.dockerfile`
- `.github/workflows/github_actions.yml`
- `pyproject.toml`
- `environment.yml`
- `docs/backend_installation.md`
- `alphapulldown/scripts/create_individual_features.py`
- `alphapulldown/scripts/run_structure_prediction.py`
- `alphapulldown/folding_backend/alphafold2_backend.py`
- `ColabFold/pyproject.toml`
- `alphafold/requirements.txt`

### Why the published image is not a reproducible release artifact

The upstream AF2 Dockerfile:

1. starts from mutable
   `nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu20.04`;
2. downloads `micromamba` from a mutable `latest` endpoint;
3. resolves mostly unpinned Conda dependencies;
4. runs `git clone --recurse-submodules
   https://github.com/KosinskiLab/AlphaPulldown.git`;
5. never checks out or verifies the `2.5.0` commit before installation.

See `docker/alphafold2.dockerfile:2-3,25-48,53-65`.

The release workflow tags the resulting image with the release name, but does
not pass the release commit to the Dockerfile. See
`.github/workflows/github_actions.yml:158-188`. A `2.5.0` image tag therefore
does not prove that the installed source is commit `1c99b15...`.

On 2026-07-30, Docker Hub reported:

- tag index:
  `sha256:1201bffa36f9aca903cc51e494283f53eb5594c7860ba499e17a5ea7aece9d8d`;
- amd64 manifest:
  `sha256:434704a18e24d59de7cbfd6f7cdc310d5dce03ded6cf91c4927b6e2c9e87110c`;
- config:
  `sha256:370458d88b165f036727061b4484495488a42ea1d9bd5c8e011c76b2724ab0c4`.

Those metadata records claim Python 3.11 and AlphaPulldown installation layers,
but the RunPod execution contract did not match them. The discrepancy must not
be resolved by assuming the registry metadata is correct.

## Verifiable upstream runtime source

PyPI publishes an immutable AlphaPulldown 2.5.0 wheel:

```text
alphapulldown-2.5.0-py3-none-any.whl
sha256:67a8496560fddf9c9570015bf88545e48502fad7cc12f995dc69a5999a0ad75a
```

The wheel contains:

- `alphapulldown`;
- the vendored AlphaFold and ColabFold Python packages;
- `create_individual_features.py`;
- `run_structure_prediction.py`;
- package metadata declaring AlphaPulldown `2.5.0`.

Local audit comparisons found identical SHA-256 values between the wheel and
the pinned Git checkout for:

- `alphapulldown/__init__.py`;
- both required CLI modules;
- `alphapulldown/folding_backend/alphafold2_backend.py`;
- `alphafold/model/config.py`;
- `colabfold/batch.py`.

This wheel, pinned by its own SHA-256, is the preferred AlphaPulldown software
artifact. The Git commit and submodule SHAs remain provenance evidence. The
image build must not clone repository HEAD.

## Replacement image specification

### Immutable base

Use the official NVIDIA amd64 runtime directly:

```text
nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu20.04
amd64 manifest:
sha256:1da6cf17f9c651323905c8cf5fd63a781a9a2fc0d28a477ca21df80a7bfaa00c
```

The recorded multi-platform index is
`sha256:8d29e0f835bf0c038a105444fa6f07fcbc0081ca11f6a9fa72fd67ac82a1de9f`.
The Dockerfile must use the amd64 manifest digest and reject any non-amd64
build.

Use a pinned micromamba bootstrap stage:

```text
mambaorg/micromamba:2.5.0
amd64 manifest:
sha256:07f1a5db3a545a0b1b0b1c8835ba654b67a8479ec77513f2a236f45e6687629b
```

### Dependency policy

Do not resolve dependencies during the production image build.

Before the Dockerfile is considered runnable, commit:

1. an explicit `linux-64` Conda lock containing Python 3.10 and required native
   packages, including HMMER, HHsuite, Kalign, OpenMM, and PDBFixer;
2. a hashed pip lock for Linux amd64/Python 3.10 containing the AlphaPulldown
   wheel URL and SHA-256, `jax==0.5.3` with CUDA 12 support,
   `tensorflow-cpu==2.20.0`, `numpy==1.26.4`, ModelCIF, the input parser, and
   every resolved transitive dependency;
3. the lock-generator version, input constraints, target platform, and
   generation command.

The production Dockerfile must install only from these locks, use
`pip --require-hashes`, run `pip check`, and contain no mutable Git clone,
`latest` URL, unconstrained package installation, or AF3 dependency.

The official backend guide identifies Python 3.10, JAX/JAXlib 0.5.3, NumPy
1.26.4, TensorFlow CPU 2.20.0, PDBFixer 1.12, and ModelCIF 1.6 as its validated
AF2 stack. OpenMM needs special resolution: the guide reports 8.1.1, while
the `2.5.0` package metadata requires `openmm>=8.2`. The lock must satisfy the
package metadata and pass the smoke suite; it must not silently force 8.1.1.

### Dockerfile shape

The implementation should have this dependency flow:

```dockerfile
FROM --platform=linux/amd64 \
  mambaorg/micromamba:2.5.0@sha256:07f1a5... AS micromamba

FROM --platform=linux/amd64 \
  nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu20.04@sha256:1da6cf...

# Copy the pinned micromamba binary.
# Create /opt/conda from the committed explicit linux-64 lock.
# Install the SHA-pinned AlphaPulldown wheel and pip lock with --require-hashes.
# Install this repository's runner with --no-deps.
# Copy and execute CPU image smoke tests.
# Record source commit, wheel hash, lock hashes, and image revision as labels.
```

This is a specification, not permission to build the current uncorrected
`deployment/runpod/Dockerfile`.

## Mandatory validation gates

### Gate 1: amd64 CPU build and image smoke test

An amd64 Docker builder or CI runner must build the image and run all of:

```text
python version is exactly the locked Python 3.10 release
importlib.metadata.version("alphapulldown") == "2.5.0"
import alphapulldown
import alphafold
import colabfold
import jax
jax.__version__ == "0.5.3"
import openmm
import alphapulldown.scripts.create_individual_features
command -v create_individual_features.py
command -v run_structure_prediction.py
pip check
```

The feature CLI may be exercised with help-only arguments. No sequence, MSA,
template, model parameter, network-service, or inference command is allowed.

`run_structure_prediction.py` imports JAX and requests a GPU at module import
time (`run_structure_prediction.py:12-13`). Its import/help test therefore
belongs to the GPU gate, not a CPU-only build gate.

The image must not be published or accepted if any CPU gate fails.

### Gate 2: software supply-chain evidence

After Gate 1:

- generate an SBOM;
- record the Dockerfile, lockfile, wheel, and project Git checksums;
- inspect the image architecture and labels;
- assign a candidate tag;
- record the immutable derived-image digest;
- retain the complete build and smoke logs.

The digest must not be promoted into `image-lock.json` until these checks pass.

### Gate 3: no-data NVIDIA smoke test

Only after Gates 1 and 2 pass may a GPU-capable environment run:

```text
nvidia-smi
import jax
jax.local_devices(backend="gpu") returns at least one GPU
import alphapulldown.scripts.run_structure_prediction
both AlphaPulldown CLI paths remain present
the installed AlphaPulldown/JAX versions equal their locks
```

This gate performs no feature generation or prediction. A RunPod Pod is not
approved before the candidate image passes the local/CI gates.

### Gate 4: scientific execution

Not approved by this audit. It remains blocked until:

- the first three gates pass;
- the derived digest is reviewed and pinned;
- AlphaFold2 model parameters are provisioned and checksummed;
- the native prediction command is separately audited for multimer settings;
- Milestone 2 isolation tests still pass.

## Current repository consequences

The following current assumptions are invalid:

| Component | Invalid assumption | Required correction |
| --- | --- | --- |
| `deployment/runpod/Dockerfile` | The official AP image contains a dependable runtime. | Rebase on immutable NVIDIA CUDA and install the SHA-pinned AP wheel from locks. |
| `deployment/runpod/image-lock.json` | The AP Docker Hub manifest is an acceptable base identity. | Record NVIDIA base, AP wheel, Git/submodule, lock, and derived image identities separately. |
| `native_runtime.py` | `/AlphaPulldown` Git metadata will exist in the image. | Read immutable build metadata/labels or a generated identity file; a wheel install has no Git checkout. |
| RunPod checklist Phase 0 | The official image should be tested again. | Remove this step; it has failed and must not be repeated. |
| Image validation | Package version and command presence are enough. | Require CPU imports, `pip check`, CLI-module checks, JAX version, SBOM, and a later GPU JAX test. |
| Scientific readiness | A derived digest is the only remaining runtime gate. | Also require locked model parameters and an audited AF2 multimer prediction command. |

The current Dockerfile and image lock are **rejected artifacts**. They must not
be built, pushed, or used to start another Pod.

## Proposed implementation files

No runtime implementation is made by this audit. The next reviewed change
should modify or add:

```text
deployment/runpod/Dockerfile
deployment/runpod/image-lock.json
deployment/runpod/conda-linux-64.lock
deployment/runpod/requirements-linux-x86_64.lock
deployment/runpod/lock-inputs/
deployment/runpod/smoke_cpu.py
deployment/runpod/smoke_gpu.py
scripts/remote/validate_native_image.sh
src/alphapulldown_dnaaf_screen/native_runtime.py
tests/test_native_image_contract.py
.github/workflows/runpod-image.yml
docs/operations/RUNPOD_EXECUTION_CHECKLIST.md
docs/validation/RUNPOD_DOCKER_NATIVE_MIGRATION_AUDIT.md
```

CI must build `linux/amd64`, run the CPU smoke gate, and retain logs before any
registry push job can run. Registry publication should require an explicit
manual approval. GPU validation remains a separate no-data gate.

## Unresolved items

1. Generate and review Linux amd64 Conda and pip locks.
2. Resolve an OpenMM version satisfying `openmm>=8.2` and the smoke suite.
3. Select the image registry and authentication mechanism.
4. Select an amd64 builder with enough disk for the image and BuildKit cache.
5. Select an NVIDIA smoke-test host after CPU CI passes.
6. Provision and checksum licensed AlphaFold2 model parameters separately.
7. Audit the project-native prediction command before it is allowed to run;
   the upstream CLI defaults `model_preset` to `monomer`.

Until these are resolved, the correct next action is image-build engineering
and CI validation, not another RunPod Pod.
