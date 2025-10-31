from collections import defaultdict
from datetime import datetime
import json

class MetricsCollector:
    """Simple metrics collector for API monitoring."""
    
    def __init__(self):
        self.total_predictions = 0
        self.predictions_by_crop = defaultdict(int)
        self.predictions_by_disease = defaultdict(int)
        self.inference_times = []
        self.start_time = datetime.utcnow()
    
    def log_prediction(self, crop_type, disease, confidence, inference_time):
        """Log a prediction."""
        self.total_predictions += 1
        self.predictions_by_crop[crop_type] += 1
        self.predictions_by_disease[disease] += 1
        self.inference_times.append(inference_time)
    
    def get_metrics(self):
        """Get current metrics."""
        avg_inference = sum(self.inference_times) / len(self.inference_times) if self.inference_times else 0
        
        return {
            "total_predictions": self.total_predictions,
            "avg_inference_time_ms": round(avg_inference, 2),
            "predictions_by_crop": dict(self.predictions_by_crop),
            "predictions_by_disease": dict(self.predictions_by_disease),
            "uptime_seconds": (datetime.utcnow() - self.start_time).total_seconds()
        }