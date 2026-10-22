from __future__ import annotations

import json
import platform
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from alphapulldown_dnaaf_screen.remote import (
    SUPPORTED_FEATURE_MODES,
    UPSTREAM_CONFIG_KEYS,
    create_run_provenance,
    feature_generation_command,
    load_remote_config,
    missing_features,
    parse_env_file,
    prediction_command,
    pinned_workflow_feature_plan,
    render_pinned_create_features_command,
    require_linux,
    stable_run_id,
    snakemake_base_command,
    upstream_cli_parameters,
    validate_configured_sif,
    validate_feature_execution_model,
    write_resolved_feature_config,
    write_resolved_prediction_config,
)
from alphapulldown_dnaaf_screen.validation import ValidationError


def write_fixture(root: Path) -> Path:
    processed = root / "data" / "processed"
    ap = processed / "alphapulldown"
    fasta = processed / "fasta"
    config = root / "config" / "remote"
    results = root / "results"
    setup_dirs = [
        ap,
        fasta,
        config,
        results / "features",
        results / "predictions",
        results / "logs",
    ]
    for path in setup_dirs:
        path.mkdir(parents=True, exist_ok=True)

    (ap / "control_sample_sheet.csv").write_text("Q5TEA3+Q96LB3\nQ8N136+Q9NQC8\n")
    (ap / "transport_baits.txt").write_text("Q5TEA3\nQ8N136\n")
    (ap / "ift_b_preys.txt").write_text("Q96LB3\nQ8WYA0\nQ86WT1\nQ8N4P2\n")
    (ap / "full_screen_pairs.tsv").write_text(
        "bait_accession\tprey_accession\nQ5TEA3\tQ96LB3\nQ5TEA3\tQ86WT1\n"
    )
    (fasta / "fasta_manifest.tsv").write_text(
        "record_id\taccession\n"
        "HUMAN_DNAAF9\tQ5TEA3\n"
        "HUMAN_DNAAF18\tQ8N136\n"
        "HUMAN_IFT74\tQ96LB3\n"
        "HUMAN_IFT81\tQ8WYA0\n"
        "HUMAN_IFT46\tQ9NQC8\n"
        "HUMAN_IFT70A\tQ86WT1\n"
        "HUMAN_IFT70B\tQ8N4P2\n"
    )
    for record_id in [
        "HUMAN_DNAAF9",
        "HUMAN_DNAAF18",
        "HUMAN_IFT74",
        "HUMAN_IFT81",
        "HUMAN_IFT46",
        "HUMAN_IFT70A",
        "HUMAN_IFT70B",
    ]:
        (fasta / f"{record_id}.fasta").write_text(f">{record_id}|TEST|{record_id}\nMA\n")
    (config / "feature_generation.example.yaml").write_text("stage: feature_generation\n")
    (config / "prediction.example.yaml").write_text("stage: prediction\n")
    env = config / "paths.env"
    env.write_text(
        "\n".join(
            [
                f"REMOTE_PROJECT_ROOT={root}",
                "REMOTE_EXECUTION_STAGE=cpu",
                "AP_WORKFLOW_DIR=${REMOTE_PROJECT_ROOT}/workflow",
                "AP_ENV_YAML=",
                "CONDA_ENV_NAME=snake",
                "AP_SNAKEMAKE_VERSION=2.5.0",
                "FEATURE_CONFIG=${REMOTE_PROJECT_ROOT}/config/remote/"
                "feature_generation.example.yaml",
                "PREDICTION_CONFIG=${REMOTE_PROJECT_ROOT}/config/remote/prediction.example.yaml",
                "FASTA_MANIFEST=${REMOTE_PROJECT_ROOT}/data/processed/fasta/fasta_manifest.tsv",
                "ALPHAPULLDOWN_INPUT_DIR=${REMOTE_PROJECT_ROOT}/data/processed/alphapulldown",
                "FASTA_DIR=${REMOTE_PROJECT_ROOT}/data/processed/fasta",
                "FEATURE_DIR=${REMOTE_PROJECT_ROOT}/results/features",
                "OUTPUT_DIR=${REMOTE_PROJECT_ROOT}/results/predictions",
                "LOG_DIR=${REMOTE_PROJECT_ROOT}/results/logs",
                "TMP_DIR=${REMOTE_PROJECT_ROOT}/results/tmp",
                "PROVENANCE_DIR=${REMOTE_PROJECT_ROOT}/results/provenance",
                "DATABASES_DIR=${REMOTE_PROJECT_ROOT}/databases",
                "BACKEND_WEIGHTS_DIR=${REMOTE_PROJECT_ROOT}/weights",
                "FEATURE_MODE=localdb",
                "FEATURE_FILE_PATTERN={record_id}_af3_input.json",
                "SNAKEMAKE_CORES=4",
                "SNAKEMAKE_JOBS=1",
                "APPTAINER_PREFIX=${REMOTE_PROJECT_ROOT}/results/containers/snakemake_apptainer",
                "SNAKEMAKE_PROFILE=",
                "SLURM_PROFILE=",
                "",
            ]
        )
    )
    return env


class RemoteHandoffTests(unittest.TestCase):
    def test_config_parsing_expands_previous_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            values = parse_env_file(env)
            self.assertEqual(values["FEATURE_DIR"], f"{tmp}/results/features")

    def test_missing_path_failure_for_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            text = env.read_text().replace("REMOTE_PROJECT_ROOT=", "#REMOTE_PROJECT_ROOT=")
            env.write_text(text)
            with self.assertRaises(ValidationError):
                load_remote_config(env)

    def test_stable_run_ids(self) -> None:
        self.assertEqual(
            stable_run_id("prediction", screen="controls", timestamp="20260713T000000Z"),
            "prediction-controls-20260713T000000Z",
        )

    def test_runtime_helpers_remain_compatible_with_python_310(self) -> None:
        for path in [
            Path("src/alphapulldown_dnaaf_screen/remote.py"),
            Path("src/alphapulldown_dnaaf_screen/provenance.py"),
            Path("src/alphapulldown_dnaaf_screen/native_runtime.py"),
        ]:
            text = path.read_text(encoding="utf-8")
            self.assertNotIn("dt.UTC", text)
            self.assertIn("dt.timezone.utc", text)

    def test_command_construction(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            command = feature_generation_command(config, dry_run=True)
            self.assertIn("snakemake", command[0])
            self.assertIn("--dry-run", command)
            self.assertNotIn("--config", command)
            self.assertIn("--snakefile", command)
            self.assertIn("--directory", command)
            self.assertIn("--software-deployment-method", command)
            self.assertIn("apptainer", command)
            self.assertIn("--apptainer-prefix", command)

    def test_feature_coverage_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = load_remote_config(write_fixture(root))
            missing = missing_features(config, "controls")
            self.assertEqual(len(missing), 4)
            for record_id in ["HUMAN_DNAAF9", "HUMAN_DNAAF18", "HUMAN_IFT74", "HUMAN_IFT46"]:
                (root / "results" / "features" / f"{record_id}_af3_input.json").write_text(
                    "feature"
                )
            self.assertEqual(missing_features(config, "controls"), [])

    def test_prediction_command_requires_no_full_screen(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            with self.assertRaises(ValidationError):
                prediction_command(config, screen="full", dry_run=True)

    def test_prediction_command_for_controls(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            command = prediction_command(config, screen="controls", dry_run=True)
            self.assertNotIn("--config", command)
            self.assertIn("--dry-run", command)

    def test_resolved_feature_config_uses_upstream_keys(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            path, inputs = write_resolved_feature_config(config, run_id="feature-test")
            self.assertTrue(inputs.exists())
            self.assertIn(f"{tmp}/data/processed/fasta/HUMAN_DNAAF9.fasta", inputs.read_text())
            keys = set(json.loads(path.read_text(encoding="utf-8")))
            self.assertLessEqual(keys, UPSTREAM_CONFIG_KEYS)
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(payload["only_generate_features"])
            self.assertEqual(payload["create_feature_arguments"]["--data_pipeline"], "alphafold3")

    def test_json_preserves_empty_collections(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            path, _ = write_resolved_feature_config(config, run_id="empty-yaml-test")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["feature_directory"], [])
            self.assertEqual(payload["recursive_report_arguments"], {})

    def test_mmseqs2_mode_uses_alphafold2_pipeline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            text = env.read_text()
            text = text.replace("FEATURE_MODE=localdb", "FEATURE_MODE=mmseqs2")
            text = text.replace("FEATURE_FILE_PATTERN={record_id}_af3_input.json\n", "")
            env.write_text(text)
            config = load_remote_config(env)
            self.assertEqual(config.feature_pattern, "{record_id}.pkl.xz")
            path, _ = write_resolved_feature_config(config, run_id="feature-mmseqs2")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["create_feature_arguments"]["--data_pipeline"], "alphafold2")
            self.assertIs(payload["create_feature_arguments"]["--use_mmseqs2"], True)
            self.assertIs(payload["create_feature_arguments"]["--skip_existing"], True)
            self.assertNotIn("alphafold3", json.dumps(payload).lower())
            self.assertNotIn("_af3_input.json", json.dumps(payload))
            self.assertEqual(payload["prediction_container"], "docker://kosinskilab/alphafold2:2.5.0")

    def test_configured_sif_path_is_emitted_into_feature_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = write_fixture(root)
            sif = root / "containers" / "kosinskilab_alphafold2_2.5.0.sif"
            env.write_text(
                env.read_text()
                .replace("FEATURE_MODE=localdb", "FEATURE_MODE=mmseqs2")
                .replace("FEATURE_FILE_PATTERN={record_id}_af3_input.json\n", "")
                + f"APPTAINER_PREDICTION_SIF={sif}\n"
            )
            config = load_remote_config(env)
            path, _ = write_resolved_feature_config(config, run_id="feature-sif")
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["prediction_container"], str(sif))

    def test_configured_sif_path_is_emitted_into_prediction_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = write_fixture(root)
            sif = root / "containers" / "kosinskilab_alphafold2_2.5.0.sif"
            env.write_text(
                env.read_text()
                .replace("FEATURE_MODE=localdb", "FEATURE_MODE=mmseqs2")
                .replace("FEATURE_FILE_PATTERN={record_id}_af3_input.json\n", "")
                + f"APPTAINER_PREDICTION_SIF={sif}\n"
            )
            config = load_remote_config(env)
            path, _ = write_resolved_prediction_config(
                config, screen="controls", run_id="prediction-sif"
            )
            payload = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(payload["prediction_container"], str(sif))

    def test_configured_sif_must_be_absolute(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            env.write_text(env.read_text() + "APPTAINER_PREDICTION_SIF=relative.sif\n")
            with self.assertRaises(ValidationError):
                load_remote_config(env)

    def test_missing_sif_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            env = write_fixture(root)
            env.write_text(env.read_text() + f"APPTAINER_PREDICTION_SIF={root / 'missing.sif'}\n")
            config = load_remote_config(env)
            with self.assertRaises(ValidationError):
                validate_configured_sif(
                    config,
                    inspect_runner=successful_inspect,
                    execution_runner=successful_inspect,
                )

    def test_zero_byte_sif_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sif = root / "empty.sif"
            sif.write_bytes(b"")
            env = write_fixture(root)
            env.write_text(env.read_text() + f"APPTAINER_PREDICTION_SIF={sif}\n")
            config = load_remote_config(env)
            with self.assertRaises(ValidationError):
                validate_configured_sif(config, inspect_runner=successful_inspect)

    def test_invalid_apptainer_inspect_fails_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sif = root / "invalid.sif"
            sif.write_bytes(b"not really a sif")
            env = write_fixture(root)
            env.write_text(env.read_text() + f"APPTAINER_PREDICTION_SIF={sif}\n")
            config = load_remote_config(env)
            with self.assertRaises(ValidationError):
                validate_configured_sif(
                    config,
                    inspect_runner=failing_inspect,
                    execution_runner=successful_inspect,
                )

    def test_valid_sif_passes_validation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sif = root / "valid.sif"
            sif.write_bytes(b"sif")
            env = write_fixture(root)
            env.write_text(env.read_text() + f"APPTAINER_PREDICTION_SIF={sif}\n")
            config = load_remote_config(env)
            validate_configured_sif(
                config,
                inspect_runner=successful_inspect,
                execution_runner=successful_inspect,
            )

    def test_sif_execution_failure_is_blocking_and_does_not_suggest_sysctl_changes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            sif = root / "valid.sif"
            sif.write_bytes(b"sif")
            env = write_fixture(root)
            env.write_text(env.read_text() + f"APPTAINER_PREDICTION_SIF={sif}\n")
            config = load_remote_config(env)
            with self.assertRaisesRegex(ValidationError, "cannot execute") as context:
                validate_configured_sif(
                    config,
                    inspect_runner=successful_inspect,
                    execution_runner=failing_user_namespace_exec,
                )
            self.assertIn("SUID helper package", str(context.exception))
            self.assertIn("Do not change host sysctl settings", str(context.exception))

    def test_feature_mode_values_are_explicit(self) -> None:
        self.assertEqual(SUPPORTED_FEATURE_MODES, {"localdb", "mmseqs2"})
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            env.write_text(env.read_text().replace("FEATURE_MODE=localdb", "FEATURE_MODE=af3"))
            with self.assertRaises(ValidationError):
                load_remote_config(env)

    def test_prediction_inputs_are_fasta_paths_for_feature_reuse(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            path, inputs = write_resolved_prediction_config(
                config, screen="controls", run_id="prediction-test"
            )
            self.assertTrue(path.exists())
            self.assertEqual(len(inputs), 1)
            text = inputs[0].read_text()
            self.assertIn("HUMAN_DNAAF9.fasta+", text)
            self.assertIn("+", text)
            self.assertNotIn("Q5TEA3+Q96LB3", text)

    def test_project_local_keys_not_passed_directly_to_snakemake(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            feature = feature_generation_command(config, dry_run=True)
            prediction = prediction_command(config, screen="controls", dry_run=True)
            forbidden = {"screen=controls", "feature_dir=", "fasta_dir=", "feature_mode="}
            joined = " ".join(feature + prediction)
            for token in forbidden:
                self.assertNotIn(token, joined)

    def test_template_project_local_keys_are_namespaced(self) -> None:
        for path in [
            Path("config/remote/feature_generation.example.yaml"),
            Path("config/remote/prediction.example.yaml"),
        ]:
            keys = top_level_keys(path)
            self.assertIn("project_local", keys)
            self.assertLessEqual(keys - {"project_local"}, UPSTREAM_CONFIG_KEYS)

    def test_no_local_execution_on_macos(self) -> None:
        with mock.patch.object(platform, "system", return_value="Darwin"):
            with self.assertRaises(ValidationError):
                require_linux()
            require_linux(allow_dry_run=True)

    def test_provenance_creation(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            config = load_remote_config(write_fixture(root))
            path = create_run_provenance(
                config=config,
                run_id="test-run",
                command=["snakemake", "--dry-run"],
                input_paths=[config.fasta_manifest],
            )
            payload = json.loads(path.read_text())
            self.assertEqual(payload["run_id"], "test-run")
            self.assertEqual(payload["command"], ["snakemake", "--dry-run"])

    def test_no_hardcoded_cluster_paths(self) -> None:
        root = Path.cwd()
        checked = [
            *Path("scripts/remote").glob("*.sh"),
            *Path("config/remote").glob("*"),
            *Path("docs/software").glob("*GUIDE.md"),
        ]
        forbidden = ["/Users/", "/well/", "/ceph/", "/scratch/", "medhasharma"]
        for path in checked:
            text = (root / path).read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, text, f"{path} contains hardcoded path token {token}")

    def test_runpod_defaults_do_not_assume_profiles_or_cluster_jobs(self) -> None:
        values = parse_env_file(Path("config/remote/paths.example.env"))
        self.assertEqual(values["REMOTE_EXECUTION_STAGE"], "cpu")
        self.assertEqual(values["REMOTE_PROJECT_ROOT"], "/workspace/alphapulldown")
        self.assertEqual(values["AP_WORKFLOW_DIR"], "/workspace/workflows/AlphaPulldownSnakemake")
        self.assertEqual(values["SNAKEMAKE_JOBS"], "1")
        self.assertEqual(values["SNAKEMAKE_PROFILE"], "")
        self.assertEqual(values["SLURM_PROFILE"], "")

    def test_bootstrap_stage_controls_nvidia_requirement(self) -> None:
        text = Path("scripts/remote/bootstrap_remote_environment.sh").read_text(encoding="utf-8")
        self.assertIn('REMOTE_EXECUTION_STAGE="${REMOTE_EXECUTION_STAGE:-gpu}"', text)
        self.assertIn('REMOTE_EXECUTION_STAGE=cpu: NVIDIA GPU/nvidia-smi is not required.', text)
        self.assertIn("nvidia-smi is required for REMOTE_EXECUTION_STAGE=gpu", text)
        self.assertIn("GPU: not detected; allowed for REMOTE_EXECUTION_STAGE=cpu", text)

    def test_validator_reports_gpu_not_required_for_cpu_stage(self) -> None:
        text = Path("scripts/remote/validate_remote_environment.sh").read_text(encoding="utf-8")
        self.assertIn('REMOTE_EXECUTION_STAGE="${REMOTE_EXECUTION_STAGE:-gpu}"', text)
        self.assertIn('report "Execution stage" "${REMOTE_EXECUTION_STAGE}"', text)
        self.assertIn("not required for REMOTE_EXECUTION_STAGE=cpu", text)
        self.assertIn("not found; required for REMOTE_EXECUTION_STAGE=gpu", text)
        self.assertIn("not required for CPU stage", text)

    def test_prediction_requires_gpu_stage_and_nvidia(self) -> None:
        text = Path("scripts/remote/run_prediction.sh").read_text(encoding="utf-8")
        self.assertIn('REMOTE_EXECUTION_STAGE="${REMOTE_EXECUTION_STAGE:-gpu}"', text)
        self.assertIn("run_prediction.sh requires REMOTE_EXECUTION_STAGE=gpu", text)
        self.assertIn("nvidia-smi is required for GPU prediction/inference", text)

    def test_bootstrap_supports_local_pinned_env_yaml(self) -> None:
        text = Path("scripts/remote/bootstrap_remote_environment.sh").read_text(encoding="utf-8")
        self.assertIn("AP_ENV_YAML", text)
        self.assertIn("ENV_SOURCE", text)
        self.assertIn("SNAKEDEPLOY_BIN", text)
        self.assertIn("env create -n", text)

    def test_remote_python_sets_repo_src_pythonpath(self) -> None:
        text = Path("scripts/remote/common.sh").read_text(encoding="utf-8")
        self.assertIn('PYTHONPATH="${REPO_ROOT}/src:${PYTHONPATH:-}"', text)

    def test_validator_does_not_require_alphapulldown_import(self) -> None:
        text = Path("scripts/remote/validate_remote_environment.sh").read_text(encoding="utf-8")
        self.assertIn("alphapulldown-input-parser importable", text)
        self.assertIn("expected for containerized AlphaPulldownSnakemake runtime", text)
        self.assertNotIn('fail "AlphaPulldown"', text)

    def test_profiles_are_optional_for_snakedeploy_layout(self) -> None:
        text = Path("scripts/remote/validate_remote_environment.sh").read_text(encoding="utf-8")
        self.assertIn("local single-node execution will use --cores", text)
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            command = feature_generation_command(config, dry_run=True)
            self.assertIn("--cores", command)
            self.assertNotIn("--profile", command)

    def test_empty_profile_values_are_omitted_from_snakemake_command(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            config = load_remote_config(write_fixture(Path(tmp)))
            command = snakemake_base_command(
                config,
                configfile=config.feature_config,
                dry_run=True,
                profile=Path(""),
            )
            self.assertIn("--cores", command)
            self.assertNotIn("--profile", command)

    def test_mmseqs2_feature_arguments_render_as_one_shell_parameter_line(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            text = env.read_text()
            text = text.replace("FEATURE_MODE=localdb", "FEATURE_MODE=mmseqs2")
            text = text.replace("FEATURE_FILE_PATTERN={record_id}_af3_input.json\n", "")
            env.write_text(text)
            config = load_remote_config(env)
            path, _ = write_resolved_feature_config(config, run_id="feature-mmseqs2-line")
            payload = json.loads(path.read_text(encoding="utf-8"))
            args = payload["create_feature_arguments"]
            self.assertIsInstance(args, dict)
            plan = pinned_workflow_feature_plan(args)
            rendered = plan.cli_parameters
            self.assertEqual(
                rendered,
                "--save_msa_files=False --use_precomputed_msas=True "
                "--max_template_date=2050-01-01 --compress_features=True "
                "--data_pipeline=alphafold2 --use_mmseqs2=True --skip_existing=True",
            )
            self.assertEqual(plan.data_pipeline, "alphafold2")
            self.assertFalse(plan.is_af3)
            self.assertEqual(plan.feature_name("HUMAN_IFT80"), "HUMAN_IFT80.pkl.xz")
            shell_command = render_pinned_create_features_command(
                fasta_path="input.fasta",
                data_directory="",
                output_directory="features",
                create_feature_arguments=args,
            )
            self.assertTrue(
                shell_command.endswith(
                "--data_pipeline=alphafold2 --use_mmseqs2=True --skip_existing=True",
                )
            )
            self.assertNotIn("\n--use_mmseqs2=True", shell_command)
            self.assertNotIn("\n--skip_existing=True", shell_command)

    def test_mmseqs2_preflight_rejects_af2_af3_mixture(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            env = write_fixture(Path(tmp))
            text = env.read_text().replace("FEATURE_MODE=localdb", "FEATURE_MODE=mmseqs2")
            text = text.replace("FEATURE_FILE_PATTERN={record_id}_af3_input.json\n", "")
            env.write_text(text)
            config = load_remote_config(env)
            validate_feature_execution_model(config)

            with mock.patch(
                "alphapulldown_dnaaf_screen.remote._base_upstream_config",
                return_value={
                    "create_feature_arguments": {
                        "--compress_features": True,
                        "--data_pipeline": "alphafold3",
                        "--use_mmseqs2": True,
                        "--skip_existing": True,
                    },
                    "structure_inference_arguments": {"--fold_backend": "alphafold3"},
                },
            ):
                with self.assertRaisesRegex(ValidationError, "alphafold2"):
                    validate_feature_execution_model(config)

    def test_feature_argument_newlines_are_rejected_before_snakemake(self) -> None:
        with self.assertRaises(ValidationError):
            upstream_cli_parameters({"--data_pipeline": "alphafold2\n--use_mmseqs2=True"})

    def test_runpod_rebuild_detects_corruption_by_execution(self) -> None:
        text = Path("scripts/remote/rebuild_runpod_runtime.sh").read_text(encoding="utf-8")
        self.assertIn("miniforge_is_healthy()", text)
        self.assertIn("import encodings, ssl, sys", text)
        self.assertIn('"${MINIFORGE_DIR}/bin/conda" --version', text)
        self.assertIn('"${MINIFORGE_DIR}/bin/mamba" --version', text)
        self.assertIn("env_is_healthy()", text)

    def test_runpod_rebuild_moves_broken_runtime_aside_safely(self) -> None:
        text = Path("scripts/remote/rebuild_runpod_runtime.sh").read_text(encoding="utf-8")
        self.assertIn('BROKEN_DIR="${MINIFORGE_DIR}.broken.${TIMESTAMP}"', text)
        self.assertIn('mv "${MINIFORGE_DIR}" "${BROKEN_DIR}"', text)
        self.assertNotIn("rm -rf", text)
        self.assertNotIn("data/processed", text)
        self.assertNotIn("alphapulldown_results", text)

    def test_runpod_rebuild_recreates_expected_envs_and_workflow(self) -> None:
        text = Path("scripts/remote/rebuild_runpod_runtime.sh").read_text(encoding="utf-8")
        self.assertIn("snakedeploy-tools", text)
        self.assertIn("create -n", text)
        self.assertIn("-c conda-forge -c bioconda", text)
        self.assertIn("snakedeploy snakemake", text)
        self.assertIn("alphapulldown_snakemake_${AP_SNAKEMAKE_VERSION}.yaml", text)
        self.assertIn("env create -n", text)
        self.assertIn("deploy-workflow", text)
        self.assertIn("--tag", text)

    def test_runpod_rebuild_checks_parser_not_alphapulldown(self) -> None:
        text = Path("scripts/remote/rebuild_runpod_runtime.sh").read_text(encoding="utf-8")
        self.assertIn("alphapulldown_input_parser", text)
        self.assertIn("expected for containerized workflow runtime", text)
        self.assertNotIn("import snakemake, alphapulldown;", text)

    def test_runpod_rebuild_is_dry_run_capable_and_workspace_scoped(self) -> None:
        text = Path("scripts/remote/rebuild_runpod_runtime.sh").read_text(encoding="utf-8")
        self.assertIn("--dry-run", text)
        self.assertIn("DRY RUN:", text)
        self.assertIn("WORKSPACE_ROOT=\"${WORKSPACE_ROOT:-/workspace}\"", text)
        self.assertIn("/workspace|/workspace/*", text)
        self.assertIn("RUNPOD_LOG_DIR", text)

    def test_bootstrap_and_validator_require_apptainer(self) -> None:
        bootstrap = Path("scripts/remote/bootstrap_remote_environment.sh").read_text(
            encoding="utf-8"
        )
        validator = Path("scripts/remote/validate_remote_environment.sh").read_text(
            encoding="utf-8"
        )
        self.assertIn("command -v apptainer", bootstrap)
        self.assertIn("Apptainer is required", bootstrap)
        self.assertIn("require_executable_apptainer_sif", bootstrap)
        self.assertIn("command -v apptainer", validator)
        self.assertIn("fail \"Apptainer\"", validator)
        self.assertIn('apptainer exec "${APPTAINER_PREDICTION_SIF}" true', validator)

    def test_historical_execution_preflight_has_safe_host_remediation(self) -> None:
        common = Path("scripts/remote/common.sh").read_text(encoding="utf-8")
        checklist = Path("docs/archive/runpod/RUNPOD_EXECUTION_CHECKLIST.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('apptainer exec "${sif_path}" true', common)
        self.assertIn("Apptainer SUID helper package", common)
        self.assertIn("Do not change host sysctl settings", common)
        self.assertIn("Historical Apptainer artifacts", checklist)
        self.assertIn("not RunPod execution inputs", checklist)
        self.assertNotIn("unprivileged_userns_clone=1", common)

    def test_apptainer_prep_detects_filesystem_types(self) -> None:
        text = Path("scripts/remote/prepare_apptainer_image.sh").read_text(encoding="utf-8")
        self.assertIn("findmnt -T", text)
        self.assertIn("CACHE_FS", text)
        self.assertIn("BUILD_FS", text)
        self.assertIn("APPTAINER_TMPDIR", text)
        self.assertIn("APPTAINER_CACHEDIR", text)

    def test_apptainer_prep_refuses_network_build_storage(self) -> None:
        text = Path("scripts/remote/prepare_apptainer_image.sh").read_text(encoding="utf-8")
        self.assertIn("is_network_fs()", text)
        self.assertIn("fuse*", text)
        self.assertIn("Refusing to build SIF on network/FUSE filesystem", text)
        self.assertIn("Warning: persistent Apptainer cache", text)

    def test_apptainer_prep_requires_local_space_and_explicit_build_dir(self) -> None:
        text = Path("scripts/remote/prepare_apptainer_image.sh").read_text(encoding="utf-8")
        self.assertIn("APPTAINER_LOCAL_BUILD_DIR must be set", text)
        self.assertIn("APPTAINER_MIN_LOCAL_FREE_GB", text)
        self.assertIn("Insufficient local build space", text)
        self.assertNotIn('APPTAINER_LOCAL_BUILD_DIR="${APPTAINER_LOCAL_BUILD_DIR:-/tmp', text)
        self.assertIn("Apptainer paths must be absolute", text)

    def test_apptainer_prep_reuses_valid_images_and_recovers_partials(self) -> None:
        text = Path("scripts/remote/prepare_apptainer_image.sh").read_text(encoding="utf-8")
        self.assertIn("validate_sif()", text)
        self.assertIn("Valid existing SIF found; refusing to rebuild", text)
        self.assertIn(".partial.${TIMESTAMP}", text)
        self.assertIn("Moved invalid/interrupted SIF aside", text)
        self.assertIn("apptainer inspect", text)

    def test_apptainer_prep_builds_locally_then_moves_completed_sif(self) -> None:
        text = Path("scripts/remote/prepare_apptainer_image.sh").read_text(encoding="utf-8")
        self.assertIn('LOCAL_SIF_TMP="${APPTAINER_LOCAL_BUILD_DIR}', text)
        self.assertIn("apptainer pull --force", text)
        self.assertIn('mv "${LOCAL_SIF_TMP}" "${APPTAINER_PREDICTION_SIF}"', text)
        self.assertIn("does not run Snakemake", text)

    def test_apptainer_prep_records_sha256_and_inspect_metadata(self) -> None:
        text = Path("scripts/remote/prepare_apptainer_image.sh").read_text(encoding="utf-8")
        self.assertIn('SIF_SHA256="${APPTAINER_PREDICTION_SIF}.sha256"', text)
        self.assertIn('SIF_INSPECT="${APPTAINER_PREDICTION_SIF}.inspect.txt"', text)
        self.assertIn('sha256sum "${APPTAINER_PREDICTION_SIF}" > "${SIF_SHA256}"', text)
        self.assertIn('apptainer inspect "${APPTAINER_PREDICTION_SIF}" > "${SIF_INSPECT}"', text)

    def test_paths_template_exposes_apptainer_preparation_knobs(self) -> None:
        values = parse_env_file(Path("config/remote/paths.example.env"))
        self.assertIn("APPTAINER_IMAGE_DIR", values)
        self.assertIn("APPTAINER_PERSISTENT_CACHE_DIR", values)
        self.assertIn("APPTAINER_PREFIX", values)
        self.assertIn("APPTAINER_LOCAL_BUILD_DIR", values)
        self.assertEqual(values["APPTAINER_LOCAL_BUILD_DIR"], "")
        self.assertEqual(values["APPTAINER_MIN_LOCAL_FREE_GB"], "28")
        self.assertIn("kosinskilab/alphafold2:2.5.0", values["APPTAINER_PREDICTION_IMAGE"])
        self.assertEqual(values["APPTAINER_PREDICTION_SIF"], "")

    def test_runpod_checklist_requires_tmux_and_native_stage_split(self) -> None:
        text = Path("docs/archive/runpod/RUNPOD_EXECUTION_CHECKLIST.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("tmux new -s alphapulldown-features", text)
        self.assertIn("tmux new -s alphapulldown-predict", text)
        self.assertIn("run_native_stage.sh", text)
        self.assertLess(
            text.index("## Phase A - Build and publish the derived image"),
            text.index("## Phase B - CPU MMseqs2 feature generation"),
        )
        self.assertLess(
            text.index("## Phase B - CPU MMseqs2 feature generation"),
            text.index("## Phase C - A40 inference"),
        )
        self.assertIn("features/*.pkl.xz", text)

    def test_runpod_checklist_retires_apptainer_for_runpod(self) -> None:
        text = Path("docs/archive/runpod/RUNPOD_EXECUTION_CHECKLIST.md").read_text(
            encoding="utf-8"
        )
        self.assertIn('CONTAINER_RUNTIME="docker-native"', text)
        self.assertIn('REMOTE_EXECUTION_STAGE="cpu"', text)
        self.assertIn('REMOTE_EXECUTION_STAGE="gpu"', text)
        self.assertIn("do not execute SIF files", text)
        self.assertIn("Do not delete the completed SIF", text)


def top_level_keys(path: Path) -> set[str]:
    keys: set[str] = set()
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        if not raw_line or raw_line.startswith("#") or raw_line.startswith(" "):
            continue
        if ":" in raw_line:
            keys.add(raw_line.split(":", 1)[0])
    return keys

def successful_inspect(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 0, stdout="ok", stderr="")


def failing_inspect(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(command, 1, stdout="", stderr="bad sif")


def failing_user_namespace_exec(command: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(
        command,
        1,
        stdout="",
        stderr="Failed to create user namespace: user namespace requires to set "
        "/proc/sys/kernel/unprivileged_userns_clone to 1",
    )


if __name__ == "__main__":
    unittest.main()
