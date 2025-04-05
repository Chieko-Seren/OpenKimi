#!/usr/bin/env python3
"""
测试KimiEngine初始化
"""
import os
import sys
import logging
import argparse

# 配置日志
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 添加项目根目录到sys.path
project_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, project_root)

try:
    from openkimi import KimiEngine
    logger.info("成功导入KimiEngine")
except ImportError as e:
    logger.error(f"导入KimiEngine时出错: {e}")
    sys.exit(1)

def test_engine_init(config_path):
    """测试引擎初始化"""
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
    
    # 检查依赖库
    try:
        logger.info("正在检查依赖库...")
        
        # 检查transformers
        try:
            import transformers
            logger.info(f"transformers 版本: {transformers.__version__}")
        except ImportError:
            logger.error("transformers库未安装")
            return False
            
        # 检查sentence-transformers
        try:
            import sentence_transformers
            logger.info(f"sentence-transformers 版本: {sentence_transformers.__version__}")
        except ImportError:
            logger.error("sentence-transformers库未安装")
            return False
            
        # 检查numpy
        try:
            import numpy
            logger.info(f"numpy 版本: {numpy.__version__}")
        except ImportError:
            logger.error("numpy库未安装")
            return False
            
        # 检查nltk
        try:
            import nltk
            logger.info(f"nltk 版本: {nltk.__version__}")
        except ImportError:
            logger.error("nltk库未安装")
            return False
    except Exception as e:
        logger.error(f"检查依赖库时出错: {e}")
        return False
    
    # 初始化引擎
    try:
        logger.info("正在初始化KimiEngine...")
        engine = KimiEngine(config_path=config_path)
        
        # 检查引擎组件
        if engine.llm_interface is None:
            logger.error("engine.llm_interface为None")
            return False
            
        if engine.rag_manager is None:
            logger.error("engine.rag_manager为None")
            return False
            
        # 测试一个简单的聊天响应
        try:
            logger.info("测试聊天功能...")
            response = engine.chat("你好")
            logger.info(f"聊天响应: {response}")
        except Exception as e:
            logger.error(f"测试聊天功能时出错: {e}")
            return False
            
        logger.info("引擎初始化和测试完成，一切正常")
        return True
    except Exception as e:
        logger.error(f"初始化KimiEngine时出错: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="测试KimiEngine初始化")
    parser.add_argument("--config", "-c", type=str, default="examples/config.json", 
                        help="配置文件路径 (默认: examples/config.json)")
    args = parser.parse_args()
    
    success = test_engine_init(args.config)
    sys.exit(0 if success else 1) 