#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
市場數據增強器 - 為AI提供豐富、高質量的實時市場數據
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from .max_client import create_max_client
from .technical_indicators import create_technical_calculator
from .data_validator import create_data_validator
from .historical_data_manager import create_historical_manager

logger = logging.getLogger(__name__)

@dataclass
class EnhancedMarketData:
    """增強的市場數據結構"""
    timestamp: datetime
    basic_data: Dict[str, Any]
    technical_indicators: Dict[str, Any]
    validation_report: Dict[str, Any]
    quality_score: float
    ai_formatted_data: str
    processing_time: float

class MarketDataEnhancer:
    """市場數據增強器"""
    
    def __init__(self):
        """初始化市場數據增強器"""
        self.max_client = create_max_client()
        self.technical_calculator = create_technical_calculator()
        self.data_validator = create_data_validator()
        self.historical_manager = create_historical_manager()
        
        # 性能統計
        self.performance_stats = {
            'total_enhancements': 0,
            'successful_enhancements': 0,
            'average_processing_time': 0.0,
            'average_quality_score': 0.0,
            'data_sources_status': {
                'max_api': True,
                'historical_database': True,
                'technical_indicators': True,
                'data_validation': True
            }
        }
        
        logger.info("🚀 市場數據增強器初始化完成（含歷史數據庫）")
    
    async def get_enhanced_market_data(self, market: str = "btctwd") -> Optional[EnhancedMarketData]:
        """
        獲取增強的市場數據
        
        Args:
            market: 交易對，默認為 btctwd
            
        Returns:
            EnhancedMarketData: 增強的市場數據，如果失敗則返回None
        """
        start_time = datetime.now()
        
        try:
            self.performance_stats['total_enhancements'] += 1
            logger.info(f"🔄 開始獲取增強市場數據: {market}")
            
            # 步驟1: 獲取基礎市場數據
            basic_data = await self._get_basic_market_data(market)
            if not basic_data:
                logger.error("❌ 獲取基礎市場數據失敗")
                return None
            
            # 步驟2: 獲取K線數據用於技術指標計算
            klines_data = await self._get_klines_data(market)
            if not klines_data:
                logger.warning("⚠️ 獲取K線數據失敗，使用基礎數據")
                klines_data = {}
            
            # 步驟3: 計算技術指標
            technical_indicators = self._calculate_technical_indicators(klines_data)
            
            # 步驟4: 合併所有數據
            combined_data = {**basic_data, **technical_indicators}
            
            # 步驟5: 數據驗證和清洗
            is_valid, validation_report = self.data_validator.validate_market_data(combined_data)
            if not is_valid:
                logger.warning("⚠️ 數據驗證未通過，進行清洗")
                combined_data = self.data_validator.clean_market_data(combined_data)
            
            # 步驟6: 格式化為AI友好的格式
            ai_formatted_data = self._format_for_ai(combined_data, technical_indicators)
            
            # 計算處理時間
            processing_time = (datetime.now() - start_time).total_seconds()
            
            # 創建增強數據對象
            enhanced_data = EnhancedMarketData(
                timestamp=datetime.now(),
                basic_data=basic_data,
                technical_indicators=technical_indicators,
                validation_report=validation_report,
                quality_score=validation_report.get('quality_score', 0.0),
                ai_formatted_data=ai_formatted_data,
                processing_time=processing_time
            )
            
            # 更新性能統計
            self._update_performance_stats(enhanced_data)
            
            logger.info(f"✅ 市場數據增強完成，質量分數: {enhanced_data.quality_score:.2f}")
            return enhanced_data
            
        except Exception as e:
            logger.error(f"❌ 市場數據增強失敗: {e}")
            return None
    
    async def _get_basic_market_data(self, market: str) -> Optional[Dict[str, Any]]:
        """獲取基礎市場數據"""
        try:
            basic_data = await self.max_client.get_enhanced_market_data(market)
            if basic_data:
                self.performance_stats['data_sources_status']['max_api'] = True
                return basic_data
            else:
                self.performance_stats['data_sources_status']['max_api'] = False
                return None
                
        except Exception as e:
            logger.error(f"❌ 獲取基礎市場數據失敗: {e}")
            self.performance_stats['data_sources_status']['max_api'] = False
            return None
    
    async def _get_klines_data(self, market: str) -> Dict[str, Any]:
        """獲取K線數據（優先使用本地數據庫）"""
        try:
            logger.info("📊 優先從本地數據庫獲取K線數據...")
            
            # 首先確保歷史數據完整性
            await self.historical_manager.ensure_historical_data(market, ['1m', '5m', '1h'])
            
            # 從本地數據庫獲取數據
            klines_data = self.historical_manager.get_multiple_timeframes(
                market, {'1m': 100, '5m': 50, '1h': 24}
            )
            
            if klines_data:
                logger.info(f"✅ 從本地數據庫獲取到 {len(klines_data)} 個時間框架的數據")
                self.performance_stats['data_sources_status']['historical_database'] = True
                return klines_data
            else:
                logger.warning("⚠️ 本地數據庫無數據，嘗試從API獲取...")
                self.performance_stats['data_sources_status']['historical_database'] = False
                
                # 回退到API獲取
                return await self._get_klines_from_api(market)
            
        except Exception as e:
            logger.error(f"❌ 從數據庫獲取K線數據失敗: {e}")
            self.performance_stats['data_sources_status']['historical_database'] = False
            
            # 回退到API獲取
            return await self._get_klines_from_api(market)
    
    async def _get_klines_from_api(self, market: str) -> Dict[str, Any]:
        """從API獲取K線數據（備用方案）"""
        try:
            logger.info("📡 從MAX API獲取K線數據...")
            
            # 並行獲取不同時間框架的K線數據
            tasks = [
                self.max_client._get_recent_klines(market, period=1, limit=100),   # 1分鐘
                self.max_client._get_recent_klines(market, period=5, limit=50),    # 5分鐘
                self.max_client._get_recent_klines(market, period=60, limit=24),   # 1小時
            ]
            
            klines_1m, klines_5m, klines_1h = await asyncio.gather(*tasks, return_exceptions=True)
            
            klines_data = {}
            
            if not isinstance(klines_1m, Exception) and klines_1m is not None:
                klines_data['1m'] = klines_1m
            
            if not isinstance(klines_5m, Exception) and klines_5m is not None:
                klines_data['5m'] = klines_5m
            
            if not isinstance(klines_1h, Exception) and klines_1h is not None:
                klines_data['1h'] = klines_1h
            
            logger.info(f"✅ 從API獲取到 {len(klines_data)} 個時間框架的數據")
            return klines_data
            
        except Exception as e:
            logger.error(f"❌ 從API獲取K線數據失敗: {e}")
            return {}
    
    def _calculate_technical_indicators(self, klines_data: Dict[str, Any]) -> Dict[str, Any]:
        """計算技術指標"""
        try:
            if not klines_data:
                logger.warning("⚠️ 無K線數據，跳過技術指標計算")
                self.performance_stats['data_sources_status']['technical_indicators'] = False
                return {}
            
            indicators = self.technical_calculator.calculate_comprehensive_indicators(klines_data)
            self.performance_stats['data_sources_status']['technical_indicators'] = True
            return indicators
            
        except Exception as e:
            logger.error(f"❌ 技術指標計算失敗: {e}")
            self.performance_stats['data_sources_status']['technical_indicators'] = False
            return {}
    
    def _format_for_ai(self, combined_data: Dict[str, Any], technical_indicators: Dict[str, Any]) -> str:
        """格式化數據為AI友好的格式"""
        try:
            # 基礎市場信息
            basic_info = self.max_client.format_data_for_ai(combined_data)
            
            # 技術指標信息
            technical_info = ""
            if technical_indicators:
                technical_info = self.technical_calculator.format_indicators_for_ai(technical_indicators)
            
            # 合併格式化信息
            formatted_data = f"""
{basic_info}

{technical_info}

🎯 AI交易建議參考:
- 當前市場狀態: {'活躍' if combined_data.get('volume_ratio', 1.0) > 1.2 else '平靜'}
- 技術面偏向: {self._get_technical_bias(technical_indicators)}
- 風險等級: {self._assess_risk_level(combined_data, technical_indicators)}
- 建議操作時機: {self._get_timing_suggestion(combined_data)}
"""
            
            return formatted_data.strip()
            
        except Exception as e:
            logger.error(f"❌ AI格式化失敗: {e}")
            return "數據格式化失敗"
    
    def _get_technical_bias(self, indicators: Dict[str, Any]) -> str:
        """獲取技術面偏向"""
        try:
            if not indicators:
                return "中性"
            
            bullish_signals = 0
            bearish_signals = 0
            
            # RSI信號
            rsi = indicators.get('medium_rsi', 50)
            if rsi < 30:
                bullish_signals += 1
            elif rsi > 70:
                bearish_signals += 1
            
            # MACD信號
            macd_signal = indicators.get('medium_macd_signal_type', '中性')
            if '金叉' in macd_signal:
                bullish_signals += 1
            elif '死叉' in macd_signal:
                bearish_signals += 1
            
            # 趨勢信號
            dominant_trend = indicators.get('dominant_trend', '震盪')
            if dominant_trend == '上升':
                bullish_signals += 1
            elif dominant_trend == '下降':
                bearish_signals += 1
            
            if bullish_signals > bearish_signals:
                return "偏多"
            elif bearish_signals > bullish_signals:
                return "偏空"
            else:
                return "中性"
                
        except Exception:
            return "中性"
    
    def _assess_risk_level(self, basic_data: Dict[str, Any], indicators: Dict[str, Any]) -> str:
        """評估風險等級"""
        try:
            risk_score = 0
            
            # 波動率風險
            volatility = indicators.get('long_volatility_level', '中等')
            if volatility == '高':
                risk_score += 2
            elif volatility == '中':
                risk_score += 1
            
            # 成交量風險
            volume_ratio = basic_data.get('volume_ratio', 1.0)
            if volume_ratio > 2.0 or volume_ratio < 0.5:
                risk_score += 1
            
            # 技術指標極端值風險
            rsi = indicators.get('medium_rsi', 50)
            if rsi > 80 or rsi < 20:
                risk_score += 1
            
            if risk_score >= 3:
                return "高風險"
            elif risk_score >= 2:
                return "中風險"
            else:
                return "低風險"
                
        except Exception:
            return "中風險"
    
    def _get_timing_suggestion(self, data: Dict[str, Any]) -> str:
        """獲取時機建議"""
        try:
            hour = data.get('hour_of_day', 12)
            
            # 基於時間的建議
            if 9 <= hour <= 11:
                return "開盤活躍期，適合短線操作"
            elif 14 <= hour <= 16:
                return "午後交易期，注意歐洲市場影響"
            elif 21 <= hour <= 23:
                return "美股開盤期，波動可能加大"
            else:
                return "相對平靜期，適合觀望"
                
        except Exception:
            return "正常交易時段"
    
    def _update_performance_stats(self, enhanced_data: EnhancedMarketData):
        """更新性能統計"""
        try:
            if enhanced_data.quality_score > 0.5:
                self.performance_stats['successful_enhancements'] += 1
            
            # 更新平均處理時間
            total_time = (
                self.performance_stats['average_processing_time'] * 
                (self.performance_stats['total_enhancements'] - 1) + 
                enhanced_data.processing_time
            )
            self.performance_stats['average_processing_time'] = total_time / self.performance_stats['total_enhancements']
            
            # 更新平均質量分數
            total_quality = (
                self.performance_stats['average_quality_score'] * 
                (self.performance_stats['total_enhancements'] - 1) + 
                enhanced_data.quality_score
            )
            self.performance_stats['average_quality_score'] = total_quality / self.performance_stats['total_enhancements']
            
        except Exception as e:
            logger.error(f"❌ 更新性能統計失敗: {e}")
    
    def get_performance_stats(self) -> Dict[str, Any]:
        """獲取性能統計"""
        return self.performance_stats.copy()
    
    def get_system_status(self) -> Dict[str, Any]:
        """獲取系統狀態"""
        return {
            'enhancer_status': 'active',
            'data_sources': self.performance_stats['data_sources_status'],
            'performance': {
                'success_rate': (
                    self.performance_stats['successful_enhancements'] / 
                    max(1, self.performance_stats['total_enhancements'])
                ),
                'average_processing_time': self.performance_stats['average_processing_time'],
                'average_quality_score': self.performance_stats['average_quality_score']
            },
            'last_update': datetime.now()
        }
    
    async def close(self):
        """關閉連接"""
        try:
            await self.max_client.close()
            await self.historical_manager.close()
            logger.info("✅ 市場數據增強器已關閉")
        except Exception as e:
            logger.error(f"❌ 關閉增強器失敗: {e}")


# 創建全局市場數據增強器實例
def create_market_enhancer() -> MarketDataEnhancer:
    """創建市場數據增強器實例"""
    return MarketDataEnhancer()


# 測試代碼
if __name__ == "__main__":
    import asyncio
    
    async def test_market_enhancer():
        """測試市場數據增強器"""
        print("🧪 測試市場數據增強器...")
        
        enhancer = create_market_enhancer()
        
        try:
            # 獲取增強市場數據
            enhanced_data = await enhancer.get_enhanced_market_data("btctwd")
            
            if enhanced_data:
                print("✅ 獲取增強市場數據成功!")
                print(f"📊 質量分數: {enhanced_data.quality_score:.2f}")
                print(f"⏱️ 處理時間: {enhanced_data.processing_time:.2f}秒")
                print(f"📈 技術指標數量: {len(enhanced_data.technical_indicators)}")
                
                print("\n🤖 AI格式化數據:")
                print(enhanced_data.ai_formatted_data)
                
                # 顯示性能統計
                stats = enhancer.get_performance_stats()
                print(f"\n📊 性能統計:")
                print(f"成功率: {stats['successful_enhancements']}/{stats['total_enhancements']}")
                print(f"平均處理時間: {stats['average_processing_time']:.2f}秒")
                print(f"平均質量分數: {stats['average_quality_score']:.2f}")
                
            else:
                print("❌ 獲取增強市場數據失敗")
                
        finally:
            await enhancer.close()
    
    # 運行測試
    asyncio.run(test_market_enhancer())