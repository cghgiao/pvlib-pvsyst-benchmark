# -*- coding: utf-8 -*-
"""
pvlib 报告生成器：重跑广州工学一号楼 290.4kWp 仿真，
输出年发电量对比图 + 月度发电曲线图，并把关键数字打印出来供报告引用。
"""
import matplotlib
matplotlib.use('Agg')  # 无界面环境
import matplotlib.pyplot as plt
import pandas as pd
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from pvlib.iotools import get_pvgis_tmy

OUT = 'D:/workbuddy-workspace'

# ---------- 1) 站址：广州大学城工学一号楼 ----------
site = Location(latitude=23.0350, longitude=113.3983,
                tz='Asia/Shanghai', altitude=21, name='Gongxue Building')

# ---------- 2) 气象：PVGIS TMY（免 key，水平面 ghi/dni/dhi）----------
weather, meta = get_pvgis_tmy(latitude=site.latitude, longitude=site.longitude,
                               map_variables=True)
print('PVGIS 气象时段:', weather.index[0], '~', weather.index[-1])

# ---------- 3) 系统参数（对齐 PVsyst 工学楼模型）----------
module_parameters = {'pdc0': 290400, 'gamma_pdc': -0.0035}      # 528*550Wp
inverter_parameters = {'pdc0': 260416, 'eta_inv_nom': 0.96}     # 5*50kWac 削波
system = PVSystem(
    surface_tilt=17.3, surface_azimuth=180,
    module_parameters=module_parameters,
    inverter_parameters=inverter_parameters,
    racking_model='open_rack', module_type='glass_polymer',
)

# ---------- 4) 建模并运行（真实气象）----------
mc = ModelChain.with_pvwatts(system, site)
mc.run_model(weather)

ac_w = mc.results.ac
annual_real_mwh = ac_w.sum() / 1e6
poa_annual = mc.results.total_irrad['poa_global'].sum() / 1000   # kWh/m²
P_rated_kw = 290.4
PR = (annual_real_mwh * 1000) / (P_rated_kw * poa_annual) * 100

# ---------- 5) 晴空近似（同 TMY 时段，无云上限）----------
cs = site.get_clearsky(weather.index)
weather_cs = weather.copy()
weather_cs['ghi'] = cs['ghi']
weather_cs['dni'] = cs['dni']
weather_cs['dhi'] = cs['dhi']
mc_cs = ModelChain.with_pvwatts(system, site)
mc_cs.run_model(weather_cs)
annual_cs_mwh = mc_cs.results.ac.sum() / 1e6

# ---------- 6) 月度发电 ----------
monthly = ac_w.groupby(ac_w.index.month).sum() / 1e6  # MWh/月

print('\n==== 关键数字 ====')
print(f'PVGIS TMY 年发电量 : {annual_real_mwh:.1f} MWh')
print(f'PVGIS TMY PR       : {PR:.1f} %')
print(f'晴空近似 年发电量  : {annual_cs_mwh:.1f} MWh')
print(f'PVsyst 参考        : 297.72 MWh / 81.91%')
print('月度(MWh):', [round(x, 1) for x in monthly.values])

# ---------- 7) 图1：年发电量三方案对比 ----------
fig, ax = plt.subplots(figsize=(6.5, 4))
labels = ['PVsyst\n(reference)', 'PVGIS TMY\n(real)', 'Clearsky\n(upper bound)']
vals = [297.72, annual_real_mwh, annual_cs_mwh]
colors = ['#4C72B0', '#DD8452', '#999999']
bars = ax.bar(labels, vals, color=colors)
for b, v in zip(bars, vals):
    ax.text(b.get_x() + b.get_width()/2, v + 8, f'{v:.1f}', ha='center', fontsize=10)
ax.set_ylabel('Annual AC Energy (MWh)')
ax.set_title('Annual Yield: pvlib vs PVsyst (290.4 kWp, Guangzhou)')
ax.set_ylim(0, max(vals)*1.15)
plt.tight_layout()
fig.savefig(f'{OUT}/pvlib_annual_compare.png', dpi=130)
plt.close(fig)

# ---------- 8) 图2：月度发电曲线 ----------
fig, ax = plt.subplots(figsize=(7, 3.6))
ax.bar(monthly.index, monthly.values, color='#55A868')
ax.set_xlabel('Month')
ax.set_ylabel('AC Energy (MWh/month)')
ax.set_title('Monthly AC Yield (PVGIS TMY, 290.4 kWp)')
ax.set_xticks(range(1, 13))
ax.set_xticklabels(['1','2','3','4','5','6','7','8','9','10','11','12'])
plt.tight_layout()
fig.savefig(f'{OUT}/pvlib_monthly.png', dpi=130)
plt.close(fig)

print('\n图表已保存: pvlib_annual_compare.png / pvlib_monthly.png')
