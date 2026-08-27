# 基于 pvlib 的广州 290.4kWp 光伏系统建模与 PVsyst 对标分析

> 使用开源光伏建模库 **pvlib-python**，对广州大学城工学一号楼 290.4 kWp 固定式光伏系统进行全年发电量仿真，并与商业软件 **PVsyst** 的结果进行对标，定位并解释两者偏差来源。

---

## 项目简介

本项目是光伏系统仿真从「商业软件」走向「开源可复现」的一次完整实践：

- 用 **pvlib** 搭建与本人实际工程（工学一号楼 PVsyst 模型）完全一致的 290.4 kWp 系统；
- 接入 **PVGIS TMY** 真实气象数据完成全年逐时仿真；
- 通过**倾角寻优**验证 PVsyst 所选 17.3° 的工程合理性；
- 与 PVsyst 结果（297.72 MWh / PR 81.91%）对标，定位 22% 偏差主因为**卫星气象数据源口径差异**，而非建模误差。

## 核心结果

| 方案 | 年发电量 | PR | 说明 |
|---|---|---|---|
| **PVsyst 参考** | 297.72 MWh | 81.91% | 原始工程目标值 |
| **PVGIS TMY（本项目）** | 363.9 MWh | 76.7% | pvlib + PVGIS SARAH-2 真实气象 |
| **晴空近似（无云上限）** | 535.9 MWh | — | 仅按太阳几何估算的上限 |

**倾角寻优**：扫描 0–40° 固定倾角，理论最优 ≈ **25°（366.47 MWh）**；PVsyst 取值 17.3° 对应 363.68 MWh，仅差 **+0.77%**，说明现选低倾角已接近最优，属合理的工程折中（省支架、减风载、利清洁）。

## 目录结构

```
pvlib-guangzhou-pv/
├── pvlib_demo.py            # 入门：clearsky 晴空近似跑通年发电量
├── pvlib_demo_v2.py         # 主程序：PVGIS TMY 真实气象 + PVsyst 参数对标
├── pvlib_tilt_optimize.py   # 最优倾角寻优（0–40°扫描）+ 曲线图
├── pvlib_report_gen.py      # 生成对比图与月度曲线（报告用）
├── pvlib项目报告.md          # 完整技术报告（方法/参数/结果/偏差分析）
├── pvlib_annual_compare.png # 年发电量三方案对比图
├── pvlib_monthly.png        # 月度发电曲线图
├── pvlib_tilt_optimize.png  # 发电量-倾角寻优曲线
├── requirements.txt
└── README.md
```

## 环境要求

- Python 3.10 – 3.13
- pvlib 0.15.2 及以上（`[optional]` 含 numba / statsmodels 等）
- 联网（首次运行自动从 PVGIS 拉取气象数据，无需 API key）

## 安装与运行

```bash
# 1) 建议新建独立虚拟环境
python -m venv pvlib
source pvlib/bin/activate        # Windows: pvlib\Scripts\activate

# 2) 安装依赖
pip install -r requirements.txt

# 3) 运行主程序（自动下载广州气象，输出对标结果）
python pvlib_demo_v2.py

# 4) 可选：运行倾角寻优 / 报告生成
python pvlib_tilt_optimize.py
python pvlib_report_gen.py
```

> 本项目在 Python 3.13 + pvlib 0.15.2 下验证通过。

## 数据源与复现说明

- **气象**：PVGIS（欧盟 JRC）SARAH-2 卫星数据，覆盖约 2005–2020，TMY 为典型气象年（非某年实测）。
- **系统参数**：倾角 17.3°、方位角正南、528×550 Wp 组件、5×50 kWac 逆变器、组件温度系数 −0.35 %/°C，均与本人 PVsyst 工程模型一致。
- **模型**：`ModelChain.with_pvwatts`（PVWatts 简化单二极管 + SAPM 温度模型）。

## 偏差分析（要点）

PVGIS 结果较 PVsyst 高约 22%、PR 低约 5 个百分点，主因为**两套气象数据源对广州多云潮湿气候的云量反演算法不同**（PVGIS=SARAH-2 卫星，PVsyst 多为 Meteonorm/本地 TMY），而非系统建模错误。系统参数（倾角、功率、逆变器削波）调整后对年发电量影响 <1.5%，进一步证明偏差来自数据源口径。

## 许可证

MIT License —— 仅用于学习与作品集展示。
