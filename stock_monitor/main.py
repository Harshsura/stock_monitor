# main.py
import tkinter as tk
from tkinter import messagebox, ttk
from utils.stock_data import fetch_stock_data, parse_stock_data
from utils.db import init_db, fetch_history, insert_history
from plot import plot_stock_data
import threading
import queue
import time
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
from datetime import datetime

# Initialize the database
init_db()

class StockMonitorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Real-Time Stock Monitor")
        self.monitoring = False
        self.previous_price = None
        self.alert_threshold = 0.05  # 5% price change for alerts
        self.data_queue = queue.Queue()  # Queue for thread-safe data passing
        self.fig = None
        self.canvas = None  # Matplotlib canvas
        self.ax = None  # Matplotlib axis

        # UI Elements
        self.symbol_label = tk.Label(root, text="Enter Stock Symbol (e.g., AAPL):")
        self.symbol_label.pack(pady=5)
        self.symbol_entry = tk.Entry(root)
        self.symbol_entry.pack(pady=5)

        self.timeframe_label = tk.Label(root, text="Select Update Timeframe:")
        self.timeframe_label.pack(pady=5)
        self.timeframe_var = tk.StringVar(value="1min")
        self.timeframe_menu = ttk.Combobox(root, textvariable=self.timeframe_var, 
                                         values=["1min", "5min", "15min"], state="readonly")
        self.timeframe_menu.pack(pady=5)

        self.start_button = tk.Button(root, text="Start Monitoring", command=self.start_monitoring)
        self.start_button.pack(pady=5)
        self.stop_button = tk.Button(root, text="Stop Monitoring", command=self.stop_monitoring, state="disabled")
        self.stop_button.pack(pady=5)

        self.history_button = tk.Button(root, text="View History", command=self.view_history)
        self.history_button.pack(pady=5)

        self.export_button = tk.Button(root, text="Export to CSV", command=self.export_to_csv, state="disabled")
        self.export_button.pack(pady=5)

        self.output_text = tk.Text(root, height=10, width=50)
        self.output_text.pack(pady=10)

        # Canvas for embedding Matplotlib plot
        self.fig, self.ax = plt.subplots(figsize=(10, 6))
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.root)
        self.canvas.get_tk_widget().pack(pady=10)

        self.dates = []
        self.prices = []
        self.symbol = ""

    def start_monitoring(self):
        """Start real-time stock data monitoring."""
        self.symbol = self.symbol_entry.get().strip().upper()
        if not self.symbol:
            self.output_text.insert(tk.END, "Error: Please enter a stock symbol.\n")
            return

        self.monitoring = True
        self.start_button.config(state="disabled")
        self.stop_button.config(state="normal")
        self.export_button.config(state="normal")  # Enable export button
        self.output_text.insert(tk.END, f"Started monitoring {self.symbol}...\n")
        
        self.dates = []
        self.prices = []
        self.previous_price = None
        if self.fig:
            self.ax.clear()  # Clear existing plot
            self.canvas.draw()

        # Start background thread for fetching data
        threading.Thread(target=self.monitor_stock, daemon=True).start()
        self.check_queue()  # Start checking the queue for updates

    def stop_monitoring(self):
        """Stop real-time stock data monitoring."""
        self.monitoring = False
        self.start_button.config(state="normal")
        self.stop_button.config(state="disabled")
        self.export_button.config(state="disabled")  # Disable export button
        self.output_text.insert(tk.END, f"Stopped monitoring {self.symbol}.\n")
        insert_history(self.symbol, "Stopped monitoring")
        if self.fig:
            self.ax.clear()
            self.canvas.draw()

    def monitor_stock(self):
        """Fetch stock data in the background."""
        timeframe = self.timeframe_var.get()
        interval_map = {"1min": 60, "5min": 300, "15min": 900}  # Seconds
        interval = interval_map[timeframe]

        while self.monitoring:
            try:
                raw_data = fetch_stock_data(self.symbol, interval=timeframe)
                dates, prices = parse_stock_data(raw_data)
                if dates and prices:
                    self.data_queue.put((dates, prices))
                else:
                    self.data_queue.put(("error", "No valid data received"))
            except Exception as e:
                self.data_queue.put(("error", str(e)))
            time.sleep(interval)  # Wait for the next update

    def check_queue(self):
        """Check the queue for new data and update UI/plot."""
        if not self.monitoring:
            return
        try:
            while True:
                item = self.data_queue.get_nowait()
                if item[0] == "error":
                    self.output_text.insert(tk.END, f"Error: {item[1]}\n")
                    insert_history(self.symbol, f"Error: {item[1]}")
                else:
                    dates, prices = item
                    self.dates = dates
                    self.prices = prices
                    latest_date = dates[-1]
                    latest_price = prices[-1]
                    self.output_text.delete(1.0, tk.END)
                    self.output_text.insert(tk.END, f"Latest Data for {self.symbol}:\nDate: {latest_date}\nPrice: ${latest_price:.2f}\n")

                    if self.previous_price is not None:
                        price_change = abs(latest_price - self.previous_price) / self.previous_price
                        if price_change >= self.alert_threshold:
                            self.output_text.insert(tk.END, f"ALERT: Price changed by {price_change*100:.2f}%!\n")
                            messagebox.showwarning("Price Alert", f"{self.symbol} price changed by {price_change*100:.2f}% to ${latest_price:.2f}")
                    self.previous_price = latest_price

                    insert_history(self.symbol, f"Fetched intraday data at {latest_date}, price: ${latest_price:.2f}")
                    plot_stock_data(self.dates, self.prices, self.symbol, self.fig, self.ax, self.canvas)
        except queue.Empty:
            pass
        if self.monitoring:
            self.root.after(1000, self.check_queue)  # Check queue every second

    def export_to_csv(self):
        """Export current stock data to a CSV file."""
        if not self.dates or not self.prices:
            self.output_text.insert(tk.END, "Error: No data available to export.\n")
            return

        try:
            # Create DataFrame from dates and prices
            df = pd.DataFrame({
                'Date': self.dates,
                'Close': self.prices
            })
            
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/{self.symbol}_data_{timestamp}.csv"
            
            # Export to CSV
            df.to_csv(filename, index=False)
            self.output_text.insert(tk.END, f"Data exported to {filename}\n")
            insert_history(self.symbol, f"Exported data to {filename}")
        except Exception as e:
            self.output_text.insert(tk.END, f"Error exporting to CSV: {e}\n")
            insert_history(self.symbol, f"Error exporting to CSV: {e}")

    def view_history(self):
        """Fetch and display operation history from the database."""
        try:
            history = fetch_history()
            if not history:
                history_str = "No history available."
            else:
                history_str = "\n".join([f"{row[1]} | {row[2]}" for row in history])
            messagebox.showinfo("Operation History", history_str)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to fetch history: {e}")

if __name__ == "__main__":
    root = tk.Tk()
    app = StockMonitorApp(root)
    root.mainloop()