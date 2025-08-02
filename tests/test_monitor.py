import unittest
from unittest.mock import patch, MagicMock
from src.vllm_top.monitor import VLLM_TOP

class TestVLLMTop(unittest.TestCase):

    @patch('src.vllm_top.monitor.requests.get')
    def test_fetch_metrics_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.text = 'vllm:num_requests_running 5\nvllm:num_requests_waiting 3\n'
        mock_get.return_value = mock_response
        
        vllm_top = VLLM_TOP()
        metrics = vllm_top.fetch_metrics()
        
        self.assertIsNotNone(metrics)
        self.assertIn('vllm:num_requests_running', metrics)
        self.assertIn('vllm:num_requests_waiting', metrics)

    @patch('src.vllm_top.monitor.requests.get')
    def test_fetch_metrics_failure(self, mock_get):
        mock_get.side_effect = Exception("Network error")
        
        vllm_top = VLLM_TOP()
        metrics = vllm_top.fetch_metrics()
        
        self.assertIsNone(metrics)

    def test_create_bar_chart(self):
        vllm_top = VLLM_TOP()
        bar_chart = vllm_top.create_bar_chart(5, 10, label="Test")
        
        self.assertIn("Test", bar_chart)
        self.assertIn("|", bar_chart)
        self.assertIn("5.0/10.0", bar_chart)

    def test_create_sparkline(self):
        vllm_top = VLLM_TOP()
        sparkline = vllm_top.create_sparkline([1, 2, 3, 4, 5], width=10)
        
        self.assertEqual(len(sparkline), 10)

if __name__ == '__main__':
    unittest.main()