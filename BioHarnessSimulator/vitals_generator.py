"""
Vital signs generator - handles the generation of realistic vital sign values
"""
import random
from typing import Dict, Tuple
from vital_types import VitalSignType, PatientSimulationMode, VitalValueRange
from config_settings import (
    NORMAL_VITAL_RANGES, 
    ABNORMAL_VITAL_RANGES, 
    EMERGENCY_VITAL_RANGES
)


class VitalSignsValueGenerator:
    """
    Generates realistic vital sign values based on simulation mode and custom ranges
    """

    def __init__(self):
        self._predefined_vital_ranges = {
            PatientSimulationMode.NORMAL_HEALTHY_PATIENT: NORMAL_VITAL_RANGES,
            PatientSimulationMode.ABNORMAL_CONDITION_PATIENT: ABNORMAL_VITAL_RANGES,
            PatientSimulationMode.EMERGENCY_CRITICAL_PATIENT: EMERGENCY_VITAL_RANGES
        }
        self._custom_vital_ranges: Dict[VitalSignType, VitalValueRange] = {}

    def set_custom_vital_range(
        self, 
        vital_type: VitalSignType, 
        minimum_value: float, 
        maximum_value: float
    ) -> None:
        """
        Set a custom range for a specific vital sign type
        
        Args:
            vital_type: The type of vital sign to configure
            minimum_value: Minimum acceptable value
            maximum_value: Maximum acceptable value
        """
        if minimum_value >= maximum_value:
            raise ValueError("Minimum value must be less than maximum value")
        
        self._custom_vital_ranges[vital_type] = (minimum_value, maximum_value)

    def remove_custom_vital_range(self, vital_type: VitalSignType) -> bool:
        """
        Remove custom range for a vital sign type, reverting to default ranges
        
        Args:
            vital_type: The type of vital sign to reset
            
        Returns:
            True if custom range was removed, False if no custom range existed
        """
        return self._custom_vital_ranges.pop(vital_type, None) is not None

    def get_vital_range_for_mode(
        self, 
        vital_type: VitalSignType, 
        simulation_mode: PatientSimulationMode
    ) -> VitalValueRange:
        """
        Get the appropriate range for a vital sign based on simulation mode
        
        Args:
            vital_type: The type of vital sign
            simulation_mode: Current simulation mode
            
        Returns:
            Tuple of (minimum_value, maximum_value)
        """
        # Check for custom ranges first
        if vital_type in self._custom_vital_ranges:
            return self._custom_vital_ranges[vital_type]
        
        # Use predefined ranges based on simulation mode
        mode_ranges = self._predefined_vital_ranges[simulation_mode]
        return mode_ranges[vital_type.value]

    def generate_vital_sign_value(
        self, 
        vital_type: VitalSignType, 
        simulation_mode: PatientSimulationMode
    ) -> float:
        """
        Generate a realistic vital sign value based on the current mode
        
        Args:
            vital_type: Type of vital sign to generate
            simulation_mode: Current simulation mode
            
        Returns:
            Generated vital sign value
        """
        minimum_value, maximum_value = self.get_vital_range_for_mode(vital_type, simulation_mode)
        
        if simulation_mode == PatientSimulationMode.NORMAL_HEALTHY_PATIENT:
            return self._generate_normal_patient_value(minimum_value, maximum_value)
        elif simulation_mode == PatientSimulationMode.ABNORMAL_CONDITION_PATIENT:
            return self._generate_abnormal_patient_value(vital_type, minimum_value, maximum_value)
        else:  # EMERGENCY_CRITICAL_PATIENT
            return self._generate_emergency_patient_value(vital_type, minimum_value, maximum_value)

    def _generate_normal_patient_value(self, min_val: float, max_val: float) -> float:
        """
        Generate values for normal/healthy patients - mostly centered with small variations
        """
        center_point = (min_val + max_val) / 2
        variation_range = (max_val - min_val) * 0.15  # 15% variation from center
        
        generated_value = random.uniform(
            center_point - variation_range, 
            center_point + variation_range
        )
        
        # Ensure value stays within bounds
        generated_value = max(min_val, min(max_val, generated_value))
        return round(generated_value, 1)

    def _generate_abnormal_patient_value(
        self, 
        vital_type: VitalSignType, 
        min_val: float, 
        max_val: float
    ) -> float:
        """
        Generate values for abnormal patients - occasional spikes outside normal ranges
        """
        # 30% chance of generating abnormal spike
        if random.random() < 0.3:
            # Generate values at extreme ends of the range
            if random.random() < 0.5:
                # Lower extreme
                spike_range = min_val + (max_val - min_val) * 0.25
                generated_value = random.uniform(min_val, spike_range)
            else:
                # Upper extreme  
                spike_range = max_val - (max_val - min_val) * 0.25
                generated_value = random.uniform(spike_range, max_val)
        else:
            # Generate relatively normal values (70% of the time)
            normal_ranges = NORMAL_VITAL_RANGES[vital_type.value]
            generated_value = random.uniform(normal_ranges[0], normal_ranges[1])
        
        return round(generated_value, 1)

    def _generate_emergency_patient_value(
        self, 
        vital_type: VitalSignType, 
        min_val: float, 
        max_val: float
    ) -> float:
        """
        Generate values for emergency patients - consistently dangerous levels
        """
        # 75% chance of generating critical emergency values
        if random.random() < 0.75:
            # Generate dangerous values at the extremes
            if random.random() < 0.5:
                # Critically low values
                critical_range = min_val + (max_val - min_val) * 0.3
                generated_value = random.uniform(min_val, critical_range)
            else:
                # Critically high values
                critical_range = max_val - (max_val - min_val) * 0.3
                generated_value = random.uniform(critical_range, max_val)
        else:
            # Occasionally return abnormal but not emergency values (25% of time)
            abnormal_ranges = ABNORMAL_VITAL_RANGES[vital_type.value]
            generated_value = random.uniform(abnormal_ranges[0], abnormal_ranges[1])
        
        return round(generated_value, 1)

    def get_all_custom_ranges(self) -> Dict[VitalSignType, VitalValueRange]:
        """
        Get all currently configured custom vital ranges
        
        Returns:
            Dictionary of vital types and their custom ranges
        """
        return self._custom_vital_ranges.copy()

    def clear_all_custom_ranges(self) -> None:
        """Clear all custom vital ranges, reverting to default behavior"""
        self._custom_vital_ranges.clear()