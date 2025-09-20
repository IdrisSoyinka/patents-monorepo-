"""Flask web application for Patent Search Agent UI."""
import logging
import os
import uuid
import traceback
from flask import Flask, render_template, request, jsonify, session, redirect, url_for
from werkzeug.serving import run_simple
from src.patent_search_agent.graph import create_graph
from langgraph.types import Command
import json

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'your-secret-key-here')

# Global variable to store the graph instance
graph_app = None
active_sessions = {}

def get_graph():
    """Get or create the graph instance."""
    global graph_app
    if graph_app is None:
        try:
            graph_app = create_graph()
            logger.info("Graph instance created successfully")
        except Exception as e:
            logger.error(f"Error creating graph: {e}")
            raise
    return graph_app

# Add request logging middleware
@app.before_request
def log_request_info():
    logger.info(f"=== INCOMING REQUEST ===")
    logger.info(f"URL: {request.url}")
    logger.info(f"Method: {request.method}")
    logger.info(f"Path: {request.path}")
    logger.info(f"Headers: {dict(request.headers)}")
    if request.method == 'POST':
        logger.info(f"Content-Type: {request.content_type}")
        logger.info(f"JSON data: {request.get_json(silent=True)}")
    logger.info("========================")

# Test endpoint
@app.route('/test')
def test():
    """Test endpoint to verify Flask is working."""
    routes = []
    for rule in app.url_map.iter_rules():
        routes.append({
            'rule': rule.rule,
            'methods': list(rule.methods),
            'endpoint': rule.endpoint
        })
    return jsonify({
        'message': 'Flask app is working!',
        'routes': routes,
        'request_method': request.method
    })

@app.route('/')
def index():
    """Main page with patent search form."""
    logger.info("Index route accessed")
    return render_template('index.html')

@app.route('/start_search', methods=['POST', 'OPTIONS'])
def start_search():
    """Start a new patent search workflow."""
    logger.info("=== START_SEARCH ENDPOINT CALLED ===")
    logger.info(f"Request method: {request.method}")
    logger.info(f"Content type: {request.content_type}")
    
    # Handle OPTIONS request for CORS
    if request.method == 'OPTIONS':
        logger.info("Handling OPTIONS request")
        response = jsonify({'status': 'OK'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    try:
        logger.info("Processing POST request")
        
        # Check if request contains JSON data
        if not request.is_json:
            logger.error(f"Request is not JSON. Content-Type: {request.content_type}")
            return jsonify({'error': 'Request must be JSON'}), 400
            
        data = request.get_json()
        logger.info(f"Received data: {data}")
        
        if not data:
            logger.error("No JSON data received")
            return jsonify({'error': 'No data received'}), 400
            
        patent_description = data.get('patent_description', '').strip()
        max_results = data.get('max_results', 10)
        
        logger.info(f"Patent description length: {len(patent_description)}")
        logger.info(f"Max results: {max_results}")
        
        if not patent_description:
            logger.error("Patent description is empty")
            return jsonify({'error': 'Patent description is required'}), 400
        
        # Create a new session
        thread_id = str(uuid.uuid4())
        session['thread_id'] = thread_id
        
        logger.info(f"Created new thread: {thread_id}")
        
        # Store session data
        active_sessions[thread_id] = {
            'patent_description': patent_description,
            'max_results': max_results,
            'current_state': None,
            'workflow_complete': False
        }
        
        # Initialize the workflow
        initial_state = {
            "patent_description": patent_description,
            "max_results": max_results,
            "messages": [],
        }
        
        config = {"configurable": {"thread_id": thread_id}}
        
        try:
            app_instance = get_graph()
            logger.info("Graph instance obtained successfully")
        except Exception as e:
            logger.error(f"Error getting graph instance: {e}")
            return jsonify({'error': f'Graph initialization failed: {str(e)}'}), 500
        
        try:
            # Run until first interrupt (human validation)
            logger.info("Running graph with initial state")
            result = app_instance.invoke(initial_state, config=config)
            logger.info("Graph execution completed")
            logger.info(f"Result keys: {result.keys() if result else 'None'}")
        except Exception as e:
            logger.error(f"Error running graph: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'error': f'Graph execution failed: {str(e)}'}), 500
        
        # Store the current state
        active_sessions[thread_id]['current_state'] = result
        
        # Check if we need human validation
        if result.get('seed_keywords'):
            logger.info("Returning keyword validation response")
            return jsonify({
                'thread_id': thread_id,
                'status': 'waiting_validation',
                'seed_keywords': result.get('seed_keywords').dict(),
                'patent_description': patent_description,
                'message': 'Please review and validate the extracted keywords.'
            })
        else:
            logger.error("No seed keywords found in result")
            logger.error(f"Result content: {result}")
            return jsonify({'error': 'Failed to extract keywords'}), 500
            
    except Exception as e:
        logger.error(f"Unexpected error in start_search: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': f'Internal server error: {str(e)}'}), 500

@app.route('/validate_keywords', methods=['POST'])
def validate_keywords():
    """Handle user validation of keywords."""
    logger.info("Validate keywords endpoint called")
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        action = data.get('action')  # 'accept', 'reject', or 'edit'
        keywords = data.get('keywords', {})
        
        if not thread_id or thread_id not in active_sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        if action not in ['accept', 'reject', 'edit']:
            return jsonify({'error': 'Invalid action'}), 400
        
        config = {"configurable": {"thread_id": thread_id}}
        app_instance = get_graph()
        
        # Create the appropriate command based on action
        if action == 'accept':
            command = Command(resume=[{"type": "accept"}])
        elif action == 'reject':
            command = Command(resume=[{"type": "reject"}])
        elif action == 'edit':
            command = Command(resume=[{
                "type": "edit",
                "args": {"keywords": keywords}
            }])
        
        # Continue the workflow
        result = app_instance.invoke(command, config=config)
        
        # Update session state
        active_sessions[thread_id]['current_state'] = result
        
        # Check if workflow is complete
        if result.get('final_queries') or result.get('search_results'):
            active_sessions[thread_id]['workflow_complete'] = True
            return jsonify({
                'status': 'complete',
                'result': {
                    'seed_keywords': result.get('seed_keywords'),
                    'enhanced_keywords': result.get('enhanced_keywords'),
                    'ipc_codes': result.get('ipc_codes'),
                    'final_queries': result.get('final_queries'),
                    'search_results': result.get('search_results'),
                    'evaluation_scores': result.get('evaluation_scores')
                }
            })
        else:
            # Still need more validation
            return jsonify({
                'status': 'waiting_validation',
                'seed_keywords': result.get('seed_keywords'),
                'message': 'Please review the updated keywords.'
            })
            
    except Exception as e:
        logger.error(f"Error validating keywords: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/get_session_status/<thread_id>')
def get_session_status(thread_id):
    """Get the current status of a search session."""
    logger.info(f"Get session status called for thread: {thread_id}")
    try:
        if thread_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = active_sessions[thread_id]
        current_state = session_data.get('current_state', {})
        
        return jsonify({
            'thread_id': thread_id,
            'workflow_complete': session_data.get('workflow_complete', False),
            'patent_description': session_data.get('patent_description'),
            'current_state': {
                'seed_keywords': current_state.get('seed_keywords'),
                'enhanced_keywords': current_state.get('enhanced_keywords'),
                'ipc_codes': current_state.get('ipc_codes'),
                'final_queries': current_state.get('final_queries'),
                'search_results': current_state.get('search_results'),
                'evaluation_scores': current_state.get('evaluation_scores')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/results/<thread_id>')
def results(thread_id):
    """Display results page."""
    logger.info(f"Results page requested for thread: {thread_id}")
    if thread_id not in active_sessions:
        return redirect(url_for('index'))
    
    session_data = active_sessions[thread_id]
    return render_template('results.html', 
                         thread_id=thread_id,
                         session_data=session_data)

@app.errorhandler(404)
def not_found_error(error):
    logger.error(f"404 error occurred: {error}")
    logger.error(f"Request URL: {request.url}")
    logger.error(f"Request method: {request.method}")
    return jsonify({'error': 'Endpoint not found', 'url': request.url}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"500 error occurred: {error}")
    return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Patent Search Agent Web Interface on port {port}")
    print(f"📝 Debug mode: {debug}")
    print(f"🌐 Access the application at: http://localhost:{port}")
    
    # Test graph creation at startup
    try:
        get_graph()
        print("✅ Graph initialization successful")
    except Exception as e:
        print(f"❌ Graph initialization failed: {e}")
        print("Please check your dependencies and Ollama setup")
    
    # Log all registered routes
    print("\n📋 Registered routes:")
    for rule in app.url_map.iter_rules():
        print(f"  {rule.rule} [{', '.join(rule.methods)}] -> {rule.endpoint}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)        }
        
        config = {"configurable": {"thread_id": thread_id}}
        app_instance = get_graph()
        
        # Run until first interrupt (human validation)
        result = app_instance.invoke(initial_state, config=config)
        
        # Store the current state
        active_sessions[thread_id]['current_state'] = result
        
        # Check if we need human validation
        if result.get('seed_keywords'):
            return jsonify({
                'thread_id': thread_id,
                'status': 'waiting_validation',
                'seed_keywords': result.get('seed_keywords'),
                'patent_description': patent_description,
                'message': 'Please review and validate the extracted keywords.'
            })
        else:
            return jsonify({'error': 'Failed to extract keywords'}), 500
            
    except Exception as e:
        logger.error(f"Error starting search: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/validate_keywords', methods=['POST'])
def validate_keywords():
    """Handle user validation of keywords."""
    try:
        data = request.get_json()
        thread_id = data.get('thread_id')
        action = data.get('action')  # 'accept', 'reject', or 'edit'
        keywords = data.get('keywords', {})
        
        if not thread_id or thread_id not in active_sessions:
            return jsonify({'error': 'Invalid session'}), 400
        
        if action not in ['accept', 'reject', 'edit']:
            return jsonify({'error': 'Invalid action'}), 400
        
        config = {"configurable": {"thread_id": thread_id}}
        app_instance = get_graph()
        
        # Create the appropriate command based on action
        if action == 'accept':
            command = Command(resume=[{"type": "accept"}])
        elif action == 'reject':
            command = Command(resume=[{"type": "reject"}])
        elif action == 'edit':
            command = Command(resume=[{
                "type": "edit",
                "args": {"keywords": keywords}
            }])
        
        # Continue the workflow
        result = app_instance.invoke(command, config=config)
        
        # Update session state
        active_sessions[thread_id]['current_state'] = result
        
        # Check if workflow is complete
        if result.get('final_queries') or result.get('search_results'):
            active_sessions[thread_id]['workflow_complete'] = True
            return jsonify({
                'status': 'complete',
                'result': {
                    'seed_keywords': result.get('seed_keywords'),
                    'enhanced_keywords': result.get('enhanced_keywords'),
                    'ipc_codes': result.get('ipc_codes'),
                    'final_queries': result.get('final_queries'),
                    'search_results': result.get('search_results'),
                    'evaluation_scores': result.get('evaluation_scores')
                }
            })
        else:
            # Still need more validation
            return jsonify({
                'status': 'waiting_validation',
                'seed_keywords': result.get('seed_keywords'),
                'message': 'Please review the updated keywords.'
            })
            
    except Exception as e:
        logger.error(f"Error validating keywords: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/get_session_status/<thread_id>')
def get_session_status(thread_id):
    """Get the current status of a search session."""
    try:
        if thread_id not in active_sessions:
            return jsonify({'error': 'Session not found'}), 404
        
        session_data = active_sessions[thread_id]
        current_state = session_data.get('current_state', {})
        
        return jsonify({
            'thread_id': thread_id,
            'workflow_complete': session_data.get('workflow_complete', False),
            'patent_description': session_data.get('patent_description'),
            'current_state': {
                'seed_keywords': current_state.get('seed_keywords'),
                'enhanced_keywords': current_state.get('enhanced_keywords'),
                'ipc_codes': current_state.get('ipc_codes'),
                'final_queries': current_state.get('final_queries'),
                'search_results': current_state.get('search_results'),
                'evaluation_scores': current_state.get('evaluation_scores')
            }
        })
        
    except Exception as e:
        logger.error(f"Error getting session status: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/results/<thread_id>')
def results(thread_id):
    """Display results page."""
    if thread_id not in active_sessions:
        return redirect(url_for('index'))
    
    session_data = active_sessions[thread_id]
    return render_template('results.html', 
                         thread_id=thread_id,
                         session_data=session_data)


@app.errorhandler(404)
def not_found_error(error):
    return render_template('404.html'), 404


@app.errorhandler(500)
def internal_error(error):
    return render_template('500.html'), 500


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    print(f"🚀 Starting Patent Search Agent Web Interface on port {port}")
    print(f"📝 Debug mode: {debug}")
    print(f"🌐 Access the application at: http://localhost:{port}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
