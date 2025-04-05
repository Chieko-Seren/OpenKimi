#!/bin/bash

# Default configuration
DEFAULT_CONFIG="./examples/config.json"
DEFAULT_HOST="127.0.0.1"
DEFAULT_PORT=8000
DEFAULT_MCP=1
AUTO_RELOAD=""
AUTO_OPEN_UI=true

# --- Parse Command Line Arguments --- 
CONFIG_FILE="$DEFAULT_CONFIG"
HOST="$DEFAULT_HOST"
PORT="$DEFAULT_PORT"
MCP_CANDIDATES="$DEFAULT_MCP"

while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        -c|--config)
        CONFIG_FILE="$2"
        shift # past argument
        shift # past value
        ;;        
        --host)
        HOST="$2"
        shift # past argument
        shift # past value
        ;;
        --port)
        PORT="$2"
        shift # past argument
        shift # past value
        ;;
        --mcp-candidates)
        MCP_CANDIDATES="$2"
        shift # past argument
        shift # past value
        ;;
        --reload)
        AUTO_RELOAD="--reload"
        shift # past argument
        ;;
        --no-open)
        AUTO_OPEN_UI=false
        shift # past argument
        ;;
        -h|--help)
        echo "Usage: $0 [options]"
        echo "Options:"
        echo "  -c, --config FILE       Path to KimiEngine JSON config file (default: $DEFAULT_CONFIG)"
        echo "      --host HOST         Host to bind the server to (default: $DEFAULT_HOST)"
        echo "      --port PORT         Port to bind the server to (default: $DEFAULT_PORT)"
        echo "      --mcp-candidates N  Number of MCP candidates (default: $DEFAULT_MCP)"
        echo "      --reload            Enable auto-reloading for development"
        echo "      --no-open           Do not automatically open the web UI in the browser"
        echo "  -h, --help            Show this help message"
        exit 0
        ;;
        *)
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

# --- Check if config file exists --- 
if [ ! -f "$CONFIG_FILE" ]; then
    echo "Error: Config file not found at $CONFIG_FILE"
    echo "Please specify a valid config file using -c or --config."
    exit 1
fi


# --- Start API Server in Background --- 
API_URL="http://$HOST:$PORT"
echo "Starting OpenKimi API server..."
echo "  Config: $CONFIG_FILE"
echo "  URL: $API_URL"
echo "  MCP Candidates: $MCP_CANDIDATES"
if [ -n "$AUTO_RELOAD" ]; then
    echo "  Auto-reload: Enabled"
fi

# Make sure current directory is in Python path
export PYTHONPATH=$PYTHONPATH:$(pwd)
echo "Setting PYTHONPATH: $PYTHONPATH"

# --- Open Web UI in a separate process --- 
if $AUTO_OPEN_UI; then
    # 在3秒后启动网站
    (
        echo "Will open Web UI in 3 seconds..."
        sleep 3
        UI_PATH="web/index.html"
        echo "Opening Web UI in browser: $UI_PATH"
        case "$(uname -s)" in
            Darwin)
                open "$UI_PATH"
                ;;
            Linux)
                if command -v xdg-open &> /dev/null; then
                    xdg-open "$UI_PATH"
                elif command -v gnome-open &> /dev/null; then
                    gnome-open "$UI_PATH"
                elif command -v kde-open &> /dev/null; then
                    kde-open "$UI_PATH"
                else
                    echo "Could not detect command to open browser. Please open '$UI_PATH' manually."
                fi
                ;;
            MINGW*|CYGWIN*|MSYS*)
                start "$UI_PATH"
                ;;
            *)
                echo "Unsupported OS for automatic opening. Please open '$UI_PATH' manually."
                ;;
        esac
    ) &
else
    echo "Web UI available at: web/index.html (relative to project root)"
fi

# Run the server in foreground 
echo "Running server in foreground..."
python -m openkimi.api.server --config "$CONFIG_FILE" --host "$HOST" --port "$PORT" --mcp-candidates "$MCP_CANDIDATES" $AUTO_RELOAD
