#!/usr/bin/env python3
"""
直接启动OpenKimi API服务器的脚本
"""
import os
import sys
import logging
import argparse
import time

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

def run_server(config_path, host='127.0.0.1', port=8000, mcp_candidates=1, reload=False):
    """直接运行服务器"""
    try:
        from openkimi import KimiEngine
        from openkimi.api.server import app
        import uvicorn
        
        logger.info(f"正在使用配置文件: {config_path}")
        
        # 检查配置文件是否存在
        if not os.path.exists(config_path):
            logger.error(f"配置文件不存在: {config_path}")
            return False
            
        # 检查配置文件内容
        try:
            import json
            with open(config_path, 'r') as f:
                config = json.load(f)
                logger.info(f"配置文件内容: {config}")
        except Exception as e:
            logger.error(f"读取配置文件时出错: {e}")
            return False
        
        # 手动初始化引擎
        logger.info("手动初始化KimiEngine...")
        try:
            engine = KimiEngine(config_path=config_path, mcp_candidates=mcp_candidates)
            logger.info("KimiEngine初始化成功")
            
            # 设置全局引擎变量
            from openkimi.api.server import initialize_engine
            
            # 创建一个类似于命令行参数的对象
            class Args:
                pass
                
            args = Args()
            args.config = config_path
            args.mcp_candidates = mcp_candidates
            
            # 调用服务器初始化函数
            initialize_engine(args)
            
            # 启动服务器
            logger.info(f"启动uvicorn服务器 在 {host}:{port}")
            uvicorn.run(
                app, 
                host=host, 
                port=port, 
                reload=reload, 
                log_level="info"
            )
            return True
            
        except Exception as e:
            logger.error(f"初始化KimiEngine时出错: {e}")
            import traceback
            traceback.print_exc()
            return False
            
    except ImportError as e:
        logger.error(f"导入所需模块时出错: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="启动OpenKimi API服务器")
    parser.add_argument("--config", "-c", type=str, default="examples/config.json", 
                        help="配置文件路径 (默认: examples/config.json)")
    parser.add_argument("--host", type=str, default="127.0.0.1", 
                        help="服务器主机名 (默认: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=8000, 
                        help="服务器端口 (默认: 8000)")
    parser.add_argument("--mcp-candidates", type=int, default=1, 
                        help="MCP候选数量 (默认: 1)")
    parser.add_argument("--reload", action="store_true", 
                        help="启用自动重载")
    args = parser.parse_args()
    
    print(f"启动OpenKimi API服务器...")
    print(f"配置文件: {args.config}")
    print(f"服务器地址: http://{args.host}:{args.port}")
    
    # 打开Web UI
    import threading
    import webbrowser
    import time
    
    def open_web_ui():
        time.sleep(3)  # 等待3秒，确保服务器已启动
        ui_path = os.path.join(project_root, "web", "index.html")
        print(f"在浏览器中打开Web UI: {ui_path}")
        webbrowser.open(f"file://{ui_path}")
    
    ui_thread = threading.Thread(target=open_web_ui)
    ui_thread.daemon = True
    ui_thread.start()
    
    # 运行服务器
    success = run_server(
        args.config, 
        host=args.host, 
        port=args.port, 
        mcp_candidates=args.mcp_candidates,
        reload=args.reload
    )
    
    sys.exit(0 if success else 1) 