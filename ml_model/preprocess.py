import numpy as np
from sklearn.preprocessing import MinMaxScaler

class FeaturePreprocessor:
    def __init__(self):
        # We use MinMaxScaler to bring delay_ms, queue_utilization, and packet_loss to a [0, 1] scale
        self.scaler = MinMaxScaler()
        self.is_fitted = False
        
    def fit(self, X):
        """Fit the scaler on the training data."""
        self.scaler.fit(X)
        self.is_fitted = True
        
    def transform(self, X):
        """Transform the features using the fitted scaler."""
        if not self.is_fitted:
            raise ValueError("Preprocessor must be fitted before calling transform().")
        return self.scaler.transform(X)
        
    def extract_features(self, link_snapshot):
        """
        Extracts the required features from a link snapshot dictionary.
        Returns a list: [queue_utilization, delay_ms, packet_loss]
        """
        queue_util = float(link_snapshot.get('queue_utilization', 0.0))
        delay_ms = float(link_snapshot.get('delay_ms', 2.0))
        packet_loss = float(link_snapshot.get('packet_loss', 0.0))
        
        # If throughput is 0 after timestamp > 2, it might indicate failure.
        throughput = float(link_snapshot.get('throughput_mbps', 0.0))
        if throughput == 0.0 and delay_ms == 5.0 and link_snapshot.get('queue_max', 100) == 100:
            # It might just be an unused alternate link, so leave it alone.
            pass
            
        return [queue_util, delay_ms, packet_loss]
