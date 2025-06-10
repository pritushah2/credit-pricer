import matplotlib.pyplot as plt
import pandas as pd


def plot_pnl_series(pnl_data, show_attribution=False):
    """
    pnl_data: list of dicts from PnLTracker.compute_pnl_series()
    show_attribution: if True, shows stacked attribution bars
    """
    df = pd.DataFrame(pnl_data)
    df["date"] = pd.to_datetime(df["date"])
    df = df.set_index("date")

    # Drop first row with None PnL
    df = df.dropna(subset=["daily_pnl"])

    # Compute cumulative
    df["cum_pnl"] = df["daily_pnl"].cumsum()

    # Plotting
    fig, ax1 = plt.subplots(figsize=(12, 6))

    # Plot daily PnL bars
    if show_attribution and "pnl_attrib" in df.columns:
        df_attr = df["pnl_attrib"].apply(pd.Series)
        df_attr.index = df.index
        df_attr.fillna(0, inplace=True)
        df_attr.plot(kind="bar", stacked=True, ax=ax1, width=0.8, alpha=0.85)
    else:
        ax1.bar(df.index, df["daily_pnl"], label="Daily PnL", color="skyblue")

    ax1.set_ylabel("Daily PnL")
    ax1.set_title("Daily and Cumulative PnL")
    ax1.legend(loc="upper left")

    # Plot cumulative PnL
    ax2 = ax1.twinx()
    ax2.plot(df.index, df["cum_pnl"], label="Cumulative PnL", color="black", linewidth=2)
    ax2.set_ylabel("Cumulative PnL")
    ax2.legend(loc="upper right")

    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    return fig
