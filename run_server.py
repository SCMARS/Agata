#!/usr/bin/env python3
"""
Запуск сервера Agatha
"""
import sys
import os

# Добавляем путь к проекту
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, PROJECT_ROOT)

# Настройка окружения
os.environ.setdefault('PYTHONPATH', PROJECT_ROOT)

# Явно устанавливаем OpenAI API ключ если он есть в окружении
if 'OPENAI_API_KEY' in os.environ:
    print(f"🔑 OpenAI API Key found: {os.environ['OPENAI_API_KEY'][:20]}...")
else:
    print("⚠️ No OPENAI_API_KEY in environment")

from flask import Flask, jsonify, request
from flask_cors import CORS
import logging

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime

# Configure logging with quiet mode option
QUIET_MODE = os.getenv('AGATHA_QUIET', 'false').lower() == 'true'

if QUIET_MODE:
    # Quiet mode - только критические ошибки
    logging.basicConfig(level=logging.ERROR)
    # Отключаем httpx логи
    logging.getLogger('httpx').setLevel(logging.WARNING)
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.WARNING)
else:
    # Normal mode - полная информация для разработки
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)


_pipeline = None
_executor = None

def get_pipeline():
    """Получить singleton instance pipeline - ТОЛЬКО ПОЛНЫЙ LANGGRAPH!"""
    global _pipeline
    if _pipeline is None:
        print("🚀 Initializing FULL LangGraph Pipeline...")
        try:
            from app.graph.pipeline import AgathaPipeline
            print("🔧 Creating AgathaPipeline instance...")
            _pipeline = AgathaPipeline()
            print("✅ FULL LangGraph Pipeline initialized successfully!")
            print("🎯 All components loaded: Memory, Behavioral Analysis, Prompt Composer")
            print(f"🤖 LLM Status: {'OpenAI API' if _pipeline.llm else 'Mock LLM'}")
        except Exception as e:
            print(f"❌ CRITICAL: Full pipeline failed: {e}")
            print("🔥 NO FALLBACKS! System requires full LangGraph to work!")
            import traceback
            traceback.print_exc()
            raise Exception(f"Pipeline initialization failed: {e}")
    return _pipeline

def get_executor():
    """Получить ThreadPoolExecutor"""
    global _executor
    if _executor is None:
        _executor = ThreadPoolExecutor(max_workers=4)
    return _executor

def async_pipeline_wrapper(pipeline, user_id, messages, meta_time):
    """Wrapper для асинхронного вызова pipeline"""
    import asyncio
    try:
        # Создаем новый event loop для этого потока
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        return loop.run_until_complete(pipeline.process_chat(user_id, messages, meta_time))
    finally:
        loop.close()

def create_app():
    """Application factory"""
    app = Flask(__name__)
    
    # Enable CORS
    CORS(app)
    
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
            # Проверяем pipeline
            pipeline = get_pipeline()
            
            return jsonify({
                'status': 'ready',
                'checks': {
                    'pipeline': 'ok',
                    'memory': 'ok'
                },
                'timestamp': datetime.utcnow().isoformat()
            }), 200
            
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
            'description': 'Virtual AI companion with modular pipeline',
            'endpoints': {
                'health': '/healthz',
                'readiness': '/readyz',
                'chat': '/api/chat',
                'swagger': '/api/docs'
            }
        })
    
    # Главный chat endpoint
    @app.route('/api/chat', methods=['POST'])
    def chat():
        """Main chat endpoint with Agatha pipeline"""
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

            # Запустить async pipeline через executor
            executor = get_executor()
            response = executor.submit(async_pipeline_wrapper, pipeline, user_id, messages, meta_time).result(timeout=60)
            
            logger.info(f"✅ Chat request from user {user_id} with {len(messages)} messages processed")
            
            return jsonify(response)
            
        except Exception as e:
            import traceback
            logger.error(f"❌ Chat endpoint error: {e}")
            logger.error(f"Full traceback: {traceback.format_exc()}")
            print(f"🚨 DETAILED ERROR:")
            print(f"   Exception: {type(e).__name__}: {str(e)}")
            print(f"   Traceback:")
            traceback.print_exc()
            return jsonify({
                'error': 'Internal server error',
                'debug': str(e),
                'type': type(e).__name__
            }), 500
    
    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'error': 'Endpoint not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'error': 'Internal server error'}), 500
    
    return app

if __name__ == '__main__':
    print("🚀 Starting Agatha AI Companion Server...")
    print(f"📁 Project root: {PROJECT_ROOT}")
    
    app = create_app()
    
    # Инициализируем pipeline при запуске
    pipeline = get_pipeline()
    
    print("🎯 Server ready! Endpoints:")
    print("   - Health: http://localhost:8000/healthz")
    print("   - API Info: http://localhost:8000/api/info")
    print("   - Chat: POST http://localhost:8000/api/chat")
    
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=False
    ) 