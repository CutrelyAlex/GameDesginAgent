"""
Command-line interface for the info aggregation module.

Usage:
    python -m src.aggregator.cli --keywords "游戏开发" "独立游戏" --providers bocha tavily
"""

import argparse
import asyncio
import logging
import sys
from pathlib import Path
from typing import List

from src.aggregator.schemas import QueryRequest
from src.aggregator.engine import AggregationEngine
from src.aggregator.io import CSVWriter

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='信息整理模块 - 聚合搜索多个关键词跨多个提供商',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  # 使用两个提供商查询单个关键词
  python -m src.aggregator.cli --keywords "深圳独立游戏" --providers bocha tavily
  
  # 查询多个关键词并保存到指定文件
  python -m src.aggregator.cli --keywords "游戏开发" "独立游戏" "Godot引擎" \\
      --providers bocha tavily --filename game_dev_results.csv
  
  # 仅使用 Bocha 提供商
  python -m src.aggregator.cli --keywords "AI Agent" --providers bocha
  
  # 启用 LLM 关键词变体生成（提高召回率）
  python -m src.aggregator.cli --keywords "深圳独立游戏" --generate-variants
  
  # 指定每个提供商返回最多 20 条结果
  python -m src.aggregator.cli --keywords "游戏开发" --max-results-per-provider 20
  
  # 获取尽可能多的结果（Bocha最多50条，Tavily最多20条）
  python -m src.aggregator.cli --keywords "AI Agent" --max-results-per-provider 100
        '''
    )
    
    parser.add_argument(
        '--keywords',
        nargs='+',
        required=True,
        help='要搜索的关键词列表'
    )
    
    parser.add_argument(
        '--providers',
        nargs='+',
        choices=['bocha', 'tavily'],
        default=['bocha', 'tavily'],
        help='要使用的提供商 (默认: 两者都用)'
    )
    
    parser.add_argument(
        '--out',
        type=str,
        default='data/results',
        help='CSV 输出目录 (默认: data/results)'
    )
    
    parser.add_argument(
        '--filename',
        type=str,
        default='results.csv',
        help='CSV 文件名 (默认: results.csv)'
    )
    
    parser.add_argument(
        '--no-cache',
        action='store_true',
        help='禁用缓存'
    )
    
    parser.add_argument(
        '--generate-variants',
        action='store_true',
        help='使用 LLM 生成关键词变体以提高召回率 (需要配置 SMALL_LLM_URL)'
    )
    
    parser.add_argument(
        '--max-results-per-provider',
        type=int,
        default=10,
        choices=range(1, 101),
        metavar='[1-100]',
        help='每个提供商的最大返回条数 (默认: 10, 范围: 1-100, 会根据API限制自动调整)'
    )
    
    parser.add_argument(
        '--max-concurrent',
        type=int,
        default=5,
        help='最大并发关键词数 (默认: 5)'
    )
    
    parser.add_argument(
        '--cache-ttl',
        type=int,
        default=86400,
        help='缓存 TTL 秒数 (默认: 86400 = 24小时)'
    )
    
    parser.add_argument(
        '--verbose',
        '-v',
        action='store_true',
        help='详细输出 (DEBUG 日志级别)'
    )
    
    return parser.parse_args()


async def main():
    """Main CLI entry point."""
    args = parse_args()
    
    # Configure logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    logger.info(f"信息整理模块 CLI 启动")
    logger.info(f"关键词: {args.keywords}")
    logger.info(f"提供商: {args.providers}")
    
    # Handle keyword variant generation if requested
    keywords_to_search = args.keywords
    if args.generate_variants:
        logger.info("启用关键词变体生成...")
        try:
            from src.aggregator.keywords import generate_variants_for_keywords
            
            print("\n🔄 正在生成关键词变体...")
            keywords_to_search = await generate_variants_for_keywords(args.keywords)
            
            print(f"✓ 已生成 {len(keywords_to_search)} 个关键词（包括原始关键词和变体）")
            if args.verbose:
                print(f"  关键词列表: {', '.join(keywords_to_search[:10])}" + 
                      (f" ... (+{len(keywords_to_search)-10} more)" if len(keywords_to_search) > 10 else ""))
            print()
        except Exception as e:
            logger.error(f"关键词变体生成失败: {e}")
            print(f"⚠ 关键词变体生成失败，将使用原始关键词: {e}\n")
            keywords_to_search = args.keywords
    
    # Create request
    request = QueryRequest(
        keywords=keywords_to_search,
        providers=args.providers,
        max_results_per_provider=args.max_results_per_provider
    )
    
    # Initialize engine
    engine = AggregationEngine(
        max_concurrent_keywords=args.max_concurrent,
        cache_ttl=args.cache_ttl,
        use_cache=not args.no_cache
    )
    
    try:
        # Execute aggregation
        logger.info("开始聚合查询...")
        print(f"🔍 正在查询 {len(keywords_to_search)} 个关键词...")
        response = await engine.aggregate(request)
        
        # Display summary
        print("\n" + "="*60)
        print(f"✓ 查询完成！共找到 {response.total_count} 条结果")
        print("="*60)
        
        for provider, results in response.by_provider.items():
            print(f"  {provider}: {len(results)} 条结果")
        
        # Save to CSV
        if response.results:
            csv_writer = CSVWriter(output_dir=args.out)
            output_path = csv_writer.write_results(response.results, args.filename)
            
            print(f"\n📁 结果已保存到:")
            print(f"   {output_path.absolute()}")
            print(f"   总行数: {len(response.results)}")
        else:
            logger.warning("未找到任何结果，跳过 CSV 写入")
            sys.exit(1)
        
        print("="*60 + "\n")
        
    except KeyboardInterrupt:
        logger.warning("用户中断")
        sys.exit(130)
    except Exception as e:
        logger.error(f"聚合失败: {e}", exc_info=True)
        sys.exit(1)
    finally:
        await engine.close()


if __name__ == '__main__':
    asyncio.run(main())
