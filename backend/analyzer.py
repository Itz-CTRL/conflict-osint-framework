from datetime import datetime

class BehaviorAnalyzer:
    """
    Analyzes scraped data to identify suspicious behavior patterns
    """

    # Keywords related to conflict and misinformation
    CONFLICT_KEYWORDS = [
        'attack', 'kill', 'war', 'bomb', 'destroy', 'fight',
        'hate', 'enemy', 'threat', 'danger', 'fake', 'lie',
        'protest', 'riot', 'coup', 'overthrow', 'uprising',
        'crisis', 'emergency', 'urgent', 'breaking', 'exposed'
    ]

    def analyze(self, username, platform_results, detailed_data=None):
        """
        Run full analysis on collected data
        Returns a complete analysis report
        """
        print(f"\n🧠 Analyzing data for: {username}")

        report = {
            'username': username,
            'analyzed_at': datetime.now().isoformat(),
            'risk_score': 0,
            'risk_level': 'LOW',
            'findings': [],
            'platform_presence': {},
            'behavior_flags': [],
            'keyword_hits': [],
            'recommendations': []
        }

        # 1. Multi-platform presence analysis
        if platform_results:
            found_on = [
                p['platform'] for p in platform_results.get('platforms', [])
                if p.get('found')
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

        # 2. Reddit behavior analysis
        if detailed_data and detailed_data.get('reddit', {}).get('found'):
            reddit = detailed_data['reddit']

            # New account flag
            if reddit.get('account_age'):
                account_year = int(reddit['account_age'][:4])
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

            # Check posts for conflict keywords
            posts = reddit.get('recent_posts', [])
            keyword_hits = []

            for post in posts:
                content = post.get('content', '').lower()
                for keyword in self.CONFLICT_KEYWORDS:
                    if keyword in content:
                        keyword_hits.append({
                            'keyword': keyword,
                            'context': post['content'][:100],
                            'platform': 'reddit'
                        })

            if keyword_hits:
                report['keyword_hits'] = keyword_hits
                report['risk_score'] += len(keyword_hits) * 5
                report['behavior_flags'].append(
                    f'{len(keyword_hits)} conflict-related keywords found in posts'
                )

        # 3. GitHub analysis
        if detailed_data and detailed_data.get('github', {}).get('found'):
            github = detailed_data['github']

            # If GitHub links to another social account
            if github.get('twitter_linked'):
                report['findings'].append(
                    f"GitHub links to Twitter account: @{github['twitter_linked']}"
                )

            # If location is available
            if github.get('location'):
                report['findings'].append(
                    f"Location on GitHub: {github['location']}"
                )

            if github.get('email'):
                report['findings'].append(
                    f"Public email found: {github['email']}"
                )

        # 4. Calculate final risk level
        score = report['risk_score']
        if score >= 50:
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

        print(f"✅ Analysis complete. Risk Level: {report['risk_level']} (Score: {score})")
        return report


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