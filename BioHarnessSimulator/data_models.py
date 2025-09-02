"""
Data models for vital signs and patient information
"""
from dataclasses import dataclass, asdict
from datetime import datetime
from typing import Optional, Dict, Any
from vital_types import VitalSignType, PatientSimulationMode


@dataclass
class PatientVitalSigns:
    """
    Complete vital signs reading from a patient monitoring device
    """
    timestamp_iso_format: str
    heart_rate_bpm: int
    blood_pressure_systolic_mmhg: int
    blood_pressure_diastolic_mmhg: int
    oxygen_saturation_percentage: int
    body_temperature_celsius: float
    respiratory_rate_per_minute: int
    simulation_mode_used: str
    monitoring_device_identifier: str
    patient_identifier: str
    data_quality_score: Optional[float] = None
    signal_strength_indicator: Optional[int] = None

    def to_dictionary(self) -> Dict[str, Any]:
        """Convert the vital signs data to a dictionary format"""
        return asdict(self)

    def to_json_serializable_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with JSON-serializable values"""
        return {
            "timestamp": self.timestamp_iso_format,
            "vitals": {
                "heart_rate": self.heart_rate_bpm,
                "bp_systolic": self.blood_pressure_systolic_mmhg,
                "bp_diastolic": self.blood_pressure_diastolic_mmhg,
                "spo2": self.oxygen_saturation_percentage,
                "temperature": self.body_temperature_celsius,
                "respiratory_rate": self.respiratory_rate_per_minute
            },
            "metadata": {
                "device_id": self.monitoring_device_identifier,
                "patient_id": self.patient_identifier,
                "mode": self.simulation_mode_used,
                "quality_score": self.data_quality_score,
                "signal_strength": self.signal_strength_indicator
            }
        }

    @classmethod
    def create_current_timestamp_reading(
        cls,
        heart_rate: int,
        bp_systolic: int,
        bp_diastolic: int,
        spo2: int,
        temperature: float,
        respiratory_rate: int,
        mode: PatientSimulationMode,
        device_id: str,
        patient_id: str
    ) -> 'PatientVitalSigns':
        """Create a vital signs reading with current timestamp"""
        return cls(
            timestamp_iso_format=datetime.now().isoformat() + "Z",
            heart_rate_bpm=heart_rate,
            blood_pressure_systolic_mmhg=bp_systolic,
            blood_pressure_diastolic_mmhg=bp_diastolic,
            oxygen_saturation_percentage=spo2,
            body_temperature_celsius=temperature,
            respiratory_rate_per_minute=respiratory_rate,
            simulation_mode_used=mode.value,
            monitoring_device_identifier=device_id,
            patient_identifier=patient_id
        )


@dataclass
class SimulatorConfiguration:
    """
    Configuration settings for the vitals simulator
    """
    current_simulation_mode: PatientSimulationMode
    data_generation_interval_seconds: int
    target_patient_identifier: str
    monitoring_device_identifier: str
    is_continuous_simulation_active: bool
    custom_vital_ranges: Dict[VitalSignType, tuple]

    def to_dictionary(self) -> Dict[str, Any]:
        """Convert configuration to dictionary format"""
        return {
            "mode": self.current_simulation_mode.value,
            "interval_seconds": self.data_generation_interval_seconds,
            "patient_id": self.target_patient_identifier,
            "device_id": self.monitoring_device_identifier,
            "is_running": self.is_continuous_simulation_active,
            "custom_ranges": {
                vital_type.value: range_tuple 
                for vital_type, range_tuple in self.custom_vital_ranges.items()
            }
        }


@dataclass
class VitalSignsRangeConfiguration:
    """
    Configuration for valid ranges of each vital sign type
    """
    vital_sign_type: VitalSignType
    minimum_acceptable_value: float
    maximum_acceptable_value: float
    measurement_unit: str

    def is_value_within_range(self, value: float) -> bool:
        """Check if a value falls within the acceptable range"""
        return self.minimum_acceptable_value <= value <= self.maximum_acceptable_value

    def to_dictionary(self) -> Dict[str, Any]:
        """Convert range configuration to dictionary"""
        return {
            "vital_type": self.vital_sign_type.value,
            "min_value": self.minimum_acceptable_value,
            "max_value": self.maximum_acceptable_value,
            "unit": self.measurement_unit
        }


@dataclass
class BroadcastingResult:
    """
    Result of attempting to broadcast vital signs data
    """
    destination_name: str
    was_successful: bool
    error_message: Optional[str] = None
    response_status_code: Optional[int] = None
    transmission_timestamp: Optional[str] = None

    def to_dictionary(self) -> Dict[str, Any]:
        """Convert broadcasting result to dictionary"""
        return asdict(self)