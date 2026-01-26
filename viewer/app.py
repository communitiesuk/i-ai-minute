# mypy: ignore-errors
# TODO: Decide on a structure for evals folder and add mypy support properly


from __future__ import annotations

import json
import os
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

from flask import Flask, abort, redirect, render_template, request, url_for


DIMENSIONS = ["faithfulness", "coverage", "conciseness", "coherence"]


def _get_runs_root() -> Path:
    root = os.environ.get("RUNS_ROOT")
    if not root:
        root = str(Path(__file__).resolve().parents[1] / "evals" / "runs")
    return Path(root)


def _run_dir(run_id: str) -> Path:
    return _get_runs_root() / run_id


def _results_path(run_id: str) -> Path:
    return _run_dir(run_id) / "results.jsonl"


def _safe_int(v: str | None, default: int) -> int:
    try:
        if v is None:
            return default
        return int(v)
    except ValueError:
        return default


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not path.exists():
        return rows
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rows.append(json.loads(line))
    return rows


def _iter_jsonl(path: Path) -> Iterable[dict[str, Any]]:
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)


def _get_nested(obj: dict[str, Any], path: list[str]) -> Any:
    cur: Any = obj
    for p in path:
        if not isinstance(cur, dict):
            return None
        cur = cur.get(p)
    return cur


def _row_key(row: dict[str, Any]) -> tuple[str | None, str | None]:
    run_id = row.get("run_id")
    ex_id = _get_nested(row, ["example", "example_id"])
    return run_id, ex_id


def _text_blob(row: dict[str, Any]) -> str:
    parts: list[str] = []
    for v in [
        _get_nested(row, ["example", "example_id"]),
        _get_nested(row, ["example", "dialogue"]),
        _get_nested(row, ["example", "reference_summary"]),
        _get_nested(row, ["candidate", "summary"]),
        _get_nested(row, ["judge", "rationale"]),
    ]:
        if isinstance(v, str):
            parts.append(v)
    return "\n".join(parts).lower()


def _judge_scores(row: dict[str, Any]) -> dict[str, Any] | None:
    judge = row.get("judge")
    if isinstance(judge, dict):
        scores = judge.get("scores")
        if isinstance(scores, dict):
            return scores
    metrics = row.get("metrics")
    if isinstance(metrics, dict):
        out: dict[str, Any] = {}
        for k, v in metrics.items():
            if isinstance(v, dict) and "score" in v:
                out[k] = v.get("score")
        return out or None
    return None


def _judge_pass(row: dict[str, Any]) -> bool | None:
    judge = row.get("judge")
    if isinstance(judge, dict) and "pass" in judge:
        v = judge.get("pass")
        if isinstance(v, bool):
            return v
    sim = row.get("similarity")
    if isinstance(sim, dict) and "pass" in sim:
        v = sim.get("pass")
        if isinstance(v, bool):
            return v
    return None


def _get_annotation(row: dict[str, Any]) -> dict[str, Any]:
    metrics = row.get("metrics")
    if isinstance(metrics, dict):
        ann = metrics.get("human_judge")
        if isinstance(ann, dict):
            return ann
    return {}


def _set_annotation(row: dict[str, Any], payload: dict[str, Any]) -> None:
    metrics = row.get("metrics")
    if not isinstance(metrics, dict):
        metrics = {}
        row["metrics"] = metrics
    metrics["human_judge"] = payload


@dataclass(frozen=True)
class RunFile:
    run_id: str
    results_path: Path
    mtime: float


def _list_run_files() -> list[RunFile]:
    root = _get_runs_root()
    if not root.exists():
        return []

    out: list[RunFile] = []
    for d in sorted(root.iterdir()):
        if not d.is_dir():
            continue
        rp = d / "results.jsonl"
        if not rp.exists():
            continue
        out.append(RunFile(run_id=d.name, results_path=rp, mtime=rp.stat().st_mtime))

    out.sort(key=lambda x: x.mtime, reverse=True)
    return out


def _atomic_rewrite_jsonl(path: Path, rows: Iterable[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False))
            f.write("\n")
    os.replace(tmp, path)


def _update_annotation_in_file(
    results_path: Path,
    *,
    run_id: str,
    example_id: str,
    dim_updates: dict[str, dict[str, Any]],
) -> None:
    def _updated_rows() -> Iterable[dict[str, Any]]:
        for row in _iter_jsonl(results_path):
            r_run_id, r_ex_id = _row_key(row)
            if r_run_id == run_id and r_ex_id == example_id:
                ann = _get_annotation(row)
                for dim, payload in dim_updates.items():
                    ann[dim] = payload
                _set_annotation(row, ann)
            yield row

    _atomic_rewrite_jsonl(results_path, _updated_rows())


def create_app() -> Flask:
    flask_app = Flask(__name__)

    @flask_app.template_filter("dt")
    def _dt_filter(v: Any) -> str:
        if isinstance(v, str):
            return v
        if isinstance(v, (int, float)):
            try:
                return datetime.fromtimestamp(float(v)).isoformat()
            except ValueError:
                return str(v)
        return str(v)

    @flask_app.get("/")
    def index():
        q = (request.args.get("q") or "").strip().lower()
        runs = _list_run_files()
        if q:
            runs = [r for r in runs if q in r.run_id.lower()]
        return render_template("index.html", runs=runs, runs_root=str(_get_runs_root()))

    @flask_app.get("/run/<run_id>")
    def run_view(run_id: str):
        rp = _results_path(run_id)
        if not rp.exists():
            abort(404)

        q = (request.args.get("q") or "").strip().lower()
        judge_pass = request.args.get("judge_pass")
        page = max(1, _safe_int(request.args.get("page"), 1))
        page_size = min(200, max(5, _safe_int(request.args.get("page_size"), 25)))

        all_rows = _load_jsonl(rp)

        def _match(row: dict[str, Any]) -> bool:
            if q and q not in _text_blob(row):
                return False
            if judge_pass in {"true", "false"}:
                jp = _judge_pass(row)
                if jp is None:
                    return False
                if judge_pass == "true" and jp is not True:
                    return False
                if judge_pass == "false" and jp is not False:
                    return False
            return True

        filtered = [r for r in all_rows if _match(r)]
        total = len(filtered)
        start = (page - 1) * page_size
        end = start + page_size
        page_rows = filtered[start:end]

        def _row_preview(row: dict[str, Any]) -> dict[str, Any]:
            return {
                "example_id": _get_nested(row, ["example", "example_id"]),
                "candidate_summary": _get_nested(row, ["candidate", "summary"]),
                "judge_pass": _judge_pass(row),
                "judge_scores": _judge_scores(row),
                "human_judge": _get_annotation(row),
            }

        previews = [_row_preview(r) for r in page_rows]

        return render_template(
            "run.html",
            run_id=run_id,
            results_path=str(rp),
            q=q,
            judge_pass=judge_pass,
            page=page,
            page_size=page_size,
            total=total,
            rows=previews,
        )

    @flask_app.get("/run/<run_id>/row/<example_id>")
    def row_view(run_id: str, example_id: str):
        rp = _results_path(run_id)
        if not rp.exists():
            abort(404)

        row: dict[str, Any] | None = None
        for r in _iter_jsonl(rp):
            r_run_id, r_ex_id = _row_key(r)
            if r_run_id == run_id and r_ex_id == example_id:
                row = r
                break

        if row is None:
            abort(404)

        judge_display = {
            "pass": _judge_pass(row),
            "scores": _judge_scores(row),
            "rationale": _get_nested(row, ["judge", "rationale"]),
        }

        ann = _get_annotation(row)
        ann_by_dim = {
            d: ann.get(d, {}) if isinstance(ann.get(d), dict) else {}
            for d in DIMENSIONS
        }

        return render_template(
            "row.html",
            run_id=run_id,
            example_id=example_id,
            row=row,
            judge_display=judge_display,
            dimensions=DIMENSIONS,
            ann_by_dim=ann_by_dim,
        )

    @flask_app.post("/run/<run_id>/row/<example_id>/annotate")
    def annotate(run_id: str, example_id: str):
        rp = _results_path(run_id)
        if not rp.exists():
            abort(404)

        dim_updates: dict[str, dict[str, Any]] = {}
        for dim in DIMENSIONS:
            score_raw = (request.form.get(f"{dim}_score") or "").strip()
            rationale = (request.form.get(f"{dim}_rationale") or "").strip()

            payload: dict[str, Any] = {}
            if score_raw:
                try:
                    score_i = int(score_raw)
                except ValueError:
                    score_i = 0
                if score_i < 1 or score_i > 5:
                    abort(400, description=f"Invalid score for {dim}: must be 1-5")
                payload["score"] = score_i
            if rationale:
                payload["rationale"] = rationale

            if payload:
                dim_updates[dim] = payload

        _update_annotation_in_file(
            rp, run_id=run_id, example_id=example_id, dim_updates=dim_updates
        )
        return redirect(url_for("row_view", run_id=run_id, example_id=example_id))

    return flask_app


app = create_app()


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", "8080")), debug=True)
