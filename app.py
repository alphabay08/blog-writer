"""
Blog Writer AI — Final Edition
Backend: Render Free Tier | Frontend: Netlify
100% Free OpenRouter models | No LinkedIn OAuth needed
"""

import os
from flask import Flask
from flask_cors import CORS
from routes.routes import blog_bp, history_bp


def create_app():
    app = Flask(__name__)

    frontend_url = os.environ.get("FRONTEND_URL", "*")
    CORS(app, origins=[frontend_url, "http://localhost:3000", "http://localhost:8080"])

    app.register_blueprint(blog_bp,    url_prefix="/api/blog")
    app.register_blueprint(history_bp, url_prefix="/api/history")

    @app.route("/health")
    def health():
        from utils.openrouter import MODELS
        return {
            "status":  "ok",
            "version": "3.1-free",
            "agents":  len(MODELS),
            "models":  list(MODELS.values()),
        }

    return app


app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)
