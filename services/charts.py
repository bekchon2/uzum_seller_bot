"""Generate matplotlib charts for Telegram"""
import io
import datetime
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates


def generate_sales_chart(daily_data: list[dict], title: str, ylabel: str) -> bytes:
    """
    daily_data: [{"date": "2024-01-01", "revenue": 500000, "orders": 5}, ...]
    Returns PNG bytes
    """
    if not daily_data:
        return _empty_chart(title)

    dates = [datetime.datetime.strptime(d["date"], "%Y-%m-%d") for d in daily_data]
    revenues = [d["revenue"] for d in daily_data]
    orders = [d["orders"] for d in daily_data]

    fig, ax1 = plt.subplots(figsize=(10, 5))
    fig.patch.set_facecolor("#1a1a2e")
    ax1.set_facecolor("#16213e")

    # Revenue bars
    bars = ax1.bar(dates, revenues, color="#e94560", alpha=0.85, width=0.6, zorder=2)
    ax1.set_ylabel(ylabel, color="#e94560", fontsize=11)
    ax1.tick_params(axis="y", labelcolor="#e94560")
    ax1.yaxis.set_major_formatter(
        matplotlib.ticker.FuncFormatter(lambda x, _: f"{x/1_000_000:.1f}M" if x >= 1_000_000 else f"{x/1000:.0f}K")
    )

    # Orders line
    ax2 = ax1.twinx()
    ax2.plot(dates, orders, color="#0f3460", marker="o", linewidth=2.5,
             markersize=7, zorder=3, markerfacecolor="#e94560", markeredgecolor="white")
    ax2.set_ylabel("Buyurtmalar / Заказы", color="#53d8fb", fontsize=11)
    ax2.tick_params(axis="y", labelcolor="#53d8fb")

    # Styling
    ax1.xaxis.set_major_formatter(mdates.DateFormatter("%d.%m"))
    ax1.xaxis.set_major_locator(mdates.DayLocator())
    plt.xticks(rotation=30, color="#cccccc")
    ax1.tick_params(axis="x", colors="#cccccc")
    ax1.tick_params(axis="y", colors="#e94560")
    ax2.tick_params(axis="y", colors="#53d8fb")

    for spine in ax1.spines.values():
        spine.set_edgecolor("#333366")
    for spine in ax2.spines.values():
        spine.set_edgecolor("#333366")

    ax1.grid(axis="y", color="#333366", linestyle="--", alpha=0.5, zorder=1)
    ax1.set_title(title, color="white", fontsize=14, fontweight="bold", pad=15)

    # Value labels on bars
    for bar, rev in zip(bars, revenues):
        if rev > 0:
            ax1.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height() + max(revenues) * 0.01,
                f"{rev/1000:.0f}K",
                ha="center", va="bottom", color="white", fontsize=8
            )

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def generate_storage_chart(products: list[dict], lang: str = "ru") -> bytes:
    """Horizontal bar chart showing days in storage per product"""
    if not products:
        return _empty_chart("Storage")

    # Sort by days desc
    products = sorted(products, key=lambda x: x.get("days_in_storage", 0), reverse=True)[:15]
    names = [p["name"][:25] for p in products]
    days = [p.get("days_in_storage", 0) for p in products]
    colors = []
    for d in days:
        if d >= 60:
            colors.append("#e94560")
        elif d >= 50:
            colors.append("#ff8c00")
        elif d >= 40:
            colors.append("#ffd700")
        else:
            colors.append("#2ecc71")

    fig, ax = plt.subplots(figsize=(10, max(4, len(names) * 0.5 + 1)))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")

    bars = ax.barh(names, days, color=colors, alpha=0.9)
    ax.axvline(x=60, color="#e94560", linestyle="--", linewidth=1.5, label="60 kun (limit)", alpha=0.8)
    ax.axvline(x=50, color="#ff8c00", linestyle=":", linewidth=1, alpha=0.6)

    for bar, d in zip(bars, days):
        ax.text(bar.get_width() + 0.5, bar.get_y() + bar.get_height() / 2,
                f"{d} kun", va="center", color="white", fontsize=9)

    title = "Omborxona holati (saqlash kunlari)" if lang == "uz" else "Статус хранения (дней на складе)"
    ax.set_title(title, color="white", fontsize=13, fontweight="bold", pad=12)
    ax.set_xlabel("Kunlar / Дней", color="#cccccc")
    ax.tick_params(colors="#cccccc")
    ax.legend(facecolor="#1a1a2e", labelcolor="white", fontsize=9)
    ax.set_xlim(0, max(max(days) + 10, 65))

    for spine in ax.spines.values():
        spine.set_edgecolor("#333366")
    ax.grid(axis="x", color="#333366", linestyle="--", alpha=0.4)

    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=120, bbox_inches="tight",
                facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()


def _empty_chart(title: str) -> bytes:
    fig, ax = plt.subplots(figsize=(8, 4))
    fig.patch.set_facecolor("#1a1a2e")
    ax.set_facecolor("#16213e")
    ax.text(0.5, 0.5, "Ma'lumot yo'q / Нет данных", ha="center", va="center",
            color="#cccccc", fontsize=14, transform=ax.transAxes)
    ax.set_title(title, color="white", fontsize=13)
    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=100, bbox_inches="tight", facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return buf.read()
