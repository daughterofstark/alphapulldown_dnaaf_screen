# Compute Environment Requirements

## Scope

The current implementation requires Linux and an NVIDIA GPU only for the
AlphaFold2-Multimer prediction stage. macOS is suitable for target preparation,
result parsing, documentation, and structure inspection.

## Required Host Capabilities

| Component | Requirement |
| --- | --- |
| Operating system | x86_64 Linux |
| Container runtime | Docker with NVIDIA Container Toolkit |
| GPU | NVIDIA GPU visible through `nvidia-smi` and Docker `--gpus all` |
| GPU memory | At least 24 GiB for the small completed assemblies; more may be needed for larger multimers |
| System RAM | At least 64 GiB is recommended for larger assemblies; 32 GiB was insufficient for one four-protein assembly |
| CPU feature stage | Network access to the MMseqs2 service and sufficient local disk for feature files |
| Storage | Persistent storage for project checkout, model parameters, features, outputs, logs, and provenance |

## Required Software

- Git
- Docker
- NVIDIA driver and NVIDIA Container Toolkit for GPU prediction
- The pinned project Docker image
- AWS CLI only when AWS command-line administration is required; it is not
  needed to run a prepared local image on an EC2 host

The container provides AlphaPulldown, AlphaFold2 dependencies, JAX, OpenMM,
HHsuite, HMMER, Kalign, and ModelCIF dependencies. Do not install these tools
globally on the host as a substitute for the pinned image.

## Persistent Files

Preserve between sessions:

- AlphaFold model parameters
- precomputed `.pkl.xz` feature files and associated MSA metadata
- benchmark configuration and provenance records
- complete prediction directories
- Docker image or an approved registry reference

Do not commit credentials, private SSH keys, cloud-specific `paths.env` files,
databases, features, or prediction outputs to Git.

## Minimum Validation

```bash
docker version
nvidia-smi
docker run --rm --gpus all alphapulldown-af2:candidate python -c 'import jax; print(jax.devices())'
```

The final command must report an NVIDIA-backed JAX device before prediction.
