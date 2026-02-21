#!/usr/bin/env python3
"""
MASTER TEST RUNNER
Runs all tests and displays comprehensive results
"""

import sys
import os
import time
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from tests.test_flash import TestFlashSimulator
from tests.test_patent1 import TestPatent1
from tests.test_patent2 import TestPatent2
from tests.test_patent3 import TestPatent3
from tests.test_integration import TestIntegration

class TestRunner:
    """Run all tests and aggregate results"""
    
    def __init__(self):
        self.all_results = {}
        self.start_time = time.time()
    
    def run_all(self):
        """Run all test suites"""
        print("=" * 70)
        print("🔬 RUNNING ALL TESTS - VIRTUAL EEPROM ON FLASH")
        print("=" * 70)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # Test suites to run
        test_suites = [
            ("Flash Simulator", TestFlashSimulator),
            ("Patent 1: Adaptive Wear", TestPatent1),
            ("Patent 2: Predictive Retirement", TestPatent2),
            ("Patent 3: Self-Healing Mapping", TestPatent3),
            ("Integration: All Components", TestIntegration)
        ]
        
        total_passed = 0
        total_tests = 0
        
        for name, TestClass in test_suites:
            print("-" * 50)
            print(f"Running: {name}")
            print("-" * 50)
            
            tester = TestClass()
            results = tester.run_all_tests()
            
            self.all_results[name] = results
            total_passed += results['passed']
            total_tests += results['total']
            
            print()
        
        # Print summary
        self.print_summary(total_passed, total_tests)
        
        # Save results to file
        self.save_results()
    
    def print_summary(self, total_passed, total_tests):
        """Print test summary"""
        print("=" * 70)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 70)
        
        for name, results in self.all_results.items():
            status = "✅ PASSED" if results['passed'] == results['total'] else "❌ FAILED"
            print(f"{status} - {name}: {results['passed']}/{results['total']} passed")
        
        print("-" * 70)
        
        overall_status = "✅ ALL TESTS PASSED" if total_passed == total_tests else "❌ SOME TESTS FAILED"
        print(f"{overall_status} - {total_passed}/{total_tests} total tests passed")
        
        elapsed = time.time() - self.start_time
        print(f"Time elapsed: {elapsed:.2f} seconds")
        print("=" * 70)
    
    def save_results(self):
        """Save test results to file - without Unicode characters to avoid encoding issues"""
        filename = f"test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("VIRTUAL EEPROM ON FLASH - TEST RESULTS\n")
            f.write("=" * 50 + "\n\n")
            
            for name, results in self.all_results.items():
                f.write(f"{name}:\n")
                f.write(f"  Passed: {results['passed']}/{results['total']}\n")
                f.write(f"  Details:\n")
                for detail in results['details']:
                    # Replace Unicode checkmarks with ASCII
                    clean_detail = detail.replace('✅', '[PASS]').replace('❌', '[FAIL]')
                    f.write(f"    {clean_detail}\n")
                f.write("\n")
            
            total_passed = sum(r['passed'] for r in self.all_results.values())
            total_tests = sum(r['total'] for r in self.all_results.values())
            
            f.write("=" * 50 + "\n")
            f.write(f"TOTAL: {total_passed}/{total_tests} tests passed\n")
        
        print(f"\n📁 Test results saved to: {filename}")

def main():
    """Main entry point"""
    runner = TestRunner()
    runner.run_all()

if __name__ == "__main__":
    main()