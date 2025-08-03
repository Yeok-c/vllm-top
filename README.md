# vllm-top

[![PyPI version](https://img.shields.io/pypi/v/vllm-top.svg)](https://pypi.org/project/vllm-top/)

<p align="center">
  <img src="demo/demo.gif" alt="Demo" width="600"/>
</p>

**vllm-top** is a Python package for monitoring and displaying metrics from the [vLLM](https://github.com/vllm-project/vllm) service. It provides a comprehensive dashboard to visualize both current state and historical performance, making it easy to track and analyze service behavior over time.

---

## 🚀 Features

- **Task State Visibility:** Instantly see GPU Cache Usage, Running and Waiting requests to help debug bottlenecks and improve throughput.
- **Minimalist Monitoring:** Lightweight dashboard that parses metrics directly from Prometheus.
- **Quick Setup:** No extra configuration — just pip install and run.

---

## 📦 Installation

Install via pip:

```bash
pip install vllm-top
```

---

## 🛠️ Usage

Start monitoring:

```bash
vllm-top
```

Change update interval (in seconds):

```bash
vllm-top --interval 5
```

Get a one-time snapshot:

```bash
vllm-top --snapshot
```

---

## 🤝 Contributing

Contributions are welcome! Please submit a pull request or open an issue for enhancements or bug fixes.

---

## 📄 License

Licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

---

## 📜 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed