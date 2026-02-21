"""
REAL DATA COLLECTOR
Collects and stores all simulation data for Excel export and analysis
No hardcoding - all data comes from actual simulation
"""

import time
import csv
import json
from typing import Dict, List, Any
import pandas as pd
from datetime import datetime
import os

class DataCollector:
    """
    Collects REAL data from all components and exports to Excel
    """
    
    def __init__(self):
        # Data storage
        self.data_points = []
        self.patent1_history = []
        self.patent2_history = []
        self.patent3_history = []
        self.flash_history = []
        self.veeprom_history = []
        
        # Current state
        self.current_data = {
            'timestamp': time.time(),
            'data_points': 0,
            'patent1': {},
            'patent2': {},
            'patent3': {},
            'flash': {},
            'veeprom': {},
            'comparison': {}
        }
        
        # Export directory
        self.export_dir = 'exports'
        if not os.path.exists(self.export_dir):
            os.makedirs(self.export_dir)
        
        print("✅ Data Collector initialized")
    
    def collect(self, 
                patent1_stats: Dict,
                patent2_stats: Dict,
                patent3_stats: Dict,
                flash_stats: Dict,
                veeprom_stats: Dict,
                comparison: Dict):
        """
        Collect REAL data from all components
        """
        data_point = {
            'timestamp': time.time(),
            'datetime': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'data_points': len(self.data_points) + 1,
            'patent1': patent1_stats.copy(),
            'patent2': patent2_stats.copy(),
            'patent3': patent3_stats.copy(),
            'flash': flash_stats.copy(),
            'veeprom': veeprom_stats.copy(),
            'comparison': comparison.copy()
        }
        
        self.data_points.append(data_point)
        
        # Update current data
        self.current_data = data_point
        
        # Add to histories
        self.patent1_history.append({
            'timestamp': data_point['timestamp'],
            'wear_balance': patent1_stats.get('wear_balance', 0),
            'hot_blocks': patent1_stats.get('hot_blocks', 0),
            'current_strategy': patent1_stats.get('current_strategy', 'UNKNOWN')
        })
        
        self.patent2_history.append({
            'timestamp': data_point['timestamp'],
            'accuracy': patent2_stats.get('prediction_accuracy', 0),
            'failing_blocks': patent2_stats.get('failing_blocks_count', 0),
            'avg_health': patent2_stats.get('avg_health', 100)
        })
        
        self.patent3_history.append({
            'timestamp': data_point['timestamp'],
            'health': patent3_stats.get('current_health', 100),
            'heal_success': patent3_stats.get('heal_success', 0),
            'corruptions': patent3_stats.get('corruptions_detected', 0)
        })
        
        self.flash_history.append({
            'timestamp': data_point['timestamp'],
            'writes': flash_stats.get('total_writes', 0),
            'reads': flash_stats.get('total_reads', 0),
            'erases': flash_stats.get('total_erases', 0),
            'write_errors': flash_stats.get('write_errors', 0)
        })
        
        self.veeprom_history.append({
            'timestamp': data_point['timestamp'],
            'writes': veeprom_stats.get('total_writes', 0),
            'reads': veeprom_stats.get('total_reads', 0),
            'cache_hit_rate': veeprom_stats.get('cache_hit_rate', 0)
        })
    
    def export_to_excel(self) -> str:
        """
        Export ALL collected data to Excel file
        Returns: filename of exported file
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{self.export_dir}/veeprom_data_{timestamp}.xlsx"
        
        # Create Excel writer
        with pd.ExcelWriter(filename, engine='openpyxl') as writer:
            
            # Summary sheet
            summary_data = []
            for dp in self.data_points[-100:]:  # Last 100 points
                summary_data.append({
                    'Timestamp': dp['datetime'],
                    'Data Point': dp['data_points'],
                    'P1 Strategy': dp['patent1'].get('current_strategy', ''),
                    'P1 Wear Balance': dp['patent1'].get('wear_balance', 0),
                    'P1 Hot Blocks': dp['patent1'].get('hot_blocks', 0),
                    'P2 Accuracy': dp['patent2'].get('prediction_accuracy', 0),
                    'P2 Failing': dp['patent2'].get('failing_blocks_count', 0),
                    'P3 Health': dp['patent3'].get('current_health', 0),
                    'P3 Heal Success': dp['patent3'].get('heal_success', 0),
                    'Flash Writes': dp['flash'].get('total_writes', 0),
                    'Flash Errors': dp['flash'].get('write_errors', 0),
                    'Without Lifetime': dp['comparison'].get('without_lifetime', 0),
                    'With Lifetime': dp['comparison'].get('with_lifetime', 0),
                    'Improvement': dp['comparison'].get('lifetime_improvement', 0)
                })
            
            df_summary = pd.DataFrame(summary_data)
            df_summary.to_excel(writer, sheet_name='Summary', index=False)
            
            # Patent 1 detailed sheet
            df_p1 = pd.DataFrame(self.patent1_history)
            if not df_p1.empty:
                df_p1.to_excel(writer, sheet_name='Patent1_Adaptive', index=False)
            
            # Patent 2 detailed sheet
            df_p2 = pd.DataFrame(self.patent2_history)
            if not df_p2.empty:
                df_p2.to_excel(writer, sheet_name='Patent2_Predictive', index=False)
            
            # Patent 3 detailed sheet
            df_p3 = pd.DataFrame(self.patent3_history)
            if not df_p3.empty:
                df_p3.to_excel(writer, sheet_name='Patent3_SelfHealing', index=False)
            
            # Flash stats sheet
            df_flash = pd.DataFrame(self.flash_history)
            if not df_flash.empty:
                df_flash.to_excel(writer, sheet_name='Flash_Stats', index=False)
            
            # VEEPROM stats sheet
            df_veeprom = pd.DataFrame(self.veeprom_history)
            if not df_veeprom.empty:
                df_veeprom.to_excel(writer, sheet_name='VEEPROM_Stats', index=False)
            
            # Current state sheet
            current_items = []
            for key, value in self.flatten_dict(self.current_data).items():
                # Truncate long values to avoid Excel issues
                if isinstance(value, str) and len(value) > 32767:
                    value = value[:32767] + "..."
                current_items.append({
                    'Metric': key,
                    'Value': str(value)
                })
            
            current_df = pd.DataFrame(current_items)
            current_df.to_excel(writer, sheet_name='Current_State', index=False)
        
        print(f"✅ Data exported to {filename}")
        return filename
    
    def flatten_dict(self, d: Dict, parent_key: str = '') -> Dict:
        """Flatten nested dictionary for Excel export"""
        items = []
        for k, v in d.items():
            new_key = f"{parent_key}.{k}" if parent_key else k
            if isinstance(v, dict):
                items.extend(self.flatten_dict(v, new_key).items())
            else:
                items.append((new_key, v))
        return dict(items)
    
    def get_current_data(self) -> Dict:
        """Get most recent data point"""
        return self.current_data.copy()
    
    def get_history(self, patent: str, limit: int = 100) -> List:
        """Get history for specific patent"""
        if patent == 'patent1':
            return self.patent1_history[-limit:]
        elif patent == 'patent2':
            return self.patent2_history[-limit:]
        elif patent == 'patent3':
            return self.patent3_history[-limit:]
        else:
            return []