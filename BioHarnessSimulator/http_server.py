"""
HTTP Server for the Vitals Simulator API
"""
import json
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Optional, Dict, Any

from simulation_engine import PatientVitalsSimulationEngine
from data_broadcaster import VitalSignsDataBroadcaster
from rule_engine_client import RuleEngineIntegrationClient
from vital_types import VitalSignType, PatientSimulationMode
from data_models import PatientVitalSigns
from config_settings import HTTP_SERVER_HOST, HTTP_SERVER_PORT


class VitalsSimulatorHTTPRequestHandler(BaseHTTPRequestHandler):
    """
    HTTP request handler for the vitals simulator API endpoints
    """
    
    # Class-level references to shared components
    simulation_engine: Optional[PatientVitalsSimulationEngine] = None
    data_broadcaster: Optional[VitalSignsDataBroadcaster] = None
    rule_engine_client: Optional[RuleEngineIntegrationClient] = None

    def _set_cors_headers_for_cross_origin_requests(self):
        """Set CORS headers to allow cross-origin requests from web browsers and mobile apps"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Requested-With')

    def _send_json_response_with_status(self, response_data: Dict[str, Any], status_code: int = 200):
        """
        Send a JSON response with appropriate headers
        
        Args:
            response_data: Data to send as JSON
            status_code: HTTP status code
        """
        self.send_response(status_code)
        self._set_cors_headers_for_cross_origin_requests()
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.end_headers()
        
        json_response = json.dumps(response_data, default=str, indent=2)
        self.wfile.write(json_response.encode('utf-8'))

    def _send_error_response_with_message(self, error_message: str, status_code: int = 400):
        """
        Send an error response with message
        
        Args:
            error_message: Error description
            status_code: HTTP error status code
        """
        error_response = {
            "error": error_message,
            "status": "failed",
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(error_response, status_code)

    def _get_current_iso_timestamp(self) -> str:
        """Get current timestamp in ISO format"""
        from datetime import datetime
        return datetime.now().isoformat() + "Z"

    def _parse_request_body_as_json(self) -> Dict[str, Any]:
        """
        Parse the request body as JSON
        
        Returns:
            Parsed JSON data or empty dict if no body
            
        Raises:
            ValueError: If JSON is invalid
        """
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            return {}
        
        request_body = self.rfile.read(content_length).decode('utf-8')
        try:
            return json.loads(request_body)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in request body: {str(e)}")

    def do_OPTIONS(self):
        """Handle preflight OPTIONS requests for CORS"""
        self.send_response(200)
        self._set_cors_headers_for_cross_origin_requests()
        self.end_headers()

    def do_GET(self):
        """Handle GET requests for retrieving data and status"""
        parsed_url = urlparse(self.path)
        endpoint_path = parsed_url.path
        
        try:
            if endpoint_path == '/api/health':
                self._handle_health_check_request()
            elif endpoint_path == '/api/vitals/current':
                self._handle_get_current_vitals_request()
            elif endpoint_path == '/api/vitals/single':
                self._handle_generate_single_vitals_request()
            elif endpoint_path == '/api/simulator/config':
                self._handle_get_simulator_configuration_request()
            elif endpoint_path == '/api/vitals/ranges':
                self._handle_get_vital_ranges_request()
            elif endpoint_path == '/api/simulator/status':
                self._handle_get_simulation_status_request()
            else:
                self._send_error_response_with_message("API endpoint not found", 404)
                
        except Exception as e:
            self._send_error_response_with_message(f"Internal server error: {str(e)}", 500)

    def do_POST(self):
        """Handle POST requests for configuration and control"""
        parsed_url = urlparse(self.path)
        endpoint_path = parsed_url.path
        
        try:
            request_data = self._parse_request_body_as_json()
            
            if endpoint_path == '/api/simulator/mode':
                self._handle_set_simulation_mode_request(request_data)
            elif endpoint_path == '/api/simulator/interval':
                self._handle_set_simulation_interval_request(request_data)
            elif endpoint_path == '/api/simulator/start':
                self._handle_start_continuous_simulation_request()
            elif endpoint_path == '/api/simulator/stop':
                self._handle_stop_continuous_simulation_request()
            elif endpoint_path == '/api/vitals/custom-range':
                self._handle_set_custom_vital_range_request(request_data)
            elif endpoint_path == '/api/simulator/patient':
                self._handle_set_patient_identifier_request(request_data)
            elif endpoint_path == '/api/connectivity/test':
                self._handle_test_connectivity_request()
            else:
                self._send_error_response_with_message("API endpoint not found", 404)
                
        except ValueError as e:
            self._send_error_response_with_message(str(e), 400)
        except Exception as e:
            self._send_error_response_with_message(f"Internal server error: {str(e)}", 500)

    def do_DELETE(self):
        """Handle DELETE requests for removing configurations"""
        parsed_url = urlparse(self.path)
        path_segments = parsed_url.path.split('/')
        
        try:
            if len(path_segments) >= 5 and path_segments[3] == "custom-range":
                vital_type_name = path_segments[4]
                self._handle_remove_custom_vital_range_request(vital_type_name)
            else:
                self._send_error_response_with_message("API endpoint not found", 404)
                
        except Exception as e:
            self._send_error_response_with_message(f"Internal server error: {str(e)}", 500)

    # GET request handlers
    def _handle_health_check_request(self):
        """Handle health check requests"""
        health_status = {
            "status": "healthy",
            "service": "BioHarness Vitals Simulator",
            "version": "1.0.0",
            "timestamp": self._get_current_iso_timestamp(),
            "uptime_info": "Service is operational"
        }
        self._send_json_response_with_status(health_status)

    def _handle_get_current_vitals_request(self):
        """Handle requests for current vital signs"""
        current_vitals = self.simulation_engine.get_most_recent_vital_signs()
        if current_vitals:
            response_data = {
                "status": "success",
                "vital_signs": current_vitals.to_dictionary(),
                "timestamp": self._get_current_iso_timestamp()
            }
        else:
            response_data = {
                "status": "no_data",
                "message": "No vital signs have been generated yet",
                "timestamp": self._get_current_iso_timestamp()
            }
        self._send_json_response_with_status(response_data)

    def _handle_generate_single_vitals_request(self):
        """Handle requests to generate a single vital signs reading"""
        vital_signs = self.simulation_engine.generate_single_vital_signs_reading()
        response_data = {
            "status": "success",
            "vital_signs": vital_signs.to_dictionary(),
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(response_data)

    def _handle_get_simulator_configuration_request(self):
        """Handle requests for current simulator configuration"""
        configuration = self.simulation_engine.get_current_simulator_configuration()
        response_data = {
            "status": "success",
            "configuration": configuration.to_dictionary(),
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(response_data)

    def _handle_get_vital_ranges_request(self):
        """Handle requests for vital sign ranges"""
        from config_settings import NORMAL_VITAL_RANGES, ABNORMAL_VITAL_RANGES, EMERGENCY_VITAL_RANGES
        
        ranges_data = {
            "status": "success",
            "vital_ranges": {
                "normal_healthy_patient": NORMAL_VITAL_RANGES,
                "abnormal_condition_patient": ABNORMAL_VITAL_RANGES,
                "emergency_critical_patient": EMERGENCY_VITAL_RANGES
            },
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(ranges_data)

    def _handle_get_simulation_status_request(self):
        """Handle requests for simulation status"""
        is_running = self.simulation_engine.is_simulation_currently_running()
        config = self.simulation_engine.get_current_simulator_configuration()
        
        status_data = {
            "status": "success",
            "simulation_status": {
                "is_running": is_running,
                "current_mode": config.current_simulation_mode.value,
                "interval_seconds": config.data_generation_interval_seconds,
                "patient_id": config.target_patient_identifier
            },
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(status_data)

    # POST request handlers
    def _handle_set_simulation_mode_request(self, request_data: Dict[str, Any]):
        """Handle requests to set simulation mode"""
        mode_value = request_data.get('mode', '').lower()
        valid_modes = [mode.value for mode in PatientSimulationMode]
        
        if mode_value not in valid_modes:
            self._send_error_response_with_message(
                f"Invalid simulation mode. Valid modes: {valid_modes}", 400
            )
            return
        
        new_mode = PatientSimulationMode(mode_value)
        self.simulation_engine.set_simulation_mode(new_mode)
        
        response_data = {
            "status": "success",
            "message": f"Simulation mode changed to {mode_value}",
            "new_mode": mode_value,
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(response_data)

    def _handle_set_simulation_interval_request(self, request_data: Dict[str, Any]):
        """Handle requests to set simulation interval"""
        interval_seconds = request_data.get('interval_seconds')
        
        if not isinstance(interval_seconds, int) or interval_seconds < 1:
            self._send_error_response_with_message(
                "Invalid interval. Must be a positive integer (minimum 1 second)", 400
            )
            return
        
        self.simulation_engine.set_data_generation_interval(interval_seconds)
        
        response_data = {
            "status": "success",
            "message": f"Simulation interval changed to {interval_seconds} seconds",
            "new_interval_seconds": interval_seconds,
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(response_data)

    def _handle_start_continuous_simulation_request(self):
        """Handle requests to start continuous simulation"""
        was_started = self.simulation_engine.start_continuous_vital_signs_simulation()
        
        if was_started:
            response_data = {
                "status": "success",
                "message": "Continuous vital signs simulation started",
                "is_running": True,
                "timestamp": self._get_current_iso_timestamp()
            }
        else:
            response_data = {
                "status": "already_running",
                "message": "Simulation is already running",
                "is_running": True,
                "timestamp": self._get_current_iso_timestamp()
            }
        
        self._send_json_response_with_status(response_data)

    def _handle_stop_continuous_simulation_request(self):
        """Handle requests to stop continuous simulation"""
        was_stopped = self.simulation_engine.stop_continuous_vital_signs_simulation()
        
        if was_stopped:
            response_data = {
                "status": "success",
                "message": "Continuous vital signs simulation stopped",
                "is_running": False,
                "timestamp": self._get_current_iso_timestamp()
            }
        else:
            response_data = {
                "status": "not_running",
                "message": "Simulation was not running",
                "is_running": False,
                "timestamp": self._get_current_iso_timestamp()
            }
        
        self._send_json_response_with_status(response_data)

    def _handle_set_custom_vital_range_request(self, request_data: Dict[str, Any]):
        """Handle requests to set custom vital ranges"""
        vital_type_name = request_data.get('vital_type')
        minimum_value = request_data.get('min_value')
        maximum_value = request_data.get('max_value')
        
        # Validate vital type
        valid_vital_types = [vt.value for vt in VitalSignType]
        if vital_type_name not in valid_vital_types:
            self._send_error_response_with_message(
                f"Invalid vital type. Valid types: {valid_vital_types}", 400
            )
            return
        
        # Validate range values
        if minimum_value is None or maximum_value is None:
            self._send_error_response_with_message(
                "Both min_value and max_value are required", 400
            )
            return
        
        if minimum_value >= maximum_value:
            self._send_error_response_with_message(
                "min_value must be less than max_value", 400
            )
            return
        
        vital_type = VitalSignType(vital_type_name)
        self.simulation_engine.set_custom_vital_sign_range(
            vital_type, float(minimum_value), float(maximum_value)
        )
        
        response_data = {
            "status": "success",
            "message": f"Custom range set for {vital_type_name}",
            "vital_type": vital_type_name,
            "range": [minimum_value, maximum_value],
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(response_data)

    def _handle_set_patient_identifier_request(self, request_data: Dict[str, Any]):
        """Handle requests to set patient identifier"""
        patient_id = request_data.get('patient_id')
        
        if not patient_id or not isinstance(patient_id, str):
            self._send_error_response_with_message(
                "Valid patient_id string is required", 400
            )
            return
        
        self.simulation_engine.set_patient_identifier(patient_id)
        
        response_data = {
            "status": "success",
            "message": f"Patient identifier set to {patient_id}",
            "patient_id": patient_id,
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(response_data)

    def _handle_test_connectivity_request(self):
        """Handle requests to test connectivity to external systems"""
        test_results = {
            "rule_engine": self.rule_engine_client.test_rule_engine_connection_and_authentication(),
            "ui_system": self.data_broadcaster.test_ui_connectivity()
        }
        
        response_data = {
            "status": "success",
            "connectivity_tests": {
                "rule_engine": test_results["rule_engine"].to_dictionary(),
                "ui_system": test_results["ui_system"].to_dictionary()
            },
            "timestamp": self._get_current_iso_timestamp()
        }
        self._send_json_response_with_status(response_data)

    # DELETE request handlers
    def _handle_remove_custom_vital_range_request(self, vital_type_name: str):
        """Handle requests to remove custom vital ranges"""
        valid_vital_types = [vt.value for vt in VitalSignType]
        if vital_type_name not in valid_vital_types:
            self._send_error_response_with_message(
                f"Invalid vital type. Valid types: {valid_vital_types}", 400
            )
            return
        
        vital_type = VitalSignType(vital_type_name)
        was_removed = self.simulation_engine.remove_custom_vital_sign_range(vital_type)
        
        if was_removed:
            response_data = {
                "status": "success",
                "message": f"Custom range removed for {vital_type_name}",
                "vital_type": vital_type_name,
                "timestamp": self._get_current_iso_timestamp()
            }
        else:
            response_data = {
                "status": "not_found",
                "message": f"No custom range was set for {vital_type_name}",
                "vital_type": vital_type_name,
                "timestamp": self._get_current_iso_timestamp()
            }
        
        self._send_json_response_with_status(response_data)


class VitalsSimulatorHTTPServer:
    """
    HTTP server for the vitals simulator with proper lifecycle management
    """

    def __init__(self, host: str = HTTP_SERVER_HOST, port: int = HTTP_SERVER_PORT):
        self.host = host
        self.port = port
        self.http_server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        
        # Initialize core components
        self.simulation_engine = PatientVitalsSimulationEngine()
        self.data_broadcaster = VitalSignsDataBroadcaster()
        self.rule_engine_client = RuleEngineIntegrationClient()
        
        # Set up broadcasting callback
        self.simulation_engine.add_data_broadcasting_callback(self._broadcast_vital_signs_data)
        
        # Configure request handler with component references
        VitalsSimulatorHTTPRequestHandler.simulation_engine = self.simulation_engine
        VitalsSimulatorHTTPRequestHandler.data_broadcaster = self.data_broadcaster
        VitalsSimulatorHTTPRequestHandler.rule_engine_client = self.rule_engine_client

    def _broadcast_vital_signs_data(self, vital_signs: PatientVitalSigns):
        """
        Callback function to broadcast vital signs to external systems
        
        Args:
            vital_signs: Vital signs data to broadcast
        """
        try:
            # Broadcast to all configured destinations
            broadcasting_results = self.data_broadcaster.broadcast_vital_signs_to_all_destinations(
                vital_signs
            )
            
            # Log broadcasting results
            for result in broadcasting_results:
                if result.was_successful:
                    print(f"Successfully broadcast vitals to {result.destination_name}")
                else:
                    print(f"Failed to broadcast vitals to {result.destination_name}: {result.error_message}")
                    
        except Exception as e:
            print(f"Error in vital signs broadcasting: {str(e)}")

    def start_server(self) -> bool:
        """
        Start the HTTP server
        
        Returns:
            True if server started successfully, False otherwise
        """
        try:
            self.http_server = HTTPServer((self.host, self.port), VitalsSimulatorHTTPRequestHandler)
            self.server_thread = threading.Thread(
                target=self.http_server.serve_forever,
                daemon=True,
                name="VitalsSimulatorHTTPServer"
            )
            self.server_thread.start()
            
            print(f"BioHarness Vitals Simulator HTTP Server started on http://{self.host}:{self.port}")
            return True
            
        except Exception as e:
            print(f"Failed to start HTTP server: {str(e)}")
            return False

    def stop_server(self):
        """Stop the HTTP server"""
        if self.http_server:
            self.http_server.shutdown()
            self.http_server.server_close()
            print("HTTP server stopped")
        
        # Also stop any running simulation
        if self.simulation_engine.is_simulation_currently_running():
            self.simulation_engine.stop_continuous_vital_signs_simulation()
            print("Continuous simulation stopped")

    def get_simulation_engine(self) -> PatientVitalsSimulationEngine:
        """Get reference to the simulation engine"""
        return self.simulation_engine

    def get_server_url(self) -> str:
        """Get the full server URL"""
        return f"http://{self.host}:{self.port}"