"""
Vital signs enumeration and type definitions
"""
from enum import Enum
from typing import Tuple, Dict


class VitalSignType(str, Enum):
    """
    Enumeration of supported vital sign types that can be monitored
    """
    HEART_RATE = "heart_rate"
    BLOOD_PRESSURE_SYSTOLIC = "bp_systolic"
    BLOOD_PRESSURE_DIASTOLIC = "bp_diastolic"
    OXYGEN_SATURATION = "spo2"
    BODY_TEMPERATURE = "temperature"
    RESPIRATORY_RATE = "respiratory_rate"


class PatientSimulationMode(str, Enum):
    """
    Simulation modes that determine the range and behavior of generated vitals
    """
    NORMAL_HEALTHY_PATIENT = "normal"
    ABNORMAL_CONDITION_PATIENT = "abnormal"
    EMERGENCY_CRITICAL_PATIENT = "emergency"


class VitalSignRangeType(str, Enum):
    """
    Types of vital sign ranges for different patient conditions
    """
    NORMAL_RANGE = "normal"
    ABNORMAL_RANGE = "abnormal"
    EMERGENCY_RANGE = "emergency"


class BroadcastingDestination(str, Enum):
    """
    Destinations where vital data can be broadcast
    """
    RULE_ENGINE = "rule_engine"
    USER_INTERFACE = "user_interface"
    BOTH_DESTINATIONS = "both"


# Type aliases for better code readability
VitalValueRange = Tuple[float, float]  # (min_value, max_value)
VitalRangesConfiguration = Dict[VitalSignType, VitalValueRange]
CustomVitalRanges = Dict[VitalSignType, VitalValueRange]