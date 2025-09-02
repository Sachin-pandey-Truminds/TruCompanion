"""
Logging configuration for the BioHarness Vitals Simulator
"""
import logging
import sys
from datetime import datetime
from config_settings import (
    LOG_LEVEL,
    LOG_FORMAT,
    LOG_FILE_PATH,
    ENABLE_CONSOLE_LOGGING,
    ENABLE_FILE_LOGGING
)


def setup_application_logging(logger_name: str = "BioHarnessSimulator") -> logging.Logger:
    """
    Set up logging configuration for the application
    
    Args:
        logger_name: Name for the logger instance
        
    Returns:
        Configured logger instance
    """
    # Create logger
    application_logger = logging.getLogger(logger_name)
    application_logger.setLevel(getattr(logging, LOG_LEVEL.upper()))
    
    # Clear any existing handlers
    application_logger.handlers.clear()
    
    # Create formatter
    log_formatter = logging.Formatter(LOG_FORMAT)
    
    # Add console handler if enabled
    if ENABLE_CONSOLE_LOGGING:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
        console_handler.setFormatter(log_formatter)
        application_logger.addHandler(console_handler)
    
    # Add file handler if enabled
    if ENABLE_FILE_LOGGING:
        try:
            file_handler = logging.FileHandler(LOG_FILE_PATH, mode='a')
            file_handler.setLevel(getattr(logging, LOG_LEVEL.upper()))
            file_handler.setFormatter(log_formatter)
            application_logger.addHandler(file_handler)
        except (OSError, IOError) as e:
            print(f"Warning: Could not create log file {LOG_FILE_PATH}: {e}")
    
    return application_logger


def log_vital_signs_generation(logger: logging.Logger, vital_signs_data, simulation_mode: str):
    """
    Log vital signs generation with proper formatting
    
    Args:
        logger: Logger instance
        vital_signs_data: Generated vital signs data
        simulation_mode: Current simulation mode
    """
    logger.info(
        f"Generated Vitals | Mode: {simulation_mode} | "
        f"HR: {vital_signs_data.heart_rate_bpm} bpm | "
        f"BP: {vital_signs_data.blood_pressure_systolic_mmhg}/"
        f"{vital_signs_data.blood_pressure_diastolic_mmhg} mmHg | "
        f"SpO2: {vital_signs_data.oxygen_saturation_percentage}% | "
        f"Temp: {vital_signs_data.body_temperature_celsius}°C | "
        f"RR: {vital_signs_data.respiratory_rate_per_minute}/min | "
        f"Patient: {vital_signs_data.patient_identifier}"
    )


def log_broadcasting_result(logger: logging.Logger, broadcasting_result):
    """
    Log the result of broadcasting vital signs data
    
    Args:
        logger: Logger instance
        broadcasting_result: Result of the broadcasting attempt
    """
    if broadcasting_result.was_successful:
        logger.info(
            f"Successfully broadcast vitals to {broadcasting_result.destination_name} "
            f"(Status: {broadcasting_result.response_status_code})"
        )
    else:
        logger.warning(
            f"Failed to broadcast vitals to {broadcasting_result.destination_name}: "
            f"{broadcasting_result.error_message}"
        )


def log_simulation_mode_change(logger: logging.Logger, old_mode: str, new_mode: str):
    """
    Log simulation mode changes
    
    Args:
        logger: Logger instance
        old_mode: Previous simulation mode
        new_mode: New simulation mode
    """
    logger.info(f"Simulation mode changed from '{old_mode}' to '{new_mode}'")


def log_configuration_change(logger: logging.Logger, parameter_name: str, old_value, new_value):
    """
    Log configuration parameter changes
    
    Args:
        logger: Logger instance
        parameter_name: Name of the parameter that changed
        old_value: Previous value
        new_value: New value
    """
    logger.info(
        f"Configuration changed | {parameter_name}: {old_value} → {new_value}"
    )


def log_api_request(logger: logging.Logger, method: str, endpoint: str, client_ip: str = None):
    """
    Log API requests
    
    Args:
        logger: Logger instance
        method: HTTP method
        endpoint: API endpoint path
        client_ip: Client IP address if available
    """
    client_info = f" from {client_ip}" if client_ip else ""
    logger.debug(f"API Request: {method} {endpoint}{client_info}")


def log_application_startup(logger: logging.Logger, server_url: str):
    """
    Log application startup information
    
    Args:
        logger: Logger instance
        server_url: URL where the server is running
    """
    logger.info("=" * 60)
    logger.info("BioHarness Vitals Simulator Starting Up")
    logger.info("=" * 60)
    logger.info(f"Server URL: {server_url}")
    logger.info(f"Start Time: {datetime.now().isoformat()}")
    logger.info("Ready to simulate patient vital signs")
    logger.info("=" * 60)


def log_application_shutdown(logger: logging.Logger):
    """
    Log application shutdown
    
    Args:
        logger: Logger instance
    """
    logger.info("=" * 60)
    logger.info("BioHarness Vitals Simulator Shutting Down")
    logger.info(f"Shutdown Time: {datetime.now().isoformat()}")
    logger.info("=" * 60)