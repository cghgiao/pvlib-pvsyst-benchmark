# pvlib 入门 Demo —— 广州 290kWp 光伏系统年发电量估算（clearsky 近似版）
# 用途：先跑通整个"建站址 -> 取气象 -> 建模 -> 跑仿真 -> 看结果"流程
#       后续把 weather 换成 NSRDB / TMY 真实气象，就能对标 PVsyst(297.72 MWh / PR 81.91%)
# 运行：在 PyCharm 里用本项目解释器直接运行本文件即可（右键 -> Run）

import pandas as pd
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain

# 1) 站址：广州（纬度 / 经度 / 时区 / 海拔）
site = Location(latitude=23.13, longitude=113.26,
                tz='Asia/Shanghai', altitude=21, name='广州')

# 2) 气象：先用晴空模型(clearsky)占位，无需任何外部数据
#    生成一整年的逐小时时间序列
times = pd.date_range('2026-01-01', '2026-12-31 23:00', freq='h', tz=site.tz)
weather = site.get_clearsky(times)   # 含 ghi / dni / dhi 三列辐照
print('气象数据样例（前 3 行）：')
print(weather.head(3))

# 3) 组件 + 逆变器参数（手动给出，避免联网下载 SAM 库）
#    用 PVWatts 简化模型：只需额定功率 pdc0 和温度系数 gamma_pdc
module_parameters = {
    'pdc0': 290000,        # 组件阵列总峰值功率 ~290 kW（528 × 550Wp）
    'gamma_pdc': -0.003,   # 功率温度系数 (1/°C)
}
inverter_parameters = {
    'pdc0': 290000,        # 逆变器额定直流输入
    'eta_inv_nom': 0.96,   # 逆变器额定效率
}

system = PVSystem(
    surface_tilt=25,            # 最优倾角（先用 20°，后面再调）
    surface_azimuth=180,        # 朝南
    module_parameters=module_parameters,
    inverter_parameters=inverter_parameters,
    racking_model='open_rack',  # 支架类型：开放式支架（PVWatts 温度模型需要）
    module_type='glass_glass',  # 组件类型：双玻（PVWatts 温度模型需要）
)

# 4) 建模并运行仿真（with_pvwatts 使用 PVWatts 直流+逆变器模型，温度模型走 sapm）
mc = ModelChain.with_pvwatts(system, site)
mc.run_model(weather)

# 5) 看结果
#    注意单位：mc.results.ac 是「瓦(W)」，全年逐时求和得到「瓦时(Wh)」
#    换算 MWh 要除以 1,000,000（不是 1,000）
annual_ac_wh = mc.results.ac.sum()
annual_ac_mwh = annual_ac_wh / 1e6
print(f'\n年 AC 发电量（clearsky 近似）≈ {annual_ac_mwh:.1f} MWh')

# 6) 说明：clearsky 无云，结果会偏乐观；换真实气象后再算 PR 对标 PVsyst
print('提示：clearsky 不考虑云遮，发电量会偏高。')
print('      下一步申请 NSRDB 免费 key 或下载 TMY.csv，替换 weather 后算 PR 对比 PVsyst。')
