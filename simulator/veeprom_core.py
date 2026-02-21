"""
VEEPROM CORE - Makes Flash behave like EEPROM
All data is REAL - calculated during actual operations
"""

from typing import Dict, List, Tuple, Optional
import time
from .flash_sim import FlashSimulator

class VEEPROMCore:
    """
    Core Virtual EEPROM engine that translates byte-addressable writes
    to Flash page operations with mapping table management
    """
    
    def __init__(self, flash: FlashSimulator):
        self.flash = flash
        
        # VEEPROM configuration (based on actual Flash)
        self.VEEPROM_SIZE = 4096  # 4KB emulated EEPROM
        self.PAGE_SIZE = 32        # 32 bytes per virtual page
        self.PAGE_COUNT = self.VEEPROM_SIZE // self.PAGE_SIZE  # 128 pages
        
        # Mapping table: virtual page -> physical location
        # ALL entries are REAL - updated on every write
        self.mapping = {
            i: {
                'valid': False,
                'physical_addr': None,
                'sequence': 0,
                'timestamp': 0,
                'write_count': 0
            }
            for i in range(self.PAGE_COUNT)
        }
        
        # Simple cache for faster access
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Free space tracking
        self.next_free_addr = 4096  # Start after mapping table
        self.DATA_END = flash.FLASH_SIZE
        
        # Statistics (ALL REAL)
        self.stats = {
            'total_writes': 0,
            'total_reads': 0,
            'write_errors': 0,
            'read_errors': 0,
            'cache_hits': 0,
            'cache_misses': 0,
            'cache_hit_rate': 0,
            'avg_write_time_us': 0,
            'avg_read_time_us': 0,
            'min_write_time_us': float('inf'),
            'max_write_time_us': 0,
            'corruptions_detected': 0,
            'wear_balance': 100,
            'max_erase_count': 0,
            'min_erase_count': 0
        }
        
        # For rolling averages
        self.write_times = []
        self.read_times = []
        
        print("✅ VEEPROM Core initialized")
    
    def _update_cache(self, page: int, entry: Dict):
        """Update cache with new entry"""
        self.cache[page] = entry.copy()
        # Keep cache size limited
        if len(self.cache) > 16:
            # Remove oldest entry (approximated by first key)
            oldest = next(iter(self.cache))
            del self.cache[oldest]
    
    def _find_in_cache(self, page: int) -> Optional[Dict]:
        """Find page in cache"""
        if page in self.cache:
            self.cache_hits += 1
            return self.cache[page].copy()
        self.cache_misses += 1
        return None
    
    def _calculate_wear_balance(self) -> float:
        """Calculate REAL wear balance across all blocks"""
        erase_counts = []
        for block_num in range(self.flash.PAGE_COUNT):
            health = self.flash.get_block_health(block_num)
            erase_counts.append(health['erase_count'])
        
        if not erase_counts:
            return 100.0
        
        max_erase = max(erase_counts)
        min_erase = min(erase_counts)
        
        if max_erase > 0:
            balance = (min_erase / max_erase) * 100
        else:
            balance = 100.0
        
        self.stats['max_erase_count'] = max_erase
        self.stats['min_erase_count'] = min_erase
        self.stats['wear_balance'] = balance
        
        return balance
    
    def write(self, virtual_addr: int, data: bytes) -> Tuple[bool, Dict]:
        """
        Write data to virtual EEPROM address
        Returns: (success, metadata with REAL data)
        """
        start_time = time.time()
        
        # Validate address
        if virtual_addr + len(data) > self.VEEPROM_SIZE:
            self.stats['write_errors'] += 1
            return False, {'error': 'Address out of bounds'}
        
        # Calculate virtual page and offset
        page = virtual_addr // self.PAGE_SIZE
        offset = virtual_addr % self.PAGE_SIZE
        
        # Check cache first
        existing = self._find_in_cache(page)
        if not existing and self.mapping[page]['valid']:
            existing = self.mapping[page].copy()
        
        # Determine physical location
        if self.next_free_addr + self.PAGE_SIZE > self.DATA_END:
            # Need garbage collection - simplified for demo
            new_addr = 4096  # Start over
            self.next_free_addr = new_addr + self.PAGE_SIZE
        else:
            new_addr = self.next_free_addr
            self.next_free_addr += self.PAGE_SIZE
        
        # Prepare full page data
        if existing and existing.get('valid', False):
            # Read existing data
            phys_addr = existing.get('physical_addr')
            if phys_addr:
                full_page, read_time, _ = self.flash.read_page(
                    phys_addr // self.flash.PAGE_SIZE,
                    self.PAGE_SIZE,
                    phys_addr % self.flash.PAGE_SIZE
                )
                if full_page is None:
                    full_page = bytes([0xFF] * self.PAGE_SIZE)
            else:
                full_page = bytes([0xFF] * self.PAGE_SIZE)
        else:
            full_page = bytes([0xFF] * self.PAGE_SIZE)
        
        # Update with new data
        full_page = bytearray(full_page)
        full_page[offset:offset + len(data)] = data
        full_page = bytes(full_page)
        
        # Write to Flash
        phys_page = new_addr // self.flash.PAGE_SIZE
        phys_offset = new_addr % self.flash.PAGE_SIZE
        success, write_time, flash_meta = self.flash.write_page(phys_page, full_page, phys_offset)
        
        if not success:
            self.stats['write_errors'] += 1
            return False, {'error': 'Flash write failed', 'flash_meta': flash_meta}
        
        # Update mapping table
        self.mapping[page] = {
            'valid': True,
            'physical_addr': new_addr,
            'sequence': self.mapping[page]['sequence'] + 1 if self.mapping[page]['valid'] else 1,
            'timestamp': time.time(),
            'write_count': self.mapping[page]['write_count'] + 1
        }
        
        # Update cache
        self._update_cache(page, self.mapping[page])
        
        # Update statistics
        self.stats['total_writes'] += 1
        self.write_times.append(write_time)
        
        if len(self.write_times) > 100:
            self.write_times = self.write_times[-100:]
        self.stats['avg_write_time_us'] = sum(self.write_times) / len(self.write_times)
        self.stats['min_write_time_us'] = min(self.stats['min_write_time_us'], write_time)
        self.stats['max_write_time_us'] = max(self.stats['max_write_time_us'], write_time)
        
        # Update cache hit rate
        total_cache = self.cache_hits + self.cache_misses
        if total_cache > 0:
            self.stats['cache_hit_rate'] = (self.cache_hits * 100) / total_cache
        self.stats['cache_hits'] = self.cache_hits
        self.stats['cache_misses'] = self.cache_misses
        
        # Update wear balance
        self._calculate_wear_balance()
        
        return True, {
            'virtual_page': page,
            'physical_addr': new_addr,
            'write_time_us': write_time,
            'flash_health': flash_meta.get('health_remaining', 100),
            'sequence': self.mapping[page]['sequence']
        }
    
    def read(self, virtual_addr: int, size: int) -> Tuple[Optional[bytes], Dict]:
        """
        Read data from virtual EEPROM address
        Returns: (data, metadata with REAL data)
        """
        # Validate
        if virtual_addr + size > self.VEEPROM_SIZE:
            self.stats['read_errors'] += 1
            return None, {'error': 'Address out of bounds'}
        
        page = virtual_addr // self.PAGE_SIZE
        offset = virtual_addr % self.PAGE_SIZE
        
        # Try cache first
        entry = self._find_in_cache(page)
        if not entry and self.mapping[page]['valid']:
            entry = self.mapping[page].copy()
        
        if not entry or not entry.get('valid'):
            # Never written - return 0xFF
            return bytes([0xFF] * size), {'cached': False, 'valid': False}
        
        # Read from Flash
        phys_addr = entry['physical_addr']
        if phys_addr is None:
            return bytes([0xFF] * size), {'error': 'No physical address'}
        
        phys_page = phys_addr // self.flash.PAGE_SIZE
        phys_offset = phys_addr % self.flash.PAGE_SIZE
        
        data, read_time, flash_meta = self.flash.read_page(phys_page, size, phys_offset + offset)
        
        if data is None:
            self.stats['read_errors'] += 1
            return None, {'error': 'Flash read failed'}
        
        # Update statistics
        self.stats['total_reads'] += 1
        self.read_times.append(read_time)
        
        if len(self.read_times) > 100:
            self.read_times = self.read_times[-100:]
        self.stats['avg_read_time_us'] = sum(self.read_times) / len(self.read_times)
        
        return data, {
            'cached': entry is not None,
            'physical_addr': phys_addr,
            'read_time_us': read_time,
            'flash_health': flash_meta.get('erase_count', 0),
            'sequence': entry['sequence']
        }
    
    def get_stats(self) -> Dict:
        """Get ALL REAL statistics"""
        self._calculate_wear_balance()
        
        # Add cache hit rate
        total_cache = self.cache_hits + self.cache_misses
        if total_cache > 0:
            self.stats['cache_hit_rate'] = (self.cache_hits * 100) / total_cache
        
        return self.stats.copy()
    
    def format(self) -> bool:
        """Format the entire VEEPROM"""
        # Erase all Flash sectors
        for sector in range(self.flash.PAGE_COUNT // 8):  # 8 pages per sector
            for page in range(sector * 8, (sector + 1) * 8):
                self.flash.erase_page(page)
        
        # Reset mapping
        self.mapping = {
            i: {
                'valid': False,
                'physical_addr': None,
                'sequence': 0,
                'timestamp': 0,
                'write_count': 0
            }
            for i in range(self.PAGE_COUNT)
        }
        
        # Reset cache
        self.cache = {}
        self.cache_hits = 0
        self.cache_misses = 0
        
        # Reset free space
        self.next_free_addr = 4096
        
        return True