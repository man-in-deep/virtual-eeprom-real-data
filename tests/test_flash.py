"""
TEST: Flash Simulation
Tests all Flash operations with REAL data validation
No hardcoding - all assertions use calculated values
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.flash_sim import FlashSimulator
import time
import random

class TestFlashSimulator:
    """Test Flash Simulator with REAL data"""
    
    def __init__(self):
        self.flash = FlashSimulator()
        self.passed = 0
        self.total = 0
        self.results = []
    
    def run_all_tests(self):
        """Run all Flash simulator tests"""
        print("\n🔧 TESTING FLASH SIMULATOR...\n")
        
        self.test_initialization()
        self.test_write_read()
        self.test_erase()
        self.test_multiple_writes()
        self.test_error_conditions()
        self.test_temperature_effects()
        self.test_voltage_effects()
        self.test_block_health()
        self.test_wear_behavior()
        self.test_statistics()
        
        return {
            'passed': self.passed,
            'total': self.total,
            'details': self.results
        }
    
    def assert_true(self, condition, message):
        """Custom assertion with tracking"""
        self.total += 1
        if condition:
            self.passed += 1
            self.results.append(f"✅ {message}")
        else:
            self.results.append(f"❌ {message}")
    
    def test_initialization(self):
        """Test Flash initialization"""
        try:
            # Check Flash size
            self.assert_true(
                self.flash.FLASH_SIZE == 128 * 1024,
                "Flash size correct (128KB)"
            )
            
            # Check page count
            self.assert_true(
                self.flash.PAGE_COUNT == 128,
                f"Page count correct ({self.flash.PAGE_COUNT})"
            )
            
            # Check all blocks initialized
            self.assert_true(
                len(self.flash.block_health) == 128,
                "All 128 blocks initialized"
            )
            
            # Check initial stats
            stats = self.flash.get_stats()
            self.assert_true(
                stats['total_writes'] == 0,
                "Initial writes = 0"
            )
            
        except Exception as e:
            self.assert_true(False, f"Initialization failed: {e}")
    
    def test_write_read(self):
        """Test basic write and read operations"""
        try:
            # Write data to page 0
            test_data = bytes([1, 2, 3, 4, 5])
            success, write_time, meta = self.flash.write_page(0, test_data, 0)
            
            self.assert_true(
                success,
                f"Write successful (time={write_time}us)"
            )
            
            # Read back
            read_data, read_time, rmeta = self.flash.read_page(0, len(test_data), 0)
            
            self.assert_true(
                read_data == test_data,
                f"Read data matches write data"
            )
            
            # Verify write time is reasonable
            self.assert_true(
                10 <= write_time <= 1000,
                f"Write time reasonable ({write_time}us)"
            )
            
            # Stats updated
            stats = self.flash.get_stats()
            self.assert_true(
                stats['total_writes'] == 1,
                f"Stats updated (writes={stats['total_writes']})"
            )
            
        except Exception as e:
            self.assert_true(False, f"Write/read test failed: {e}")
    
    def test_erase(self):
        """Test erase operation"""
        try:
            # Write data first
            test_data = bytes([0xAA] * 100)
            self.flash.write_page(1, test_data, 0)
            
            # Erase page
            success, erase_time, meta = self.flash.erase_page(1)
            
            self.assert_true(
                success,
                f"Erase successful (time={erase_time}us)"
            )
            
            # Verify erase time is reasonable
            self.assert_true(
                100 <= erase_time <= 5000,
                f"Erase time reasonable ({erase_time}us)"
            )
            
            # Read back - should be 0xFF
            read_data, read_time, rmeta = self.flash.read_page(1, 100, 0)
            
            self.assert_true(
                all(b == 0xFF for b in read_data),
                "Data erased (all 0xFF)"
            )
            
            # Erase count increased
            health = self.flash.get_block_health(1)
            self.assert_true(
                health['erase_count'] > 0,
                f"Erase count increased ({health['erase_count']})"
            )
            
        except Exception as e:
            self.assert_true(False, f"Erase test failed: {e}")
    
    def test_multiple_writes(self):
        """Test multiple writes to same block"""
        try:
            write_times = []
            
            for i in range(10):
                data = bytes([i] * 50)
                success, write_time, meta = self.flash.write_page(2, data, i*50)
                write_times.append(write_time)
                
                self.assert_true(
                    success,
                    f"Write {i+1} successful"
                )
            
            # Verify all writes succeeded
            for i in range(10):
                read_data, read_time, rmeta = self.flash.read_page(2, 50, i*50)
                expected = bytes([i] * 50)
                
                self.assert_true(
                    read_data == expected,
                    f"Read {i+1} matches write"
                )
            
            # Write times should vary
            self.assert_true(
                len(set(write_times)) > 1,
                "Write times vary (realistic)"
            )
            
        except Exception as e:
            self.assert_true(False, f"Multiple writes test failed: {e}")
    
    def test_error_conditions(self):
        """Test error conditions"""
        try:
            # Write to invalid page
            success, write_time, meta = self.flash.write_page(999, bytes([1]), 0)
            self.assert_true(
                not success,
                "Invalid page write fails correctly"
            )
            
            # Read from invalid page
            data, read_time, rmeta = self.flash.read_page(999, 1, 0)
            self.assert_true(
                data is None,
                "Invalid page read fails correctly"
            )
            
            # Write with offset beyond page
            success, write_time, meta = self.flash.write_page(3, bytes([1]), 2000)
            self.assert_true(
                not success,
                "Offset beyond page fails correctly"
            )
            
        except Exception as e:
            self.assert_true(False, f"Error conditions test failed: {e}")
    
    def test_temperature_effects(self):
        """Test temperature effects on performance"""
        try:
            # Write at room temperature
            self.flash.set_temperature(25)
            success1, time1, meta1 = self.flash.write_page(4, bytes([1]*100), 0)
            
            # Write at high temperature
            self.flash.set_temperature(85)
            success2, time2, meta2 = self.flash.write_page(4, bytes([2]*100), 100)
            
            # High temp should be slower
            self.assert_true(
                time2 > time1,
                f"High temperature increases write time ({time1}us -> {time2}us)"
            )
            
            # Write at low temperature
            self.flash.set_temperature(-10)
            success3, time3, meta3 = self.flash.write_page(4, bytes([3]*100), 200)
            
            # Verify temperature impact recorded
            health = self.flash.get_block_health(4)
            self.assert_true(
                'temperature_impact' in health,
                "Temperature impact tracked"
            )
            
        except Exception as e:
            self.assert_true(False, f"Temperature test failed: {e}")
    
    def test_voltage_effects(self):
        """Test voltage effects on performance"""
        try:
            # Write at normal voltage
            self.flash.set_voltage(3.3)
            success1, time1, meta1 = self.flash.write_page(5, bytes([1]*100), 0)
            
            # Write at low voltage
            self.flash.set_voltage(2.5)
            success2, time2, meta2 = self.flash.write_page(5, bytes([2]*100), 100)
            
            # Low voltage should be slower
            self.assert_true(
                time2 > time1,
                f"Low voltage increases write time ({time1}us -> {time2}us)"
            )
            
            # Verify voltage impact recorded
            health = self.flash.get_block_health(5)
            self.assert_true(
                'voltage_impact' in health,
                "Voltage impact tracked"
            )
            
        except Exception as e:
            self.assert_true(False, f"Voltage test failed: {e}")
    
    def test_block_health(self):
        """Test block health calculation"""
        try:
            # Write and erase multiple times
            for i in range(100):
                self.flash.write_page(6, bytes([i % 256] * 50), 0)  # FIX: Use modulo
                if i % 10 == 0:
                    self.flash.erase_page(6)
            
            # Get health
            health = self.flash.get_block_health(6)
            
            self.assert_true(
                'health_score' in health,
                "Health score calculated"
            )
            
            self.assert_true(
                0 <= health['health_score'] <= 100,
                f"Health score in range ({health['health_score']:.1f})"
            )
            
            self.assert_true(
                health['erase_count'] > 0,
                f"Erase count tracked ({health['erase_count']})"
            )
            
            self.assert_true(
                health['write_count'] > 0,
                f"Write count tracked ({health['write_count']})"
            )
            
        except Exception as e:
            self.assert_true(False, f"Block health test failed: {e}")
    
    def test_wear_behavior(self):
        """Test wear behavior over time"""
        try:
            # Simulate heavy wear on block 7
            initial_health = self.flash.get_block_health(7)['health_score']
            
            for i in range(500):
                # FIX: Use modulo 256 to ensure byte values are valid (0-255)
                self.flash.write_page(7, bytes([i % 256] * 100), 0)
                if i % 20 == 0:
                    self.flash.erase_page(7)
            
            final_health = self.flash.get_block_health(7)['health_score']
            
            self.assert_true(
                final_health < initial_health,
                f"Health degrades with wear ({initial_health:.1f}% -> {final_health:.1f}%)"
            )
            
            # Endurance remaining should decrease
            health = self.flash.get_block_health(7)
            self.assert_true(
                health['endurance_remaining'] < 10000,
                f"Endurance decreases ({health['endurance_remaining']})"
            )
            
        except Exception as e:
            self.assert_true(False, f"Wear behavior test failed: {e}")
    
    def test_statistics(self):
        """Test statistics collection"""
        try:
            # Perform various operations
            for i in range(20):
                self.flash.write_page(i % 10, bytes([i % 256] * 10), 0)  # FIX: Use modulo
                if i % 5 == 0:
                    self.flash.read_page(i % 10, 10, 0)
                if i % 8 == 0:
                    self.flash.erase_page(i % 10)
            
            # Get stats
            stats = self.flash.get_stats()
            
            self.assert_true(
                stats['total_writes'] > 0,
                f"Writes tracked ({stats['total_writes']})"
            )
            
            self.assert_true(
                stats['total_reads'] > 0,
                f"Reads tracked ({stats['total_reads']})"
            )
            
            self.assert_true(
                stats['total_erases'] > 0,
                f"Erases tracked ({stats['total_erases']})"
            )
            
            self.assert_true(
                stats['avg_write_time_us'] > 0,
                f"Avg write time calculated ({stats['avg_write_time_us']:.1f}us)"
            )
            
            self.assert_true(
                stats['avg_read_time_us'] > 0,
                f"Avg read time calculated ({stats['avg_read_time_us']:.1f}us)"
            )
            
            self.assert_true(
                stats['wear_balance'] >= 0,
                f"Wear balance calculated ({stats['wear_balance']:.1f}%)"
            )
            
        except Exception as e:
            self.assert_true(False, f"Statistics test failed: {e}")


if __name__ == "__main__":
    tester = TestFlashSimulator()
    results = tester.run_all_tests()
    
    print(f"\n📊 RESULTS: {results['passed']}/{results['total']} tests passed")
    for detail in results['details']:
        print(f"  {detail}")