from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from alphapulldown_dnaaf_screen.native_cli import main as native_main
from alphapulldown_dnaaf_screen.native_runtime import (
    ALPHAPULLDOWN_SOURCE_REVISION,
    ALPHAPULLDOWN_WHEEL_SHA256,
    BASE_IMAGE_DIGEST,
    FORBIDDEN_EXECUTABLES,
    UNBUILT_IMAGE_DIGEST,
    feature_commands,
    load_native_config,
    prediction_commands,
    runtime_identity,
    validate_host_runtime,
    validate_runtime_identity,
    write_native_provenance,
)
from alphapulldown_dnaaf_screen.validation import ValidationError

EXPECTED_SCENARIOS = {
    "human_dnaaf18_ift46_negative",
    "human_dnaaf9_ift74_ift81_known",
    "human_dnaaf9_ift46_ift74_ift81_exploratory",
    "human_dnaaf9_ift80_ift172_exploratory",
    "human_dnai1_ift46_ift74_ift81_exploratory",
    "human_dnai2_ift46_ift74_ift81_exploratory",
    "human_dnai1_dnai2_ift46_ift74_ift81_exploratory",
    "human_dnai1_dnai2_ift80_ift172_exploratory",
}


def native_fixture(
    root: Path,
    *,
    stage: str = "cpu",
    derived_digest: str = UNBUILT_IMAGE_DIGEST,
) -> Path:
    source_root = Path.cwd()
    benchmark_root = root / "data/processed/benchmarks"
    benchmark_inputs = benchmark_root / "alphapulldown_inputs"
    benchmark_fasta = benchmark_root / "fasta"
    fasta_dir = root / "data/processed/fasta"
    deployment = root / "deployment/aws"
    weights_dir = root / "alphafold2-model-weights"
    for path in [benchmark_inputs, benchmark_fasta, fasta_dir, deployment, weights_dir]:
        path.mkdir(parents=True, exist_ok=True)

    shutil.copy2(
        source_root / "data/processed/benchmarks/milestone2_scenarios.json",
        benchmark_root / "milestone2_scenarios.json",
    )
    shutil.copy2(
        source_root
        / "data/processed/benchmarks/alphapulldown_inputs/milestone2_sample_sheet.tsv",
        benchmark_inputs / "milestone2_sample_sheet.tsv",
    )
    shutil.copy2(
        source_root / "data/processed/benchmarks/fasta/fasta_manifest.tsv",
        benchmark_fasta / "fasta_manifest.tsv",
    )
    for row in (benchmark_fasta / "fasta_manifest.tsv").read_text().splitlines()[1:]:
        record_id = row.split("\t", 1)[0]
        shutil.copy2(
            source_root / "data/processed/fasta" / f"{record_id}.fasta",
            fasta_dir / f"{record_id}.fasta",
        )
    shutil.copy2(
        source_root / "deployment/aws/image-lock.json",
        deployment / "image-lock.json",
    )

    env = root / "paths.env"
    env.write_text(
        "\n".join(
            [
                f"REMOTE_PROJECT_ROOT={root}",
                f"REMOTE_EXECUTION_STAGE={stage}",
                "CONTAINER_RUNTIME=docker-native",
                "PYTHON_BIN=python3",
                "FEATURE_MODE=mmseqs2",
                "FEATURE_FILE_PATTERN={fasta_identifier}.pkl.xz",
                "NATIVE_DATA_PIPELINE=alphafold2",
                "NATIVE_FOLD_BACKEND=alphafold2",
                "NATIVE_ENABLE_ALPHAJUDGE=false",
                "MAX_TEMPLATE_DATE=2050-01-01",
                "DATABASES_DIR=",
                f"BACKEND_WEIGHTS_DIR={weights_dir}",
                f"FASTA_DIR={fasta_dir}",
                f"FASTA_MANIFEST={benchmark_fasta / 'fasta_manifest.tsv'}",
                f"ALPHAPULLDOWN_INPUT_DIR={benchmark_inputs}",
                f"FEATURE_DIR={root / 'results/milestone2_benchmark/features'}",
                f"OUTPUT_DIR={root / 'results/milestone2_benchmark/alphapulldown'}",
                f"LOG_DIR={root / 'results/milestone2_benchmark/logs'}",
                f"TMP_DIR={root / 'results/milestone2_benchmark/tmp'}",
                f"PROVENANCE_DIR={root / 'results/provenance/milestone2_benchmark'}",
                f"NATIVE_IMAGE_LOCK={deployment / 'image-lock.json'}",
                f"ALPHAPULLDOWN_BASE_IMAGE_DIGEST={BASE_IMAGE_DIGEST}",
                f"ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST={derived_digest}",
                "ALPHAPULLDOWN_EXPECTED_VERSION=2.5.0",
                "ALPHAPULLDOWN_EXPECTED_REVISION=",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return env


def create_features(config) -> None:
    config.feature_dir.mkdir(parents=True, exist_ok=True)
    manifest = config.fasta_manifest.read_text(encoding="utf-8").splitlines()[1:]
    for row in manifest:
        record_id = row.split("\t", 1)[0]
        accession = row.split("\t")[1]
        display_name = record_id.removeprefix("HUMAN_")
        (config.feature_dir / f"{record_id}_{accession}_{display_name}.pkl.xz").write_bytes(
            b"feature"
        )


class DockerNativeRuntimeTests(unittest.TestCase):
    def test_valid_config_is_strictly_milestone2(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp)))
            self.assertEqual(config.container_runtime, "docker-native")
            self.assertEqual(config.feature_pattern, "{fasta_identifier}.pkl.xz")
            self.assertIn("benchmarks/fasta", str(config.fasta_manifest))
            self.assertNotEqual(
                config.fasta_manifest,
                config.project_root / "data/processed/fasta/fasta_manifest.tsv",
            )

    def test_target_universe_manifest_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = native_fixture(root)
            target_manifest = root / "data/processed/fasta/fasta_manifest.tsv"
            target_manifest.write_text("record_id\taccession\n", encoding="utf-8")
            env.write_text(
                env.read_text().replace(
                    str(root / "data/processed/benchmarks/fasta/fasta_manifest.tsv"),
                    str(target_manifest),
                )
            )
            with self.assertRaisesRegex(ValidationError, "benchmark FASTA manifest"):
                load_native_config(env)

    def test_af3_selectors_and_alphajudge_are_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = native_fixture(Path(tmp))
            env.write_text(
                env.read_text()
                .replace("NATIVE_DATA_PIPELINE=alphafold2", "NATIVE_DATA_PIPELINE=alphafold3")
                .replace("NATIVE_ENABLE_ALPHAJUDGE=false", "NATIVE_ENABLE_ALPHAJUDGE=true")
            )
            with self.assertRaisesRegex(ValidationError, "AlphaFold2 only"):
                load_native_config(env)

            env = native_fixture(Path(tmp))
            env.write_text(
                env.read_text().replace(
                    "NATIVE_ENABLE_ALPHAJUDGE=false", "NATIVE_ENABLE_ALPHAJUDGE=true"
                )
            )
            with self.assertRaisesRegex(ValidationError, "AlphaJudge"):
                load_native_config(env)

    def test_apptainer_configuration_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = native_fixture(Path(tmp))
            env.write_text(env.read_text() + "APPTAINER_PREDICTION_SIF=/workspace/test.sif\n")
            with self.assertRaisesRegex(ValidationError, "incompatible"):
                load_native_config(env)

    def test_blocked_chlamydomonas_scenario_cannot_be_added(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = native_fixture(root)
            sample = (
                root
                / "data/processed/benchmarks/alphapulldown_inputs/milestone2_sample_sheet.tsv"
            )
            with sample.open("a", encoding="utf-8") as handle:
                handle.write("chlamy_dnaaf18_ift46_positive\t\t\n")
            with self.assertRaisesRegex(ValidationError, "blocked"):
                load_native_config(env)

    def test_feature_commands_preserve_af2_mmseqs2_semantics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp)))
            commands = feature_commands(config)
            self.assertEqual(len(commands), 9)
            for command in commands:
                self.assertEqual(command[0], "create_individual_features.py")
                self.assertIn("--data_dir=", command)
                self.assertIn("--compress_features=True", command)
                self.assertIn("--data_pipeline=alphafold2", command)
                self.assertIn("--use_mmseqs2=True", command)
                self.assertIn("--skip_existing=True", command)
                self.assertNotIn("\n", " ".join(command))
                self.assertFalse(FORBIDDEN_EXECUTABLES.intersection(command))
                self.assertNotIn("alphafold3", " ".join(command).lower())

    def test_stage_guards_are_directional(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp), stage="cpu"))
            with self.assertRaisesRegex(ValidationError, "REMOTE_EXECUTION_STAGE=gpu"):
                prediction_commands(config)

            config = load_native_config(native_fixture(Path(tmp), stage="gpu"))
            with self.assertRaisesRegex(ValidationError, "REMOTE_EXECUTION_STAGE=cpu"):
                feature_commands(config)

    def test_prediction_emits_exactly_eight_ready_human_scenarios(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp), stage="gpu"))
            create_features(config)
            commands = prediction_commands(config)
            self.assertEqual(len(commands), 8)
            scenario_ids = {
                next(arg for arg in command if arg.startswith("--output_directory=")).split("/")[-1]
                for command in commands
            }
            self.assertEqual(scenario_ids, EXPECTED_SCENARIOS)
            for command in commands:
                self.assertEqual(command[0], "run_structure_prediction.py")
                self.assertIn("--fold_backend=alphafold2", command)
                self.assertIn("--convert_to_modelcif=False", command)
                self.assertNotIn("chlamy_dnaaf18_ift46_positive", " ".join(command))
                self.assertNotIn("alphajudge", " ".join(command).lower())
                input_argument = next(arg for arg in command if arg.startswith("--input="))
                self.assertNotRegex(input_argument, r"(?:=|\\+)HUMAN_[A-Z0-9]+(?=\\+|$)")
                self.assertRegex(input_argument, r"HUMAN_[A-Z0-9]+_[A-Z0-9]+_[A-Z0-9]+")

    def test_prediction_can_select_one_permitted_scenario(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp), stage="gpu"))
            create_features(config)
            commands = prediction_commands(
                config, scenario_id="human_dnaaf18_ift46_negative"
            )
            self.assertEqual(len(commands), 1)
            self.assertIn(
                "human_dnaaf18_ift46_negative",
                " ".join(commands[0]),
            )
            with self.assertRaisesRegex(ValidationError, "blocked"):
                prediction_commands(
                    config, scenario_id="chlamy_dnaaf18_ift46_positive"
                )

    def test_prediction_uses_real_alphapulldown_fasta_identifier_feature_names(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp), stage="gpu"))
            create_features(config)
            prediction_commands(config)
            self.assertTrue(
                (
                    config.feature_dir / "HUMAN_IFT80_Q9P2H3_IFT80.pkl.xz"
                ).is_file()
            )
            self.assertFalse((config.feature_dir / "HUMAN_IFT80.pkl.xz").exists())

    def test_prediction_uses_feature_identifiers_not_internal_record_ids(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp), stage="gpu"))
            create_features(config)
            commands = prediction_commands(config)
            first_input = next(arg for arg in commands[0] if arg.startswith("--input="))
            self.assertEqual(
                first_input,
                "--input=HUMAN_DNAAF18_Q8N136_DNAAF18+HUMAN_IFT46_Q9NQC8_IFT46",
            )

    def test_prediction_refuses_missing_features(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp), stage="gpu"))
            with self.assertRaisesRegex(ValidationError, "Missing required AF2 feature"):
                prediction_commands(config)

    def test_prediction_refuses_empty_or_missing_model_weights_directory(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = native_fixture(root, stage="gpu")
            create_features(load_native_config(env))
            env.write_text(
                env.read_text().replace("BACKEND_WEIGHTS_DIR=" + str(root / "alphafold2-model-weights"), "BACKEND_WEIGHTS_DIR=")
            )
            with self.assertRaisesRegex(ValidationError, "BACKEND_WEIGHTS_DIR"):
                prediction_commands(load_native_config(env))

            env = native_fixture(root, stage="gpu")
            create_features(load_native_config(env))
            missing = root / "missing-model-weights"
            env.write_text(
                env.read_text().replace(
                    "BACKEND_WEIGHTS_DIR=" + str(root / "alphafold2-model-weights"),
                    "BACKEND_WEIGHTS_DIR=" + str(missing),
                )
            )
            with self.assertRaisesRegex(ValidationError, "does not exist"):
                prediction_commands(load_native_config(env))

    def test_scientific_execution_requires_real_derived_digest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp), stage="cpu"))
            with mock.patch(
                "alphapulldown_dnaaf_screen.native_runtime.platform.system",
                return_value="Linux",
            ):
                with self.assertRaisesRegex(ValidationError, "real derived image digest"):
                    validate_host_runtime(
                        config,
                        command="features",
                        dry_run=False,
                        which=lambda name: f"/usr/bin/{name}",
                    )

    def test_scientific_execution_requires_promoted_lock_and_revision(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(
                native_fixture(Path(tmp), stage="cpu", derived_digest="sha256:derived")
            )
            with mock.patch(
                "alphapulldown_dnaaf_screen.native_runtime.platform.system",
                return_value="Linux",
            ):
                with self.assertRaisesRegex(ValidationError, "image-lock.json"):
                    validate_host_runtime(
                        config,
                        command="features",
                        dry_run=False,
                        which=lambda name: f"/usr/bin/{name}",
                    )

    def test_gpu_preflight_requires_nvidia_and_checks_it(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(
                native_fixture(Path(tmp), stage="gpu", derived_digest="sha256:derived")
            )
            lock = json.loads(config.image_lock.read_text())
            lock["derived_image_digest"] = "sha256:derived"
            config.image_lock.write_text(json.dumps(lock))
            env = Path(tmp) / "paths.env"
            env.write_text(
                env.read_text().replace(
                    "ALPHAPULLDOWN_EXPECTED_REVISION=",
                    "ALPHAPULLDOWN_EXPECTED_REVISION=abc123",
                )
            )
            config = load_native_config(env)
            with mock.patch(
                "alphapulldown_dnaaf_screen.native_runtime.platform.system",
                return_value="Linux",
            ):
                with self.assertRaisesRegex(ValidationError, "nvidia-smi"):
                    validate_host_runtime(
                        config,
                        command="predict",
                        dry_run=False,
                        which=lambda name: None if name == "nvidia-smi" else f"/usr/bin/{name}",
                    )

                seen: list[list[str]] = []

                def successful_gpu(command):
                    seen.append(list(command))
                    return subprocess.CompletedProcess(command, 0, "A40", "")

                validate_host_runtime(
                    config,
                    command="predict",
                    dry_run=False,
                    which=lambda name: f"/usr/bin/{name}",
                    runner=successful_gpu,
                )
                self.assertEqual(seen[0][0], "nvidia-smi")

    def test_runtime_identity_and_provenance_are_complete(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_native_config(native_fixture(Path(tmp)))
            commands = feature_commands(config)
            identity = runtime_identity(
                config,
                package_version="2.5.0",
                source_revision="abc123",
            )
            validate_runtime_identity(config, identity)
            path = write_native_provenance(
                config,
                run_id="native-test",
                stage_command="features",
                commands=commands,
                dry_run=True,
                status="dry-run",
                identity=identity,
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["runtime"]["base_image_digest"], BASE_IMAGE_DIGEST)
            self.assertEqual(payload["runtime"]["derived_image_digest"], UNBUILT_IMAGE_DIGEST)
            self.assertEqual(payload["runtime"]["alphapulldown_version"], "2.5.0")
            self.assertEqual(payload["runtime"]["alphapulldown_revision"], "abc123")
            self.assertTrue(payload["inputs"])
            self.assertTrue(all(item["sha256"] for item in payload["inputs"]))
            self.assertFalse(payload["feature_semantics"]["alphajudge_enabled"])

    def test_native_cli_dry_run_is_offline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = native_fixture(Path(tmp))
            self.assertEqual(native_main(["--config", str(env), "features", "--dry-run"]), 0)

    def test_aws_dockerfile_is_immutable_amd64_and_has_no_nested_runtime(self) -> None:
        text = Path("deployment/aws/Dockerfile").read_text(encoding="utf-8")
        self.assertIn("FROM --platform=linux/amd64", text)
        self.assertIn(f"@{BASE_IMAGE_DIGEST}", text)
        self.assertIn(ALPHAPULLDOWN_WHEEL_SHA256, text)
        self.assertIn(ALPHAPULLDOWN_SOURCE_REVISION, text)
        self.assertIn("smoke_cpu.py", text)
        self.assertIn('CMD ["sleep", "infinity"]', text)
        self.assertIn(
            "COPY --from=micromamba /bin/micromamba /usr/local/bin/micromamba",
            text,
        )
        self.assertNotIn(
            "COPY --from=micromamba /usr/local/bin/micromamba",
            text,
        )
        self.assertNotIn("python -m pip install --no-cache-dir --no-deps .", text)
        self.assertNotIn("COPY pyproject.toml README.md", text)
        for token in ["git clone", "apptainer", "singularity", "docker.sock"]:
            self.assertNotIn(token, text.lower())

    def test_aws_smoke_scripts_validate_help_output_not_only_exit_status(self) -> None:
        for path, expected_flag in [
            (Path("deployment/aws/smoke_cpu.py"), "use_mmseqs2"),
            (Path("deployment/aws/smoke_gpu.py"), "--output_directory"),
        ]:
            text = path.read_text(encoding="utf-8")
            self.assertIn("result.returncode not in (0, 1)", text)
            self.assertIn("stdout=subprocess.PIPE", text)
            self.assertIn(expected_flag, text)
            self.assertNotIn("check=True", text)

    def test_image_lock_records_successful_aws_smoke_validation(self) -> None:
        payload = json.loads(Path("deployment/aws/image-lock.json").read_text())
        self.assertEqual(payload["base_image_digest"], BASE_IMAGE_DIGEST)
        self.assertEqual(
            payload["derived_image_digest"],
            "sha256:458537ff9ac8363406f0ce545c74d5a954595de651f1a0dc770577ec49e70759",
        )
        self.assertEqual(payload["derived_image_identity_kind"], "docker-local-image-id")
        self.assertEqual(payload["derived_image_reference"], "alphapulldown-af2:candidate")
        self.assertEqual(payload["validated_on"], "2026-08-29")
        self.assertIn("GPU smoke test", payload["validation_checks"][1])
        self.assertEqual(payload["alphapulldown_wheel_sha256"], ALPHAPULLDOWN_WHEEL_SHA256)
        self.assertEqual(payload["expected_alphapulldown_revision"], ALPHAPULLDOWN_SOURCE_REVISION)

    def test_rejected_runpod_dockerfile_cannot_be_accidentally_built(self) -> None:
        self.assertFalse(Path("deployment/runpod/Dockerfile").exists())
        self.assertFalse(Path("deployment/runpod/image-lock.json").exists())
        text = Path("deployment/runpod/Dockerfile.rejected").read_text(encoding="utf-8")
        self.assertIn("Do not build or deploy", text)

    def test_aws_scripts_only_build_or_smoke_test_images(self) -> None:
        build_script = Path("scripts/aws/build_candidate_image.sh").read_text(encoding="utf-8")
        gpu_script = Path("scripts/aws/smoke_gpu_image.sh").read_text(encoding="utf-8")
        self.assertIn("--platform linux/amd64", build_script)
        self.assertIn("smoke_cpu.py", build_script)
        self.assertIn("conda-explicit.txt", build_script)
        self.assertIn("pip-freeze.txt", build_script)
        self.assertIn("--gpus all", gpu_script)
        for text in [build_script, gpu_script]:
            self.assertNotIn("create_individual_features.py", text)
            self.assertNotIn("run_structure_prediction.py", text)

    def test_aws_stage_wrapper_uses_validated_image_and_benchmark_mount(self) -> None:
        wrapper = Path("scripts/aws/run_milestone2_stage.sh").read_text(encoding="utf-8")
        configure = Path("scripts/aws/configure_milestone2_runtime.sh").read_text(
            encoding="utf-8"
        )
        template = Path("config/benchmarks/milestone2_aws.example.env").read_text(
            encoding="utf-8"
        )
        self.assertIn("docker image inspect", wrapper)
        self.assertIn("ALPHAPULLDOWN_DERIVED_IMAGE_DIGEST", wrapper)
        self.assertIn("--volume", wrapper)
        self.assertIn("BACKEND_WEIGHTS_DIR", wrapper)
        self.assertIn("model-weights directory does not exist on the host", wrapper)
        self.assertIn('"${BACKEND_WEIGHTS_DIR}:${BACKEND_WEIGHTS_DIR}:ro"', wrapper)
        self.assertIn("--user", wrapper)
        self.assertIn("--gpus all", wrapper)
        self.assertIn("alphapulldown_dnaaf_screen.native_cli", wrapper)
        self.assertNotIn("snakemake --", wrapper.lower())
        self.assertNotIn("apptainer exec", wrapper.lower())
        self.assertIn("Refusing to overwrite", configure)
        self.assertIn("__PROJECT_ROOT__", template)
        self.assertIn('NATIVE_IMAGE_REFERENCE="alphapulldown-af2:candidate"', template)
        self.assertIn("benchmarks/fasta/fasta_manifest.tsv", template)
        self.assertNotIn("data/processed/fasta/fasta_manifest.tsv", template)

    def test_legacy_runpod_wrappers_refuse_native_mode(self) -> None:
        for path in [
            Path("scripts/remote/run_feature_generation.sh"),
            Path("scripts/remote/run_prediction.sh"),
        ]:
            text = path.read_text(encoding="utf-8")
            self.assertIn('== "docker-native"', text)
            self.assertIn("run_native_stage.sh", text)


if __name__ == "__main__":
    unittest.main()
