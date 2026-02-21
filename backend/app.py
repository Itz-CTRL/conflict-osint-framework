from flask import Flask, jsonify, request
from flask_cors import CORS
from database import Session, Investigation, Finding, init_db
from scraper import OSINTScraper
from analyzer import BehaviorAnalyzer
from network_builder import NetworkGraphBuilder
import json

# Initialize
init_db()
app = Flask(__name__)
CORS(app)
scraper = OSINTScraper()
analyzer = BehaviorAnalyzer()

@app.route('/api/health', methods=['GET'])
def health():
    return jsonify({'status': 'online', 'platform': 'SOKO AERIAL OSINT'})

@app.route('/api/investigations', methods=['GET'])
def get_all():
    session = Session()
    investigations = session.query(Investigation).all()
    result = [i.to_dict() for i in investigations]
    session.close()
    return jsonify(result)

@app.route('/api/investigations', methods=['POST'])
def create():
    data = request.get_json()
    username = data.get('username', '').strip()

    if not username:
        return jsonify({'error': 'Username is required'}), 400

    session = Session()
    inv = Investigation(username=username, status='pending')
    session.add(inv)
    session.commit()
    result = inv.to_dict()
    session.close()
    return jsonify(result), 201

@app.route('/api/investigate/<int:inv_id>', methods=['POST'])
def investigate(inv_id):
    session = Session()
    inv = session.query(Investigation).filter_by(id=inv_id).first()

    if not inv:
        session.close()
        return jsonify({'error': 'Investigation not found'}), 404

    username = inv.username
    inv.status = 'running'
    session.commit()

    try:
        # Step 1: Search username across platforms
        platform_results = scraper.search_username(username)

        # Step 2: Get detailed data from reliable sources
        reddit_data = scraper.get_reddit_data(username)
        github_data = scraper.get_github_data(username)

        detailed_data = {
            'reddit': reddit_data,
            'github': github_data
        }

        # Step 3: Save platform findings
        for platform_result in platform_results['platforms']:
            finding = Finding(
                investigation_id=inv_id,
                platform=platform_result['platform'],
                username=username,
                profile_url=platform_result.get('url', ''),
                data=json.dumps(platform_result),
                found=1 if platform_result.get('found') else 0
            )
            session.add(finding)

        # Step 4: Run behavior analysis
        analysis = analyzer.analyze(username, platform_results, detailed_data)

        # Step 5: Save analysis as a finding
        analysis_finding = Finding(
            investigation_id=inv_id,
            platform='ANALYSIS',
            username=username,
            profile_url='',
            data=json.dumps({
                'platform_results': platform_results,
                'reddit': reddit_data,
                'github': github_data,
                'analysis': analysis
            }),
            found=1
        )
        session.add(analysis_finding)

        inv.status = 'completed'
        session.commit()

        result = {
            'investigation_id': inv_id,
            'username': username,
            'status': 'completed',
            'platform_results': platform_results,
            'detailed_data': detailed_data,
            'analysis': analysis
        }

        session.close()
        return jsonify(result)

    except Exception as e:
        inv.status = 'failed'
        session.commit()
        session.close()
        return jsonify({'error': str(e)}), 500

@app.route('/api/investigations/<int:inv_id>', methods=['GET'])
def get_one(inv_id):
    session = Session()
    inv = session.query(Investigation).filter_by(id=inv_id).first()

    if not inv:
        session.close()
        return jsonify({'error': 'Not found'}), 404

    findings = session.query(Finding).filter_by(investigation_id=inv_id).all()

    # Build network graph
    builder = NetworkGraphBuilder()
    network_data = builder.build_from_investigation(inv.to_dict(), [f.to_dict() for f in findings])

    result = {
        'investigation': inv.to_dict(),
        'findings': [f.to_dict() for f in findings],
        'network': network_data,
        'stats': builder.get_graph_stats()
    }
    session.close()
    return jsonify(result)

@app.route('/api/investigations/<int:inv_id>', methods=['DELETE'])
def delete_investigation(inv_id):
    session = Session()
    inv = session.query(Investigation).filter_by(id=inv_id).first()

    if not inv:
        session.close()
        return jsonify({'error': 'Investigation not found'}), 404

    # Delete all findings associated with this investigation
    session.query(Finding).filter_by(investigation_id=inv_id).delete()
    # Delete the investigation
    session.delete(inv)
    session.commit()
    session.close()
    return jsonify({'message': 'Investigation deleted successfully'}), 200

if __name__ == '__main__':
    print("\n" + "="*50)
    print("  SOKO AERIAL OSINT PLATFORM")
    print("  Backend running on http://127.0.0.1:5000")
    print("="*50 + "\n")
    app.run(debug=True, port=5000)