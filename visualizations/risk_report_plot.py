import matplotlib.pyplot as plt
import numpy as np

def plot_risk_report(cs01_by_tenor, ir01_by_tenor):
    tenors = sorted(set(cs01_by_tenor) | set(ir01_by_tenor))
    cs01 = [cs01_by_tenor.get(t, 0) for t in tenors]
    ir01 = [ir01_by_tenor.get(t, 0) for t in tenors]

    bar_width = 0.35
    x = np.arange(len(tenors))

    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(x - bar_width/2, cs01, width=bar_width, label="CS01", color="steelblue")
    ax.bar(x + bar_width/2, ir01, width=bar_width, label="IR01", color="orange")

    ax.set_xticks(x)
    ax.set_xticklabels([f"{t}Y" for t in tenors])
    ax.set_xlabel("Tenor")
    ax.set_ylabel("Sensitivity (bps)")
    ax.set_title("CS01 and IR01 by Tenor")
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5)

    return fig
