"""
Main simulation engine that coordinates vital signs generation and broadcasting
"""
import threading
import time
from typing import Optional, List, Callable
from datetime import datetime

from vital_types import VitalSignType, PatientSimulationMode
from data_models import PatientVitalSigns, SimulatorConfiguration
from vitals_generator import VitalSignsValueGenerator
from config_settings import (
    DEFAULT_SIMULATION_INTERVAL_SECONDS,
    DEFAULT_PATIENT_IDENTIFIER,
    DEFAULT_DEVICE_IDENTIFIER,
    MINIMUM_SIMULATION_INTERVAL_SECONDS
)


class PatientVitalsSimulationEngine:
    """
    Main engine that orchestrates the generation and broadcasting of patient vital signs
    """

    def __init__(self):
        self._current_simulation_mode = PatientSimulationMode.NORMAL_HEALTHY_PATIENT
        self._data_generation_interval_seconds = DEFAULT_SIMULATION_INTERVAL_SECONDS
        self._target_patient_identifier = DEFAULT_PATIENT_IDENTIFIER
        self._monitoring_device_identifier = DEFAULT_DEVICE_IDENTIFIER
        
        self._is_continuous_simulation_running = False
        self._simulation_thread: Optional[threading.Thread] = None
        self._thread_safety_lock = threading.Lock()
        
        # Vital signs generator
        self._vital_signs_generator = VitalSignsValueGenerator()
        
        # Current state
        self._most_recent_vital_signs: Optional[PatientVitalSigns] = None
        
        # Callback functions for data broadcasting
        self._data_broadcasting_callbacks: List[Callable[[PatientVitalSigns], None]] = []

    def set_simulation_mode(self, new_mode: PatientSimulationMode) -> None:
        """
        Change the current simulation mode
        
        Args:
            new_mode: The new simulation mode to use
        """
        with self._thread_safety_lock:
            self._current_simulation_mode = new_mode

    def set_data_generation_interval(self, interval_seconds: int) -> None:
        """
        Set the interval between vital signs generations
        
        Args:
            interval_seconds: Time in seconds between data generations (minimum 1)
        """
        if interval_seconds < MINIMUM_SIMULATION_INTERVAL_SECONDS:
            raise ValueError(f"Interval must be at least {MINIMUM_SIMULATION_INTERVAL_SECONDS} seconds")
        
        with self._thread_safety_lock:
            self._data_generation_interval_seconds = interval_seconds

    def set_patient_identifier(self, patient_id: str) -> None:
        """Set the identifier for the patient being simulated"""
        with self._thread_safety_lock:
            self._target_patient_identifier = patient_id

    def set_device_identifier(self, device_id: str) -> None:
        """Set the identifier for the monitoring device"""
        with self._thread_safety_lock:
            self._monitoring_device_identifier = device_id

    def add_data_broadcasting_callback(
        self, 
        callback_function: Callable[[PatientVitalSigns], None]
    ) -> None:
        """
        Add a callback function that will be called whenever new vital signs are generated
        
        Args:
            callback_function: Function that takes PatientVitalSigns as parameter
        """
        self._data_broadcasting_callbacks.append(callback_function)

    def remove_data_broadcasting_callback(
        self, 
        callback_function: Callable[[PatientVitalSigns], None]
    ) -> bool:
        """
        Remove a previously added callback function
        
        Returns:
            True if callback was found and removed, False otherwise
        """
        try:
            self._data_broadcasting_callbacks.remove(callback_function)
            return True
        except ValueError:
            return False

    def set_custom_vital_sign_range(
        self, 
        vital_type: VitalSignType, 
        minimum_value: float, 
        maximum_value: float
    ) -> None:
        """
        Set a custom range for a specific vital sign type
        
        Args:
            vital_type: Type of vital sign to configure
            minimum_value: Minimum value in the custom range
            maximum_value: Maximum value in the custom range
        """
        self._vital_signs_generator.set_custom_vital_range(
            vital_type, minimum_value, maximum_value
        )

    def remove_custom_vital_sign_range(self, vital_type: VitalSignType) -> bool:
        """
        Remove custom range for a vital sign type
        
        Returns:
            True if custom range was removed, False if no custom range existed
        """
        return self._vital_signs_generator.remove_custom_vital_range(vital_type)

    def generate_single_vital_signs_reading(self) -> PatientVitalSigns:
        """
        Generate a single vital signs reading based on current configuration
        
        Returns:
            Complete vital signs reading
        """
        # Generate individual vital sign values
        heart_rate = int(self._vital_signs_generator.generate_vital_sign_value(
            VitalSignType.HEART_RATE, self._current_simulation_mode
        ))
        
        bp_systolic = int(self._vital_signs_generator.generate_vital_sign_value(
            VitalSignType.BLOOD_PRESSURE_SYSTOLIC, self._current_simulation_mode
        ))
        
        bp_diastolic = int(self._vital_signs_generator.generate_vital_sign_value(
            VitalSignType.BLOOD_PRESSURE_DIASTOLIC, self._current_simulation_mode
        ))
        
        oxygen_saturation = int(self._vital_signs_generator.generate_vital_sign_value(
            VitalSignType.OXYGEN_SATURATION, self._current_simulation_mode
        ))
        
        body_temperature = self._vital_signs_generator.generate_vital_sign_value(
            VitalSignType.BODY_TEMPERATURE, self._current_simulation_mode
        )
        
        respiratory_rate = int(self._vital_signs_generator.generate_vital_sign_value(
            VitalSignType.RESPIRATORY_RATE, self._current_simulation_mode
        ))

        # Create vital signs reading
        vital_signs = PatientVitalSigns.create_current_timestamp_reading(
            heart_rate=heart_rate,
            bp_systolic=bp_systolic,
            bp_diastolic=bp_diastolic,
            spo2=oxygen_saturation,
            temperature=body_temperature,
            respiratory_rate=respiratory_rate,
            mode=self._current_simulation_mode,
            device_id=self._monitoring_device_identifier,
            patient_id=self._target_patient_identifier
        )

        # Store as most recent reading
        with self._thread_safety_lock:
            self._most_recent_vital_signs = vital_signs

        # Notify all registered callbacks (for broadcasting)
        self._notify_data_broadcasting_callbacks(vital_signs)

        return vital_signs

    def get_most_recent_vital_signs(self) -> Optional[PatientVitalSigns]:
        """
        Get the most recently generated vital signs reading
        
        Returns:
            Most recent vital signs or None if no readings generated yet
        """
        with self._thread_safety_lock:
            return self._most_recent_vital_signs

    def get_current_simulator_configuration(self) -> SimulatorConfiguration:
        """
        Get the current configuration of the simulator
        
        Returns:
            Current simulator configuration
        """
        with self._thread_safety_lock:
            return SimulatorConfiguration(
                current_simulation_mode=self._current_simulation_mode,
                data_generation_interval_seconds=self._data_generation_interval_seconds,
                target_patient_identifier=self._target_patient_identifier,
                monitoring_device_identifier=self._monitoring_device_identifier,
                is_continuous_simulation_active=self._is_continuous_simulation_running,
                custom_vital_ranges=self._vital_signs_generator.get_all_custom_ranges()
            )

    def start_continuous_vital_signs_simulation(self) -> bool:
        """
        Start continuous generation of vital signs at the configured interval
        
        Returns:
            True if simulation started successfully, False if already running
        """
        with self._thread_safety_lock:
            if self._is_continuous_simulation_running:
                return False

            self._is_continuous_simulation_running = True
            self._simulation_thread = threading.Thread(
                target=self._continuous_simulation_loop,
                daemon=True,
                name="VitalSignsSimulationThread"
            )
            self._simulation_thread.start()
            return True

    def stop_continuous_vital_signs_simulation(self) -> bool:
        """
        Stop the continuous generation of vital signs
        
        Returns:
            True if simulation was stopped, False if not running
        """
        with self._thread_safety_lock:
            if not self._is_continuous_simulation_running:
                return False

            self._is_continuous_simulation_running = False
            return True

    def is_simulation_currently_running(self) -> bool:
        """
        Check if continuous simulation is currently active
        
        Returns:
            True if simulation is running, False otherwise
        """
        with self._thread_safety_lock:
            return self._is_continuous_simulation_running

    def _continuous_simulation_loop(self) -> None:
        """
        Main loop for continuous vital signs generation
        Runs in a separate thread and generates data at configured intervals
        """
        while self._is_continuous_simulation_running:
            try:
                self.generate_single_vital_signs_reading()
                time.sleep(self._data_generation_interval_seconds)
            except Exception as exception:
                # Log error but continue simulation
                print(f"Error in simulation loop: {exception}")
                time.sleep(1)  # Brief pause before retrying

    def _notify_data_broadcasting_callbacks(self, vital_signs: PatientVitalSigns) -> None:
        """
        Notify all registered callbacks about new vital signs data
        
        Args:
            vital_signs: The newly generated vital signs data
        """
        for callback_function in self._data_broadcasting_callbacks:
            try:
                callback_function(vital_signs)
            except Exception as exception:
                print(f"Error in data broadcasting callback: {exception}")