from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
import os
import sys
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# Add the parent directory to the path to import from app
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from config.settings import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ГЛОБАЛЬНЫЙ PIPELINE INSTANCE для избежания пересоздания
_pipeline = None
_executor = ThreadPoolExecutor(max_workers=4)

def get_pipeline():
    """Получить singleton instance pipeline"""
    global _pipeline
    if _pipeline is None:
        try:
            from graph.pipeline import AgathaPipeline
            _pipeline = AgathaPipeline()
            print("✅ Pipeline initialized successfully")
        except Exception as e:
            print(f"❌ Pipeline initialization failed: {e}")
            # Создаем mock pipeline
            class MockPipeline:
                async def process_chat(self, user_id, messages, meta_time=None):
                    return {
                        "parts": [f"Mock response for user {user_id}: {messages[-1].get('content', 'No content')}"],
                        "has_question": False,
                        "delays_ms": [0]
                    }
            _pipeline = MockPipeline()
    return _pipeline

def run_async_in_thread(async_func, *args, **kwargs):
    """Запускать async функции в отдельном потоке"""
    def wrapper():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(async_func(*args, **kwargs))
        finally:
            loop.close()
    
    future = _executor.submit(wrapper)
    return future.result(timeout=30)  # 30 секунд timeout

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
    # Configuration
    app.config['DEBUG'] = settings.DEBUG
    
    # Health check endpoints
    @app.route('/healthz')
    def health_check():
        """Basic health check endpoint"""
        return jsonify({
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'service': 'agatha-api'
        }), 200
    
    @app.route('/readyz')
    def readiness_check():
        """Readiness check endpoint"""
        try:
            # TODO: Реальные проверки подключений
            checks = {
                'database': 'ok',
                'redis': 'ok',
                'llm': 'ok'
            }
            
            all_ready = all(status == 'ok' for status in checks.values())
            
            return jsonify({
                'status': 'ready' if all_ready else 'not_ready',
                'checks': checks,
                'timestamp': datetime.utcnow().isoformat()
            }), 200 if all_ready else 503
            
        except Exception as e:
            logger.error(f"Readiness check failed: {e}")
            return jsonify({
                'status': 'not_ready',
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }), 503
    
    # API Info endpoint
    @app.route('/api/info')
    def api_info():
        """API information endpoint"""
        return jsonify({
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
    
    # ИСПРАВЛЕННЫЙ chat endpoint
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Main chat endpoint with Agatha pipeline - ИСПРАВЛЕНО"""
        try:
            data = request.get_json()
            
            # Validate input
            if not data:
                return jsonify({'error': 'No data provided'}), 400
            
            user_id = data.get('user_id')
            messages = data.get('messages', [])
            meta_time = data.get('metaTime')
            
            if not user_id:
                return jsonify({'error': 'user_id is required'}), 400
            
            if not messages:
                return jsonify({'error': 'messages are required'}), 400
            
            # Получить pipeline singleton
            pipeline = get_pipeline()
            
            # ПРАВИЛЬНЫЙ async вызов в отдельном потоке
            response = run_async_in_thread(
                pipeline.process_chat, 
                user_id, 
                messages, 
                meta_time
            )
            
            logger.info(f"Chat request from user {user_id} with {len(messages)} messages processed")
            
            return jsonify(response)
            
        except Exception as e:
            logger.error(f"Chat endpoint error: {e}")
            return jsonify({'error': 'Internal server error'}), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(
        host=settings.HOST,
        port=settings.PORT,
        debug=settings.DEBUG
    ) 