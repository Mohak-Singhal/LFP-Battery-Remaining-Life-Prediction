"""
Endur-Cert Battery Valuation Engine
Core logic for health scoring, grading, and valuation
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List, Tuple


class BatteryEngine:
    """
    Main engine for battery health assessment and valuation.
    
    Converts RUL to Health Score, applies thermal penalties,
    and grades batteries into three career paths.
    """
    
    # Constants
    LFP_STANDARD_LIFE = 3000  # cycles
    TEMPERATURE_DEGRADATION_RATE = 2  # Degradation doubles every 10°C
    HIGH_HEAT_THRESHOLD = 35  # °C
    STANDARD_TEMP = 25  # °C reference temperature
    
    # Grade boundaries (% SoH)
    GRADE_A_MIN = 85
    GRADE_B_MIN = 70
    
    # New battery pack price (INR) - configurable
    NEW_PACK_PRICE = 250000  # ₹2.5 Lakhs
    
    # Application multipliers for second-life careers
    APPLICATION_MULTIPLIERS = {
        'Grade A': {
            'category': 'High-Power Mobility',
            'multiplier': 1.0,
            'applications': ['e-Rickshaws', 'Last-Mile Delivery', 'Two-Wheeler Charging']
        },
        'Grade B': {
            'category': 'Stationary Energy Storage',
            'multiplier': 0.85,
            'applications': ['Home UPS', 'Solar Microgrids', 'Telecom Backup', 'Renewable Integration']
        },
        'Grade C': {
            'category': 'Resource Recovery',
            'multiplier': 0.2,
            'applications': ['Lithium Reclamation', 'Phosphate Recovery', 'Recycling & Refurbishment']
        }
    }
    
    def __init__(self, new_pack_price: float = NEW_PACK_PRICE):
        """Initialize the battery engine with configurable pack price."""
        self.new_pack_price = new_pack_price
    
    def calculate_health_score(self, predicted_rul: float) -> float:
        """
        Convert RUL (cycles) to State-of-Health percentage.
        
        Health Score = (RUL / 3000) × 100
        
        Args:
            predicted_rul: Remaining Useful Life in cycles
            
        Returns:
            Health Score percentage (0-100)
        """
        soh = (predicted_rul / self.LFP_STANDARD_LIFE) * 100
        # Cap at 100% in case of prediction artifacts
        return min(100, max(0, soh))
    
    def calculate_temperature_penalty(self, avg_operating_temp: float) -> Tuple[float, str]:
        """
        Calculate thermal penalty/bonus based on LFP degradation rates.
        
        LFP degrades faster at higher temps. For every 10°C above 25°C,
        degradation roughly doubles.
        
        Args:
            avg_operating_temp: Average operating temperature in Celsius
            
        Returns:
            Tuple of (penalty_factor, assessment_text)
            - penalty_factor: Multiplier to apply (0.5 to 1.2)
            - assessment_text: Human-readable assessment
        """
        temp_diff = avg_operating_temp - self.STANDARD_TEMP
        
        if temp_diff <= -10:
            # Very cool operation - bonus
            penalty = 1.2
            assessment = "⚡ Cooling Bonus: Operated in ideal conditions"
        elif temp_diff < 0:
            # Cool operation
            penalty = 1.1
            assessment = "✓ Good: Operated below standard temperature"
        elif temp_diff < 10:
            # Normal operation
            penalty = 1.0
            assessment = "= Normal: Operated near standard temperature"
        elif temp_diff < 20:
            # Hot operation
            # Penalty = 1 / (2^(temp_diff/10))
            penalty = 1.0 / (self.TEMPERATURE_DEGRADATION_RATE ** (temp_diff / 10))
            assessment = f"⚠ Heat Tax: {assessment_detail(temp_diff)} {avg_operating_temp:.0f}°C)"
        else:
            # Very hot operation
            penalty = 1.0 / (self.TEMPERATURE_DEGRADATION_RATE ** (temp_diff / 10))
            assessment = f"🔥 Severe Heat Tax: Operated at extreme temp ({avg_operating_temp:.0f}°C)"
        
        return penalty, assessment
    
    def grade_battery(self, health_score: float) -> str:
        """
        Assign grade based on health score.
        
        Grade A: >85% SoH - High-Power Mobility
        Grade B: 70-85% SoH - Stationary Storage
        Grade C: <70% SoH - Resource Recovery
        
        Args:
            health_score: State-of-Health percentage
            
        Returns:
            Grade string ('Grade A', 'Grade B', or 'Grade C')
        """
        if health_score >= self.GRADE_A_MIN:
            return 'Grade A'
        elif health_score >= self.GRADE_B_MIN:
            return 'Grade B'
        else:
            return 'Grade C'
    
    def calculate_residual_value(self, health_score: float, grade: str, 
                                  temperature_penalty: float) -> float:
        """
        Calculate fair market price (Blue Book Value) in Rupees.
        
        Value = (New Pack Price × SoH%) × Application Multiplier - Temperature Penalty
        
        Args:
            health_score: State-of-Health percentage (0-100)
            grade: Battery grade ('Grade A', 'Grade B', 'Grade C')
            temperature_penalty: Thermal penalty factor (0.5-1.2)
            
        Returns:
            Residual value in INR
        """
        multiplier = self.APPLICATION_MULTIPLIERS[grade]['multiplier']
        
        # Base valuation
        value = (self.new_pack_price * (health_score / 100)) * multiplier
        
        # Apply thermal adjustment
        # If penalty < 1.0, it reduces value; if > 1.0, it increases value
        adjusted_value = value * temperature_penalty
        
        # Floor at minimum recycling value
        min_recycling_value = self.new_pack_price * 0.15
        
        return max(min_recycling_value, adjusted_value)
    
    def process_battery(self, battery_id: str, predicted_rul: float, 
                       avg_operating_temp: float) -> Dict:
        """
        Process a single battery through the full assessment pipeline.
        
        Args:
            battery_id: Unique identifier for the battery
            predicted_rul: Remaining Useful Life in cycles
            avg_operating_temp: Average operating temperature in Celsius
            
        Returns:
            Dictionary containing complete assessment results
        """
        # Step 1: Calculate health score
        soh = self.calculate_health_score(predicted_rul)
        
        # Step 2: Apply thermal audit
        temp_penalty, temp_assessment = self.calculate_temperature_penalty(avg_operating_temp)
        
        # Step 3: Grade battery
        grade = self.grade_battery(soh)
        
        # Step 4: Calculate residual value
        residual_value = self.calculate_residual_value(soh, grade, temp_penalty)
        
        # Step 5: Get second-life career path
        career_info = self.APPLICATION_MULTIPLIERS[grade]
        
        return {
            'Battery_ID': battery_id,
            'Predicted_RUL': predicted_rul,
            'Avg_Operating_Temp': avg_operating_temp,
            'Health_Score_%': round(soh, 2),
            'Grade': grade,
            'Category': career_info['category'],
            'Applications': ', '.join(career_info['applications']),
            'Temperature_Penalty_Factor': round(temp_penalty, 3),
            'Temperature_Assessment': temp_assessment,
            'Residual_Value_INR': round(residual_value, 2),
            'Assessment_Date': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    
    def process_fleet(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Process an entire fleet of batteries.
        
        Args:
            df: DataFrame with columns [Battery_ID, Predicted_RUL, Average_Operating_Temperature]
            
        Returns:
            DataFrame with full assessment for each battery
        """
        results = []
        
        for _, row in df.iterrows():
            result = self.process_battery(
                battery_id=row['Battery_ID'],
                predicted_rul=row['Predicted_RUL'],
                avg_operating_temp=row['Average_Operating_Temperature']
            )
            results.append(result)
        
        return pd.DataFrame(results)
    
    def get_fleet_summary(self, assessed_df: pd.DataFrame) -> Dict:
        """
        Generate summary statistics for a fleet assessment.
        
        Args:
            assessed_df: DataFrame output from process_fleet()
            
        Returns:
            Dictionary with fleet-level statistics
        """
        gradeA_count = len(assessed_df[assessed_df['Grade'] == 'Grade A'])
        gradeB_count = len(assessed_df[assessed_df['Grade'] == 'Grade B'])
        gradeC_count = len(assessed_df[assessed_df['Grade'] == 'Grade C'])
        
        return {
            'Total_Batteries': len(assessed_df),
            'Grade_A_Count': gradeA_count,
            'Grade_A_Percentage': round((gradeA_count / len(assessed_df)) * 100, 1),
            'Grade_B_Count': gradeB_count,
            'Grade_B_Percentage': round((gradeB_count / len(assessed_df)) * 100, 1),
            'Grade_C_Count': gradeC_count,
            'Grade_C_Percentage': round((gradeC_count / len(assessed_df)) * 100, 1),
            'Total_Residual_Value_INR': round(assessed_df['Residual_Value_INR'].sum(), 2),
            'Avg_Health_Score_%': round(assessed_df['Health_Score_%'].mean(), 2),
            'Avg_Operating_Temp_C': round(assessed_df['Avg_Operating_Temp'].mean(), 1),
            'Min_Residual_Value_INR': round(assessed_df['Residual_Value_INR'].min(), 2),
            'Max_Residual_Value_INR': round(assessed_df['Residual_Value_INR'].max(), 2),
        }


def assessment_detail(temp_diff: float) -> str:
    """Helper function for temperature assessment text."""
    if 10 <= temp_diff < 15:
        return "Operated at elevated temp ("
    elif 15 <= temp_diff < 20:
        return "Operated at high temp ("
    else:
        return "Operated at extreme temp ("
