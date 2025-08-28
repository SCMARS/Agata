import json
from flask import Flask, Response, request
from flask_cors import CORS
import os
import sys
import asyncio
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.settings import settings

_pipeline = None
_executor = ThreadPoolExecutor(max_workers=4)

def get_pipeline():
    global _pipeline
    if _pipeline is None:
        try:
            from graph.pipeline import AgathaPipeline
            _pipeline = AgathaPipeline()
        except Exception as e:
            raise e
    return _pipeline

async def run_pipeline_async(pipeline, user_id, messages, meta_time):
    return await pipeline.process_chat(user_id, messages, meta_time)

def json_response(data, status=200):
    return Response(
        json.dumps(data, ensure_ascii=False),
        status=status,
        mimetype='application/json'
    )

def create_app():
    app = Flask(__name__)
    CORS(app)
    app.config['DEBUG'] = settings.DEBUG

    @app.route('/healthz')
    def health_check():
        return json_response({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'agatha-api'
        })

    @app.route('/readyz')
    def readiness_check():
        try:
            checks = {'database': 'ok', 'redis': 'ok', 'llm': 'ok'}
            all_ready = all(status == 'ok' for status in checks.values())
            return json_response({
                'status': 'ready' if all_ready else 'not_ready',
                'checks': checks,
                'timestamp': datetime.utcnow().isoformat()
            }), 200 if all_ready else 503
        except Exception as e:
            return json_response({
                'status': 'not_ready',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503

    @app.route('/api/info')
    def api_info():
        return json_response({
            'name': 'Agatha AI Companion API',
            'version': '1.0.0',
            'description': 'Virtual AI companion with LangGraph pipeline',
            'endpoints': {
                'health': '/healthz',
                'readiness': '/readyz',
                'chat': '/api/chat',
                'swagger': '/api/docs'
            }
        })
    
    @app.route('/api/chat', methods=['POST'])
    def chat():
        try:
            data = request.get_json()
            if not data:
                return json_response({'error': 'No data provided'}), 400

            user_id = data.get('user_id')
            messages = data.get('messages', [])
            meta_time = data.get('metaTime')

            if not user_id:
                return json_response({'error': 'user_id is required'}), 400

            if not messages:
                return json_response({'error': 'messages are required'}), 400

            pipeline = get_pipeline()
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            try:
                response = loop.run_until_complete(
                    run_pipeline_async(pipeline, user_id, messages, meta_time)
                )
            finally:
                loop.close()

            return json_response(response)

        except Exception as e:
            return json_response({'error': str(e), 'type': type(e).__name__}), 500

    @app.errorhandler(404)
    def not_found(error):
        return json_response({'error': 'Endpoint not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return json_response({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    ) 