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
            from app.graph.pipeline import AgathaPipeline
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
                'memory': {
                    'add': '/api/memory/<user_id>/add',
                    'search': '/api/memory/<user_id>/search', 
                    'overview': '/api/memory/<user_id>/overview',
                    'clear': '/api/memory/<user_id>/clear'
                },
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
            
            # Преобразуем messages в правильный формат если нужно
            if messages and isinstance(messages[0], str):
                messages = [{'role': 'user', 'content': msg} for msg in messages]

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

    # Memory Management Endpoints
    @app.route('/api/memory/<user_id>/add', methods=['POST'])
    def add_to_memory(user_id):
        """Добавляет сообщение в память пользователя"""
        try:
            data = request.get_json()
            if not data:
                return json_response({'error': 'No data provided'}), 400

            role = data.get('role')
            content = data.get('content')
            metadata = data.get('metadata', {})

            if not role or not content:
                return json_response({'error': 'role and content are required'}), 400

            # Импортируем систему памяти
            from app.memory.memory_levels import MemoryLevelsManager
            from app.memory.base import Message, MemoryContext
            from datetime import datetime

            # Создаем менеджер памяти
            memory_manager = MemoryLevelsManager(user_id)
            
            # Создаем сообщение и контекст
            message = Message(
                role=role,
                content=content,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            context = MemoryContext(
                user_id=user_id,
                conversation_id=data.get('conversation_id'),
                day_number=data.get('day_number', 1)
            )

            # Добавляем в память
            result = memory_manager.add_message(message, context)

            return json_response({
                'success': True,
                'message': 'Added to memory',
                'result': result,
                'user_id': user_id
            })

        except Exception as e:
            return json_response({'error': str(e), 'type': type(e).__name__}, 500)

    @app.route('/api/memory/<user_id>/search', methods=['POST'])
    def search_memory(user_id):
        """Ищет в памяти пользователя"""
        try:
            data = request.get_json()
            if not data:
                return json_response({'error': 'No data provided'}), 400

            query = data.get('query')
            max_results = data.get('max_results', 5)
            levels = data.get('levels')  # список уровней для поиска

            if not query:
                return json_response({'error': 'query is required'}), 400

            # Импортируем систему памяти
            from app.memory.memory_levels import MemoryLevelsManager, MemoryLevel
            
            memory_manager = MemoryLevelsManager(user_id)
            
            # Конвертируем строки в enum если нужно
            if levels:
                level_enums = []
                for level_str in levels:
                    try:
                        level_enums.append(MemoryLevel(level_str))
                    except ValueError:
                        pass
                levels = level_enums if level_enums else None

            # Выполняем поиск
            results = memory_manager.search_memory(query, levels=levels, max_results=max_results)
            
            # Конвертируем результаты в JSON-совместимый формат
            serializable_results = []
            for result in results:
                serializable_results.append({
                    'content': result.content,
                    'source_level': result.source_level.value,
                    'relevance_score': result.relevance_score,
                    'metadata': result.metadata,
                    'created_at': result.created_at.isoformat() if result.created_at else None
                })

            return json_response({
                'success': True,
                'query': query,
                'results': serializable_results,
                'total_found': len(serializable_results),
                'user_id': user_id
            })

        except Exception as e:
            return json_response({'error': str(e), 'type': type(e).__name__}, 500)

    @app.route('/api/memory/<user_id>/overview', methods=['GET'])
    def get_memory_overview(user_id):
        """Получает обзор памяти пользователя"""
        try:
            from app.memory.memory_levels import MemoryLevelsManager
            
            memory_manager = MemoryLevelsManager(user_id)
            overview = memory_manager.get_memory_overview()
            
            return json_response({
                'success': True,
                'user_id': user_id,
                'overview': overview
            })

        except Exception as e:
            return json_response({'error': str(e), 'type': type(e).__name__}, 500)

    @app.route('/api/memory/<user_id>/clear', methods=['POST'])
    def clear_memory(user_id):
        """Очищает память пользователя"""
        try:
            from app.memory.memory_levels import MemoryLevelsManager
            
            memory_manager = MemoryLevelsManager(user_id)
            
            # Очищаем все уровни памяти
            if memory_manager.short_term:
                memory_manager.short_term.clear()
            if memory_manager.long_term:
                memory_manager.long_term.clear()
            
            return json_response({
                'success': True,
                'message': 'Memory cleared',
                'user_id': user_id
            })

        except Exception as e:
            return json_response({'error': str(e), 'type': type(e).__name__}, 500)

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