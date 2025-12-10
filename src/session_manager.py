"""
Session Manager Module
======================

Handles backup, restore, and encryption of browser sessions for Antigravity.
Provides secure storage of authentication cookies to avoid repeated logins.

Author: TawanaNetworkLtc
License: MIT
"""

import os
import sys
import json
import sqlite3
import shutil
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

try:
    from Crypto.Cipher import AES
    from Crypto.Protocol.KDF import PBKDF2
    from Crypto.Random import get_random_bytes
except ImportError:
    print("Missing pycryptodome. Install: pip install pycryptodome")
    sys.exit(1)


class SessionManager:
    """
    Manages browser session backup, restore, and encryption.
    
    Features:
    - Backup valid session cookies after successful login
    - Encrypt session data at rest
    - Restore sessions before launching Antigravity
    - Validate session expiration
    - Manage multiple saved sessions
    """
    
    # Session validity period (days)
    SESSION_VALIDITY_DAYS = 30
    
    # Encryption parameters
    KEY_SIZE = 32  # 256-bit
    SALT_SIZE = 32
    NONCE_SIZE = 16
    
    def __init__(self, storage_dir: str, logger: logging.Logger, dry_run: bool = False):
        """
        Initialize SessionManager.
        
        Args:
            storage_dir: Directory to store encrypted sessions
            logger: Logger instance for detailed logging
            dry_run: If True, only simulate operations
        """
        self.logger = logger
        self.dry_run = dry_run
        self.storage_dir = storage_dir
        
        # Create storage directory
        if not dry_run:
            os.makedirs(storage_dir, exist_ok=True)
        
        # Generate or load encryption key
        self.key_file = os.path.join(storage_dir, '.key')
        self.master_key = self._get_or_create_master_key()
        
        self.logger.info(f"SessionManager initialized (Storage: {storage_dir}, Dry-run: {dry_run})")
    
    # ==================== Encryption ====================
    
    def _get_or_create_master_key(self) -> bytes:
        """
        Get existing master key or create new one.
        
        Returns:
            32-byte master key
        """
        if os.path.exists(self.key_file) and not self.dry_run:
            try:
                with open(self.key_file, 'rb') as f:
                    key = f.read()
                    if len(key) == self.KEY_SIZE:
                        self.logger.debug("Loaded existing master key")
                        return key
            except Exception as e:
                self.logger.warning(f"Could not load master key: {e}")
        
        # Generate new key
        key = get_random_bytes(self.KEY_SIZE)
        
        if not self.dry_run:
            try:
                with open(self.key_file, 'wb') as f:
                    f.write(key)
                # Set restrictive permissions (owner only)
                if os.name != 'nt':  # Unix-like
                    os.chmod(self.key_file, 0o600)
                self.logger.debug("Created new master key")
            except Exception as e:
                self.logger.error(f"Could not save master key: {e}")
        
        return key
    
    def encrypt_session(self, data: Dict) -> bytes:
        """
        Encrypt session data using AES-256-GCM.
        
        Args:
            data: Session data dictionary
        
        Returns:
            Encrypted data as bytes
        """
        self.logger.debug("Encrypting session data...")
        
        try:
            # Convert dict to JSON
            json_data = json.dumps(data).encode('utf-8')
            
            # Generate salt and nonce
            salt = get_random_bytes(self.SALT_SIZE)
            nonce = get_random_bytes(self.NONCE_SIZE)
            
            # Derive key from master key + salt
            key = PBKDF2(self.master_key, salt, dkLen=self.KEY_SIZE)
            
            # Encrypt using AES-GCM
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            ciphertext, tag = cipher.encrypt_and_digest(json_data)
            
            # Combine: salt + nonce + tag + ciphertext
            encrypted = salt + nonce + tag + ciphertext
            
            self.logger.debug(f"Encrypted {len(json_data)} bytes to {len(encrypted)} bytes")
            return encrypted
            
        except Exception as e:
            self.logger.error(f"Encryption failed: {e}")
            raise
    
    def decrypt_session(self, encrypted: bytes) -> Dict:
        """
        Decrypt session data.
        
        Args:
            encrypted: Encrypted data bytes
        
        Returns:
            Decrypted session data dictionary
        """
        self.logger.debug("Decrypting session data...")
        
        try:
            # Extract components
            salt = encrypted[:self.SALT_SIZE]
            nonce = encrypted[self.SALT_SIZE:self.SALT_SIZE + self.NONCE_SIZE]
            tag = encrypted[self.SALT_SIZE + self.NONCE_SIZE:self.SALT_SIZE + self.NONCE_SIZE + 16]
            ciphertext = encrypted[self.SALT_SIZE + self.NONCE_SIZE + 16:]
            
            # Derive key
            key = PBKDF2(self.master_key, salt, dkLen=self.KEY_SIZE)
            
            # Decrypt
            cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
            json_data = cipher.decrypt_and_verify(ciphertext, tag)
            
            # Parse JSON
            data = json.loads(json_data.decode('utf-8'))
            
            self.logger.debug(f"Decrypted {len(encrypted)} bytes to {len(json_data)} bytes")
            return data
            
        except Exception as e:
            self.logger.error(f"Decryption failed: {e}")
            raise
    
    # ==================== Session Operations ====================
    
    def backup_session(self, browser: str, profile_path: str, session_name: Optional[str] = None) -> bool:
        """
        Backup browser session cookies.
        
        Args:
            browser: Browser key (e.g., 'chrome')
            profile_path: Path to browser profile
            session_name: Optional name for session (auto-generated if None)
        
        Returns:
            True if backup successful
        """
        self.logger.info(f"Backing up session from {browser} profile...")
        
        # Determine cookie database path
        if browser == 'firefox':
            cookie_db = os.path.join(profile_path, 'cookies.sqlite')
        else:
            cookie_db = os.path.join(profile_path, 'Network', 'Cookies')
            if not os.path.exists(cookie_db):
                cookie_db = os.path.join(profile_path, 'Cookies')
        
        if not os.path.exists(cookie_db):
            self.logger.error(f"Cookie database not found: {cookie_db}")
            return False
        
        try:
            # Read cookies from database
            conn = sqlite3.connect(cookie_db)
            cursor = conn.cursor()
            
            # Get all cookies (we'll store everything, filter on restore if needed)
            cursor.execute("SELECT host_key, name, value, path, expires_utc, is_secure, is_httponly FROM cookies")
            cookies = cursor.fetchall()
            conn.close()
            
            if not cookies:
                self.logger.warning("No cookies found in database")
                return False
            
            # Create session data
            session_data = {
                'browser': browser,
                'profile_path': profile_path,
                'backup_time': datetime.now().isoformat(),
                'cookie_count': len(cookies),
                'cookies': [
                    {
                        'host_key': c[0],
                        'name': c[1],
                        'value': c[2],
                        'path': c[3],
                        'expires_utc': c[4],
                        'is_secure': c[5],
                        'is_httponly': c[6]
                    }
                    for c in cookies
                ]
            }
            
            # Generate session name if not provided
            if session_name is None:
                session_name = f"{browser}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            
            # Encrypt and save
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would backup {len(cookies)} cookies as '{session_name}'")
                return True
            
            encrypted = self.encrypt_session(session_data)
            session_file = os.path.join(self.storage_dir, f"{session_name}.session")
            
            with open(session_file, 'wb') as f:
                f.write(encrypted)
            
            # Set restrictive permissions
            if os.name != 'nt':
                os.chmod(session_file, 0o600)
            
            self.logger.info(f"✓ Backed up {len(cookies)} cookies to '{session_name}'")
            return True
            
        except Exception as e:
            self.logger.error(f"Session backup failed: {e}")
            return False
    
    def restore_session(self, session_name: str, browser: str, profile_path: str) -> bool:
        """
        Restore session cookies to browser.
        
        Args:
            session_name: Name of saved session
            browser: Browser key
            profile_path: Path to browser profile
        
        Returns:
            True if restore successful
        """
        self.logger.info(f"Restoring session '{session_name}' to {browser}...")
        
        session_file = os.path.join(self.storage_dir, f"{session_name}.session")
        
        if not os.path.exists(session_file):
            self.logger.error(f"Session file not found: {session_file}")
            return False
        
        try:
            # Load and decrypt session
            with open(session_file, 'rb') as f:
                encrypted = f.read()
            
            session_data = self.decrypt_session(encrypted)
            
            # Validate session
            if not self.validate_session(session_data):
                self.logger.warning("Session validation failed")
                return False
            
            # Determine cookie database path
            if browser == 'firefox':
                cookie_db = os.path.join(profile_path, 'cookies.sqlite')
            else:
                cookie_db = os.path.join(profile_path, 'Network', 'Cookies')
                if not os.path.exists(cookie_db):
                    cookie_db = os.path.join(profile_path, 'Cookies')
            
            if not os.path.exists(cookie_db):
                self.logger.error(f"Cookie database not found: {cookie_db}")
                return False
            
            if self.dry_run:
                self.logger.info(f"[DRY RUN] Would restore {session_data['cookie_count']} cookies")
                return True
            
            # Create backup of current cookies
            backup_path = f"{cookie_db}.backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            shutil.copy2(cookie_db, backup_path)
            self.logger.debug(f"Created backup: {backup_path}")
            
            # Insert cookies into database
            conn = sqlite3.connect(cookie_db)
            cursor = conn.cursor()
            
            restored_count = 0
            for cookie in session_data['cookies']:
                try:
                    # Check if cookie already exists
                    cursor.execute(
                        "SELECT COUNT(*) FROM cookies WHERE host_key=? AND name=?",
                        (cookie['host_key'], cookie['name'])
                    )
                    exists = cursor.fetchone()[0] > 0
                    
                    if exists:
                        # Update existing cookie
                        cursor.execute(
                            "UPDATE cookies SET value=?, path=?, expires_utc=?, is_secure=?, is_httponly=? WHERE host_key=? AND name=?",
                            (cookie['value'], cookie['path'], cookie['expires_utc'], cookie['is_secure'], cookie['is_httponly'], cookie['host_key'], cookie['name'])
                        )
                    else:
                        # Insert new cookie
                        cursor.execute(
                            "INSERT INTO cookies (host_key, name, value, path, expires_utc, is_secure, is_httponly) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (cookie['host_key'], cookie['name'], cookie['value'], cookie['path'], cookie['expires_utc'], cookie['is_secure'], cookie['is_httponly'])
                        )
                    
                    restored_count += 1
                    
                except sqlite3.Error as e:
                    self.logger.warning(f"Could not restore cookie {cookie['name']}: {e}")
            
            conn.commit()
            conn.close()
            
            self.logger.info(f"✓ Restored {restored_count}/{session_data['cookie_count']} cookies")
            return True
            
        except Exception as e:
            self.logger.error(f"Session restore failed: {e}")
            return False
    
    def validate_session(self, session_data: Dict) -> bool:
        """
        Validate session data structure and expiration.
        
        Args:
            session_data: Session data dictionary
        
        Returns:
            True if session is valid
        """
        required_fields = ['browser', 'backup_time', 'cookies']
        
        # Check required fields
        for field in required_fields:
            if field not in session_data:
                self.logger.error(f"Session missing required field: {field}")
                return False
        
        # Check expiration
        try:
            backup_time = datetime.fromisoformat(session_data['backup_time'])
            age = datetime.now() - backup_time
            
            if age.days > self.SESSION_VALIDITY_DAYS:
                self.logger.warning(f"Session expired ({age.days} days old)")
                return False
            
            self.logger.debug(f"Session age: {age.days} days (valid)")
            
        except Exception as e:
            self.logger.error(f"Could not parse backup time: {e}")
            return False
        
        return True
    
    def is_session_expired(self, session_name: str) -> bool:
        """
        Check if a saved session is expired.
        
        Args:
            session_name: Name of saved session
        
        Returns:
            True if expired
        """
        session_file = os.path.join(self.storage_dir, f"{session_name}.session")
        
        if not os.path.exists(session_file):
            return True
        
        try:
            with open(session_file, 'rb') as f:
                encrypted = f.read()
            
            session_data = self.decrypt_session(encrypted)
            return not self.validate_session(session_data)
            
        except Exception as e:
            self.logger.error(f"Could not check session expiration: {e}")
            return True
    
    # ==================== Session Management ====================
    
    def list_saved_sessions(self) -> List[Dict]:
        """
        List all saved sessions.
        
        Returns:
            List of session info dictionaries
        """
        self.logger.debug("Listing saved sessions...")
        
        if not os.path.exists(self.storage_dir):
            return []
        
        sessions = []
        
        for filename in os.listdir(self.storage_dir):
            if not filename.endswith('.session'):
                continue
            
            session_name = filename[:-8]  # Remove .session extension
            session_file = os.path.join(self.storage_dir, filename)
            
            try:
                # Get file info
                stat = os.stat(session_file)
                
                # Try to load session data
                with open(session_file, 'rb') as f:
                    encrypted = f.read()
                
                session_data = self.decrypt_session(encrypted)
                
                sessions.append({
                    'name': session_name,
                    'browser': session_data.get('browser', 'unknown'),
                    'backup_time': session_data.get('backup_time', 'unknown'),
                    'cookie_count': session_data.get('cookie_count', 0),
                    'file_size': stat.st_size,
                    'expired': not self.validate_session(session_data)
                })
                
            except Exception as e:
                self.logger.warning(f"Could not load session {session_name}: {e}")
                sessions.append({
                    'name': session_name,
                    'browser': 'unknown',
                    'backup_time': 'unknown',
                    'cookie_count': 0,
                    'file_size': stat.st_size,
                    'expired': True,
                    'error': str(e)
                })
        
        self.logger.debug(f"Found {len(sessions)} saved sessions")
        return sessions
    
    def delete_session(self, session_name: str) -> bool:
        """
        Delete a saved session.
        
        Args:
            session_name: Name of session to delete
        
        Returns:
            True if deleted successfully
        """
        self.logger.info(f"Deleting session '{session_name}'...")
        
        session_file = os.path.join(self.storage_dir, f"{session_name}.session")
        
        if not os.path.exists(session_file):
            self.logger.warning(f"Session not found: {session_name}")
            return False
        
        if self.dry_run:
            self.logger.info(f"[DRY RUN] Would delete session '{session_name}'")
            return True
        
        try:
            os.remove(session_file)
            self.logger.info(f"✓ Deleted session '{session_name}'")
            return True
        except Exception as e:
            self.logger.error(f"Could not delete session: {e}")
            return False
    
    def delete_expired_sessions(self) -> int:
        """
        Delete all expired sessions.
        
        Returns:
            Number of sessions deleted
        """
        self.logger.info("Deleting expired sessions...")
        
        sessions = self.list_saved_sessions()
        deleted_count = 0
        
        for session in sessions:
            if session.get('expired', True):
                if self.delete_session(session['name']):
                    deleted_count += 1
        
        self.logger.info(f"Deleted {deleted_count} expired sessions")
        return deleted_count


if __name__ == "__main__":
    # Test code
    logging.basicConfig(
        level=logging.DEBUG,
        format='[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    logger = logging.getLogger(__name__)
    
    storage_dir = os.path.join(os.path.expanduser('~'), '.antigravity-cleaner', 'sessions')
    manager = SessionManager(storage_dir, logger, dry_run=True)
    
    sessions = manager.list_saved_sessions()
    print(f"\nFound {len(sessions)} sessions:")
    for session in sessions:
        print(f"  - {session['name']}: {session['browser']}, {session['cookie_count']} cookies")
