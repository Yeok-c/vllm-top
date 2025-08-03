import sys
import os

# Try relative import first, fall back to absolute import
try:
    from .monitor import VLLM_TOP
except ImportError:
    # If relative import fails, try absolute import
    try:
        from vllm_top.monitor import VLLM_TOP
    except ImportError:
        # Last resort: add current directory to path and import
        current_dir = os.path.dirname(os.path.abspath(__file__))
        sys.path.insert(0, current_dir)
        from monitor import VLLM_TOP

def parse_vllm_metrics_once():
    """Function for one-time metrics parsing"""
    monitor = VLLM_TOP()
    grouped_metrics = monitor.fetch_metrics()
    
    if not grouped_metrics:
        print("Failed to fetch metrics")
        return
    
    monitor.update_history(grouped_metrics)
    monitor.display_metrics(grouped_metrics)

def main():
    """Main entry point for the vllm-top CLI"""
    if len(sys.argv) > 1 and sys.argv[1] == "--snapshot":
        # One-time snapshot
        parse_vllm_metrics_once()
    else:
        # Continuous monitoring mode
        interval = int(sys.argv[2]) if len(sys.argv) > 2 else 0.1
        monitor = VLLM_TOP()
        monitor.run_monitor(interval)

if __name__ == "__main__":
    main()