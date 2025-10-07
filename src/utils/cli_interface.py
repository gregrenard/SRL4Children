"""
ChildGuard-LLM V1.1 - CLI Interface Utilities
Version: 1.1.0
Date: 23 août 2025

Provides formatted CLI output, progress tracking, and user interaction utilities.
"""

import sys
import time
from typing import Dict, Any, List, Optional
from datetime import datetime
import json


class CLIInterface:
    """
    CLI Interface for formatted output and user interaction
    
    Features:
    - Colored console output
    - Progress tracking
    - Formatted tables and summaries
    - Error handling and user prompts
    """
    
    # ANSI color codes
    COLORS = {
        'red': '\033[91m',
        'green': '\033[92m',
        'yellow': '\033[93m',
        'blue': '\033[94m',
        'magenta': '\033[95m',
        'cyan': '\033[96m',
        'white': '\033[97m',
        'bold': '\033[1m',
        'end': '\033[0m'
    }
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.start_time = None
        
    def print_header(self, title: str) -> None:
        """Print formatted header"""
        print(f"\n{self.COLORS['bold']}{self.COLORS['blue']}{'='*60}{self.COLORS['end']}")
        print(f"{self.COLORS['bold']}{self.COLORS['blue']}{title:^60}{self.COLORS['end']}")
        print(f"{self.COLORS['bold']}{self.COLORS['blue']}{'='*60}{self.COLORS['end']}\n")
        
    def print_section(self, title: str) -> None:
        """Print formatted section header"""
        print(f"\n{self.COLORS['bold']}{self.COLORS['cyan']}{title}{self.COLORS['end']}")
        print(f"{self.COLORS['cyan']}{'-' * len(title)}{self.COLORS['end']}")
        
    def print_success(self, message: str) -> None:
        """Print success message"""
        print(f"{self.COLORS['green']}✅ {message}{self.COLORS['end']}")
        
    def print_warning(self, message: str) -> None:
        """Print warning message"""
        print(f"{self.COLORS['yellow']}⚠️  {message}{self.COLORS['end']}")
        
    def print_error(self, message: str) -> None:
        """Print error message"""
        print(f"{self.COLORS['red']}❌ {message}{self.COLORS['end']}")
        
    def print_info(self, message: str) -> None:
        """Print info message"""
        print(f"{self.COLORS['blue']}ℹ️  {message}{self.COLORS['end']}")
        
    def print_progress(self, current: int, total: int, prefix: str = "Progress") -> None:
        """Print progress bar"""
        if total == 0:
            percentage = 100
        else:
            percentage = (current / total) * 100
            
        filled = int(percentage / 2)
        bar = '█' * filled + '░' * (50 - filled)
        
        print(f"\r{prefix}: |{bar}| {current}/{total} ({percentage:.1f}%)", end='', flush=True)
        
        if current == total:
            print()  # New line when complete
            
    def print_benchmark_summary(self, summary: Dict[str, Any]) -> None:
        """Print formatted benchmark summary"""
        self.print_section("Benchmark Summary")
        
        print(f"{'Version:':<25} {summary.get('version', 'Unknown')}")
        print(f"{'Timestamp:':<25} {summary.get('timestamp', 'Unknown')}")
        print(f"{'Records Processed:':<25} {summary.get('total_records_processed', 0)}")
        print(f"{'Models Evaluated:':<25} {summary.get('total_models', 0)}")
        print(f"{'Criteria Used:':<25} {summary.get('criteria_evaluated', 0)}")
        print(f"{'Processing Time:':<25} {self.format_duration(summary.get('total_processing_time_seconds', 0))}")
        print(f"{'Avg Time/Record:':<25} {summary.get('avg_processing_time_per_record', 0):.2f}s")
        
    def print_model_statistics(self, model_stats: Dict[str, Any]) -> None:
        """Print formatted model statistics"""
        self.print_section("Model Performance")
        
        for model, stats in model_stats.items():
            print(f"\n{self.COLORS['bold']}{model}:{self.COLORS['end']}")
            print(f"  Records: {stats.get('count', 0)}")
            print(f"  Avg Final Score: {stats.get('avg_final_score', 0):.3f}")
            
            if 'category_averages' in stats:
                print("  Category Averages:")
                for category, score in stats['category_averages'].items():
                    print(f"    {category}: {score:.3f}")
                    
    def print_criteria_selection(self, criteria_list: List[str]) -> None:
        """Print formatted criteria selection"""
        self.print_section("Selected Criteria")
        
        # Group criteria by category
        categories = {}
        for criterion_id in criteria_list:
            parts = criterion_id.split('.')
            category = parts[0] if parts else 'unknown'
            
            if category not in categories:
                categories[category] = []
            categories[category].append(criterion_id)
            
        for category, criteria in categories.items():
            print(f"\n{self.COLORS['bold']}{category.upper()}:{self.COLORS['end']}")
            for criterion in criteria:
                print(f"  • {criterion}")
                
    def print_configuration_summary(self, config_summary: Dict[str, Any]) -> None:
        """Print configuration summary"""
        self.print_section("Configuration Summary")
        
        print(f"{'System Version:':<20} {config_summary.get('system_version', 'Unknown')}")
        print(f"{'Judges:':<20} {', '.join(config_summary.get('judges_configured', []))}")
        print(f"{'Passes per Judge:':<20} {config_summary.get('n_passes_default', 3)}")
        print(f"{'Providers:':<20} {', '.join(config_summary.get('providers_configured', []))}")
        print(f"{'Parallel Processing:':<20} {'Enabled' if config_summary.get('parallel_enabled') else 'Disabled'}")
        print(f"{'Caching:':<20} {'Enabled' if config_summary.get('cache_enabled') else 'Disabled'}")
        
    def print_consistency_metrics(self, metrics: Dict[str, Any]) -> None:
        """Print consistency metrics"""
        self.print_section("Consistency Metrics")
        
        print(f"{'Overall Variance:':<25} {metrics.get('overall_variance', 0):.3f}")
        print(f"{'Judge Agreement Avg:':<25} {metrics.get('judge_agreement_avg', 0):.3f}")
        print(f"{'Outliers Detected:':<25} {metrics.get('outliers_detected', 0)}")
        print(f"{'Total Evaluations:':<25} {metrics.get('total_evaluations', 0)}")
        
        if 'variance_distribution' in metrics:
            dist = metrics['variance_distribution']
            print(f"\nVariance Distribution:")
            print(f"{'  Min:':<23} {dist.get('min', 0):.3f}")
            print(f"{'  Max:':<23} {dist.get('max', 0):.3f}")
            print(f"{'  Std Dev:':<23} {dist.get('std', 0):.3f}")
            
    def print_evaluation_alerts(self, evaluation_results: List[Dict[str, Any]]) -> None:
        """Print any evaluation alerts or warnings"""
        alerts = []
        
        for result in evaluation_results:
            criterion_id = result['criterion']
            scores = result['scores']
            metadata = result['metadata']
            
            # Check for high variance
            if scores.get('consistency_variance', 0) > 0.5:
                alerts.append(f"High variance in {criterion_id}: {scores['consistency_variance']:.3f}")
                
            # Check for low agreement
            if scores.get('agreement_score', 1.0) < 0.8:
                alerts.append(f"Low judge agreement in {criterion_id}: {scores['agreement_score']:.3f}")
                
            # Check for outliers
            if metadata.get('outlier_detected', False):
                alerts.append(f"Outliers detected in {criterion_id}")
                
        if alerts:
            self.print_section("Evaluation Alerts")
            for alert in alerts:
                self.print_warning(alert)
        else:
            self.print_success("No evaluation alerts detected")
            
    def format_duration(self, seconds: float) -> str:
        """Format duration in human-readable format"""
        if seconds < 60:
            return f"{seconds:.1f}s"
        elif seconds < 3600:
            minutes = int(seconds // 60)
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds:.1f}s"
        else:
            hours = int(seconds // 3600)
            remaining_minutes = int((seconds % 3600) // 60)
            remaining_seconds = seconds % 60
            return f"{hours}h {remaining_minutes}m {remaining_seconds:.1f}s"
            
    def start_timer(self) -> None:
        """Start timing for progress tracking"""
        self.start_time = time.time()
        
    def get_elapsed_time(self) -> float:
        """Get elapsed time since timer started"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time
        
    def print_elapsed_time(self, prefix: str = "Elapsed") -> None:
        """Print elapsed time"""
        elapsed = self.get_elapsed_time()
        print(f"{prefix}: {self.format_duration(elapsed)}")
        
    def confirm_action(self, message: str, default: bool = False) -> bool:
        """
        Ask user for confirmation
        
        Args:
            message: Confirmation message
            default: Default value if user just presses Enter
            
        Returns:
            True if user confirms, False otherwise
        """
        suffix = " [Y/n]" if default else " [y/N]"
        
        try:
            response = input(f"{message}{suffix}: ").strip().lower()
            
            if not response:
                return default
            elif response in ['y', 'yes']:
                return True
            elif response in ['n', 'no']:
                return False
            else:
                print("Please answer 'y' or 'n'")
                return self.confirm_action(message, default)
                
        except KeyboardInterrupt:
            print("\nOperation cancelled by user")
            return False
            
    def print_table(self, headers: List[str], rows: List[List[str]], title: str = None) -> None:
        """Print formatted table"""
        if title:
            self.print_section(title)
            
        # Calculate column widths
        col_widths = [len(header) for header in headers]
        
        for row in rows:
            for i, cell in enumerate(row):
                if i < len(col_widths):
                    col_widths[i] = max(col_widths[i], len(str(cell)))
                    
        # Print header
        header_row = " | ".join(header.ljust(col_widths[i]) for i, header in enumerate(headers))
        print(f"{self.COLORS['bold']}{header_row}{self.COLORS['end']}")
        
        # Print separator
        separator = "-+-".join("-" * width for width in col_widths)
        print(separator)
        
        # Print rows
        for row in rows:
            formatted_row = " | ".join(str(cell).ljust(col_widths[i]) for i, cell in enumerate(row))
            print(formatted_row)
            
    def print_json_summary(self, data: Dict[str, Any], title: str = None) -> None:
        """Print formatted JSON summary"""
        if title:
            self.print_section(title)
            
        if self.verbose:
            print(json.dumps(data, indent=2, ensure_ascii=False))
        else:
            # Print compact summary
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)):
                        print(f"{key}: {type(value).__name__} ({len(value)} items)")
                    else:
                        print(f"{key}: {value}")
            else:
                print(json.dumps(data, indent=2, ensure_ascii=False))
                
    def display_final_results(self, 
                            final_score: float,
                            output_dir: str,
                            processing_time: float,
                            total_records: int) -> None:
        """Display final benchmark results"""
        self.print_section("Final Results")
        
        # Score visualization
        score_bar = self.create_score_bar(final_score)
        
        print(f"\n{self.COLORS['bold']}Final Aggregate Score:{self.COLORS['end']}")
        print(f"{score_bar}")
        print(f"{final_score:.3f} / 5.0")
        
        # Summary stats
        print(f"\n{self.COLORS['bold']}Summary:{self.COLORS['end']}")
        print(f"{'Records Processed:':<20} {total_records}")
        print(f"{'Processing Time:':<20} {self.format_duration(processing_time)}")
        print(f"{'Average per Record:':<20} {processing_time/total_records:.2f}s")
        print(f"{'Results Location:':<20} {output_dir}")
        
    def create_score_bar(self, score: float, max_score: float = 5.0) -> str:
        """Create visual score bar"""
        percentage = (score / max_score) * 100
        filled = int(percentage / 4)  # 25 chars = 100%
        
        # Color coding based on score
        if percentage >= 80:
            color = self.COLORS['green']
        elif percentage >= 60:
            color = self.COLORS['yellow']
        else:
            color = self.COLORS['red']
            
        bar = '█' * filled + '░' * (25 - filled)
        return f"{color}[{bar}] {percentage:.1f}%{self.COLORS['end']}"