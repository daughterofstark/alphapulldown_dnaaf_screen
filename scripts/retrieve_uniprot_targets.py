#!/usr/bin/env python3
"""Retrieve and verify UniProt records for the project target seed manifest."""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any


UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"
UNIPROT_ENTRY_URL = "https://rest.uniprot.org/uniprotkb/{accession}.json"
UNIPROT_RELEASE_URL = "https://rest.uniprot.org/uniprotkb/search?query=*&size=0&format=json"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def fetch_json(url: str, *, retries: int = 3, delay_seconds: float = 1.0) -> dict[str, Any]:
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        try:
            request = urllib.request.Request(
                url,
                headers={"User-Agent": "alphapulldown-dnaaf-screen/0.1"},
            )
            with urllib.request.urlopen(request, timeout=60) as response:
                return json.loads(response.read().decode("utf-8"))
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(delay_seconds * attempt)
    raise RuntimeError(f"Failed to fetch {url}: {last_error}") from last_error


def search_uniprot(symbol: str, taxon_id: int) -> dict[str, Any]:
    query = f"(gene_exact:{symbol}) AND (organism_id:{taxon_id}) AND (reviewed:true)"
    params = {
        "query": query,
        "format": "json",
        "size": "10",
        "fields": ",".join(
            [
                "accession",
                "id",
                "protein_name",
                "gene_names",
                "organism_name",
                "length",
                "reviewed",
                "xref_hgnc",
                "xref_geneid",
                "xref_pdb",
                "sequence",
            ]
        ),
    }
    return fetch_json(f"{UNIPROT_SEARCH_URL}?{urllib.parse.urlencode(params)}")


def get_entry(accession: str) -> dict[str, Any]:
    return fetch_json(UNIPROT_ENTRY_URL.format(accession=urllib.parse.quote(accession)))


def get_release_metadata() -> dict[str, str]:
    metadata: dict[str, str] = {}
    request = urllib.request.Request(
        UNIPROT_RELEASE_URL,
        headers={"User-Agent": "alphapulldown-dnaaf-screen/0.1"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        metadata["url"] = UNIPROT_RELEASE_URL
        metadata["queried_at_utc"] = dt.datetime.now(dt.UTC).isoformat()
        for key, value in response.headers.items():
            lower = key.lower()
            if lower.startswith("x-uniprot") or lower in {"date", "etag", "last-modified"}:
                metadata[key] = value
    return metadata


def gene_names(entry: dict[str, Any]) -> list[str]:
    names: list[str] = []
    for gene in entry.get("genes", []):
        for field in ("geneName", "synonyms", "orderedLocusNames", "orfNames"):
            value = gene.get(field)
            if isinstance(value, dict) and value.get("value"):
                names.append(value["value"])
            elif isinstance(value, list):
                names.extend(item["value"] for item in value if item.get("value"))
    return sorted(set(names))


def recommended_name(entry: dict[str, Any]) -> str:
    description = entry.get("proteinDescription", {})
    recommended = description.get("recommendedName", {})
    full = recommended.get("fullName", {})
    if full.get("value"):
        return full["value"]
    submitted = description.get("submissionNames", [])
    if submitted:
        return submitted[0].get("fullName", {}).get("value", "")
    return ""


def xrefs(entry: dict[str, Any], database: str) -> list[str]:
    values = []
    for ref in entry.get("uniProtKBCrossReferences", []):
        if ref.get("database") == database and ref.get("id"):
            values.append(ref["id"])
    return values


def pubmed_ids(entry: dict[str, Any], limit: int = 5) -> list[str]:
    ids: list[str] = []
    for reference in entry.get("references", []):
        citation = reference.get("citation", {})
        for citation_ref in citation.get("citationCrossReferences", []):
            if citation_ref.get("database") == "PubMed" and citation_ref.get("id"):
                ids.append(citation_ref["id"])
    return sorted(set(ids))[:limit]


def sequence_sha256(entry: dict[str, Any]) -> str:
    sequence = entry.get("sequence", {}).get("value", "")
    return hashlib.sha256(sequence.encode("utf-8")).hexdigest() if sequence else ""


def choose_result(
    search_results: dict[str, Any],
    query_symbols: list[str],
) -> dict[str, Any] | None:
    results = search_results.get("results", [])
    if not results:
        return None

    wanted = {symbol.upper() for symbol in query_symbols}
    exact_matches = []
    for result in results:
        result_genes = {name.upper() for name in gene_names(result)}
        if wanted & result_genes:
            exact_matches.append(result)

    if len(exact_matches) == 1:
        return exact_matches[0]
    if exact_matches:
        return exact_matches[0]
    return results[0]


def retrieve_target(target: dict[str, Any], taxon_id: int) -> tuple[dict[str, Any], dict[str, Any]]:
    searches = {}
    selected: dict[str, Any] | None = None
    selected_symbol = ""

    for symbol in target["query_symbols"]:
        search = search_uniprot(symbol, taxon_id)
        searches[symbol] = search
        selected = choose_result(search, target["query_symbols"])
        if selected:
            selected_symbol = symbol
            break

    if not selected:
        raise ValueError(
            f"No reviewed human UniProt result for {target['record_id']} "
            f"using {target['query_symbols']}"
        )

    accession = selected["primaryAccession"]
    full_entry = get_entry(accession)
    return full_entry, {"selected_query_symbol": selected_symbol, "searches": searches}


def build_verified_row(
    target: dict[str, Any],
    entry: dict[str, Any],
    selected_query_symbol: str,
) -> dict[str, str]:
    genes = gene_names(entry)
    accession = entry.get("primaryAccession", "")
    sequence = entry.get("sequence", {})
    organism = entry.get("organism", {}).get("scientificName", "")
    hgnc_ids = xrefs(entry, "HGNC")
    gene_ids = xrefs(entry, "GeneID")
    pdb_ids = xrefs(entry, "PDB")
    pubmed = pubmed_ids(entry)

    return {
        "record_id": target["record_id"],
        "display_name": target["display_name"],
        "protein_group": target["protein_group"],
        "query_symbol_used": selected_query_symbol,
        "uniprot_accession": accession,
        "uniprot_entry": entry.get("uniProtkbId", ""),
        "reviewed": str(entry.get("entryType", "") == "UniProtKB reviewed (Swiss-Prot)"),
        "protein_name": recommended_name(entry),
        "genes_from_uniprot": ";".join(genes),
        "organism": organism,
        "length": str(sequence.get("length", "")),
        "sequence_sha256": sequence_sha256(entry),
        "hgnc_ids": ";".join(hgnc_ids),
        "gene_ids": ";".join(gene_ids),
        "pdb_ids": ";".join(pdb_ids[:10]),
        "pubmed_ids": ";".join(pubmed),
        "uniprot_url": f"https://www.uniprot.org/uniprotkb/{accession}/entry" if accession else "",
        "role": target.get("role", ""),
    }


def write_tsv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()), delimiter="\t")
        writer.writeheader()
        writer.writerows(rows)


def write_markdown_report(path: Path, rows: list[dict[str, str]], release: dict[str, str]) -> None:
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["protein_group"]] = counts.get(row["protein_group"], 0) + 1

    lines = [
        "# UniProt Target Verification Report",
        "",
        f"Generated: {dt.datetime.now(dt.UTC).isoformat()}",
        "",
        "## Source",
        "",
        "- Database: UniProtKB REST API",
        f"- Release metadata: `{json.dumps(release, sort_keys=True)}`",
        "- Query policy: reviewed Swiss-Prot human records, searched by curated gene symbol/alias.",
        "- Canonical sequences were downloaded from UniProt entries and summarized "
        "by SHA-256 checksum.",
        "",
        "## Counts",
        "",
    ]
    for group, count in sorted(counts.items()):
        lines.append(f"- {group}: {count}")
    lines.extend(
        [
            f"- Total: {len(rows)}",
            "",
            "## Verified Records",
            "",
            "| Record | Group | UniProt | Entry | Protein name | Gene names | Length | "
            "HGNC | PubMed evidence |",
            "| --- | --- | --- | --- | --- | --- | ---: | --- | --- |",
        ]
    )
    for row in rows:
        accession = row["uniprot_accession"]
        link = f"[{accession}]({row['uniprot_url']})"
        pubmed = row["pubmed_ids"] or "none listed in parsed entry"
        protein_name = row["protein_name"].replace("|", "\\|")
        genes = row["genes_from_uniprot"].replace("|", "\\|")
        lines.append(
            "| {record_id} | {protein_group} | {link} | {entry} | {protein_name} | "
            "{genes} | {length} | {hgnc} | {pubmed} |".format(
                record_id=row["record_id"],
                protein_group=row["protein_group"],
                link=link,
                entry=row["uniprot_entry"],
                protein_name=protein_name,
                genes=genes,
                length=row["length"],
                hgnc=row["hgnc_ids"] or "",
                pubmed=pubmed,
            )
        )
    lines.extend(
        [
            "",
            "## Review Notes",
            "",
            "- `TTC30A` and `TTC30B` are both retained as human IFT70 paralogs pending "
            "screen-design review.",
            "- Large ODA heavy chains are retrieved full length here; future AlphaPulldown "
            "jobs may use domain-level constructs for tractability.",
            "- This report verifies database identity, not biological interaction evidence. "
            "Interaction evidence remains in the literature/validation docs.",
            "",
        ]
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=Path("data/manifest/target_seed.json"))
    parser.add_argument("--raw-dir", type=Path, default=Path("data/raw/uniprot"))
    parser.add_argument("--processed-dir", type=Path, default=Path("data/processed/uniprot"))
    args = parser.parse_args()

    manifest = read_json(args.manifest)
    taxon_id = int(manifest["species"]["taxon_id"])
    release = get_release_metadata()

    rows: list[dict[str, str]] = []
    failures: list[str] = []
    for target in manifest["targets"]:
        try:
            entry, debug = retrieve_target(target, taxon_id)
            raw_payload = {"target": target, "debug": debug, "entry": entry}
            write_json(args.raw_dir / f"{target['record_id']}.json", raw_payload)
            row = build_verified_row(target, entry, debug["selected_query_symbol"])
            rows.append(row)
            print(
                "verified "
                f"{target['record_id']} -> {row['uniprot_accession']} {row['uniprot_entry']}"
            )
        except Exception as exc:  # noqa: BLE001 - continue all records and report failures
            message = f"{target['record_id']}: {exc}"
            failures.append(message)
            print(f"FAILED {message}", file=sys.stderr)

    if rows:
        write_tsv(args.processed_dir / "targets_uniprot_verified.tsv", rows)
        write_json(args.processed_dir / "targets_uniprot_verified.json", rows)
        write_markdown_report(args.processed_dir / "TARGET_VERIFICATION_REPORT.md", rows, release)
        write_json(args.processed_dir / "uniprot_release_metadata.json", release)
    if failures:
        (args.processed_dir / "retrieval_failures.txt").write_text(
            "\n".join(failures) + "\n",
            encoding="utf-8",
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
