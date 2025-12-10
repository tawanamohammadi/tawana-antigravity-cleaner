"""
Network Optimizer Module
========================

Provides network diagnostics and optimization for Antigravity login issues.
Tests connectivity, DNS resolution, proxy settings, and SSL certificates.

Author: TawanaNetworkLtc
License: MIT
"""

import os
import sys
import platform
import subprocess
import socket
import ssl
import logging
from typing import Dict, List, Optional, Tuple
from datetime import datetime

try:
    import requests
except ImportError:
    print("Missing requests. Install: pip install requests")
    sys.exit(1)


class NetworkOptimizer:
    """
    Handles network diagnostics and optimization for Antigravity login.
    
    Features:
    - Test connectivity to Google services
    - DNS resolution diagnostics
    - Proxy/VPN conflict detection
    - SSL certificate verification
    - Network stack reset
    - Detailed diagnostic reporting
    """
    
    # Critical Google endpoints for Antigravity
    GOOGLE_ENDPOINTS = [
        'https://accounts.google.com',
        'https://oauth2.googleapis.com',
        'https://www.google.com',
        'https://apis.google.com'
    ]
    
    DNS_TEST_DOMAINS = [
        'accounts.google.com',
        'oauth2.googleapis.com',
        'www.google.com',
        'apis.google.com'
    ]
    
    def __init__(self, logger: logging.Logger, dry_run: bool = False):
        """
        Initialize NetworkOptimizer.
        
        Args:
            logger: Logger instance for detailed logging
            dry_run: If True, only simulate operations
        """
        self.logger = logger
        self.dry_run = dry_run
        self.current_os = platform.system().lower()
        
        self.logger.info(f"NetworkOptimizer initialized (OS: {self.current_os}, Dry-run: {dry_run})")
    
    # ==================== Connectivity Testing ====================
    
    def test_google_connectivity(self) -> Dict[str, any]:
        """
        Test connectivity to Google services.
        
        Returns:
            Dictionary with test results for each endpoint
        """
        self.logger.info("Testing connectivity to Google services...")
        
        results = {
            'overall_status': 'unknown',
            'endpoints': {},
            'accessible_count': 0,
            'total_count': len(self.GOOGLE_ENDPOINTS)
        }
        
        for endpoint in self.GOOGLE_ENDPOINTS:
            self.logger.debug(f"Testing {endpoint}...")
            
            try:
                response = requests.get(endpoint, timeout=5, allow_redirects=True)
                
                status = {
                    'accessible': response.status_code < 400,
                    'status_code': response.status_code,
                    'response_time_ms': int(response.elapsed.total_seconds() * 1000),
                    'error': None
                }
                
                if status['accessible']:
                    results['accessible_count'] += 1
                    self.logger.debug(f"✓ {endpoint} - {response.status_code} ({status['response_time_ms']}ms)")
                else:
                    self.logger.warning(f"✗ {endpoint} - {response.status_code}")
                
                results['endpoints'][endpoint] = status
                
            except requests.exceptions.Timeout:
                self.logger.error(f"✗ {endpoint} - Timeout")
                results['endpoints'][endpoint] = {
                    'accessible': False,
                    'status_code': None,
                    'response_time_ms': None,
                    'error': 'Timeout'
                }
            except requests.exceptions.ConnectionError as e:
                self.logger.error(f"✗ {endpoint} - Connection error: {e}")
                results['endpoints'][endpoint] = {
                    'accessible': False,
                    'status_code': None,
                    'response_time_ms': None,
                    'error': f'Connection error: {str(e)[:100]}'
                }
            except Exception as e:
                self.logger.error(f"✗ {endpoint} - Error: {e}")
                results['endpoints'][endpoint] = {
                    'accessible': False,
                    'status_code': None,
                    'response_time_ms': None,
                    'error': str(e)[:100]
                }
        
        # Determine overall status
        if results['accessible_count'] == results['total_count']:
            results['overall_status'] = 'excellent'
        elif results['accessible_count'] >= results['total_count'] * 0.75:
            results['overall_status'] = 'good'
        elif results['accessible_count'] >= results['total_count'] * 0.5:
            results['overall_status'] = 'poor'
        else:
            results['overall_status'] = 'critical'
        
        self.logger.info(f"Connectivity test complete: {results['accessible_count']}/{results['total_count']} endpoints accessible ({results['overall_status']})")
        
        return results
    
    def check_dns_resolution(self, domains: Optional[List[str]] = None) -> Dict[str, any]:
        """
        Check DNS resolution for critical domains.
        
        Args:
            domains: List of domains to test (uses defaults if None)
        
        Returns:
            Dictionary with DNS resolution results
        """
        if domains is None:
            domains = self.DNS_TEST_DOMAINS
        
        self.logger.info(f"Testing DNS resolution for {len(domains)} domains...")
        
        results = {
            'overall_status': 'unknown',
            'domains': {},
            'resolved_count': 0,
            'total_count': len(domains)
        }
        
        for domain in domains:
            self.logger.debug(f"Resolving {domain}...")
            
            try:
                start_time = datetime.now()
                ip_addresses = socket.gethostbyname_ex(domain)[2]
                resolution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
                
                results['domains'][domain] = {
                    'resolved': True,
                    'ip_addresses': ip_addresses,
                    'resolution_time_ms': resolution_time_ms,
                    'error': None
                }
                
                results['resolved_count'] += 1
                self.logger.debug(f"✓ {domain} -> {', '.join(ip_addresses)} ({resolution_time_ms}ms)")
                
            except socket.gaierror as e:
                self.logger.error(f"✗ {domain} - DNS resolution failed: {e}")
                results['domains'][domain] = {
                    'resolved': False,
                    'ip_addresses': [],
                    'resolution_time_ms': None,
                    'error': f'DNS resolution failed: {e}'
                }
            except Exception as e:
                self.logger.error(f"✗ {domain} - Error: {e}")
                results['domains'][domain] = {
                    'resolved': False,
                    'ip_addresses': [],
                    'resolution_time_ms': None,
                    'error': str(e)
                }
        
        # Determine overall status
        if results['resolved_count'] == results['total_count']:
            results['overall_status'] = 'excellent'
        elif results['resolved_count'] >= results['total_count'] * 0.75:
            results['overall_status'] = 'good'
        else:
            results['overall_status'] = 'critical'
        
        self.logger.info(f"DNS test complete: {results['resolved_count']}/{results['total_count']} domains resolved ({results['overall_status']})")
        
        return results
    
    def detect_proxy_settings(self) -> Dict[str, any]:
        """
        Detect system and environment proxy settings.
        
        Returns:
            Dictionary with proxy configuration
        """
        self.logger.info("Detecting proxy settings...")
        
        proxy_info = {
            'has_proxy': False,
            'environment_proxies': {},
            'system_proxy': None,
            'potential_conflicts': []
        }
        
        # Check environment variables
        env_proxy_vars = ['HTTP_PROXY', 'HTTPS_PROXY', 'http_proxy', 'https_proxy', 'ALL_PROXY', 'all_proxy']
        
        for var in env_proxy_vars:
            value = os.environ.get(var)
            if value:
                proxy_info['environment_proxies'][var] = value
                proxy_info['has_proxy'] = True
                self.logger.debug(f"Found environment proxy: {var}={value}")
        
        # Check system proxy (Windows)
        if self.current_os == 'windows':
            try:
                import winreg
                
                internet_settings = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r'Software\Microsoft\Windows\CurrentVersion\Internet Settings'
                )
                
                try:
                    proxy_enable = winreg.QueryValueEx(internet_settings, 'ProxyEnable')[0]
                    if proxy_enable:
                        proxy_server = winreg.QueryValueEx(internet_settings, 'ProxyServer')[0]
                        proxy_info['system_proxy'] = proxy_server
                        proxy_info['has_proxy'] = True
                        self.logger.debug(f"Found system proxy: {proxy_server}")
                except FileNotFoundError:
                    pass
                
                winreg.CloseKey(internet_settings)
                
            except Exception as e:
                self.logger.warning(f"Could not read system proxy settings: {e}")
        
        # Detect potential conflicts
        if len(proxy_info['environment_proxies']) > 2:
            proxy_info['potential_conflicts'].append("Multiple environment proxy variables set")
        
        if proxy_info['system_proxy'] and proxy_info['environment_proxies']:
            proxy_info['potential_conflicts'].append("Both system and environment proxies configured")
        
        self.logger.info(f"Proxy detection complete: {'Proxy detected' if proxy_info['has_proxy'] else 'No proxy'}")
        
        return proxy_info
    
    def verify_ssl_certificates(self) -> Dict[str, any]:
        """
        Verify SSL certificate store integrity.
        
        Returns:
            Dictionary with SSL verification results
        """
        self.logger.info("Verifying SSL certificates...")
        
        results = {
            'overall_status': 'unknown',
            'endpoints': {},
            'valid_count': 0,
            'total_count': len(self.GOOGLE_ENDPOINTS)
        }
        
        for endpoint in self.GOOGLE_ENDPOINTS:
            self.logger.debug(f"Verifying SSL for {endpoint}...")
            
            try:
                # Parse hostname from URL
                hostname = endpoint.replace('https://', '').replace('http://', '').split('/')[0]
                
                # Create SSL context
                context = ssl.create_default_context()
                
                # Connect and verify
                with socket.create_connection((hostname, 443), timeout=5) as sock:
                    with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                        cert = ssock.getpeercert()
                        
                        results['endpoints'][endpoint] = {
                            'valid': True,
                            'issuer': dict(x[0] for x in cert['issuer']),
                            'subject': dict(x[0] for x in cert['subject']),
                            'version': cert['version'],
                            'error': None
                        }
                        
                        results['valid_count'] += 1
                        self.logger.debug(f"✓ {endpoint} - SSL valid")
                
            except ssl.SSLError as e:
                self.logger.error(f"✗ {endpoint} - SSL error: {e}")
                results['endpoints'][endpoint] = {
                    'valid': False,
                    'issuer': None,
                    'subject': None,
                    'version': None,
                    'error': f'SSL error: {e}'
                }
            except Exception as e:
                self.logger.error(f"✗ {endpoint} - Error: {e}")
                results['endpoints'][endpoint] = {
                    'valid': False,
                    'issuer': None,
                    'subject': None,
                    'version': None,
                    'error': str(e)
                }
        
        # Determine overall status
        if results['valid_count'] == results['total_count']:
            results['overall_status'] = 'excellent'
        elif results['valid_count'] >= results['total_count'] * 0.75:
            results['overall_status'] = 'good'
        else:
            results['overall_status'] = 'critical'
        
        self.logger.info(f"SSL verification complete: {results['valid_count']}/{results['total_count']} certificates valid ({results['overall_status']})")
        
        return results
    
    # ==================== Network Optimization ====================
    
    def clear_dns_cache(self) -> bool:
        """
        Clear system DNS cache.
        
        Returns:
            True if successful
        """
        self.logger.info("Clearing DNS cache...")
        
        if self.dry_run:
            self.logger.info("[DRY RUN] Would clear DNS cache")
            return True
        
        try:
            if self.current_os == 'windows':
                subprocess.run(['ipconfig', '/flushdns'], check=True, capture_output=True)
            elif self.current_os == 'darwin':
                subprocess.run(['dscacheutil', '-flushcache'], check=True, capture_output=True)
                subprocess.run(['killall', '-HUP', 'mDNSResponder'], check=False, capture_output=True)
            elif self.current_os == 'linux':
                # Try systemd-resolved
                result = subprocess.run(['resolvectl', 'flush-caches'], check=False, capture_output=True)
                if result.returncode != 0:
                    # Try older method
                    subprocess.run(['systemd-resolve', '--flush-caches'], check=False, capture_output=True)
            
            self.logger.info("✓ DNS cache cleared successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to clear DNS cache: {e}")
            return False
        except Exception as e:
            self.logger.error(f"Error clearing DNS cache: {e}")
            return False
    
    def reset_network_stack(self) -> bool:
        """
        Reset network stack (Windows only).
        
        Returns:
            True if successful
        """
        self.logger.info("Resetting network stack...")
        
        if self.current_os != 'windows':
            self.logger.warning("Network stack reset only supported on Windows")
            return False
        
        if self.dry_run:
            self.logger.info("[DRY RUN] Would reset network stack")
            return True
        
        commands = [
            ['netsh', 'winsock', 'reset'],
            ['netsh', 'int', 'ip', 'reset'],
            ['ipconfig', '/flushdns']
        ]
        
        success = True
        
        for cmd in commands:
            try:
                self.logger.debug(f"Executing: {' '.join(cmd)}")
                subprocess.run(cmd, check=True, capture_output=True)
                self.logger.debug(f"✓ {' '.join(cmd)}")
            except subprocess.CalledProcessError as e:
                self.logger.error(f"✗ {' '.join(cmd)} failed: {e}")
                success = False
        
        if success:
            self.logger.info("✓ Network stack reset complete (restart recommended)")
        else:
            self.logger.warning("Network stack reset completed with errors")
        
        return success
    
    # ==================== Diagnostic Reporting ====================
    
    def generate_diagnostic_report(self) -> str:
        """
        Generate comprehensive network diagnostic report.
        
        Returns:
            Formatted diagnostic report as string
        """
        self.logger.info("Generating diagnostic report...")
        
        # Run all diagnostics
        connectivity = self.test_google_connectivity()
        dns = self.check_dns_resolution()
        proxy = self.detect_proxy_settings()
        ssl = self.verify_ssl_certificates()
        
        # Build report
        report_lines = []
        report_lines.append("=" * 70)
        report_lines.append("ANTIGRAVITY NETWORK DIAGNOSTIC REPORT")
        report_lines.append("=" * 70)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append(f"OS: {platform.system()} {platform.release()}")
        report_lines.append("")
        
        # Connectivity
        report_lines.append("--- GOOGLE CONNECTIVITY ---")
        report_lines.append(f"Status: {connectivity['overall_status'].upper()}")
        report_lines.append(f"Accessible: {connectivity['accessible_count']}/{connectivity['total_count']}")
        for endpoint, status in connectivity['endpoints'].items():
            symbol = "✓" if status['accessible'] else "✗"
            report_lines.append(f"  {symbol} {endpoint}: {status.get('status_code', 'N/A')}")
            if status['error']:
                report_lines.append(f"      Error: {status['error']}")
        report_lines.append("")
        
        # DNS
        report_lines.append("--- DNS RESOLUTION ---")
        report_lines.append(f"Status: {dns['overall_status'].upper()}")
        report_lines.append(f"Resolved: {dns['resolved_count']}/{dns['total_count']}")
        for domain, status in dns['domains'].items():
            symbol = "✓" if status['resolved'] else "✗"
            ips = ', '.join(status['ip_addresses']) if status['ip_addresses'] else 'N/A'
            report_lines.append(f"  {symbol} {domain}: {ips}")
        report_lines.append("")
        
        # Proxy
        report_lines.append("--- PROXY SETTINGS ---")
        if proxy['has_proxy']:
            report_lines.append("⚠ Proxy detected (may interfere with login)")
            if proxy['system_proxy']:
                report_lines.append(f"  System: {proxy['system_proxy']}")
            for var, value in proxy['environment_proxies'].items():
                report_lines.append(f"  {var}: {value}")
            if proxy['potential_conflicts']:
                report_lines.append("  Conflicts:")
                for conflict in proxy['potential_conflicts']:
                    report_lines.append(f"    - {conflict}")
        else:
            report_lines.append("✓ No proxy configured")
        report_lines.append("")
        
        # SSL
        report_lines.append("--- SSL CERTIFICATES ---")
        report_lines.append(f"Status: {ssl['overall_status'].upper()}")
        report_lines.append(f"Valid: {ssl['valid_count']}/{ssl['total_count']}")
        for endpoint, status in ssl['endpoints'].items():
            symbol = "✓" if status['valid'] else "✗"
            report_lines.append(f"  {symbol} {endpoint}")
            if status['error']:
                report_lines.append(f"      Error: {status['error']}")
        report_lines.append("")
        
        # Recommendations
        report_lines.append("--- RECOMMENDATIONS ---")
        recommendations = []
        
        if connectivity['overall_status'] in ['poor', 'critical']:
            recommendations.append("⚠ Poor connectivity detected. Check internet connection.")
        
        if dns['overall_status'] == 'critical':
            recommendations.append("⚠ DNS issues detected. Try clearing DNS cache.")
        
        if proxy['has_proxy']:
            recommendations.append("⚠ Proxy detected. Consider disabling for Antigravity login.")
        
        if ssl['overall_status'] in ['poor', 'critical']:
            recommendations.append("⚠ SSL certificate issues. May need to update certificate store.")
        
        if not recommendations:
            recommendations.append("✓ No critical issues detected.")
        
        for rec in recommendations:
            report_lines.append(f"  {rec}")
        
        report_lines.append("=" * 70)
        
        report = "\n".join(report_lines)
        self.logger.info("Diagnostic report generated")
        
        return report


if __name__ == "__main__":
    # Test code
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    
    optimizer = NetworkOptimizer(logger, dry_run=False)
    report = optimizer.generate_diagnostic_report()
    print(report)
