"""Tests for the chooser module."""

import pytest
from polynomial_generator.chooser import choose_m_n, validate_m_n


class TestChooseMN:
    """Test cases for choose_m_n function."""
    
    def test_choose_m_n_basic(self):
        """Test basic functionality of choose_m_n."""
        m, n = choose_m_n(10)
        assert isinstance(m, int)
        assert isinstance(n, int)
        assert m >= 1
        assert n >= 2
    
    def test_choose_m_n_constraints(self):
        """Test that choose_m_n respects the defined constraints."""
        delta = 20
        m, n = choose_m_n(delta)
        
        # Check m constraints: m ∈ [1, min(δ, ⌊√δ⌋ + 5)]
        max_m = min(delta, int(delta**0.5) + 5)
        assert 1 <= m <= max_m
        
        # Check n constraints: n ∈ [2, min(δ, m+3, 10)]
        max_n = min(delta, m + 3, 10)
        assert 2 <= n <= max_n
    
    def test_choose_m_n_reproducibility(self):
        """Test that same seed produces same results."""
        seed = 42
        m1, n1 = choose_m_n(15, seed=seed)
        m2, n2 = choose_m_n(15, seed=seed)
        assert m1 == m2
        assert n1 == n2
    
    def test_choose_m_n_different_seeds(self):
        """Test that different seeds can produce different results."""
        # Note: This is probabilistic, but very likely to pass
        results = set()
        for seed in range(10):
            results.add(choose_m_n(20, seed=seed))
        
        # Should get at least 2 different results in 10 tries
        assert len(results) >= 2
    
    def test_choose_m_n_edge_cases(self):
        """Test edge cases for choose_m_n."""
        # Small delta
        m, n = choose_m_n(1)
        assert m == 1  # Only possible value
        assert n >= 2
        
        # Larger delta
        m, n = choose_m_n(100)
        assert m >= 1
        assert n >= 2
    
    def test_choose_m_n_invalid_delta(self):
        """Test that invalid delta raises ValueError."""
        with pytest.raises(ValueError):
            choose_m_n(0)
        
        with pytest.raises(ValueError):
            choose_m_n(-5)


class TestValidateMN:
    """Test cases for validate_m_n function."""
    
    def test_validate_m_n_valid_cases(self):
        """Test valid (m, n, delta) combinations."""
        assert validate_m_n(3, 4, 10) == True
        assert validate_m_n(1, 2, 5) == True
        assert validate_m_n(5, 3, 20) == True
    
    def test_validate_m_n_invalid_cases(self):
        """Test invalid (m, n, delta) combinations."""
        # Invalid m
        assert validate_m_n(0, 3, 10) == False
        assert validate_m_n(-1, 3, 10) == False
        
        # Invalid n
        assert validate_m_n(3, 1, 10) == False
        assert validate_m_n(3, 0, 10) == False
        
        # Invalid delta
        assert validate_m_n(3, 4, -1) == False
    
    def test_validate_m_n_boundary_cases(self):
        """Test boundary cases for validation."""
        # Minimum valid case
        assert validate_m_n(1, 2, 0) == True
        
        # Case where delta + m < m (impossible)
        # This shouldn't happen with our chooser, but test the validator
        assert validate_m_n(5, 3, 0) == True  # Still valid: need 5 total degree, have 5 monomials