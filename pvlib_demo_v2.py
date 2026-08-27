# pvlib Demo 第二版 —— 用真实气象数据（PVGIS TMY，免 API key）跑广州 290kWp
# 对比：真实气象(TMY) vs 晴空近似 vs PVsyst 参考值(297.72 MWh / PR 81.91%)
# 运行：PyCharm 里用 venv 解释器 Run 本文件（需要联网，自动从 PVGIS 下载数据）
#
# 数据说明：PVGIS 对中国默认用 SARAH-2 卫星数据（覆盖 2005–2020，新版 SARAH-3 到 2023），
#          返回的 TMY 是从这段时期里挑“典型月”合成的“典型气象年”，不是某一年实测。

import pandas as pd
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from pvlib.iotools import get_pvgis_tmy

# ---------- 1) 站址：广州工学一号楼 ----------
# 注意：pvlib 的方位角以正北为 0°、顺时针增加；正南 = 180°。
#       PVsyst 里显示"方位角 0.0°"就是正南，对应 pvlib 的 180°。
site = Location(latitude=23.0350, longitude=113.3983,
                tz='Asia/Shanghai', altitude=21, name='工学一号楼')

# ---------- 2) 拉取真实气象（PVGIS TMY，免费、无需 key）----------
print('正在从 PVGIS 下载广州 TMY 真实气象数据...')
data, meta = get_pvgis_tmy(
    latitude=site.latitude, longitude=site.longitude,
    map_variables=True,
)
# PVGIS 返回的是 UTC 时间（缺省年 1990），转成广州时区
if data.index.tz is None:
    data.index = data.index.tz_localize('UTC')
data.index = data.index.tz_convert('Asia/Shanghai')
print('PVGIS 返回字段：', list(data.columns))

# ModelChain 只需要这几列（get_pvgis_tmy 已自带 ghi/dni/dhi）
weather = data[['ghi', 'dni', 'dhi', 'temp_air', 'wind_speed']].copy()

# 同时生成“晴空近似”做对照（用 TMY 的时间索引）
clearsky = site.get_clearsky(data.index)

# ---------- 3) 系统参数（按 PVsyst 截图填写） ----------
# 组件：JA Solar JAM72-S30-550-MR，550 Wp，共 528 块
#       Pmax 温度系数 -0.35 %/°C = -0.0035 /°C
module_parameters = {
    'pdc0': 528 * 550,      # 290,400 W = 290.4 kWp
    'gamma_pdc': -0.0035,   # 1/°C
}
# 逆变器：Sungrow SG50CX-P2，5 台 × 50 kWac = 250 kWac
#         pdc0 设为 250kW/0.96 ≈ 260.4 kWdc，这样 AC 输出会限制在 250 kW（模拟削波）
inverter_parameters = {
    'pdc0': int(250000 / 0.96),  # 260,416 Wdc
    'eta_inv_nom': 0.96,
}
system = PVSystem(
    surface_tilt=17.3, surface_azimuth=180,  # PVsyst：倾角 17.3°，方位角 0.0°=正南
    module_parameters=module_parameters,
    inverter_parameters=inverter_parameters,
    racking_model='open_rack',
    module_type='glass_polymer',  # 标准玻璃+白色背板组件（非双玻）
)

# ---------- 4) 跑两版仿真 ----------
mc_real = ModelChain.with_pvwatts(system, site)
mc_real.run_model(weather)
annual_real_mwh = mc_real.results.ac.sum() / 1e6   # mc.results.ac 单位 W，求和=Wh，换 MWh 除 1e6

mc_cs = ModelChain.with_pvwatts(system, site)
mc_cs.run_model(clearsky)
annual_cs_mwh = mc_cs.results.ac.sum() / 1e6

# ---------- 5) 算 PR（基于 ModelChain 内部算出的 POA 斜面辐照）----------
poa_annual = mc_real.results.total_irrad['poa_global'].sum() / 1000  # kWh/m²
P_rated_kw = 290.4  # 与 module_parameters['pdc0'] 一致
PR = (annual_real_mwh * 1000) / (P_rated_kw * poa_annual) * 100     # %

# ---------- 6) 输出对比 ----------
print('\n========== 工学一号楼 290.4 kWp 年发电量对比 ==========')
print('PVsyst 参考值        : 297.72 MWh  /  PR 81.91%')
print('真实气象(PVGIS TMY)  : %.1f MWh  /  PR ≈ %.1f%%' % (annual_real_mwh, PR))
print('晴空近似(TMY 时段)   : %.1f MWh  (无云上限)' % annual_cs_mwh)
print('====================================================')
print('说明：PVGIS(SARAH2) 与 PVsyst 数据库口径不同，数值会有差异；')
print('      若想要与 PVsyst 更高一致性，可改用 NSRDB(需免费 NLR API key) 再算一版。')
