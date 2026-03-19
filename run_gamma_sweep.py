"""
ANIMA-03 — γ-Sweep: Mapping the Personality Parameter Space
=============================================================
David Ohio | Independent Researcher | odavidohio@gmail.com
HUGO AGI Framework — March 2026

Purpose: Map the behavioral trait landscape across γ values to
determine optimal parameters for different agent profiles.

Design:
  - Arm D only (full treatment: memory + exposure + HUGO field)
  - 8 γ values: 0.90, 0.93, 0.95, 0.97, 0.985, 0.99, 0.995, 0.999
  - 3 seeds per γ value
  - 2 passes × 2 sessions per pass = 4 sessions per seed
  - Total: 96 sessions (~6-7 hours estimated)

Output: γ → trait profile mapping for agent role assignment.
"""

import os, sys, json, time, subprocess, argparse
from pathlib import Path
from datetime import datetime

# Fix Windows console encoding
import io
if sys.stdout.encoding and sys.stdout.encoding.lower() not in ('utf-8', 'utf8'):
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

GAMMA_VALUES = [0.90, 0.93, 0.95, 0.97, 0.985, 0.99, 0.995, 0.999]
SEEDS = [1, 42, 7]
N_SESSIONS = 2       # sessions per pass
N_PASSES = 2         # passes per seed


LOG_BASE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        "logs", "gamma_sweep")

def sweep_dir(gamma: float, seed: int) -> str:
    """Directory for a specific gamma/seed run."""
    tag = f"g{gamma:.3f}"
    return os.path.join(LOG_BASE, tag, f"seed_{seed}")


def is_run_complete(gamma: float, seed: int) -> bool:
    """Check if a gamma/seed run has all expected session files."""
    base = sweep_dir(gamma, seed)
    for p in [1, 2]:
        for s in range(1, N_SESSIONS + 1):
            path = os.path.join(base, f"pass_{p}", f"session_{s:02d}.json")
            if not os.path.exists(path):
                return False
    return True


def run_gamma_seed(gamma: float, seed: int, backend: str, model: str,
                   tick: float, resume: bool = False) -> dict:
    """Run a single gamma/seed combination via subprocess."""
    if resume and is_run_complete(gamma, seed):
        print(f"  [SKIP] gamma={gamma:.3f} seed={seed} — already complete")
        return {"gamma": gamma, "seed": seed, "status": "skipped", "elapsed": 0}

    # Build log dir for this gamma/seed
    log_dir = os.path.join(LOG_BASE, f"g{gamma:.3f}")
    sessions = ",".join(str(s) for s in range(1, N_SESSIONS + 1))

    cmd = [
        sys.executable, "-u", "run_longitudinal.py",
        "--arm", "D",
        "--seed", str(seed),
        "--backend", backend,
        "--model", model,
        "--tick", str(tick),
        "--gamma", str(gamma),
        "--sessions", sessions,
        "--log-dir", log_dir,
        "--reset",
    ]

    t0 = time.time()
    cwd = os.path.dirname(os.path.abspath(__file__))

    try:
        proc = subprocess.Popen(
            cmd, stdout=sys.stdout, stderr=subprocess.PIPE,
            cwd=cwd, encoding="utf-8", errors="replace", bufsize=1,
        )
        _, stderr = proc.communicate()
        returncode = proc.returncode
    except Exception as e:
        returncode = -1
        stderr = str(e)

    elapsed = time.time() - t0
    status = "ok" if returncode == 0 else f"fail(rc={returncode})"

    return {
        "gamma": gamma, "seed": seed,
        "status": status, "elapsed": round(elapsed, 1),
    }


def score_gamma(gamma: float) -> list:
    """Score all seeds for a given gamma using coherence_scorer."""
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from coherence_scorer import score_arm_with_base
    results = []
    for seed in SEEDS:
        try:
            log_dir = os.path.join(LOG_BASE, f"g{gamma:.3f}")
            scores = score_arm_with_base("D", seed, log_base=log_dir)
            scores["gamma"] = gamma
            scores["seed"] = seed
            results.append(scores)
        except Exception as e:
            print(f"  [SCORE ERROR] gamma={gamma:.3f} seed={seed}: {e}")
    return results


def extract_traits(gamma: float) -> dict:
    """Extract the 14 behavioral traits from session logs."""
    import numpy as np
    all_theta_var = []
    all_kappa_katashi_frac = []
    all_self_step = []
    all_diversity = []
    all_regen = []
    all_sga_rho = []

    for seed in SEEDS:
        for p in range(1, N_PASSES + 1):
            for s in range(1, N_SESSIONS + 1):
                fpath = os.path.join(LOG_BASE, f"g{gamma:.3f}",
                                     f"arm_D", f"seed_{seed}",
                                     f"pass_{p}", f"session_{s:02d}.json")
                if not os.path.exists(fpath):
                    continue
                try:
                    with open(fpath, encoding="utf-8") as f:
                        sess = json.load(f)
                except Exception:
                    continue

                turns = sess.get("turns", [])
                if not turns:
                    continue

                # Theta variance (emotional stability)
                thetas = [t["theta"] for t in turns if "theta" in t]
                if len(thetas) >= 3:
                    all_theta_var.append(float(np.var(thetas)))

                # Kappa regime fractions (structural rigidity)
                regimes = [t.get("kappa_regime", "") for t in turns]
                if regimes:
                    katashi_frac = sum(1 for r in regimes if r == "katashi") / len(regimes)
                    all_kappa_katashi_frac.append(katashi_frac)

                # Self emergence step
                summary = sess.get("summary", {})
                se_step = summary.get("self_emergence_step")
                if se_step is not None and se_step > 0:
                    all_self_step.append(se_step)

                # Diversity
                divs = [t["diversity"] for t in turns if "diversity" in t]
                if divs:
                    all_diversity.append(float(np.mean(divs)))

                # Regeneration rate
                regens = [t["R_regen"] for t in turns
                          if "R_regen" in t and t["R_regen"] is not None]
                if regens:
                    all_regen.append(float(np.mean(regens)))

                # Action fidelity (SGA rho)
                rhos = [t["sga_rho"] for t in turns if "sga_rho" in t]
                if rhos:
                    all_sga_rho.append(float(np.mean(rhos)))

    def safe_mean(vals):
        return round(float(np.mean(vals)), 4) if vals else None

    def safe_std(vals):
        return round(float(np.std(vals)), 4) if vals else None

    return {
        "gamma": gamma,
        "theta_variance": {"mean": safe_mean(all_theta_var), "std": safe_std(all_theta_var)},
        "katashi_fraction": {"mean": safe_mean(all_kappa_katashi_frac), "std": safe_std(all_kappa_katashi_frac)},
        "self_emergence_step": {"mean": safe_mean(all_self_step), "std": safe_std(all_self_step)},
        "diversity": {"mean": safe_mean(all_diversity), "std": safe_std(all_diversity)},
        "regen_rate": {"mean": safe_mean(all_regen), "std": safe_std(all_regen)},
        "action_fidelity": {"mean": safe_mean(all_sga_rho), "std": safe_std(all_sga_rho)},
    }


def main():
    parser = argparse.ArgumentParser(
        description="ANIMA-03: γ-Sweep — Map the Personality Parameter Space"
    )
    parser.add_argument("--backend", default="ollama")
    parser.add_argument("--model", default="llama3.1:8b")
    parser.add_argument("--tick", type=float, default=2.0)
    parser.add_argument("--resume", action="store_true",
                        help="Skip completed gamma/seed combinations")
    parser.add_argument("--score-only", action="store_true",
                        help="Skip runs, only score existing logs")
    parser.add_argument("--gammas", type=str, default=None,
                        help="Override gamma values (comma-separated, e.g. '0.97,0.99,0.995')")
    args = parser.parse_args()

    gammas = GAMMA_VALUES
    if args.gammas:
        gammas = [float(g) for g in args.gammas.split(",")]

    total = len(gammas) * len(SEEDS)
    print("=" * 72)
    print("  ANIMA-03 — γ-Sweep: Personality Parameter Space")
    print("  David Ohio | odavidohio@gmail.com")
    print("=" * 72)
    print(f"  Gamma values: {gammas}")
    print(f"  Seeds: {SEEDS}")
    print(f"  Sessions per pass: {N_SESSIONS}")
    print(f"  Total runs: {total}")
    print()

    # Phase 1: Run experiments
    if not args.score_only:
        t0 = time.time()
        run_log = []
        done = 0
        for gamma in gammas:
            for seed in SEEDS:
                done += 1
                print(f"\n[{done}/{total}] gamma={gamma:.3f} seed={seed}")
                result = run_gamma_seed(
                    gamma, seed, args.backend, args.model,
                    args.tick, resume=args.resume,
                )
                run_log.append(result)
                print(f"  => {result['status']} ({result['elapsed']}s)")

        elapsed = time.time() - t0
        print(f"\n  Phase 1 complete: {elapsed:.0f}s total")

        # Save run log
        os.makedirs(LOG_BASE, exist_ok=True)
        with open(os.path.join(LOG_BASE, "sweep_run_log.json"), "w") as f:
            json.dump(run_log, f, indent=2)


    # Phase 2: Score all gammas
    print("\n" + "=" * 72)
    print("  Phase 2: Scoring all gamma values")
    print("=" * 72)

    import numpy as np
    all_scores = []
    for gamma in gammas:
        scores = score_gamma(gamma)
        all_scores.extend(scores)
        if scores:
            dcs_vals = [s["DCS"] for s in scores if s.get("DCS")]
            ilr_vals = [s["ILR"] for s in scores if s.get("ILR")]
            psi_vals = [s["PSI"] for s in scores if s.get("PSI") is not None]
            print(f"  gamma={gamma:.3f}: "
                  f"DCS={np.mean(dcs_vals):.3f}+{np.std(dcs_vals):.3f}  "
                  f"ILR={np.mean(ilr_vals):.3f}+{np.std(ilr_vals):.3f}  "
                  + (f"PSI={np.mean(psi_vals):.3f}" if psi_vals else "PSI=N/A"))


    # Phase 3: Extract behavioral traits
    print("\n" + "=" * 72)
    print("  Phase 3: Extracting behavioral traits")
    print("=" * 72)

    all_traits = []
    for gamma in gammas:
        traits = extract_traits(gamma)
        all_traits.append(traits)
        tv = traits.get("theta_variance", {})
        kf = traits.get("katashi_fraction", {})
        dv = traits.get("diversity", {})
        print(f"  gamma={gamma:.3f}: "
              f"theta_var={tv.get('mean','?')}  "
              f"katashi={kf.get('mean','?')}  "
              f"diversity={dv.get('mean','?')}")


    # Phase 4: Summary table
    print("\n" + "=" * 72)
    print("  Phase 4: γ → Profile Mapping")
    print("=" * 72)

    header = (f"  {'gamma':>7s}  {'DCS':>8s}  {'NRF':>8s}  {'ILR':>8s}  "
              f"{'PSI':>8s}  {'θ_var':>8s}  {'katashi':>8s}  {'div':>8s}")
    print(header)
    print("  " + "-" * (len(header) - 2))

    for gamma in gammas:
        g_scores = [s for s in all_scores if s.get("gamma") == gamma]
        g_traits = next((t for t in all_traits if t["gamma"] == gamma), {})

        dcs = np.mean([s["DCS"] for s in g_scores]) if g_scores else 0
        nrf = np.mean([s["NRF"] for s in g_scores]) if g_scores else 0
        ilr = np.mean([s["ILR"] for s in g_scores]) if g_scores else 0
        psi_vals = [s["PSI"] for s in g_scores if s.get("PSI") is not None]
        psi = np.mean(psi_vals) if psi_vals else float('nan')

        tv = g_traits.get("theta_variance", {}).get("mean", "?")
        kf = g_traits.get("katashi_fraction", {}).get("mean", "?")
        dv = g_traits.get("diversity", {}).get("mean", "?")

        psi_str = f"{psi:>8.3f}" if not np.isnan(psi) else f"{'N/A':>8s}"
        tv_str = f"{tv:>8.4f}" if isinstance(tv, float) else f"{'?':>8s}"
        kf_str = f"{kf:>8.4f}" if isinstance(kf, float) else f"{'?':>8s}"
        dv_str = f"{dv:>8.4f}" if isinstance(dv, float) else f"{'?':>8s}"

        print(f"  {gamma:>7.3f}  {dcs:>8.3f}  {nrf:>8.3f}  {ilr:>8.3f}  "
              f"{psi_str}  {tv_str}  {kf_str}  {dv_str}")


    # Save comprehensive results
    out_path = os.path.join(LOG_BASE, "gamma_sweep_results.json")
    results_data = {
        "metadata": {
            "timestamp": datetime.now().isoformat(),
            "author": "David Ohio",
            "email": "odavidohio@gmail.com",
            "experiment": "ANIMA-03 gamma sweep",
            "gamma_values": gammas,
            "seeds": SEEDS,
            "sessions_per_pass": N_SESSIONS,
            "passes": N_PASSES,
        },
        "scores": all_scores,
        "traits": all_traits,
    }
    os.makedirs(LOG_BASE, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results_data, f, indent=2, default=str)

    print(f"\n  Results saved: {out_path}")
    print("\n" + "=" * 72)
    print("  GAMMA SWEEP COMPLETE")
    print("=" * 72)


if __name__ == "__main__":
    main()
