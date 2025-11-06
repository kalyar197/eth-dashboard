# trends/backend/app.py
"""
Flask API server for Google Trends data collection system.

Provides REST endpoints for:
- Keyword management (CRUD)
- Trend data retrieval
- Status tracking
- Region information
"""

from flask import Flask, jsonify, request
from flask_cors import CORS

from data.trends_manager import TrendsManager
from config import FLASK_HOST, FLASK_PORT, CORS_ORIGINS

# Initialize Flask app
app = Flask(__name__)
CORS(app, origins=CORS_ORIGINS)

# Initialize trends manager
manager = TrendsManager()


@app.route('/api/keywords', methods=['GET'])
def get_keywords():
    """
    Get list of all keywords.

    Returns:
        JSON: {keywords: [{id, keyword, created_at, status, ...}, ...]}
    """
    try:
        keywords = manager.get_all_keywords()
        return jsonify({'keywords': keywords})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/keywords', methods=['POST'])
def add_keyword():
    """
    Add new keyword and trigger data fetch.

    Request Body:
        {keyword: string}

    Returns:
        JSON: {id, keyword, status, ...}
    """
    try:
        data = request.json
        keyword = data.get('keyword', '').strip()

        if not keyword:
            return jsonify({'error': 'Keyword is required'}), 400

        result = manager.add_keyword(keyword)
        return jsonify(result), 201

    except ValueError as e:
        # Duplicate keyword or validation error
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/keywords/<keyword_id>', methods=['DELETE'])
def delete_keyword(keyword_id):
    """
    Delete keyword and associated data.

    Args:
        keyword_id: UUID string

    Returns:
        JSON: {success: bool, message: string}
    """
    try:
        success = manager.delete_keyword(keyword_id)

        if success:
            return jsonify({'success': True, 'message': 'Keyword deleted successfully'})
        else:
            return jsonify({'error': 'Keyword not found'}), 404

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trends/<keyword>', methods=['GET'])
def get_trend_data_by_keyword(keyword):
    """
    Get trend data for a keyword across all regions.

    Args:
        keyword: Search term

    Returns:
        JSON: {
            keyword: string,
            regions: {
                'US-NY-501': [[timestamp, value], ...],
                'CH-ZH': [[timestamp, value], ...],
                ...
            }
        }
    """
    try:
        data = manager.get_trend_data_for_keyword(keyword)

        if not data:
            return jsonify({'error': f'No data found for keyword "{keyword}"'}), 404

        return jsonify({
            'keyword': keyword,
            'regions': data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trends/<keyword>/<region>', methods=['GET'])
def get_trend_data_by_keyword_region(keyword, region):
    """
    Get trend data for specific keyword and region.

    Args:
        keyword: Search term
        region: Geographic code

    Returns:
        JSON: {
            keyword: string,
            region: string,
            data: [[timestamp, value], ...]
        }
    """
    try:
        from data.storage import load_trend_data
        data = load_trend_data(keyword, region)

        if not data:
            return jsonify({
                'error': f'No data found for "{keyword}" in region "{region}"'
            }), 404

        return jsonify({
            'keyword': keyword,
            'region': region,
            'data': data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/trends/region/<region>', methods=['GET'])
def get_trend_data_by_region(region):
    """
    Get trend data for all keywords in a specific region.

    Args:
        region: Geographic code

    Returns:
        JSON: {
            region: string,
            keywords: {
                'bitcoin': [[timestamp, value], ...],
                'ethereum': [[timestamp, value], ...],
                ...
            }
        }
    """
    try:
        data = manager.get_trend_data_for_region(region)

        if not data:
            return jsonify({'error': f'No data found for region "{region}"'}), 404

        return jsonify({
            'region': region,
            'keywords': data
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/status/<keyword_id>', methods=['GET'])
def get_status(keyword_id):
    """
    Get fetch status for a keyword.

    Args:
        keyword_id: UUID string

    Returns:
        JSON: {
            id, keyword, status,
            completed_regions: [...],
            failed_regions: [...],
            progress: {current, total}
        }
    """
    try:
        keyword = manager.get_keyword_by_id(keyword_id)

        if not keyword:
            return jsonify({'error': 'Keyword not found'}), 404

        from config import ALL_REGION_CODES
        return jsonify({
            'id': keyword['id'],
            'keyword': keyword['keyword'],
            'status': keyword['status'],
            'completed_regions': keyword.get('completed_regions', []),
            'failed_regions': keyword.get('failed_regions', []),
            'progress': {
                'current': len(keyword.get('completed_regions', [])),
                'total': len(ALL_REGION_CODES)
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/regions', methods=['GET'])
def get_regions():
    """
    Get list of all configured regions.

    Returns:
        JSON: {regions: [{code, label, level, country, note}, ...]}
    """
    try:
        regions = manager.get_all_regions()
        return jsonify({'regions': regions})
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.

    Returns:
        JSON: {status: 'ok', message: string}
    """
    return jsonify({
        'status': 'ok',
        'message': 'Google Trends API server is running'
    })


if __name__ == '__main__':
    print("\n" + "="*70)
    print("Google Trends Data Collection System - API Server")
    print("="*70)
    print(f"Running on: http://{FLASK_HOST}:{FLASK_PORT}")
    print(f"CORS enabled for: {', '.join(CORS_ORIGINS)}")
    print("="*70 + "\n")

    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=False)
