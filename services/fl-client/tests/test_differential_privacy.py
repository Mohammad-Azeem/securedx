"""
SecureDx AI — Differential Privacy Tests

Verifies that gradient privatization:
  - Clips gradient norms correctly
  - Adds noise that cannot trivially be removed
  - Maintains correct gradient shape post-privatization
  - Rejects invalid privacy budget parameters
"""

import numpy as np
import pytest

import sys
sys.path.insert(0, '/app')  # For docker context

from client.fl_client import DifferentialPrivacyEngine, KrumValidator


class TestDifferentialPrivacy:

    def test_gradient_clipping_reduces_large_norm(self):
        """Gradients with L2 norm > clip_norm must be clipped."""
        dp = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5, clip_norm=1.0)

        # Create gradient with norm >> 1.0
        large_grad = [np.ones((100,), dtype=np.float32) * 10.0]
        clipped = dp.clip_gradients(large_grad)

        clipped_norm = np.linalg.norm(clipped[0])
        assert clipped_norm <= 1.0 + 1e-6, f"Clip failed: norm={clipped_norm:.4f}"

    def test_gradient_clipping_preserves_small_norm(self):
        """Gradients already within clip_norm must not be scaled down."""
        dp = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5, clip_norm=1.0)

        small_grad = [np.array([0.1, 0.2, 0.3], dtype=np.float32)]
        original_norm = np.linalg.norm(small_grad[0])
        clipped = dp.clip_gradients(small_grad)
        clipped_norm = np.linalg.norm(clipped[0])

        assert abs(clipped_norm - original_norm) < 1e-5, "Small gradient was incorrectly clipped"

    def test_noise_changes_gradient_values(self):
        """Adding DP noise must change gradient values."""
        dp = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5, clip_norm=1.0)
        np.random.seed(42)

        original = [np.zeros((50,), dtype=np.float32)]
        noisy = dp.add_noise([g.copy() for g in original], n_samples=100)

        assert not np.allclose(original[0], noisy[0], atol=1e-6), \
            "DP noise was not added — privacy guarantee violated!"

    def test_noise_preserves_gradient_shape(self):
        """DP noise must not change the shape of gradient tensors."""
        dp = DifferentialPrivacyEngine(epsilon=1.0, delta=1e-5, clip_norm=1.0)

        grads = [
            np.random.randn(10, 5).astype(np.float32),
            np.random.randn(5).astype(np.float32),
        ]
        noisy = dp.add_noise(grads, n_samples=100)

        for original, privatized in zip(grads, noisy):
            assert original.shape == privatized.shape, "Shape changed after DP noise!"

    def test_invalid_epsilon_rejected(self):
        """Negative or zero epsilon must be rejected."""
        with pytest.raises((ValueError, Exception)):
            DifferentialPrivacyEngine(epsilon=0.0, delta=1e-5, clip_norm=1.0)

        with pytest.raises((ValueError, Exception)):
            DifferentialPrivacyEngine(epsilon=-1.0, delta=1e-5, clip_norm=1.0)

    def test_invalid_delta_rejected(self):
        """Delta must be in (0, 1)."""
        with pytest.raises((ValueError, Exception)):
            DifferentialPrivacyEngine(epsilon=1.0, delta=0.0, clip_norm=1.0)

        with pytest.raises((ValueError, Exception)):
            DifferentialPrivacyEngine(epsilon=1.0, delta=1.5, clip_norm=1.0)

    def test_higher_epsilon_produces_less_noise(self):
        """Higher ε = less privacy = less noise. Verify this relationship."""
        np.random.seed(123)
        grads = [np.ones((1000,), dtype=np.float32)]

        dp_high_privacy = DifferentialPrivacyEngine(epsilon=0.1, delta=1e-5, clip_norm=1.0)
        dp_low_privacy  = DifferentialPrivacyEngine(epsilon=5.0, delta=1e-5, clip_norm=1.0)

        noisy_high = dp_high_privacy.add_noise([g.copy() for g in grads], n_samples=1000)
        noisy_low  = dp_low_privacy.add_noise([g.copy() for g in grads], n_samples=1000)

        variance_high = np.var(noisy_high[0] - grads[0])
        variance_low  = np.var(noisy_low[0] - grads[0])

        assert variance_high > variance_low, \
            "Lower epsilon should produce higher noise variance (more privacy)"


class TestKrumValidator:

    def test_rejects_nan_gradients(self):
        """Gradients containing NaN must be quarantined."""
        validator = KrumValidator()
        bad_grads = [np.array([1.0, float('nan'), 3.0], dtype=np.float32)]

        is_valid, reason = validator.validate(bad_grads)
        assert not is_valid, "NaN gradient should be rejected"
        assert "NaN" in reason or "Inf" in reason

    def test_rejects_inf_gradients(self):
        """Gradients containing Inf must be quarantined."""
        validator = KrumValidator()
        bad_grads = [np.array([1.0, float('inf'), 3.0], dtype=np.float32)]

        is_valid, reason = validator.validate(bad_grads)
        assert not is_valid, "Inf gradient should be rejected"

    def test_accepts_normal_gradients(self):
        """Normal gradients must pass validation."""
        validator = KrumValidator()
        normal_grads = [np.random.randn(50).astype(np.float32) * 0.1]

        is_valid, reason = validator.validate(normal_grads)
        assert is_valid, f"Valid gradient was rejected: {reason}"

    def test_detects_anomalous_norm(self):
        """Gradient with norm >> historical average must be flagged."""
        validator = KrumValidator(norm_threshold_multiplier=5.0)

        # Establish baseline with small gradients
        for _ in range(5):
            small = [np.random.randn(50).astype(np.float32) * 0.01]
            validator.validate(small)

        # Now submit a huge gradient
        huge = [np.ones(50, dtype=np.float32) * 1000.0]
        is_valid, reason = validator.validate(huge)

        assert not is_valid, "Anomalously large gradient should be flagged as potential poisoning"
