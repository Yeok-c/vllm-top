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
    import argparse
    parser = argparse.ArgumentParser(description="vLLM Metrics Monitor")
    parser.add_argument("--url", type=str, default="http://0.0.0.0:8000/metrics", help="vLLM metrics endpoint URL")
    parser.add_argument("--insecure", action="store_true", help="Disable SSL certificate verification")
    parser.add_argument("--snapshot", action="store_true", help="One-time metrics snapshot")
    parser.add_argument("--interval", type=float, default=0.1, help="Refresh interval in seconds")
    
    # Handle positional arguments like the original code did (if any)
    # The original code used sys.argv[1] == "--snapshot" and sys.argv[2] for interval.
    # We'll transition to a proper parser but keep compatibility if possible.
    args, unknown = parser.parse_known_args()

    if args.snapshot:
        # One-time snapshot
        monitor = VLLM_TOP(metrics_url=args.url, verify_ssl=not args.insecure)
        grouped_metrics = monitor.fetch_metrics()
        if grouped_metrics:
            monitor.update_history(grouped_metrics)
            monitor.display_metrics(grouped_metrics)
        else:
            print("Failed to fetch metrics")
    else:
        # Continuous monitoring mode
        monitor = VLLM_TOP(metrics_url=args.url, verify_ssl=not args.insecure)
        monitor.run_monitor(args.interval)

if __name__ == "__main__":
    main()