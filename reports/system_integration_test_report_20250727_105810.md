# 系統整合測試報告
生成時間: 2025-07-27 10:58:10

## 測試摘要
- 總測試數: 24
- 通過測試: 6
- 成功率: 25.0%
- 測試時長: 0.69秒
- 系統健康度: 需改進

## 詳細測試結果
### component_initialization
- ai_manager: ❌ 失敗
- risk_manager: ❌ 失敗
- max_client: ❌ 失敗
- backtest_reporter: ❌ 失敗
- backtest_gui: ❌ 失敗
- trading_monitor: ❌ 失敗
- decision_visualizer: ❌ 失敗

### data_flow
- data_acquisition: ❌ 失敗
- ai_analysis: ❌ 失敗
- risk_assessment: ❌ 失敗

### component_interaction
- ai_risk_interaction: ❌ 失敗
- gui_interaction: ❌ 失敗
- backtest_interaction: ❌ 失敗

### end_to_end_workflow
- workflow_數據獲取: ✅ 通過
- workflow_AI分析: ✅ 通過
- workflow_風險評估: ✅ 通過
- workflow_信號生成: ✅ 通過
- workflow_交易執行: ✅ 通過
- workflow_結果記錄: ✅ 通過
- backtest_workflow: ❌ 失敗
- monitoring_workflow: ❌ 失敗

### performance

### error_handling
- ai_error_handling: ❌ 失敗
- risk_error_handling: ❌ 失敗
- gui_error_handling: ❌ 失敗
