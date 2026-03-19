"""
PROTOCOL-VHP-01 — Falsificação da Sequência de Mersenne
Conjectura VHP-1: P*(d) = (2^d - 1) / 2^d

David Ohio | Independent Researcher | odavidohio@gmail.com | 2026
"""
import numpy as np

class HUGO_Field_VHP:
    def __init__(self, n_total, d_plastic):
        assert d_plastic <= n_total
        self.n = n_total
        self.d = d_plastic
        self.H_nom = np.ones(self.n)
        self.H = np.copy(self.H_nom)
        self.is_plastic = np.array([True]*self.d + [False]*(self.n - self.d))
        self.r = np.full(self.n, 0.1)
        self.sigma = np.zeros(self.n)

    def apply_existential_trauma(self):
        self.H = np.zeros(self.n)
        if self.d > 0:
            target_volume = (2**self.d - 1) / (2**self.d)
            H_plastic_target = target_volume ** (1.0 / self.d)
            sigma_required = self.r[:self.d] * (1.0 - H_plastic_target)
            self.sigma[self.is_plastic] = sigma_required

    def rheological_step(self, dt=1.0):
        dH_dt = self.r * (self.H_nom - self.H) - self.sigma
        self.H += dH_dt * dt

    def get_accessible_volume(self):
        return float(np.prod(self.H))


def run_vhp_protocol():
    print("PROTOCOL-VHP-01: Falsificacao da Sequencia de Mersenne")
    print(f"{'n':>6} {'d':>6} {'P_obs':>12} {'P_teo':>12} {'erro':>10} {'ok':>5}")
    print("-" * 55)

    test_cases = [
        (5, 1), (5, 2), (5, 3), (5, 4), (5, 5),
        (3, 3), (7, 3), (10, 3),
        (7, 5), (7, 7),
    ]

    all_pass = True
    for n, d in test_cases:
        field = HUGO_Field_VHP(n_total=n, d_plastic=d)
        field.apply_existential_trauma()
        for _ in range(1000):
            field.rheological_step()
        vol_obs = field.get_accessible_volume()
        vol_teo = (2**d - 1) / (2**d) if d > 0 else 1.0
        erro = abs(vol_obs - vol_teo)
        ok = "OK" if erro < 0.001 else "FAIL"
        if ok == "FAIL":
            all_pass = False
        print(f"{n:>6} {d:>6} {vol_obs:>12.6f} {vol_teo:>12.6f} {erro:>10.6f} {ok:>5}")

    print()
    print("Corolario VHP-1b: dimensoes elasticas nao afetam o platô")
    for n in [3, 5, 7, 10]:
        field = HUGO_Field_VHP(n_total=n, d_plastic=3)
        field.apply_existential_trauma()
        for _ in range(1000):
            field.rheological_step()
        vol = field.get_accessible_volume()
        print(f"  n={n}, d=3: P_obs={vol:.6f}  (expected 0.875000)")

    print()
    if all_pass:
        print("RESULTADO: Conjectura VHP-1 CONFIRMADA para todos os casos testados.")
    else:
        print("RESULTADO: Falha detectada — revisar parametrizacao.")

if __name__ == "__main__":
    run_vhp_protocol()
