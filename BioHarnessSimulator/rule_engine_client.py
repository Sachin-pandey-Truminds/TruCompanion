"""
Rule Engine Client - specialized client for communicating with the rule engine
"""
import json
from typing import Dict, Any, Optional
from datetime import datetime

from data_broadcaster import VitalSignsDataBroadcaster
from data_models import PatientVitalSigns, BroadcastingResult


class RuleEngineIntegrationClient:
    """
    Specialized client for integrating with the TruHeal rule engine system
    """

    def __init__(self, rule_engine_base_url: str = None, vitals_endpoint: str = None):
        """
        Initialize the rule engine client
        
        Args:
            rule_engine_base_url: Base URL of the rule engine service
            vitals_endpoint: Specific endpoint for vitals data submission
        """
        self._data_broadcaster = VitalSignsDataBroadcaster()
        
        if rule_engine_base_url and vitals_endpoint:
            self._data_broadcaster.set_rule_engine_endpoint(rule_engine_base_url, vitals_endpoint)

    def submit_vital_signs_for_rule_evaluation(
        self, 
        patient_vital_signs: PatientVitalSigns
    ) -> BroadcastingResult:
        """
        Submit vital signs data to the rule engine for evaluation and processing
        
        Args:
            patient_vital_signs: Complete vital signs reading to evaluate
            
        Returns:
            Result of the submission attempt
        """
        # Format data specifically for rule engine consumption
        rule_engine_payload = self._format_vital_signs_for_rule_engine(patient_vital_signs)
        
        # Add rule engine specific metadata
        rule_engine_payload.update({
            "submission_source": "BioHarness_Vitals_Simulator",
            "requires_immediate_processing": self._determine_urgency_level(patient_vital_signs),
            "data_quality_indicators": {
                "signal_strength": patient_vital_signs.signal_strength_indicator or 100,
                "data_completeness": 100,  # Simulator always provides complete data
                "measurement_confidence": patient_vital_signs.data_quality_score or 0.95
            }
        })
        
        return self._data_broadcaster.broadcast_to_rule_engine(patient_vital_signs)

    def test_rule_engine_connection_and_authentication(self) -> BroadcastingResult:
        """
        Test the connection to the rule engine and verify authentication
        
        Returns:
            Result of the connection test
        """
        return self._data_broadcaster.test_rule_engine_connectivity()

    def configure_rule_engine_endpoints(
        self, 
        base_url: str, 
        vitals_submission_endpoint: str
    ) -> None:
        """
        Configure the rule engine connection endpoints
        
        Args:
            base_url: Base URL of the rule engine service
            vitals_submission_endpoint: Endpoint path for submitting vitals data
        """
        self._data_broadcaster.set_rule_engine_endpoint(base_url, vitals_submission_endpoint)

    def enable_rule_engine_integration(self, is_enabled: bool = True) -> None:
        """
        Enable or disable rule engine integration
        
        Args:
            is_enabled: True to enable integration, False to disable
        """
        self._data_broadcaster.enable_rule_engine_broadcasting(is_enabled)

    def _format_vital_signs_for_rule_engine(
        self, 
        vital_signs: PatientVitalSigns
    ) -> Dict[str, Any]:
        """
        Format vital signs data in the format expected by the rule engine
        
        Args:
            vital_signs: Raw vital signs data
            
        Returns:
            Formatted data dictionary for rule engine consumption
        """
        return {
            "deviceId": vital_signs.monitoring_device_identifier,
            "patientId": vital_signs.patient_identifier,
            "timestamp": vital_signs.timestamp_iso_format,
            "readings": {
                "heartRate": vital_signs.heart_rate_bpm,
                "bloodPressure": {
                    "systolic": vital_signs.blood_pressure_systolic_mmhg,
                    "diastolic": vital_signs.blood_pressure_diastolic_mmhg
                },
                "oxygenSaturation": vital_signs.oxygen_saturation_percentage,
                "bodyTemperature": vital_signs.body_temperature_celsius,
                "respiratoryRate": vital_signs.respiratory_rate_per_minute
            },
            "metadata": {
                "simulationMode": vital_signs.simulation_mode_used,
                "generatedAt": datetime.now().isoformat(),
                "dataSource": "BioHarness_Simulator"
            }
        }

    def _determine_urgency_level(self, vital_signs: PatientVitalSigns) -> bool:
        """
        Determine if the vital signs require immediate processing based on values
        
        Args:
            vital_signs: Vital signs data to analyze
            
        Returns:
            True if urgent processing is needed, False otherwise
        """
        # Define critical thresholds that require immediate attention
        critical_thresholds = {
            "heart_rate_critical_low": 40,
            "heart_rate_critical_high": 150,
            "bp_systolic_critical_low": 70,
            "bp_systolic_critical_high": 180,
            "oxygen_saturation_critical": 85,
            "temperature_critical_low": 35.0,
            "temperature_critical_high": 40.0,
            "respiratory_rate_critical_low": 8,
            "respiratory_rate_critical_high": 30
        }

        # Check for critical values
        if (vital_signs.heart_rate_bpm < critical_thresholds["heart_rate_critical_low"] or
            vital_signs.heart_rate_bpm > critical_thresholds["heart_rate_critical_high"]):
            return True

        if (vital_signs.blood_pressure_systolic_mmhg < critical_thresholds["bp_systolic_critical_low"] or
            vital_signs.blood_pressure_systolic_mmhg > critical_thresholds["bp_systolic_critical_high"]):
            return True

        if vital_signs.oxygen_saturation_percentage < critical_thresholds["oxygen_saturation_critical"]:
            return True

        if (vital_signs.body_temperature_celsius < critical_thresholds["temperature_critical_low"] or
            vital_signs.body_temperature_celsius > critical_thresholds["temperature_critical_high"]):
            return True

        if (vital_signs.respiratory_rate_per_minute < critical_thresholds["respiratory_rate_critical_low"] or
            vital_signs.respiratory_rate_per_minute > critical_thresholds["respiratory_rate_critical_high"]):
            return True

        # Check if simulation mode indicates emergency
        if vital_signs.simulation_mode_used == "emergency":
            return True

        return False