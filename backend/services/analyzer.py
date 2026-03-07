"""Behavior Analysis Service
Analyzes scraped data to identify suspicious behavioral patterns
and computes risk scores for investigations.
"""

from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class BehaviorAnalyzer:
    """
    Analyzes scraped data to identify suspicious behavior patterns
    Computes risk scores based on platform presence, keywords, account age.
    """

    # Keywords related to conflict and misinformation
    CONFLICT_KEYWORDS = [
        'attack', 'kill', 'war', 'bomb', 'destroy', 'fight',
        'hate', 'enemy', 'threat', 'danger', 'fake', 'lie',
        'protest', 'riot', 'coup', 'overthrow', 'uprising',
        'crisis', 'emergency', 'urgent', 'breaking', 'exposed'
    ]
    
    # Scam/fraud keywords
    SCAM_KEYWORDS = [
        'lottery', 'prize', 'verify', 'claim', 'reward', 'bitcoin',
        'crypto', 'money transfer', 'western union', 'urgent action',
        'update payment', 'confirm identity', 'limited time'
    ]
    
    # Risk score calculation constants
    RISK_THRESHOLDS = {
        'LOW': 25,
        'MEDIUM': 50,
        'HIGH': 75,
        'CRITICAL': 90
    }

    def analyze(self, username, platform_results, detailed_data=None):
        """
        Run full analysis on collected data.
        Returns a complete analysis report.
        Handles partial or missing data gracefully.
        """
        logger.info(f"Starting analysis for: {username}")

        report = {
            'username': username,
            'analyzed_at': datetime.now().isoformat(),
            'risk_score': 0,
            'risk_level': 'LOW',
            'findings': [],
            'platform_presence': {},
            'behavior_flags': [],
            'keyword_hits': [],
            'recommendations': [],
            'analysis_notes': []
        }

        try:
            # 1. Multi-platform presence analysis
            if platform_results and isinstance(platform_results, dict):
                platforms_list = platform_results.get('platforms', [])
                if platforms_list:
                    found_on = [
                        p.get('platform', 'Unknown') for p in platforms_list
                        if isinstance(p, dict) and p.get('found') is True
                    ]
                    report['platform_presence'] = {
                        'found_on': found_on,
                        'count': len(found_on),
                        'platforms_checked': platform_results.get('total_checked', 0)
                    }

                    # Risk: Found on many platforms = coordinated presence
                    if len(found_on) >= 7:
                        report['risk_score'] += 20
                        report['behavior_flags'].append(
                            f'Present on {len(found_on)} platforms simultaneously'
                        )
                    elif len(found_on) >= 4:
                        report['risk_score'] += 10
                        report['behavior_flags'].append(
                            f'Active on {len(found_on)} platforms'
                        )
                    
                    logger.info(f"Platform analysis: found on {len(found_on)} platforms")
        except Exception as e:
            logger.error(f"Error in platform presence analysis: {str(e)}")
            report['analysis_notes'].append(f'Platform analysis error: {str(e)}')

        try:
            # 2. Reddit behavior analysis
            if detailed_data and isinstance(detailed_data, dict):
                reddit = detailed_data.get('reddit', {})
                
                if reddit and isinstance(reddit, dict) and reddit.get('found') is True:
                    try:
                        # New account flag
                        account_age = reddit.get('account_age')
                        if account_age:
                            try:
                                account_year = int(account_age[:4])
                                current_year = datetime.now().year
                                age_years = current_year - account_year

                                if age_years < 1:
                                    report['risk_score'] += 25
                                    report['behavior_flags'].append(
                                        'Very new account (less than 1 year old) - possible fake'
                                    )
                                elif age_years < 2:
                                    report['risk_score'] += 10
                                    report['behavior_flags'].append(
                                        'Relatively new account (less than 2 years old)'
                                    )
                            except (ValueError, TypeError) as e:
                                logger.debug(f"Error parsing Reddit account age: {str(e)}")

                        # Check posts for conflict keywords
                        posts = reddit.get('recent_posts', [])
                        if posts and isinstance(posts, list):
                            keyword_hits = []

                            for post in posts:
                                if isinstance(post, dict):
                                    content = post.get('content', '').lower() if post.get('content') else ''
                                    for keyword in self.CONFLICT_KEYWORDS:
                                        if keyword and keyword in content:
                                            keyword_hits.append({
                                                'keyword': keyword,
                                                'context': post.get('content', '')[:100],
                                                'platform': 'reddit'
                                            })

                            if keyword_hits:
                                report['keyword_hits'] = keyword_hits
                                report['risk_score'] += min(len(keyword_hits) * 5, 20)  # Cap at 20
                                report['behavior_flags'].append(
                                    f'{len(keyword_hits)} conflict-related keywords found in posts'
                                )
                        
                        logger.info(f"Reddit analysis complete")
                    except Exception as e:
                        logger.error(f"Error in Reddit analysis: {str(e)}")
                        report['analysis_notes'].append(f'Reddit analysis error: {str(e)}')
        except Exception as e:
            logger.error(f"Error accessing Reddit data: {str(e)}")
            report['analysis_notes'].append(f'Reddit data access error: {str(e)}')

        try:
            # 3. GitHub analysis
            if detailed_data and isinstance(detailed_data, dict):
                github = detailed_data.get('github', {})
                
                if github and isinstance(github, dict) and github.get('found') is True:
                    try:
                        # If GitHub links to another social account
                        twitter_linked = github.get('twitter_linked')
                        if twitter_linked:
                            report['findings'].append(
                                f"GitHub links to Twitter account: @{twitter_linked}"
                            )

                        # If location is available
                        location = github.get('location')
                        if location:
                            report['findings'].append(
                                f"Location on GitHub: {location}"
                            )

                        # If email is publicly available
                        email = github.get('email')
                        if email:
                            report['findings'].append(
                                f"Public email found: {email}"
                            )
                        
                        # GitHub profile maturity
                        public_repos = github.get('public_repos', 0)
                        if public_repos > 0:
                            report['findings'].append(
                                f"Has {public_repos} public repositories"
                            )
                        
                        logger.info(f"GitHub analysis complete")
                    except Exception as e:
                        logger.error(f"Error in GitHub analysis: {str(e)}")
                        report['analysis_notes'].append(f'GitHub analysis error: {str(e)}')
        except Exception as e:
            logger.error(f"Error accessing GitHub data: {str(e)}")
            report['analysis_notes'].append(f'GitHub data access error: {str(e)}')

        try:
            # 4. Calculate final risk level
            # ===== CRITICAL FIX: If no real findings, threat must be 0 =====
            # Check if any actual indicators were found
            has_real_findings = (
                len(report.get('platform_presence', {}).get('found_on', [])) > 0 or
                len(report.get('keyword_hits', [])) > 0 or
                len(report.get('behavior_flags', [])) > 0 or
                len(report.get('findings', [])) > 0
            )
            
            if not has_real_findings:
                # No real findings - threat level must be 0
                logger.info(f"[THREAT_SCORING] No real findings for {username}, setting risk_score=0")
                report['risk_score'] = 0
                report['risk_level'] = 'LOW'
                report['findings'] = []
                report['behavior_flags'] = []
                report['recommendations'] = ['No threats detected. Continue standard monitoring.']
                return report
            
            # Cap risk score at 100
            score = min(report['risk_score'], 100)
            report['risk_score'] = score
            
            logger.info(f"[THREAT_SCORING] Real findings detected: score={score}, has_platforms={len(report.get('platform_presence', {}).get('found_on', []))}, keywords={len(report.get('keyword_hits', []))}")
            
            if score >= 75:
                report['risk_level'] = 'CRITICAL'
                report['recommendations'].append(
                    'Escalate to senior investigator immediately'
                )
                report['recommendations'].append(
                    'Collect full post history before account is deleted'
                )
                report['recommendations'].append(
                    'Consider law enforcement notification'
                )
            elif score >= 50:
                report['risk_level'] = 'HIGH'
                report['recommendations'].append(
                    'Escalate to senior investigator immediately'
                )
                report['recommendations'].append(
                    'Collect full post history before account is deleted'
                )
            elif score >= 25:
                report['risk_level'] = 'MEDIUM'
                report['recommendations'].append(
                    'Monitor account for further activity'
                )
                report['recommendations'].append(
                    'Cross-reference with known misinformation campaigns'
                )
            else:
                report['risk_level'] = 'LOW'
                report['recommendations'].append(
                    'Continue monitoring, low immediate threat'
                )
            
            logger.info(f"Analysis complete: username={username}, risk_score={score}, risk_level={report['risk_level']}")
        
        except Exception as e:
            logger.error(f"Error calculating risk level: {str(e)}")
            report['analysis_notes'].append(f'Risk level calculation error: {str(e)}')
            # Ensure risk_level is set
            if 'risk_level' not in report:
                report['risk_level'] = 'UNKNOWN'
        
        return report
    
    def calculate_risk_from_factors(self, factors: dict) -> dict:
        """
        Calculate risk score from multiple factors.
        
        Args:
            factors: Dict with keys like:
                - platform_count: number of platforms where found
                - email_count: number of linked emails
                - phone_linked: boolean
                - account_age: account age in days
                - follower_count: number of followers
                - posting_frequency: posts per week
                - mention_count: number of mentions
                - reported_spam: boolean
                - uses_voip: boolean
                
        Returns:
            Dict with risk_score (0-100), risk_level, confidence, and factors
        """
        risk_score = 20  # Base risk
        risk_factors = []
        
        # Platform presence analysis
        platform_count = factors.get('platform_count', 0)
        if platform_count >= 10:
            risk_score += 25
            risk_factors.append(f'Present on {platform_count} platforms (high coordination)')
        elif platform_count >= 7:
            risk_score += 15
            risk_factors.append(f'Active on {platform_count} platforms')
        elif platform_count >= 4:
            risk_score += 8
            risk_factors.append(f'Presence on {platform_count} platforms')
        
        # Linked accounts factor
        email_count = factors.get('email_count', 0)
        if email_count >= 5:
            risk_score += 20
            risk_factors.append(f'Multiple email addresses ({email_count}) linked')
        elif email_count >= 3:
            risk_score += 10
            risk_factors.append(f'Several emails linked ({email_count})')
        
        # Phone linked
        if factors.get('phone_linked', False):
            risk_score += 15
            risk_factors.append('Phone number linked to account')
        
        # Account age
        account_age = factors.get('account_age', 365)
        if account_age < 30:
            risk_score += 25
            risk_factors.append('Very new account (< 1 month)')
        elif account_age < 90:
            risk_score += 15
            risk_factors.append('Relatively new account (< 3 months)')
        elif account_age < 365:
            risk_score += 8
            risk_factors.append('Account less than 1 year old')
        
        # Spam reports
        if factors.get('reported_spam', False):
            risk_score += 30
            risk_factors.append('Reported as spam or suspicious')
        
        # VoIP usage
        if factors.get('uses_voip', False):
            risk_score += 15
            risk_factors.append('Associated with VoIP number')
        
        # Posting frequency
        posting_freq = factors.get('posting_frequency', 0)
        if posting_freq > 50:  # More than 50 posts per week
            risk_score += 12
            risk_factors.append('Abnormally high posting frequency')
        
        # Mentions/engagement
        mention_count = factors.get('mention_count', 0)
        if mention_count > 100:
            risk_score += 10
            risk_factors.append(f'Frequently mentioned ({mention_count}+)')
        
        # Clamp score to 0-100
        risk_score = max(0, min(100, risk_score))
        
        # Determine risk level
        if risk_score >= self.RISK_THRESHOLDS['CRITICAL']:
            risk_level = 'CRITICAL'
            confidence = min(95, 60 + (risk_score - 90))
        elif risk_score >= self.RISK_THRESHOLDS['HIGH']:
            risk_level = 'HIGH'
            confidence = min(90, 50 + (risk_score - 75) / 15 * 40)
        elif risk_score >= self.RISK_THRESHOLDS['MEDIUM']:
            risk_level = 'MEDIUM'
            confidence = min(85, 40 + (risk_score - 50) / 25 * 45)
        elif risk_score >= self.RISK_THRESHOLDS['LOW']:
            risk_level = 'LOW'
            confidence = min(80, 30 + (risk_score - 25) / 25 * 50)
        else:
            risk_level = 'MINIMAL'
            confidence = 70
        
        confidence = round(confidence)
        
        return {
            'risk_score': risk_score,
            'risk_level': risk_level,
            'confidence': confidence,
            'factors': risk_factors
        }
    
    def get_risk_score(self, analysis_report):
        """Extract risk score from analysis report"""
        return analysis_report.get('risk_score', 0)
    
    def get_risk_category(self, score):
        """Categorize risk score (0-100 scale)"""
        if score >= 80:
            return 'CRITICAL'
        elif score >= 60:
            return 'HIGH'
        elif score >= 40:
            return 'MEDIUM'
        elif score >= 20:
            return 'LOW'
        else:
            return 'MINIMAL'


if __name__ == '__main__':
    # Test analyzer
    analyzer = BehaviorAnalyzer()
    test_results = {
        'platforms': [
            {'platform': 'Facebook', 'found': True},
            {'platform': 'Twitter', 'found': True},
            {'platform': 'Instagram', 'found': True},
        ],
        'total_checked': 10
    }
    report = analyzer.analyze('testuser', test_results)
    import json
    print(json.dumps(report, indent=2))