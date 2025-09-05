"""Tests for the CLI module."""

import pytest
from click.testing import CliRunner
from polynomial_generator.cli import main


class TestCLI:
    """Test cases for the command-line interface."""
    
    def test_cli_basic(self):
        """Test basic CLI functionality."""
        runner = CliRunner()
        result = runner.invoke(main, ['--delta', '10'])
        
        assert result.exit_code == 0
        assert 'δ (difficulty parameter): 10' in result.output
        assert 'Chosen (m, n):' in result.output
        assert 'Exponent matrix K' in result.output
        assert 'Coefficients:' in result.output
        assert 'Symbolic polynomial:' in result.output
        assert 'Baseline Kbase(P):' in result.output
    
    def test_cli_with_seed(self):
        """Test CLI with seed for reproducibility."""
        runner = CliRunner()
        
        # Run twice with same seed
        result1 = runner.invoke(main, ['--delta', '15', '--seed', '42'])
        result2 = runner.invoke(main, ['--delta', '15', '--seed', '42'])
        
        assert result1.exit_code == 0
        assert result2.exit_code == 0
        assert result1.output == result2.output  # Should be identical
    
    def test_cli_verbose(self):
        """Test CLI verbose output."""
        runner = CliRunner()
        result = runner.invoke(main, ['--delta', '10', '--verbose'])
        
        assert result.exit_code == 0
        assert 'Algorithm steps:' in result.output
        assert 'Row degrees' in result.output
        assert 'Constraint contributions' in result.output
    
    def test_cli_custom_coefficients(self):
        """Test CLI with custom coefficient range."""
        runner = CliRunner()
        result = runner.invoke(main, [
            '--delta', '5', 
            '--coeff-min', '1', 
            '--coeff-max', '3'
        ])
        
        assert result.exit_code == 0
        # Check that output is reasonable (hard to verify exact coefficient values from output)
        assert 'Coefficients:' in result.output
    
    def test_cli_invalid_delta(self):
        """Test CLI error handling for invalid delta."""
        runner = CliRunner()
        result = runner.invoke(main, ['--delta', '0'])
        
        assert result.exit_code == 1  # Should exit with error
        assert 'Error:' in result.output
    
    def test_cli_missing_delta(self):
        """Test CLI error when delta is missing."""
        runner = CliRunner()
        result = runner.invoke(main, [])
        
        assert result.exit_code != 0  # Should fail
        assert 'Missing option' in result.output or 'Usage:' in result.output
    
    def test_cli_help(self):
        """Test CLI help output."""
        runner = CliRunner()
        result = runner.invoke(main, ['--help'])
        
        assert result.exit_code == 0
        assert 'Generate random polynomial instance' in result.output
        assert '--delta' in result.output
        assert '--seed' in result.output
    
    def test_cli_verification_success(self):
        """Test that CLI shows successful verification."""
        runner = CliRunner()
        result = runner.invoke(main, ['--delta', '8', '--seed', '123'])
        
        assert result.exit_code == 0
        assert '✓ Baseline matches target' in result.output
    
    def test_cli_matrix_formatting(self):
        """Test that matrix is properly formatted in output."""
        runner = CliRunner()
        result = runner.invoke(main, ['--delta', '5', '--seed', '456'])
        
        assert result.exit_code == 0
        # Should contain matrix with brackets
        assert '[' in result.output
        assert ']' in result.output