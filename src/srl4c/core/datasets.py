"""Core datasets logic.

This module provides dataset-related functionality used by both CLI and API.
"""

from collections import defaultdict

import pandas as pd

from srl4c.paths import DATASETS_DIR


def get_all_datasets() -> dict[str, dict]:
    """Get all datasets with metadata.

    Returns:
        Dict mapping dataset name to {path, rows, principles}
    """
    datasets = {}
    if not DATASETS_DIR.exists():
        return datasets

    for f in DATASETS_DIR.glob("*.csv"):
        try:
            df = pd.read_csv(f)
            prompt_col = next((c for c in df.columns if c.lower() in ["prompt", "question"]), None)
            cat_col = next((c for c in df.columns if c.lower() in ["category", "cat"]), None)

            if prompt_col:
                principles = set()
                if cat_col:
                    principles = set(df[cat_col].dropna().unique())

                datasets[f.stem] = {
                    "path": f,
                    "rows": len(df),
                    "principles": list(principles),
                }
        except Exception:
            continue

    return datasets


def get_prompt_stats_by_principle() -> dict[str, dict]:
    """Count prompts and get samples for each principle across all datasets.

    Returns:
        Dict mapping principle_id to {count, samples}
    """
    stats = defaultdict(lambda: {"count": 0, "samples": []})

    if not DATASETS_DIR.exists():
        return dict(stats)

    for csv_file in DATASETS_DIR.glob("*.csv"):
        try:
            df = pd.read_csv(csv_file)
            cat_col = next((c for c in df.columns if c.lower() in ["category", "cat"]), None)
            prompt_col = next((c for c in df.columns if c.lower() in ["prompt", "question"]), None)

            if not cat_col or not prompt_col:
                continue

            for _, row in df.iterrows():
                principle_id = str(row[cat_col]) if pd.notna(row[cat_col]) else ""
                prompt = str(row[prompt_col]) if pd.notna(row[prompt_col]) else ""

                if principle_id and prompt:
                    stats[principle_id]["count"] += 1
                    if len(stats[principle_id]["samples"]) < 3:
                        stats[principle_id]["samples"].append(prompt)
        except Exception:
            continue

    return dict(stats)


def get_dataset_prompts(dataset_name: str) -> list[dict]:
    """Get all prompts from a specific dataset.

    Args:
        dataset_name: Name of the dataset (without .csv extension)

    Returns:
        List of dicts with {id, category, prompt}
    """
    csv_path = DATASETS_DIR / f"{dataset_name}.csv"
    if not csv_path.exists():
        return []

    try:
        df = pd.read_csv(csv_path)
        id_col = next(
            (c for c in df.columns if c.lower() in ["promptid", "prompt_id", "id"]),
            None,
        )
        cat_col = next((c for c in df.columns if c.lower() in ["category", "cat"]), None)
        prompt_col = next((c for c in df.columns if c.lower() in ["prompt", "question"]), None)

        if not prompt_col:
            return []

        prompts = []
        for idx, row in df.iterrows():
            prompts.append(
                {
                    "id": str(row[id_col]) if id_col and pd.notna(row[id_col]) else str(idx + 1),
                    "category": str(row[cat_col]) if cat_col and pd.notna(row[cat_col]) else "",
                    "prompt": str(row[prompt_col]) if pd.notna(row[prompt_col]) else "",
                }
            )
        return prompts
    except Exception:
        return []
