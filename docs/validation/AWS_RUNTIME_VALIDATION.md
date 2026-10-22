# AWS Runtime Validation Record

## Environment Validation

On 2026-08-29, the project Docker image passed no-data CPU and GPU checks on
AWS EC2:

- AlphaPulldown 2.5.0 and the feature-generation CLI loaded successfully.
- JAX 0.5.3 detected an NVIDIA A10G through Docker.
- The AlphaPulldown prediction CLI loaded with the AlphaFold2 backend.

The validated local image ID was
`sha256:458537ff9ac8363406f0ce545c74d5a954595de651f1a0dc770577ec49e70759`.
It is local to the EBS-backed host, not a registry artifact.

## Scientific Execution

The validated runtime subsequently generated MMseqs2 features for nine human
benchmark proteins and completed four AlphaFold2-Multimer prediction sets.
The full results and interpretation are recorded in
[Milestone 2 Pilot Results](MILESTONE2_PILOT_RESULTS.md).

## Limitation Identified

An L40S GPU had adequate VRAM for a DNAAF9 + IFT46 + IFT74 + IFT81 assembly,
but the 32 GiB host was terminated by the kernel during output processing.
Future large assemblies require more host system RAM; incomplete runs must not
be analysed as results.
