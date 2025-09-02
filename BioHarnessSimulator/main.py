#!/usr/bin/env python3
"""
Main entry point for the BioHarness Vitals Simulator

This application simulates patient vital signs similar to the BioHarness device,
with configurable modes and automatic broadcasting to rule engines and UI systems.
"""

import signal
import sys
import time
from typing import Optional

# Import our application components
from http_server import VitalsSimulatorHTTPServer
from logger_config import (
    setup_application_logging,
    log_application_startup,
    log_application_shutdown,
    log_vital_signs_generation,
    log_broadcasting_result
)
from config_settings import HTTP_SERVER_HOST, HTTP_SERVER_PORT
from vital_types import PatientSimulationMode


class BioHarnessVitalsSimulatorApplication:
    """
    Main application class that coordinates all components of the vitals simulator
    """

    def __init__(self):
        # Set up logging
        self.application_logger = setup_application_logging("BioHarnessSimulator")
        
        # Initialize HTTP server
        self.http_server = VitalsSimulatorHTTPServer(
            host=HTTP_SERVER_HOST,
            port=HTTP_SERVER_PORT
        )
        
        # Application state
        self.is_application_running = False
        
        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._handle_shutdown_signal)
        signal.signal(signal.SIGTERM, self._handle_shutdown_signal)

    def start_application(self) -> bool:
        """
        Start the BioHarness Vitals Simulator application
        
        Returns:
            True if application started successfully, False otherwise
        """
        try:
            # Start the HTTP server
            server_started = self.http_server.start_server()
            if not server_started:
                self.application_logger.error("Failed to start HTTP server")
                return False
            
            # Set up data broadcasting callbacks for logging
            simulation_engine = self.http_server.get_simulation_engine()
            simulation_engine.add_data_broadcasting_callback(self._log_vital_signs_callback)
            
            # Log successful startup
            server_url = self.http_server.get_server_url()
            log_application_startup(self.application_logger, server_url)
            
            self.is_application_running = True
            return True
            
        except Exception as e:
            self.application_logger.error(f"Failed to start application: {str(e)}")
            return False

    def stop_application(self):
        """Stop the application gracefully"""
        if self.is_application_running:
            log_application_shutdown(self.application_logger)
            
            # Stop the HTTP server (this also stops any running simulation)
            self.http_server.stop_server()
            
            self.is_application_running = False
            self.application_logger.info("Application stopped successfully")

    def run_application_main_loop(self):
        """
        Run the main application loop
        Keeps the application running until shutdown signal is received
        """
        if not self.is_application_running:
            self.application_logger.error("Application not started. Call start_application() first.")
            return

        try:
            self.application_logger.info("Application is running. Press Ctrl+C to stop.")
            
            # Main application loop - just keep the application alive
            while self.is_application_running:
                time.sleep(1)
                
        except KeyboardInterrupt:
            self.application_logger.info("Received keyboard interrupt")
        finally:
            self.stop_application()

    def demonstrate_simulator_capabilities(self):
        """
        Run a demonstration of the simulator's capabilities
        """
        if not self.is_application_running:
            self.application_logger.warning("Start application first to run demonstration")
            return

        self.application_logger.info("Starting simulator capabilities demonstration...")
        
        simulation_engine = self.http_server.get_simulation_engine()
        
        # Demonstrate each simulation mode
        demo_modes = [
            PatientSimulationMode.NORMAL_HEALTHY_PATIENT,
            PatientSimulationMode.ABNORMAL_CONDITION_PATIENT,
            PatientSimulationMode.EMERGENCY_CRITICAL_PATIENT
        ]
        
        for mode in demo_modes:
            self.application_logger.info(f"Demonstrating {mode.value} mode...")
            simulation_engine.set_simulation_mode(mode)
            
            # Generate 3 sample readings for each mode
            for sample_number in range(3):
                vital_signs = simulation_engine.generate_single_vital_signs_reading()
                self.application_logger.info(
                    f"Sample {sample_number + 1}: "
                    f"HR={vital_signs.heart_rate_bpm}, "
                    f"BP={vital_signs.blood_pressure_systolic_mmhg}/"
                    f"{vital_signs.blood_pressure_diastolic_mmhg}, "
                    f"SpO2={vital_signs.oxygen_saturation_percentage}%, "
                    f"Temp={vital_signs.body_temperature_celsius}°C, "
                    f"RR={vital_signs.respiratory_rate_per_minute}"
                )
                time.sleep(1)  # Small delay between samples
        
        # Reset to normal mode after demonstration
        simulation_engine.set_simulation_mode(PatientSimulationMode.NORMAL_HEALTHY_PATIENT)
        self.application_logger.info("Demonstration completed. Reset to normal mode.")

    def _handle_shutdown_signal(self, signal_number, frame):
        """
        Handle shutdown signals (SIGINT, SIGTERM)
        
        Args:
            signal_number: Signal number received
            frame: Current stack frame
        """
        self.application_logger.info(f"Received shutdown signal {signal_number}")
        self.is_application_running = False

    def _log_vital_signs_callback(self, vital_signs_data):
        """
        Callback function to log vital signs generation
        
        Args:
            vital_signs_data: Generated vital signs data
        """
        log_vital_signs_generation(
            self.application_logger,
            vital_signs_data,
            vital_signs_data.simulation_mode_used
        )


def print_application_banner():
    """Print application startup banner"""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║             BioHarness Vitals Simulator v1.0                ║
    ║                                                              ║
    ║     Simulates patient vital signs with configurable modes   ║
    ║     Broadcasts data to rule engines and UI systems          ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    print(banner)


def print_usage_information():
    """Print usage information and available API endpoints"""
    usage_info = """
    🚀 Server Configuration:
       • HTTP API Server: http://localhost:8000
       • Health Check: GET /api/health
       • Current Vitals: GET /api/vitals/current
       • Generate Reading: GET /api/vitals/single
    
    🎛️  Configuration Endpoints:
       • Set Mode: POST /api/simulator/mode {"mode": "normal|abnormal|emergency"}
       • Set Interval: POST /api/simulator/interval {"interval_seconds": 10}
       • Start Simulation: POST /api/simulator/start
       • Stop Simulation: POST /api/simulator/stop
    
    📊 Vital Signs Monitored:
       • Heart Rate (bpm)
       • Blood Pressure (mmHg) - Systolic/Diastolic
       • Oxygen Saturation (%)
       • Body Temperature (°C)
       • Respiratory Rate (per minute)
    
    📱 Integration:
       • iOS App: Connect to HTTP API endpoints
       • Rule Engine: Automatic broadcasting of vital data
       • UI Systems: Real-time data streaming
    
    Press Ctrl+C to stop the simulator
    """
    print(usage_info)


def main():
    """Main entry point of the application"""
    print_application_banner()
    
    # Create and start the application
    simulator_application = BioHarnessVitalsSimulatorApplication()
    
    # Start the application
    application_started = simulator_application.start_application()
    if not application_started:
        print("❌ Failed to start the BioHarness Vitals Simulator")
        sys.exit(1)
    
    # Print usage information
    print_usage_information()
    
    # Optionally run a quick demonstration
    if len(sys.argv) > 1 and sys.argv[1] == "--demo":
        simulator_application.demonstrate_simulator_capabilities()
    
    # Run the main application loop
    try:
        simulator_application.run_application_main_loop()
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        simulator_application.stop_application()
        sys.exit(1)
    
    print("\n✅ BioHarness Vitals Simulator stopped successfully")


if __name__ == "__main__":
    main()