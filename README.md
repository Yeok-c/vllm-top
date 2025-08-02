# vllm-top

vllm-top is a Python package designed for monitoring and displaying metrics from the vLLM (Variable-length Language Model) service. It provides a comprehensive dashboard that visualizes the current state and historical performance of the service, making it easier to track its behavior and performance over time.

## Features

- Fetches and parses metrics from the vLLM service.
- Displays real-time metrics in a terminal dashboard.
- Supports background monitoring at a configurable frequency.
- Visualizes historical data with bar charts and sparklines.
- Provides cumulative statistics for prompt and generation tokens.

## Installation

To install the package, you can use pip:

```bash
pip install vllm-top
```

## Usage

To run the monitoring functionality, you can execute the following command:

```bash
python -m vllm_top.main --monitor [INTERVAL]
```

Replace `[INTERVAL]` with the desired refresh interval in seconds (default is 2 seconds).

For a one-time snapshot of the metrics, run:

```bash
python -m vllm_top.main
```

## Contributing

Contributions are welcome! Please feel free to submit a pull request or open an issue for any enhancements or bug fixes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

## Changelog

For a detailed list of changes and updates, please refer to the CHANGELOG.md file.