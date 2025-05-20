# plot.py
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

def plot_stock_data(dates, prices, symbol, fig, ax, canvas):
    """Plot stock data using Matplotlib embedded in Tkinter."""
    ax.clear()
    ax.plot(dates, prices, marker='o', linestyle='-', color='blue')
    ax.set_title(f"{symbol} Stock Price Trends", fontsize=16)
    ax.set_xlabel("Date", fontsize=12)
    ax.set_ylabel("Closing Price (USD)", fontsize=12)
    ax.grid(True, linestyle='--', alpha=0.6)
    
    if dates:
        step = max(1, len(dates) // 5)
        ax.set_xticks(range(0, len(dates), step))
        ax.set_xticklabels(dates[::step], rotation=45, fontsize=8)
    
    fig.tight_layout()
    canvas.draw()