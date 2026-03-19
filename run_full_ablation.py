"""
ANIMA — run_full_ablation.py
==============================
Executa ablacao completa: 4 arms x 5 seeds para PROTOCOL-ANIMA-02.

Uso:
    python run_full_ablation.py
    python run_full_ablation.py --backend ollama --model llama3.1:8b
    python run_full_ablation.py --arms A D --seeds 42 7      # subset
    python run_full_ablation.py --resume                     # pula runs ja completados

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
import sys, os, time, argparse, subprocess, json
from datetime import datetime, timedelta

SEEDS   = [1, 42, 7, 99, 31]
ARMS    = ["A", "B", "C", "D"]
LOG_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "logs", "longitudinal")


def is_run_complete(arm: str, seed: int) -> bool:
    """Verifica se um arm/seed ja foi completado (todos os logs existem)."""
    n_passes = 2 if arm == "D" else 1
    for p in range(1, n_passes + 1):
        for s in range(1, 6):
            path = os.path.join(LOG_BASE, f"arm_{arm}", f"seed_{seed}",
                                f"pass_{p}", f"session_{s:02d}.json")
            if not os.path.exists(path):
                return False
    return True


def clean_state(arm: str, seed: int):
    """Remove estado serializado de runs anteriores para garantir run limpo."""
    state_dir = os.path.join(LOG_BASE, f"arm_{arm}", f"seed_{seed}")
    for fname in ["field_state.json", "field_state.json.memory.json"]:
        fpath = os.path.join(state_dir, fname)
        if os.path.exists(fpath):
            os.remove(fpath)


def run_single(arm: str, seed: int, backend: str, model: str,
               tick: float, hugo_mode: str = "standard",
               gamma: float = None, archetype: str = None) -> dict:
    """Executa um arm/seed via subprocess com output em tempo real."""
    cmd = [
        sys.executable, "-u", "run_longitudinal.py",
        "--arm", arm,
        "--seed", str(seed),
        "--backend", backend,
        "--model", model,
        "--tick", str(tick),
        "--hugo-mode", hugo_mode,
    ]
    if archetype is not None:
        cmd.extend(["--archetype", archetype])
    elif gamma is not None:
        cmd.extend(["--gamma", str(gamma)])
    t0 = time.time()
    cwd = os.path.dirname(os.path.abspath(__file__))
    stderr_buf = []
    try:
        proc = subprocess.Popen(
            cmd, stdout=sys.stdout, stderr=subprocess.PIPE,
            cwd=cwd, encoding="utf-8", errors="replace",
            bufsize=1,
        )
        _, stderr = proc.communicate()
        if stderr:
            stderr_buf.append(stderr)
        returncode = proc.returncode
    except Exception as e:
        returncode = -1
        stderr_buf.append(str(e))
    elapsed = time.time() - t0
    stderr_text = "".join(stderr_buf)
    return {
        "arm": arm, "seed": seed,
        "elapsed_s": round(elapsed, 1),
        "returncode": returncode,
        "success": returncode == 0,
        "stderr_tail": stderr_text[-500:] if stderr_text else "",
    }


def score_single(arm: str, seed: int) -> dict:
    """Roda coherence_scorer para um arm/seed e retorna metricas."""
    cmd = [sys.executable, "coherence_scorer.py", "--arm", arm,
           "--seed", str(seed)]
    result = subprocess.run(cmd, capture_output=True, text=True,
                            cwd=os.path.dirname(os.path.abspath(__file__)),
                            encoding="utf-8", errors="replace")
    if result.returncode != 0:
        return {"arm": arm, "seed": seed, "error": result.stderr[-300:]}

    # Parse output
    metrics = {"arm": arm, "seed": seed}
    for line in result.stdout.split("\n"):
        line = line.strip()
        if "DCS" in line and ":" in line and "Pass" not in line:
            metrics["DCS"] = float(line.split(":")[-1].strip())
        elif "NRF" in line and ":" in line and "Pass" not in line:
            metrics["NRF"] = float(line.split(":")[-1].strip())
        elif "ILR" in line and ":" in line and "Pass" not in line:
            metrics["ILR"] = float(line.split(":")[-1].strip())
        elif "PSI" in line and ":" in line:
            val = line.split(":")[-1].strip()
            metrics["PSI"] = float(val) if val != "N/A" else None
        # Per-pass metrics
        for prefix in ["DCS", "NRF", "ILR"]:
            if prefix in line and "Pass 1" in line:
                parts = line.split()
                for j, p in enumerate(parts):
                    if p == "Pass" and j+1 < len(parts) and parts[j+1] == "1":
                        # format: "DCS   0.607   0.626 ~  0.019"
                        pass
            if line.startswith(prefix) and len(line.split()) >= 4:
                parts = line.split()
                if len(parts) >= 4:
                    try:
                        metrics[f"{prefix}_p1"] = float(parts[1])
                        metrics[f"{prefix}_p2"] = float(parts[2])
                    except (ValueError, IndexError):
                        pass
    return metrics


def main():
    parser = argparse.ArgumentParser(
        description="ANIMA PROTOCOL-ANIMA-02: Full Ablation Study")
    parser.add_argument("--arms", nargs="+", default=ARMS,
                        choices=ARMS, help="Arms to run (default: A B C D)")
    parser.add_argument("--seeds", nargs="+", type=int, default=SEEDS,
                        help="Seeds to run (default: 1 42 7 99 31)")
    parser.add_argument("--backend", default="ollama")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--tick", type=float, default=2.0)
    parser.add_argument("--hugo-mode", choices=["standard","persistent","exploratory"],
                        default="standard",
                        help="HUGO field regulation preset (research parameter)")
    parser.add_argument("--resume", action="store_true",
                        help="Skip already-completed runs")
    parser.add_argument("--score-only", action="store_true",
                        help="Skip runs, only score existing logs")
    parser.add_argument("--clean", action="store_true",
                        help="Delete ALL existing logs and re-run everything from scratch")
    args = parser.parse_args()

    arms  = args.arms
    seeds = args.seeds
    total_runs = len(arms) * len(seeds)

    print("=" * 70)
    print("  ANIMA PROTOCOL-ANIMA-02: Full Ablation Study")
    print(f"  David Ohio | odavidohio@gmail.com | {datetime.now():%Y-%m-%d}")
    print("=" * 70)
    print(f"  Arms:    {arms}")
    print(f"  Seeds:   {seeds}")
    print(f"  Backend: {args.backend} | Model: {args.model}")
    print(f"  Total:   {total_runs} runs")
    print(f"  Resume:  {args.resume}")
    print(f"  Clean:   {args.clean}")
    print("=" * 70)

    # ── Clean mode: delete all existing logs for selected arms/seeds ───
    if args.clean:
        import shutil
        print("\n  [CLEAN] Deleting existing logs...")
        for arm in arms:
            for seed in seeds:
                d = os.path.join(LOG_BASE, f"arm_{arm}", f"seed_{seed}")
                if os.path.exists(d):
                    shutil.rmtree(d)
                    print(f"    Deleted: {d}")
        print("  [CLEAN] Done.\n")


    # ── Phase 1: Run experiments ──────────────────────────────────────────
    if not args.score_only:
        results = []
        completed = 0
        skipped = 0
        failed = 0
        t_global = time.time()

        for arm in arms:
            for seed in seeds:
                completed += 1
                tag = f"[{completed}/{total_runs}] Arm {arm} seed {seed}"

                if args.resume and is_run_complete(arm, seed):
                    print(f"\n{tag} — SKIP (already complete)")
                    skipped += 1
                    continue

                # Clean previous state
                clean_state(arm, seed)

                elapsed_so_far = time.time() - t_global
                if completed > 1 and (completed - skipped - 1) > 0:
                    avg_per_run = elapsed_so_far / (completed - skipped - 1)
                    remaining = total_runs - completed
                    eta = timedelta(seconds=int(avg_per_run * remaining))
                    print(f"\n{tag} — STARTING (ETA remaining: {eta})")
                else:
                    print(f"\n{tag} — STARTING")

                r = run_single(arm, seed, args.backend, args.model, args.tick, args.hugo_mode)
                results.append(r)

                if r["success"]:
                    print(f"  DONE in {r['elapsed_s']:.0f}s")
                else:
                    failed += 1
                    print(f"  FAILED (code {r['returncode']})")
                    print(f"  stderr: {r['stderr_tail'][:200]}")

        elapsed_total = time.time() - t_global
        print(f"\n{'='*70}")
        print(f"  Phase 1 complete: {completed - skipped - failed} ok, "
              f"{skipped} skipped, {failed} failed")
        print(f"  Total time: {timedelta(seconds=int(elapsed_total))}")
        print(f"{'='*70}")

        # Save run log
        run_log_path = os.path.join(LOG_BASE, "ablation_run_log.json")
        with open(run_log_path, "w") as f:
            json.dump({"timestamp": datetime.now().isoformat(),
                        "args": vars(args), "results": results}, f, indent=2)
        print(f"  Run log: {run_log_path}")


    # ── Phase 2: Score all completed runs ─────────────────────────────────
    print(f"\n{'='*70}")
    print("  Phase 2: Scoring all completed runs")
    print(f"{'='*70}")

    all_scores = []
    for arm in arms:
        for seed in seeds:
            if is_run_complete(arm, seed):
                sc = score_single(arm, seed)
                all_scores.append(sc)
                dcs = sc.get("DCS", "?")
                nrf = sc.get("NRF", "?")
                ilr = sc.get("ILR", "?")
                psi = sc.get("PSI", "N/A")
                err = sc.get("error", "")
                if err:
                    print(f"  Arm {arm} seed {seed}: ERROR — {err[:100]}")
                else:
                    psi_str = f"{float(psi):+.3f}" if psi is not None and psi != "N/A" else "N/A"
                    print(f"  Arm {arm} seed {seed}: "
                          f"DCS={dcs:.3f}  NRF={nrf:.3f}  "
                          f"ILR={ilr:.3f}  PSI={psi_str}")
            else:
                print(f"  Arm {arm} seed {seed}: INCOMPLETE — skipping")


    # ── Phase 3: Summary statistics by arm ────────────────────────────────
    print(f"\n{'='*70}")
    print("  Phase 3: Summary Statistics by Arm")
    print(f"{'='*70}")

    from statistics import mean as smean, stdev as sstdev

    header = (f"{'Arm':>4} | {'N':>3} | {'DCS mean':>9} {'±':>1} {'sd':>5} | "
              f"{'NRF mean':>9} {'±':>1} {'sd':>5} | "
              f"{'ILR mean':>9} {'±':>1} {'sd':>5} | "
              f"{'PSI mean':>9} {'±':>1} {'sd':>5}")
    print(header)
    print("-" * len(header))

    arm_summary = {}
    for arm in arms:
        arm_scores = [s for s in all_scores
                      if s["arm"] == arm and "error" not in s]
        if not arm_scores:
            print(f"{arm:>4} | {'N/A':>3} | no completed runs")
            continue

        n = len(arm_scores)
        for metric in ["DCS", "NRF", "ILR"]:
            vals = [s[metric] for s in arm_scores if metric in s]
            if vals:
                m, sd = smean(vals), sstdev(vals) if len(vals) > 1 else 0.0
                arm_summary.setdefault(arm, {})[metric] = (m, sd)

        psi_vals = [s["PSI"] for s in arm_scores
                    if "PSI" in s and s["PSI"] is not None]
        if psi_vals:
            m, sd = smean(psi_vals), sstdev(psi_vals) if len(psi_vals) > 1 else 0.0
            arm_summary.setdefault(arm, {})["PSI"] = (m, sd)

        s = arm_summary.get(arm, {})
        def fmt(metric):
            if metric in s:
                return f"{s[metric][0]:>9.3f} ± {s[metric][1]:>5.3f}"
            return f"{'N/A':>9} {'':>1} {'':>5}"

        psi_fmt = fmt("PSI") if "PSI" in s else f"{'N/A':>9}   {'':>5}"
        print(f"{arm:>4} | {n:>3} | {fmt('DCS')} | "
              f"{fmt('NRF')} | {fmt('ILR')} | {psi_fmt}")


    # ── Phase 4: Causal analysis preview ──────────────────────────────────
    print(f"\n{'='*70}")
    print("  Phase 4: Causal Analysis Preview")
    print(f"{'='*70}")

    a = arm_summary.get("A", {})
    d = arm_summary.get("D", {})
    if a and d:
        for metric in ["DCS", "NRF", "ILR"]:
            if metric in a and metric in d:
                delta = d[metric][0] - a[metric][0]
                direction = "UP" if delta > 0 else "DOWN"
                print(f"  D vs A ({metric}): {delta:+.3f} ({direction})")
        if "PSI" in d:
            print(f"  D PSI (policy shift): {d['PSI'][0]:+.3f} ± {d['PSI'][1]:.3f}")
    else:
        print("  Insufficient data for D vs A comparison")

    # ── Save full scores ──────────────────────────────────────────────────
    scores_path = os.path.join(LOG_BASE, "ablation_scores.json")
    with open(scores_path, "w") as f:
        json.dump({"timestamp": datetime.now().isoformat(),
                    "scores": all_scores,
                    "summary": {k: {m: list(v) for m, v in s.items()}
                                for k, s in arm_summary.items()}},
                  f, indent=2)
    print(f"\n  Scores saved: {scores_path}")
    print(f"\n{'='*70}")
    print("  ABLATION STUDY COMPLETE")
    print(f"{'='*70}")


if __name__ == "__main__":
    main()
