#!/usr/bin/env pwsh
# Quick installation and verification script for the aggregator module

Write-Host "=== 信息整理模块 - 安装与验证 ===" -ForegroundColor Cyan
Write-Host ""

# Check Python version
Write-Host "检查 Python 版本..." -ForegroundColor Yellow
$pythonVersion = python --version 2>&1
Write-Host "  ✓ $pythonVersion" -ForegroundColor Green
Write-Host ""

# Install dependencies
Write-Host "安装依赖包..." -ForegroundColor Yellow
python -m pip install --quiet --upgrade pip
pip install --quiet httpx pydantic python-dotenv
Write-Host "  ✓ 依赖包安装完成" -ForegroundColor Green
Write-Host ""

# Verify imports
Write-Host "验证模块导入..." -ForegroundColor Yellow
$env:PYTHONPATH = $PSScriptRoot
$testImport = python -c @"
try:
    from src.aggregator.schemas import QueryRequest, QueryResult
    from src.aggregator.providers import BochaClient, TavilyClient
    from src.aggregator.engine import AggregationEngine
    from src.aggregator.io import CSVWriter
    print('SUCCESS')
except Exception as e:
    print(f'ERROR: {e}')
    exit(1)
"@

if ($testImport -eq "SUCCESS") {
    Write-Host "  ✓ 所有模块导入成功" -ForegroundColor Green
}
else {
    Write-Host "  ✗ 模块导入失败: $testImport" -ForegroundColor Red
    exit 1
}
Write-Host ""

# Check .env file
Write-Host "检查配置文件..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "  ✓ .env 文件存在" -ForegroundColor Green
}
else {
    Write-Host "  ⚠ .env 文件不存在，请从 .env.example 复制并配置 API keys" -ForegroundColor Yellow
}
Write-Host ""

# Show CLI help
Write-Host "显示 CLI 帮助..." -ForegroundColor Yellow
Write-Host "---" -ForegroundColor Gray
python -m src.aggregator.cli --help
Write-Host "---" -ForegroundColor Gray
Write-Host ""

Write-Host "=== 安装完成 ===" -ForegroundColor Green
Write-Host ""
Write-Host "使用示例:" -ForegroundColor Cyan
Write-Host "  python -m src.aggregator.cli --keywords `"深圳独立游戏`" --providers bocha tavily" -ForegroundColor White
Write-Host ""
