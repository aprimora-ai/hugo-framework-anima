"""Quick test: compare HUGO regulation modes."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))
from chat_anima import HUGOField

modes = ["standard", "persistent", "exploratory"]
for mode in modes:
    f = HUGOField(seed=42, mode=mode)
    for _ in range(35):
        f.inject_I(0.3)
        s = f.tick()
    step = s["step"]
    theta = s["theta"]
    rm = s["regulation_mode"]
    dr = s["decay_rate"]
    H = [round(h, 4) for h in f.H]
    print(f"{mode:<12s} | step={step} theta={theta:.4f} mode={rm} decay={dr} H={H}")
