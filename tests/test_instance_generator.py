"""Tests for the instance_generator module."""

import pytest
import numpy as np
import sympy as sp
from polynomial_generator.instance_generator import (
    generate_random_instance,
    _sample_row_totals, 
    _distribute_exponents,
    _calculate_baseline
)


class TestGenerateRandomInstance:
    """Test cases for generate_random_instance function."""
    
    def test_generate_basic(self):
        """Test basic instance generation."""
        result = generate_random_instance(delta=10)
        
        # Check return type and keys
        assert isinstance(result, dict)
        expected_keys = {'delta', 'm', 'n', 'matrix', 'coefficients', 'polynomial', 'baseline'}
        assert set(result.keys()) == expected_keys
        
        # Check basic properties
        assert result['delta'] == 10
        assert result['m'] >= 1
        assert result['n'] >= 2
        assert result['matrix'].shape == (result['m'], result['n'])
        assert len(result['coefficients']) == result['m']
        assert isinstance(result['polynomial'], sp.Basic)  # SymPy expression
    
    def test_baseline_correctness(self):
        """Test that baseline equals target delta."""
        for delta in [1, 5, 10, 25, 50]:
            result = generate_random_instance(delta=delta, seed=42)
            assert result['baseline'] == delta, f"Baseline {result['baseline']} != delta {delta}"
    
    def test_reproducibility(self):
        """Test that same seed produces same results."""
        seed = 123
        result1 = generate_random_instance(delta=15, seed=seed)
        result2 = generate_random_instance(delta=15, seed=seed)
        
        assert result1['m'] == result2['m']
        assert result1['n'] == result2['n']
        assert np.array_equal(result1['matrix'], result2['matrix'])
        assert result1['coefficients'] == result2['coefficients']
        assert result1['polynomial'] == result2['polynomial']
    
    def test_coefficient_ranges(self):
        """Test custom coefficient ranges."""
        result = generate_random_instance(delta=10, coeff_range=(1, 5))
        
        # All coefficients should be in range [1, 5]
        for coeff in result['coefficients']:
            assert 1 <= coeff <= 5
            assert coeff != 0  # Should be nonzero
    
    def test_nonzero_coefficients(self):
        """Test that coefficients are always nonzero."""
        result = generate_random_instance(delta=10, coeff_range=(-2, 2))
        
        for coeff in result['coefficients']:
            assert coeff != 0
    
    def test_invalid_inputs(self):
        """Test error handling for invalid inputs."""
        # Invalid delta
        with pytest.raises(ValueError):
            generate_random_instance(delta=0)
        
        with pytest.raises(ValueError):
            generate_random_instance(delta=-5)
        
        # Invalid coefficient range (only allows 0)
        with pytest.raises(ValueError):
            generate_random_instance(delta=5, coeff_range=(0, 0))
    
    def test_matrix_properties(self):
        """Test properties of the generated exponent matrix."""
        result = generate_random_instance(delta=20, seed=42)
        matrix = result['matrix']
        
        # Matrix should be non-negative integers
        assert matrix.dtype == int
        assert np.all(matrix >= 0)
        
        # Each row should have degree >= 1 (sum of exponents >= 1)
        row_degrees = np.sum(matrix, axis=1)
        assert np.all(row_degrees >= 1)
        
        # Sum of all (row_degree - 1) should equal delta
        baseline = sum(max(0, degree - 1) for degree in row_degrees)
        assert baseline == result['delta']


class TestSampleRowTotals:
    """Test cases for _sample_row_totals function."""
    
    def test_sample_row_totals_basic(self):
        """Test basic functionality."""
        totals = _sample_row_totals(m=3, target_sum=10)
        
        assert len(totals) == 3
        assert sum(totals) == 10
        assert all(t >= 1 for t in totals)
    
    def test_sample_row_totals_minimum_case(self):
        """Test minimum case where all totals are 1."""
        totals = _sample_row_totals(m=5, target_sum=5)
        assert totals == [1, 1, 1, 1, 1]
    
    def test_sample_row_totals_invalid(self):
        """Test invalid inputs."""
        with pytest.raises(ValueError):
            _sample_row_totals(m=5, target_sum=3)  # target_sum < m


class TestDistributeExponents:
    """Test cases for _distribute_exponents function."""
    
    def test_distribute_exponents_basic(self):
        """Test basic functionality."""
        exponents = _distribute_exponents(total_degree=6, n_variables=3)
        
        assert len(exponents) == 3
        assert sum(exponents) == 6
        assert all(exp >= 0 for exp in exponents)
    
    def test_distribute_exponents_zero_degree(self):
        """Test zero total degree."""
        exponents = _distribute_exponents(total_degree=0, n_variables=4)
        assert len(exponents) == 4
        assert sum(exponents) == 0
        assert all(exp == 0 for exp in exponents)
    
    def test_distribute_exponents_single_variable(self):
        """Test with single variable."""
        exponents = _distribute_exponents(total_degree=5, n_variables=1)
        assert len(exponents) == 1
        assert exponents[0] == 5


class TestCalculateBaseline:
    """Test cases for _calculate_baseline function."""
    
    def test_calculate_baseline_basic(self):
        """Test basic baseline calculation."""
        # Matrix where each row has degree 3, 2, 1
        matrix = np.array([
            [2, 1, 0],  # degree 3, contributes 2
            [1, 1, 0],  # degree 2, contributes 1  
            [0, 1, 0],  # degree 1, contributes 0
        ])
        
        baseline = _calculate_baseline(matrix)
        assert baseline == 3  # 2 + 1 + 0
    
    def test_calculate_baseline_edge_cases(self):
        """Test edge cases for baseline calculation."""
        # All rows have degree 1
        matrix = np.array([
            [1, 0],
            [0, 1],
            [1, 0]
        ])
        baseline = _calculate_baseline(matrix)
        assert baseline == 0  # All contribute 0
        
        # Empty matrix
        matrix = np.array([]).reshape(0, 3)
        baseline = _calculate_baseline(matrix)
        assert baseline == 0