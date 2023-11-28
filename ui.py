import tkinter as tk
import requests
import json
from threading import Timer
import statistics

class DashboardApp:
    def __init__(self, root):
        self.root = root
        root.title("Load Testing Dashboard")
        root.geometry("500x400")

        self.update_button = tk.Button(root, text="Update Data", command=self.update_data, padx=10, pady=5)
        self.update_button.pack(pady=10)

        self.start_stop_button = tk.Button(root, text="Start Test", command=self.toggle_test, padx=10, pady=5)
        self.start_stop_button.pack(pady=5)

        self.clear_button = tk.Button(root, text="Clear Metrics", command=self.clear_metrics, padx=10, pady=5)
        self.clear_button.pack(pady=5)

        self.metrics_frame = tk.Frame(root)
        self.metrics_frame.pack(pady=10)

        self.create_metric_label("Max Response Time: ", "max_response_time")
        self.create_metric_label("Mean Response Time: ", "mean_response_time")
        self.create_metric_label("Median Response Time: ", "median_response_time")
        self.create_metric_label("Min Response Time: ", "min_response_time")
        self.create_metric_label("Mode Response Time: ", "mode_response_time")

        self.status_label = tk.Label(root, text="Test Status: Stopped", font=("Helvetica", 12))
        self.status_label.pack(pady=5)

        self.heartbeat_label = tk.Label(root, text="Heartbeat Status: N/A", font=("Helvetica", 12))
        self.heartbeat_label.pack(pady=5)

        self.auto_update = False
        self.test_running = False
        self.update_data()

        # Periodically update the heartbeat status (every 5 seconds in this example)
        self.update_heartbeat_status()

    def create_metric_label(self, label_text, metric_key):
        label_frame = tk.Frame(self.metrics_frame)
        label_frame.pack(fill="x")
        label = tk.Label(label_frame, text=label_text, font=("Helvetica", 12), width=20, anchor="w")
        label.pack(side="left")
        metric_value = tk.Label(label_frame, text="N/A", font=("Helvetica", 12))
        metric_value.pack(side="right")
        setattr(self, metric_key + "_label", metric_value)

    def fetch_metrics(self):
        try:
            response = requests.get("http://127.0.0.1:5000/metrics")
            return response.json()
        except requests.RequestException as e:
            return {"error": str(e)}

    def fetch_heartbeat_status(self):
        try:
            response = requests.get("http://127.0.0.1:5000/heartbeat")
            status = response.json()["heartbeat"]
            return status if status else "N/A"
        except requests.RequestException as e:
            return "N/A"

    def update_heartbeat_status(self):
        heartbeat_status = self.fetch_heartbeat_status()
        self.heartbeat_label.config(text=f"Heartbeat Status: {heartbeat_status}")
        if self.auto_update:
            self.root.after(5000, self.update_heartbeat_status)

    def calculate_statistics(self, metrics_list):
        if not metrics_list:
            return {
                "max_response_time": "N/A",
                "mean_response_time": "N/A",
                "median_response_time": "N/A",
                "min_response_time": "N/A"
            }

        max_response_time = max(metrics["metrics"]["max_latency"] for metrics in metrics_list)
        mean_response_time = statistics.mean(metrics["metrics"]["mean_latency"] for metrics in metrics_list)
        median_response_time = statistics.median(metrics["metrics"]["median_latency"] for metrics in metrics_list)
        min_response_time = min(metrics["metrics"]["min_latency"] for metrics in metrics_list)

        return {
            "max_response_time": max_response_time,
            "mean_response_time": mean_response_time,
            "median_response_time": median_response_time,
            "min_response_time": min_response_time
        }



    def update_data(self):
        metrics = self.fetch_metrics()
        statistics_data = self.calculate_statistics(metrics)
        heartbeat_status = self.fetch_heartbeat_status()

        for metric, value in statistics_data.items():
            label = getattr(self, metric + "_label")
            label.config(text=f"{metric}: {value:.4f} seconds")

        self.heartbeat_label.config(text=f"Heartbeat Status: {heartbeat_status}")

        if self.auto_update:
            Timer(1, self.update_data).start()

    def toggle_test(self):
        if self.test_running:
            self.test_running = False
            self.status_label.config(text="Test Status: Stopped")
            self.start_stop_button.config(text="Start Test")
        else:
            self.test_running = True
            self.status_label.config(text="Test Status: Running")
            self.start_stop_button.config(text="Stop Test")

    def clear_metrics(self):
        for metric in ["max_response_time", "mean_response_time", "median_response_time", "min_response_time", "mode_response_time"]:
            label = getattr(self, metric + "_label")
            label.config(text=f"{metric}: N/A")

root = tk.Tk()
app = DashboardApp(root)
root.mainloop()
