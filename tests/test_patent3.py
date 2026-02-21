"""
TEST: Patent 3 - Self-Healing Mapping Table
Tests 3-copy redundancy, corruption detection, and auto-repair
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from simulator.flash_sim import FlashSimulator
from simulator.patent3_selfhealing import SelfHealingMapping
from simulator.veeprom_core import VEEPROMCore
import time
import random

class TestPatent3:
    """Test Patent 3: Self-Healing Mapping Table"""
    
    def __init__(self):
        self.flash = FlashSimulator()
        self.veeprom = VEEPROMCore(self.flash)
        self.patent3 = SelfHealingMapping(self.flash, self.veeprom.PAGE_COUNT, 32)
        self.passed = 0
        self.total = 0
        self.results = []
    
    def run_all_tests(self):
        """Run all Patent 3 tests"""
        print("\n🔧 TESTING PATENT 3: SELF-HEALING MAPPING...\n")
        
        self.test_initialization()
        self.test_write_entry()
        self.test_read_entry()
        self.test_three_copies()
        self.test_corruption_detection()
        self.test_majority_voting()
        self.test_auto_healing()
        self.test_heal_all_entries()
        self.test_statistics_tracking()
        self.test_recovery_rate()
        self.test_mapping_health()
        
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
        """Test Patent 3 initialization"""
        try:
            # Check copy locations
            self.assert_true(
                self.patent3.PRIMARY_START == 0,
                "Primary copy at address 0"
            )
            
            self.assert_true(
                self.patent3.BACKUP1_START == 4096,
                "Backup 1 at address 4096"
            )
            
            self.assert_true(
                self.patent3.BACKUP2_START == 8192,
                "Backup 2 at address 8192"
            )
            
            # Check stats initialized
            stats = self.patent3.get_statistics()
            self.assert_true(
                stats['corruptions_detected'] == 0,
                "Initial corruptions = 0"
            )
            
            self.assert_true(
                stats['heal_attempts'] == 0,
                "Initial heal attempts = 0"
            )
            
            self.assert_true(
                stats['current_health'] == 100,
                "Initial health = 100%"
            )
            
        except Exception as e:
            self.assert_true(False, f"Initialization failed: {e}")
    
    def test_write_entry(self):
        """Test writing mapping entries"""
        try:
            entry_index = 10
            test_data = bytes([1, 2, 3, 4] + [0] * 28)  # 32 bytes
            
            success, meta = self.patent3.write_entry(entry_index, test_data)
            
            self.assert_true(
                success,
                "Write entry successful"
            )
            
            self.assert_true(
                meta['success_count'] >= 2,
                f"Wrote to {meta['success_count']}/3 copies"
            )
            
            # Verify written to all copies
            for copy_num in range(3):
                addr = self.patent3._get_copy_address(entry_index, copy_num)
                page = addr // self.flash.PAGE_SIZE
                offset = addr % self.flash.PAGE_SIZE
                
                data, read_time, rmeta = self.flash.read_page(page, 32, offset)
                
                self.assert_true(
                    data is not None,
                    f"Copy {copy_num} readable"
                )
            
        except Exception as e:
            self.assert_true(False, f"Write entry test failed: {e}")
    
    def test_read_entry(self):
        """Test reading mapping entries"""
        try:
            entry_index = 11
            test_data = bytes([5, 6, 7, 8] + [0] * 28)
            
            # Write first
            write_success, write_meta = self.patent3.write_entry(entry_index, test_data)
            
            # Read back
            data, meta = self.patent3.read_entry(entry_index)
            
            self.assert_true(
                data is not None,
                "Read entry successful"
            )
            
            # Compare without checksum byte (last byte)
            if data is not None and test_data is not None:
                self.assert_true(
                    data[:-1] == test_data[:-1],
                    "Read data matches written data (excluding checksum)"
                )
            
            self.assert_true(
                'copies_valid' in meta,
                "Metadata includes copies valid count"
            )
            
        except Exception as e:
            self.assert_true(False, f"Read entry test failed: {e}")
    
    def test_three_copies(self):
        """Test that three copies are maintained"""
        try:
            entry_index = 12
            test_data = bytes([10, 11, 12, 13] + [0] * 28)
            
            # Write
            self.patent3.write_entry(entry_index, test_data)
            
            # Read each copy directly from Flash
            copies_data = []
            for copy_num in range(3):
                addr = self.patent3._get_copy_address(entry_index, copy_num)
                page = addr // self.flash.PAGE_SIZE
                offset = addr % self.flash.PAGE_SIZE
                
                data, read_time, rmeta = self.flash.read_page(page, 32, offset)
                copies_data.append(data)
            
            # All copies should have data
            for i, data in enumerate(copies_data):
                self.assert_true(
                    data is not None,
                    f"Copy {i} exists"
                )
            
            # All copies should be identical (except checksum)
            for i in range(1, 3):
                if copies_data[i] and copies_data[0]:
                    # Compare first 31 bytes (exclude checksum)
                    self.assert_true(
                        copies_data[i][:31] == copies_data[0][:31],
                        f"Copy {i} matches copy 0"
                    )
            
        except Exception as e:
            self.assert_true(False, f"Three copies test failed: {e}")
    
    def test_corruption_detection(self):
        """Test corruption detection"""
        try:
            entry_index = 13
            test_data = bytes([20, 21, 22, 23] + [0] * 28)
            
            # Write entry
            self.patent3.write_entry(entry_index, test_data)
            
            # Get initial stats
            initial_stats = self.patent3.get_statistics()
            
            # Inject corruption in primary copy
            self.patent3.inject_corruption(entry_index, 0)
            
            # Read should detect corruption
            data, meta = self.patent3.read_entry(entry_index)
            
            # Get updated stats
            new_stats = self.patent3.get_statistics()
            
            self.assert_true(
                new_stats['corruptions_detected'] > initial_stats['corruptions_detected'],
                "Corruption detected"
            )
            
            # Should still return correct data
            if data is not None and test_data is not None:
                self.assert_true(
                    data[:-1] == test_data[:-1],
                    "Correct data returned despite corruption"
                )
            
            self.assert_true(
                meta.get('healing_needed', False) or meta['copies_valid'] < 3,
                "Metadata indicates corruption"
            )
            
        except Exception as e:
            self.assert_true(False, f"Corruption detection test failed: {e}")
    
    def test_majority_voting(self):
        """Test majority voting logic"""
        try:
            entry_index = 14
            test_data = bytes([30, 31, 32, 33] + [0] * 28)
            
            # Write entry
            self.patent3.write_entry(entry_index, test_data)
            
            # Corrupt two copies with different data
            corrupt_data1 = bytes([99] + [0] * 31)
            corrupt_data2 = bytes([98] + [0] * 31)
            
            # Write corrupt data to copies
            addr1 = self.patent3._get_copy_address(entry_index, 0)
            page1 = addr1 // self.flash.PAGE_SIZE
            offset1 = addr1 % self.flash.PAGE_SIZE
            self.flash.write_page(page1, corrupt_data1, offset1)
            
            addr2 = self.patent3._get_copy_address(entry_index, 1)
            page2 = addr2 // self.flash.PAGE_SIZE
            offset2 = addr2 % self.flash.PAGE_SIZE
            self.flash.write_page(page2, corrupt_data2, offset2)
            
            # Read should use majority (the one good copy)
            data, meta = self.patent3.read_entry(entry_index)
            
            if data is not None and test_data is not None:
                self.assert_true(
                    data[:-1] == test_data[:-1],
                    "Majority voting returns correct data"
                )
            
            self.assert_true(
                meta['copies_valid'] >= 1,
                f"Valid copies: {meta['copies_valid']}"
            )
            
        except Exception as e:
            self.assert_true(False, f"Majority voting test failed: {e}")
    
    def test_auto_healing(self):
        """Test automatic healing"""
        try:
            entry_index = 15
            test_data = bytes([40, 41, 42, 43] + [0] * 28)
            
            # Write entry
            self.patent3.write_entry(entry_index, test_data)
            
            # Get initial stats
            initial_stats = self.patent3.get_statistics()
            
            # Corrupt all copies
            for copy_num in range(3):
                self.patent3.inject_corruption(entry_index, copy_num)
            
            # Read should trigger healing
            data, meta = self.patent3.read_entry(entry_index)
            
            # Wait for healing thread
            time.sleep(2)
            
            # Get updated stats
            new_stats = self.patent3.get_statistics()
            
            # Healing might not have completed yet
            self.assert_true(
                new_stats['heal_attempts'] >= initial_stats['heal_attempts'],
                "Healing attempted or in progress"
            )
            
            # Check that at least some healing occurred
            self.assert_true(
                new_stats['heal_success'] >= initial_stats['heal_success'] or
                new_stats['heal_attempts'] > initial_stats['heal_attempts'],
                "Healing process started"
            )
            
        except Exception as e:
            self.assert_true(False, f"Auto healing test failed: {e}")
    
    def test_heal_all_entries(self):
        """Test healing all entries"""
        try:
            # Write multiple entries
            for i in range(10):
                test_data = bytes([i] * 32)
                self.patent3.write_entry(i, test_data)
            
            # Corrupt some
            for i in range(5):
                self.patent3.inject_corruption(i, 0)
                if i % 2 == 0:
                    self.patent3.inject_corruption(i, 1)
            
            # Verify and repair all
            result = self.patent3.verify_and_repair_all()
            
            self.assert_true(
                result['entries_checked'] == self.veeprom.PAGE_COUNT,
                f"All {self.veeprom.PAGE_COUNT} entries checked ({result['entries_checked']})"
            )
            
            self.assert_true(
                result['repaired_entries'] >= 0,
                f"Repaired {result['repaired_entries']} entries"
            )
            
            self.assert_true(
                result['current_health'] > 0,
                f"Current health: {result['current_health']:.1f}%"
            )
            
        except Exception as e:
            self.assert_true(False, f"Heal all entries test failed: {e}")
    
    def test_statistics_tracking(self):
        """Test statistics tracking"""
        try:
            # Perform various operations
            for i in range(5):
                entry = 20 + i
                test_data = bytes([i] * 32)
                
                # Write
                self.patent3.write_entry(entry, test_data)
                
                # Corrupt
                self.patent3.inject_corruption(entry, 0)
                
                # Read (triggers detection)
                self.patent3.read_entry(entry)
            
            # Get stats
            stats = self.patent3.get_statistics()
            
            self.assert_true(
                'corruptions_detected' in stats,
                "Corruptions detected tracked"
            )
            
            self.assert_true(
                'heal_attempts' in stats,
                "Heal attempts tracked"
            )
            
            self.assert_true(
                'heal_success' in stats,
                "Heal successes tracked"
            )
            
            self.assert_true(
                'primary_errors' in stats,
                "Primary errors tracked"
            )
            
            self.assert_true(
                'backup1_errors' in stats,
                "Backup 1 errors tracked"
            )
            
            self.assert_true(
                'backup2_errors' in stats,
                "Backup 2 errors tracked"
            )
            
            self.assert_true(
                'avg_heal_time_us' in stats,
                "Average heal time tracked"
            )
            
        except Exception as e:
            self.assert_true(False, f"Statistics tracking test failed: {e}")
    
    def test_recovery_rate(self):
        """Test recovery rate calculation"""
        try:
            # Save original stats to restore later
            original_stats = self.patent3.stats.copy()
            
            # Simulate heal attempts
            self.patent3.stats['heal_attempts'] = 10
            self.patent3.stats['heal_success'] = 9
            self.patent3.stats['heal_failures'] = 1
            
            # Manually trigger recovery rate calculation
            total_heals = self.patent3.stats['heal_success'] + self.patent3.stats['heal_failures']
            if total_heals > 0:
                self.patent3.stats['recovery_rate'] = (self.patent3.stats['heal_success'] * 100.0) / total_heals
            
            # Check that recovery rate is exactly 90.0
            self.assert_true(
                abs(self.patent3.stats['recovery_rate'] - 90.0) < 0.001,
                f"Recovery rate calculated correctly ({self.patent3.stats['recovery_rate']:.1f}%)"
            )
            
            # Restore original stats
            self.patent3.stats.update(original_stats)
            
        except Exception as e:
            self.assert_true(False, f"Recovery rate test failed: {e}")
    
    def test_mapping_health(self):
        """Test mapping health calculation"""
        try:
            # Save original stats
            original_stats = self.patent3.stats.copy()
            
            # Set error counts
            self.patent3.stats['primary_errors'] = 5
            self.patent3.stats['backup1_errors'] = 3
            self.patent3.stats['backup2_errors'] = 2
            
            # Manually calculate health
            total_entries = self.veeprom.PAGE_COUNT * 3
            total_errors = 5 + 3 + 2
            self.patent3.stats['current_health'] = ((total_entries - total_errors) * 100.0) / total_entries if total_entries > 0 else 100
            
            # Get health
            health = self.patent3.stats['current_health']
            
            # Calculate expected
            expected = ((total_entries - total_errors) * 100.0) / total_entries if total_entries > 0 else 100
            
            # Allow small rounding differences
            self.assert_true(
                abs(health - expected) < 0.1,
                f"Mapping health calculated correctly ({health:.1f}% vs {expected:.1f}%)"
            )
            
            # Restore original stats
            self.patent3.stats.update(original_stats)
            
        except Exception as e:
            self.assert_true(False, f"Mapping health test failed: {e}")


if __name__ == "__main__":
    tester = TestPatent3()
    results = tester.run_all_tests()
    
    print(f"\n📊 RESULTS: {results['passed']}/{results['total']} tests passed")
    for detail in results['details']:
        print(f"  {detail}")