"""
Username Suggestion Engine

Provides fuzzy matching on previously investigated usernames
for autocomplete and suggestion functionality.
"""

import logging
from typing import List, Dict, Tuple
from difflib import SequenceMatcher, get_close_matches
from database import db
from models import Investigation

logger = logging.getLogger(__name__)


class SuggestionEngine:
    """
    Generate username suggestions based on:
    - Previously investigated usernames (fuzzy match)
    - Common variations (underscore, numbers, suffix patterns)
    - Partial matches
    """
    
    def __init__(self, min_similarity: float = 0.6):
        """
        Initialize suggestion engine.
        
        Args:
            min_similarity: Minimum similarity score (0-1) for fuzzy matching
        """
        self.min_similarity = min_similarity
    
    def get_username_suggestions(self, query: str, limit: int = 10) -> List[Dict[str, any]]:
        """
        Get username suggestions using fuzzy matching on history.
        
        Args:
            query: Partial or complete username string
            limit: Maximum suggestions to return
            
        Returns:
            List of suggestion dicts with username, confidence, and metadata
            
        Example:
            >>> engine = SuggestionEngine()
            >>> suggestions = engine.get_username_suggestions("john")
            >>> # Returns: [
            >>>   {"username": "johndoe", "confidence": 0.95, "previous_cases": 2},
            >>>   {"username": "john_smith", "confidence": 0.87, "previous_cases": 1},
            >>> ]
        """
        try:
            if not query or len(query.strip()) < 2:
                # Return recent investigations if query too short
                return self._get_recent_usernames(limit)
            
            query = query.strip().lower()
            
            # Get all previous usernames from database
            all_investigations = Investigation.query.all()
            username_counts = {}
            
            for inv in all_investigations:
                # Prefer primary_entity on Investigation model
                username = None
                try:
                    if getattr(inv, 'case_type', None) == 'username' and getattr(inv, 'primary_entity', None):
                        username = inv.primary_entity
                    else:
                        # Fallback for legacy attribute
                        username = getattr(inv, 'primary_entity', None) or getattr(inv, 'username', None)
                except Exception:
                    username = getattr(inv, 'primary_entity', None) or getattr(inv, 'username', None)
                
                if username:
                    username_lower = username.lower()
                    if username_lower not in username_counts:
                        username_counts[username_lower] = {'original': username, 'count': 0}
                    username_counts[username_lower]['count'] += 1
            
            # Score all usernames by fuzzy similarity
            scored_usernames = []
            
            for username_lower, data in username_counts.items():
                original = data['original']
                count = data['count']
                
                # Calculate similarity score
                similarity = SequenceMatcher(None, query, username_lower).ratio()
                
                # Boost score for exact prefix match
                if username_lower.startswith(query):
                    similarity = min(1.0, similarity + 0.15)
                
                # Boost score for frequent investigations
                frequency_boost = min(0.1, count * 0.05)
                final_score = min(1.0, similarity + frequency_boost)
                
                if final_score >= self.min_similarity:
                    scored_usernames.append({
                        'username': original,
                        'confidence': round(final_score, 3),
                        'investigation_count': count,
                        'similarity': round(similarity, 3)
                    })
            
            # Sort by confidence and return
            scored_usernames.sort(key=lambda x: x['confidence'], reverse=True)
            
            return scored_usernames[:limit]
        
        except Exception as e:
            logger.error(f"Error generating username suggestions: {str(e)}")
            return []
    
    def _get_recent_usernames(self, limit: int = 10) -> List[Dict[str, any]]:
        """
        Return most recent investigated usernames.
        
        Args:
            limit: Maximum usernames to return
            
        Returns:
            List of recent usernames sorted by date
        """
        try:
            recent_investigations = Investigation.query.order_by(
                Investigation.created_at.desc()
            ).limit(limit).all()
            
            suggestions = []
            for inv in recent_investigations:
                try:
                    username = inv.primary_entity if getattr(inv, 'case_type', None) == 'username' else getattr(inv, 'primary_entity', None) or getattr(inv, 'username', None)
                except Exception:
                    username = getattr(inv, 'primary_entity', None) or getattr(inv, 'username', None)

                if username:
                    suggestions.append({
                        'username': username,
                        'confidence': 1.0,
                        'investigation_count': 1,
                        'recent': True
                    })
            
            return suggestions
        
        except Exception as e:
            logger.error(f"Error getting recent usernames: {str(e)}")
            return []
    
    def get_common_variations(self, username: str) -> List[str]:
        """
        Generate common username variations for expanded search.
        
        Args:
            username: Base username
            
        Returns:
            List of common variations (e.g., with dots, underscores, numbers)
            
        Example:
            >>> variations = engine.get_common_variations("john")
            >>> # Returns: ["john.", "john_", "john123", "j0hn", ...]
        """
        variations = set()
        
        # Original
        variations.add(username)
        
        # Common separators
        variations.add(username.replace('_', '.'))
        variations.add(username.replace('.', '_'))
        
        # Numeric suffixes
        for num in ['123', '2022', '2023', '2024', '2025', '2026', '1', '0']:
            variations.add(username + num)
        
        # Common prefixes
        for prefix in ['_', '.', 'real', 'the', 'official']:
            variations.add(prefix + username)
        
        # L33t variations (common in gaming/hacking)
        leet_map = {'a': '4', 'e': '3', 'i': '1', 'o': '0', 's': '5', 't': '7'}
        leet_version = username
        for char, replacement in leet_map.items():
            leet_version = leet_version.replace(char, replacement)
            if leet_version != username:
                variations.add(leet_version)
        
        return sorted(list(variations))
    
    def calculate_similarity(self, username1: str, username2: str) -> float:
        """
        Calculate similarity score between two usernames (0-1).
        
        Args:
            username1: First username
            username2: Second username
            
        Returns:
            Similarity score from 0 (completely different) to 1 (identical)
        """
        username1 = username1.lower()
        username2 = username2.lower()
        
        if username1 == username2:
            return 1.0
        
        return SequenceMatcher(None, username1, username2).ratio()
