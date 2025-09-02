"""
Data broadcasting system for sending vital signs to external systems
"""
import requests
import json
import time
from typing import List, Optional
from datetime import datetime

from data_models import PatientVitalSigns, BroadcastingResult
from vital_types import BroadcastingDestination
from config_settings import (
    RULE_ENGINE_BASE_URL,
    RULE_ENGINE_VITALS_ENDPOINT,
    RULE_ENGINE_CONNECTION_TIMEOUT_SECONDS,
    RULE_ENGINE_REQUEST_RETRY_COUNT,
    UI_HTTP_ENDPOINT,
    UI_CONNECTION_TIMEOUT_SECONDS,
    ENABLE_RULE_ENGINE_BROADCASTING,
    ENABLE_UI_BROADCASTING,
    BROADCASTING_RETRY_DELAY_SECONDS,
    MAX_BROADCASTING_RETRIES
)


class VitalSignsDataBroadcaster:
    """
    Handles broadcasting of vital signs data to external systems like rule engines and UIs
    """

    def __init__(self):
        self._rule_engine_endpoint_url = f"{RULE_ENGINE_BASE_URL}{RULE_ENGINE_VITALS_ENDPOINT}"
        self._ui_endpoint_url = UI_HTTP_ENDPOINT
        self._is_rule_engine_broadcasting_enabled = ENABLE_RULE_ENGINE_BROADCASTING
        self._is_ui_broadcasting_enabled = ENABLE_UI_BROADCASTING

    def broadcast_vital_signs_to_all_destinations(
        self, 
        vital_signs_data: PatientVitalSigns
    ) -> List[BroadcastingResult]:
        """
        Broadcast vital signs data to all configured destinations
        
        Args:
            vital_signs_data: The vital signs data to broadcast
            
        Returns:
            List of broadcasting results for each destination
        """
        broadcasting_results = []

        # Broadcast to rule engine if enabled
        if self._is_rule_engine_broadcasting_enabled:
            rule_engine_result = self.broadcast_to_rule_engine(vital_signs_data)
            broadcasting_results.append(rule_engine_result)

        # Broadcast to UI if enabled
        if self._is_ui_broadcasting_enabled:
            ui_result = self.broadcast_to_user_interface(vital_signs_data)
            broadcasting_results.append(ui_result)

        return broadcasting_results

    def broadcast_to_rule_engine(self, vital_signs_data: PatientVitalSigns) -> BroadcastingResult:
        """
        Send vital signs data to the rule engine for processing and analysis
        
        Args:
            vital_signs_data: The vital signs data to send to rule engine
            
        Returns:
            Result of the broadcasting attempt
        """
        return self._send_http_post_request_with_retries(
            destination_name="Rule Engine",
            endpoint_url=self._rule_engine_endpoint_url,
            payload_data=vital_signs_data.to_json_serializable_dict(),
            timeout_seconds=RULE_ENGINE_CONNECTION_TIMEOUT_SECONDS,
            max_retry_attempts=RULE_ENGINE_REQUEST_RETRY_COUNT
        )

    def broadcast_to_user_interface(self, vital_signs_data: PatientVitalSigns) -> BroadcastingResult:
        """
        Send vital signs data to the user interface for display
        
        Args:
            vital_signs_data: The vital signs data to send to UI
            
        Returns:
            Result of the broadcasting attempt
        """
        return self._send_http_post_request_with_retries(
            destination_name="User Interface",
            endpoint_url=self._ui_endpoint_url,
            payload_data=vital_signs_data.to_json_serializable_dict(),
            timeout_seconds=UI_CONNECTION_TIMEOUT_SECONDS,
            max_retry_attempts=MAX_BROADCASTING_RETRIES
        )

    def set_rule_engine_endpoint(self, base_url: str, endpoint_path: str) -> None:
        """
        Configure the rule engine endpoint URL
        
        Args:
            base_url: Base URL of the rule engine service
            endpoint_path: Specific endpoint path for vital signs data
        """
        self._rule_engine_endpoint_url = f"{base_url}{endpoint_path}"

    def set_ui_endpoint(self, endpoint_url: str) -> None:
        """
        Configure the user interface endpoint URL
        
        Args:
            endpoint_url: Full URL of the UI endpoint
        """
        self._ui_endpoint_url = endpoint_url

    def enable_rule_engine_broadcasting(self, is_enabled: bool = True) -> None:
        """
        Enable or disable broadcasting to rule engine
        
        Args:
            is_enabled: True to enable, False to disable
        """
        self._is_rule_engine_broadcasting_enabled = is_enabled

    def enable_ui_broadcasting(self, is_enabled: bool = True) -> None:
        """
        Enable or disable broadcasting to user interface
        
        Args:
            is_enabled: True to enable, False to disable
        """
        self._is_ui_broadcasting_enabled = is_enabled

    def test_rule_engine_connectivity(self) -> BroadcastingResult:
        """
        Test connectivity to the rule engine endpoint
        
        Returns:
            Result of the connectivity test
        """
        test_payload = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Connectivity test from BioHarness Simulator"
        }
        
        return self._send_http_post_request_with_retries(
            destination_name="Rule Engine (Test)",
            endpoint_url=self._rule_engine_endpoint_url,
            payload_data=test_payload,
            timeout_seconds=RULE_ENGINE_CONNECTION_TIMEOUT_SECONDS,
            max_retry_attempts=1  # Only one attempt for test
        )

    def test_ui_connectivity(self) -> BroadcastingResult:
        """
        Test connectivity to the user interface endpoint
        
        Returns:
            Result of the connectivity test
        """
        test_payload = {
            "test": True,
            "timestamp": datetime.now().isoformat(),
            "message": "Connectivity test from BioHarness Simulator"
        }
        
        return self._send_http_post_request_with_retries(
            destination_name="User Interface (Test)",
            endpoint_url=self._ui_endpoint_url,
            payload_data=test_payload,
            timeout_seconds=UI_CONNECTION_TIMEOUT_SECONDS,
            max_retry_attempts=1  # Only one attempt for test
        )

    def _send_http_post_request_with_retries(
        self,
        destination_name: str,
        endpoint_url: str,
        payload_data: dict,
        timeout_seconds: int,
        max_retry_attempts: int
    ) -> BroadcastingResult:
        """
        Send HTTP POST request with retry logic
        
        Args:
            destination_name: Human-readable name of the destination
            endpoint_url: URL to send the request to
            payload_data: Data to send in the request body
            timeout_seconds: Request timeout in seconds
            max_retry_attempts: Maximum number of retry attempts
            
        Returns:
            Result of the broadcasting attempt
        """
        last_exception = None
        
        for attempt_number in range(max_retry_attempts):
            try:
                response = requests.post(
                    url=endpoint_url,
                    json=payload_data,
                    timeout=timeout_seconds,
                    headers={
                        'Content-Type': 'application/json',
                        'User-Agent': 'BioHarness-Vitals-Simulator/1.0'
                    }
                )
                
                # Check if request was successful
                if response.status_code in [200, 201, 202]:
                    return BroadcastingResult(
                        destination_name=destination_name,
                        was_successful=True,
                        response_status_code=response.status_code,
                        transmission_timestamp=datetime.now().isoformat()
                    )
                else:
                    # HTTP error status
                    return BroadcastingResult(
                        destination_name=destination_name,
                        was_successful=False,
                        error_message=f"HTTP {response.status_code}: {response.text}",
                        response_status_code=response.status_code,
                        transmission_timestamp=datetime.now().isoformat()
                    )
                    
            except requests.exceptions.Timeout:
                last_exception = f"Request timeout after {timeout_seconds} seconds"
            except requests.exceptions.ConnectionError:
                last_exception = f"Connection error to {endpoint_url}"
            except requests.exceptions.RequestException as e:
                last_exception = f"Request error: {str(e)}"
            except Exception as e:
                last_exception = f"Unexpected error: {str(e)}"
            
            # Wait before retrying (except on last attempt)
            if attempt_number < max_retry_attempts - 1:
                time.sleep(BROADCASTING_RETRY_DELAY_SECONDS)
        
        # All attempts failed
        return BroadcastingResult(
            destination_name=destination_name,
            was_successful=False,
            error_message=f"Failed after {max_retry_attempts} attempts. Last error: {last_exception}",
            transmission_timestamp=datetime.now().isoformat()
        )