from prometheus_client.parser import text_string_to_metric_families
import requests
from collections import defaultdict, deque
import time
import os
import threading

class VLLM_TOP:
    def __init__(self, history_size=50, max_running=255, max_waiting=1000):
        self.history_size = history_size
        self.max_running = max_running
        self.max_waiting = max_waiting
        self.running_history = deque(maxlen=history_size)
        self.waiting_history = deque(maxlen=history_size)
        self.cache_usage_history = deque(maxlen=history_size)
        self.timestamps = deque(maxlen=history_size)
        
        # Background monitoring
        self.background_running = []
        self.background_waiting = []
        self.background_cache = []
        self.background_lock = threading.Lock()
        self.is_monitoring = False
        
    def clear_screen(self):
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def create_bar_chart(self, value, max_value, width=40, label=""):
        """Create a horizontal bar chart in terminal"""
        if max_value == 0:
            percentage = 0
        else:
            percentage = min(value / max_value, 1.0)
        
        filled_width = int(percentage * width)
        bar = "█" * filled_width + "░" * (width - filled_width)
        return f"{label:<25} |{bar}| {value:.1f}/{max_value:.0f} ({percentage*100:.0f}%)"
       
    def create_sparkline(self, data, width=60, fixed_min=0, fixed_max=None, label_min=None, label_max=None, label_prefix=""):
        """Triple-height sparkline with Unicode blocks for max smoothness (24 levels, 8 per row), framed with min/max labels and dynamic offset.
        Each column fills from the bottom up, like a histogram."""
        if not data or len(data) < 2:
            spark_rows = [("░" * width) for _ in range(3)]
        else:
            min_val = fixed_min
            max_val = fixed_max if fixed_max is not None else 1

            if max_val == min_val:
                spark_rows = [("▄" * width) for _ in range(3)]
            else:
                blocks = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
                levels = 24  # 8 per row, 3 rows
                data_width = min(len(data), width)
                col_levels = []
                for i in range(data_width):
                    normalized = max(0, min(1, (data[i] - min_val) / (max_val - min_val)))
                    col_levels.append(int(normalized * (levels - 1)))

                # Fill from bottom up: if a column's level is high, fill all lower rows too
                spark_rows = []
                for row in range(3):
                    line = ""
                    base = (2 - row) * 8
                    for lvl in col_levels:
                        if lvl >= base:
                            # Pick the block for this row, or the highest if above
                            block_idx = min(max(lvl - base, 0), 7)
                            line += blocks[block_idx]
                        else:
                            line += " "
                    spark_rows.append(line)

        # Frame drawing
        adjusted_width = int(width*0.845)
        left_pad = " " * len(label_prefix)
        top_border = left_pad + "┌" + ("─" * adjusted_width) + "┐"
        bottom_border = left_pad + "└" + ("─" * adjusted_width) + "┘"
        framed_rows = [top_border]
        for r in spark_rows:
            framed_rows.append(left_pad + "│" + r + "│")
        framed_rows.append(bottom_border)

        # Add min/max labels if provided
        if label_min is not None or label_max is not None:
            min_label = f"{label_min}" if label_min is not None else f"{fixed_min}"
            max_label = f"{label_max}" if label_max is not None else f"{fixed_max}"
            # Place max at top left, min at bottom left (after frame character and left_pad)
            framed_rows[1] = f"{left_pad}│{max_label:<6}" + framed_rows[1][len(left_pad)+7:]
            framed_rows[-2] = f"{left_pad}│{min_label:<6}" + framed_rows[-2][len(left_pad)+7:]

        return "\n".join(framed_rows)
    
    def fetch_metrics(self):        
        """Fetch and parse vLLM metrics"""
        try:
            metrics = requests.get("http://0.0.0.0:8000/metrics", timeout=5).text
            grouped_metrics = defaultdict(list)
            
            for fam in text_string_to_metric_families(metrics):
                for sample in fam.samples:
                    base_name = sample.name.split('_bucket')[0].split('_count')[0].split('_sum')[0]
                    grouped_metrics[base_name].append({
                        'name': sample.name,
                        'value': sample.value,
                        'labels': sample.labels
                    })
            
            return grouped_metrics
        except Exception as e:
            print(f"Error fetching metrics: {e}")
            return None
            
    def background_monitor(self):
        """Continuously monitor metrics at 10Hz"""
        while self.is_monitoring:
            grouped_metrics = self.fetch_metrics()
            if grouped_metrics:
                running = grouped_metrics.get('vllm:num_requests_running', [{}])[0].get('value', 0)
                waiting = grouped_metrics.get('vllm:num_requests_waiting', [{}])[0].get('value', 0)
                cache_usage = grouped_metrics.get('vllm:gpu_cache_usage_perc', [{}])[0].get('value', 0)
                
                with self.background_lock:
                    self.background_running.append(running)
                    self.background_waiting.append(waiting)
                    self.background_cache.append(cache_usage)
                    
                    # Keep only last 100 samples (10 seconds at 10Hz)
                    if len(self.background_running) > 100:
                        self.background_running.pop(0)
                        self.background_waiting.pop(0)
                        self.background_cache.pop(0)
            
            time.sleep(0.1)  # 10Hz
    
    def get_averaged_metrics(self):
        """Get averaged metrics from background monitoring"""
        with self.background_lock:
            if not self.background_running:
                return 0, 0, 0
            
            avg_running = sum(self.background_running) / len(self.background_running)
            avg_waiting = sum(self.background_waiting) / len(self.background_waiting)
            avg_cache = sum(self.background_cache) / len(self.background_cache)
            
            return avg_running, avg_waiting, avg_cache
    
    def update_history(self, grouped_metrics):
        """Update rolling history with new metrics"""
        if grouped_metrics:
            # Use background averaged values if available
            if self.background_running:
                running, waiting, cache_usage = self.get_averaged_metrics()
            else:
                running = grouped_metrics.get('vllm:num_requests_running', [{}])[0].get('value', 0)
                waiting = grouped_metrics.get('vllm:num_requests_waiting', [{}])[0].get('value', 0)
                cache_usage = grouped_metrics.get('vllm:gpu_cache_usage_perc', [{}])[0].get('value', 0)
            
            self.running_history.append(running)
            self.waiting_history.append(waiting)
            self.cache_usage_history.append(cache_usage * 100)  # Convert to percentage for display
            self.timestamps.append(time.time())
    

    def get_model_name(self, grouped_metrics):
        """Extract model name from metrics labels"""
        # Try to find model_name from any metric that has it
        for metric_list in grouped_metrics.values():
            for sample in metric_list:
                labels = sample.get('labels', {})
                if 'model_name' in labels:
                    return labels['model_name']
        return "Unknown"

    def display_metrics(self, grouped_metrics):
        """Display comprehensive metrics dashboard"""
        self.clear_screen()
        
        # Show model name
        model_name = self.get_model_name(grouped_metrics)
        print(f"vLLM METRICS DASHBOARD - Model: {model_name}")
        print("=" * 80)
        
        # Current state metrics (averaged from background monitoring)
        if self.background_running:
            running, waiting, cache_usage = self.get_averaged_metrics()
            cache_usage_display = cache_usage * 100  # Convert for display
            print("\nCURRENT STATE")
        else:
            running = grouped_metrics.get('vllm:num_requests_running', [{}])[0].get('value', 0)
            waiting = grouped_metrics.get('vllm:num_requests_waiting', [{}])[0].get('value', 0)
            cache_usage = grouped_metrics.get('vllm:gpu_cache_usage_perc', [{}])[0].get('value', 0)
            cache_usage_display = cache_usage * 100
            print("\nCURRENT STATE")
        
        print("-" * 40)
        print(self.create_bar_chart(running, self.max_running, label="Running Requests"))
        print(self.create_bar_chart(waiting, self.max_waiting, label="Waiting Requests"))
        print(self.create_bar_chart(cache_usage_display, 100, label="GPU Cache Usage (%)"))
        
        # Rolling histograms with fixed scaling
        print("\nROLLING HISTORY (Last 50 measurements)")
        print("-" * 60)
        
        if len(self.running_history) > 1:
            print(f"Running:  \n{self.create_sparkline(list(self.running_history), fixed_min=0, fixed_max=self.max_running)}")
            print(f"          Min: {min(self.running_history):.1f} | Max: {max(self.running_history):.1f} | Avg: {sum(self.running_history)/len(self.running_history):.1f}")
            
            print(f"Waiting:  \n{self.create_sparkline(list(self.waiting_history), fixed_min=0, fixed_max=self.max_waiting)}")
            print(f"          Min: {min(self.waiting_history):.1f} | Max: {max(self.waiting_history):.1f} | Avg: {sum(self.waiting_history)/len(self.waiting_history):.1f}")
            
            print(f"Cache %:  \n{self.create_sparkline(list(self.cache_usage_history), fixed_min=0, fixed_max=100)}")
            print(f"          Min: {min(self.cache_usage_history):.3f}% | Max: {max(self.cache_usage_history):.3f}% | Avg: {sum(self.cache_usage_history)/len(self.cache_usage_history):.3f}%")
        # Cumulative statistics
        print("\n📋 CUMULATIVE STATISTICS")
        print("-" * 40)
        
        prompt_tokens = grouped_metrics.get('vllm:prompt_tokens_total', [{}])[0].get('value', 0)
        generation_tokens = grouped_metrics.get('vllm:generation_tokens_total', [{}])[0].get('value', 0)
        
        print(f"Total Prompt Tokens:     {prompt_tokens:,.0f}")
        print(f"Total Generation Tokens: {generation_tokens:,.0f}")
        
        # Latency metrics
        latency_samples = grouped_metrics.get('vllm:e2e_request_latency_seconds', [])
        if latency_samples:
            count_sample = next((s for s in latency_samples if s['name'].endswith('_count')), None)
            sum_sample = next((s for s in latency_samples if s['name'].endswith('_sum')), None)
            
            if count_sample and sum_sample and count_sample['value'] > 0:
                total_requests = count_sample['value']
                avg_latency = sum_sample['value'] / total_requests
                print(f"Total Requests:          {total_requests:,.0f}")
                print(f"Average E2E Latency:     {avg_latency:.4f}s")
                
                if prompt_tokens > 0:
                    tokens_per_request = prompt_tokens / total_requests
                    gen_tokens_per_request = generation_tokens / total_requests
                    print(f"Avg Prompt Length:       {tokens_per_request:.1f} tokens")
                    print(f"Avg Generation Length:   {gen_tokens_per_request:.1f} tokens")
        
        print(f"\n⏰ Last updated: {time.strftime('%H:%M:%S')}")
        print("Press Ctrl+C to exit...")

    def run_monitor(self, interval=0.1):
        """Run continuous monitoring"""
        print("Starting vLLM metrics monitoring...")
        print(f"Display refresh interval: {interval} seconds")
        print("Background monitoring at 10Hz...")
        
        # Start background monitoring thread
        self.is_monitoring = True
        background_thread = threading.Thread(target=self.background_monitor, daemon=True)
        background_thread.start()
        
        try:
            # Give background thread time to collect some data
            time.sleep(1)
            
            while True:
                grouped_metrics = self.fetch_metrics()
                if grouped_metrics:
                    self.update_history(grouped_metrics)
                    self.display_metrics(grouped_metrics)
                else:
                    print("Failed to fetch metrics. Retrying...")
                
                time.sleep(interval)
                
        except KeyboardInterrupt:
            print("\n\nStopping background monitoring...")
            self.is_monitoring = False
            print("Monitoring stopped.")


# Legacy alias for backward compatibility
VLLMMetricsMonitor = VLLM_TOP