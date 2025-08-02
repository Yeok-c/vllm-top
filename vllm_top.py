from prometheus_client.parser import text_string_to_metric_families
import requests
from collections import defaultdict, deque
import time
import os
import sys
import threading

class VLLMMetricsMonitor:
    def __init__(self, history_size=50):
        self.history_size = history_size
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
        return f"{label:<25} |{bar}| {value:.1f}/{max_value:.1f} ({percentage*100:.4f}%)"
       

    def create_sparkline(self, data, width=60):
        """Create a sparkline chart for historical data"""
        if not data or len(data) < 2:
            return "░" * width
        
        min_val = min(data)
        max_val = max(data)
        
        if max_val == min_val:
            return "▄" * len(data)
        
        sparkline = ""
        # Only create sparkline for actual data points, no padding
        data_width = min(len(data), width)
        
        for i in range(data_width):
            # Normalize value to 0-8 range for block characters
            normalized = (data[i] - min_val) / (max_val - min_val)
            block_height = int(normalized * 8)
            
            blocks = ["▁", "▂", "▃", "▄", "▅", "▆", "▇", "█"]
            sparkline += blocks[min(block_height, 7)]
        
        return sparkline
    
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
    
    def display_metrics(self, grouped_metrics):
        """Display comprehensive metrics dashboard"""
        self.clear_screen()
        
        print("🚀 vLLM METRICS DASHBOARD")
        print("=" * 80)
        
        # Current state metrics (averaged from background monitoring)
        if self.background_running:
            running, waiting, cache_usage = self.get_averaged_metrics()
            cache_usage_display = cache_usage * 100  # Convert for display
            print("\n📊 CURRENT STATE (10Hz Averaged)")
        else:
            running = grouped_metrics.get('vllm:num_requests_running', [{}])[0].get('value', 0)
            waiting = grouped_metrics.get('vllm:num_requests_waiting', [{}])[0].get('value', 0)
            cache_usage = grouped_metrics.get('vllm:gpu_cache_usage_perc', [{}])[0].get('value', 0)
            cache_usage_display = cache_usage * 100
            print("\n📊 CURRENT STATE")
        
        print("-" * 40)
        max_queue = max(max(self.waiting_history) if self.waiting_history else [100], 100)
        print(self.create_bar_chart(running, 10, label="Running Requests"))
        print(self.create_bar_chart(waiting, max_queue, label="Waiting Requests"))
        print(self.create_bar_chart(cache_usage_display, 100, label="GPU Cache Usage (%)"))
        
        # Rolling histograms
        print("\n📈 ROLLING HISTORY (Last 50 measurements)")
        print("-" * 60)
        
        if len(self.running_history) > 1:
            print(f"Running:  {self.create_sparkline(list(self.running_history))}")
            print(f"          Min: {min(self.running_history):.1f} | Max: {max(self.running_history):.1f} | Avg: {sum(self.running_history)/len(self.running_history):.1f}")
            
            print(f"Waiting:  {self.create_sparkline(list(self.waiting_history))}")
            print(f"          Min: {min(self.waiting_history):.1f} | Max: {max(self.waiting_history):.1f} | Avg: {sum(self.waiting_history)/len(self.waiting_history):.1f}")
            
            print(f"Cache %:  {self.create_sparkline(list(self.cache_usage_history))}")
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

    def run_monitor(self, interval=2):
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
            sys.exit(0)

def parse_vllm_metrics_once():
    """Original function for one-time metrics parsing"""
    monitor = VLLMMetricsMonitor()
    grouped_metrics = monitor.fetch_metrics()
    
    if not grouped_metrics:
        print("Failed to fetch metrics")
        return
    
    monitor.update_history(grouped_metrics)
    monitor.display_metrics(grouped_metrics)

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--monitor":
        # Continuous monitoring mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        monitor = VLLMMetricsMonitor()
        monitor.run_monitor(interval)
    else:
        # One-time snapshot
        parse_vllm_metrics_once()