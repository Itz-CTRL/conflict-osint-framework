"""
Rate Limiting Service for API Protection

Tracks request frequency, handles rate limiting, and provides warnings
to prevent excessive external API usage and ensure responsive searches.
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
from collections import defaultdict
import threading

logger = logging.getLogger(__name__)


class RateLimiter:
    """
    Advanced rate limiting with sliding window tracking.
    Supports per-user, per-IP, and per-action rate limits.
    """
    
    def __init__(self, enabled: bool = False):
        """
        Initialize rate limiter with tracking buckets.
        
        Args:
            enabled: Whether rate limiting is enabled (default: False for full performance)
        """
        self.enabled = enabled
        self.requests = defaultdict(list)  # Track request timestamps
        self.lock = threading.Lock()
        
        # Rate limit configurations (requests per time window)
        self.limits = {
            'global': {'requests': 100, 'window': 60},  # 100 req/min globally
            'ip': {'requests': 50, 'window': 60},  # 50 req/min per IP
            'user': {'requests': 30, 'window': 60},  # 30 req/min per user
            'deep_scan': {'requests': 5, 'window': 3600},  # 5 deep scans/hour
            'phone_lookup': {'requests': 100, 'window': 3600},  # 100 lookups/hour
            'email_harvest': {'requests': 20, 'window': 3600},  # 20 harvests/hour
            'crawler': {'requests': 10, 'window': 3600},  # 10 crawls/hour
            'scraper': {'requests': 50, 'window': 3600},  # 50 scrapes/hour
        }
    
    def _clean_old_entries(self, key: str, window_seconds: int) -> None:
        """Remove request records older than the time window"""
        cutoff = datetime.utcnow() - timedelta(seconds=window_seconds)
        self.requests[key] = [
            timestamp for timestamp in self.requests[key] 
            if timestamp > cutoff
        ]
    
    def check_limit(
        self,
        key: str,
        limit_type: str = 'user',
        action: Optional[str] = None
    ) -> Tuple[bool, Dict[str, any]]:
        """
        Check if request is within rate limits.
        
        Args:
            key: Identifier (IP, user_id, etc.)
            limit_type: Type of limit to check ('user', 'ip', 'deep_scan', etc.)
            action: Optional specific action identifier
            
        Returns:
            Tuple of (is_allowed, info_dict)
            info_dict contains:
                - allowed: bool
                - remaining: int
                - reset_in: int (seconds until limit resets)
                - status: str ('ok', 'warning', 'limited', 'blocked')
                - message: str
        """
        # If rate limiting is disabled, always allow
        if not self.enabled:
            return True, {
                'allowed': True,
                'remaining': 999999,
                'limit': 999999,
                'window_seconds': 3600,
                'reset_in': 0,
                'status': 'ok',
                'message': 'Rate limiting disabled - full performance mode'
            }
        
        with self.lock:
            # Get limit config
            if limit_type not in self.limits:
                limit_type = 'user'
            
            limit_config = self.limits[limit_type]
            max_requests = limit_config['requests']
            window_seconds = limit_config['window']
            
            # Compose full key with action if provided
            full_key = f"{limit_type}:{key}"
            if action:
                full_key = f"{full_key}:{action}"
            
            # Clean old entries
            self._clean_old_entries(full_key, window_seconds)
            
            # Get current request count
            current_count = len(self.requests[full_key])
            remaining = max(0, max_requests - current_count)
            
            # Determine status
            is_allowed = current_count < max_requests
            
            if not is_allowed:
                status = 'blocked'
                reset_in = window_seconds
            elif remaining < 3:  # Warning threshold
                status = 'warning'
                reset_in = window_seconds
            else:
                status = 'ok'
                reset_in = 0
            
            # Calculate time until oldest request expires
            if self.requests[full_key]:
                oldest = self.requests[full_key][0]
                reset_time = oldest + timedelta(seconds=window_seconds)
                reset_in = max(0, (reset_time - datetime.utcnow()).total_seconds())
            
            info = {
                'allowed': is_allowed,
                'remaining': remaining,
                'limit': max_requests,
                'window_seconds': window_seconds,
                'reset_in': int(reset_in),
                'status': status,
                'message': self._get_message(status, remaining, reset_in, max_requests)
            }
            
            # Record this request if allowed
            if is_allowed:
                self.requests[full_key].append(datetime.utcnow())
            
            return is_allowed, info
    
    def _get_message(self, status: str, remaining: int, reset_in: int, limit: int) -> str:
        """Generate appropriate message based on status"""
        messages = {
            'ok': f'Request allowed. {remaining} requests remaining.',
            'warning': f'⚠️ Approaching rate limit. Only {remaining} requests left before throttling.',
            'blocked': f'❌ Rate limit exceeded. Please wait {int(reset_in)}s before retrying.',
        }
        return messages.get(status, 'Unknown status')
    
    def get_stats(self, key: str, limit_type: str = 'user') -> Dict:
        """Get current statistics for a key"""
        with self.lock:
            full_key = f"{limit_type}:{key}"
            self._clean_old_entries(full_key, self.limits[limit_type]['window'])
            
            count = len(self.requests[full_key])
            limit_config = self.limits[limit_type]
            
            return {
                'current': count,
                'limit': limit_config['requests'],
                'window': limit_config['window'],
                'available': max(0, limit_config['requests'] - count),
                'percentage': int((count / limit_config['requests']) * 100)
            }
    
    def record_action(self, key: str, action: str) -> None:
        """Manually record an action (used by specific services)"""
        with self.lock:
            full_key = f"action:{key}:{action}"
            self.requests[full_key].append(datetime.utcnow())
    
    def reset_limit(self, key: str, limit_type: str = 'user') -> None:
        """Reset rate limit for a specific key (admin function)"""
        with self.lock:
            full_key = f"{limit_type}:{key}"
            if full_key in self.requests:
                del self.requests[full_key]
            logger.info(f"Rate limit reset for {full_key}")
    
    def clear_all(self) -> None:
        """Clear all tracking data (admin function)"""
        with self.lock:
            self.requests.clear()
            logger.info("All rate limit tracking cleared")


# Global rate limiter instance
global_rate_limiter = RateLimiter()
