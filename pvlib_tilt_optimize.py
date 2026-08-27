# -*- coding: utf-8 -*-
"""
广州 290.4 kWp 光伏系统 —— 最优安装倾角寻优
固定朝南(azimuth=180)，扫描 0~40° 倾角，找出年发电量最大的那一个。
运行：python pvlib_tilt_optimize.py
"""
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pvlib
from pvlib.location import Location
from pvlib.pvsystem import PVSystem
from pvlib.modelchain import ModelChain
from pvlib.iotools import get_pvgis_tmy

OUT = 'D:/workbuddy-workspace'

# ---------- 1) 站址 & 系统参数（与 v2 一致）----------
site = Location(latitude=23.0350, longitude=113.3983,
                tz='Asia/Shanghai', altitude=21, name='Gongxue Building')
module_parameters = {'pdc0': 290400, 'gamma_pdc': -0.0035}
inverter_parameters = {'pdc0': 260416, 'eta_inv_nom': 0.96}

# ---------- 2) 下载一次 PVGIS TMY 气象（后面复用）----------
weather, _ = get_pvgis_tmy(latitude=site.latitude, longitude=site.longitude,
                           map_variables=True)

# ---------- 3) 扫描倾角 0~40° ----------
tilts = list(range(0, 41, 1))      # 每 1° 一步
yields = []                        # 存每年的 MWh
for t in tilts:
    system = PVSystem(
        surface_tilt=t, surface_azimuth=180,
        module_parameters=module_parameters,
        inverter_parameters=inverter_parameters,
        racking_model='open_rack', module_type='glass_polymer',
    )
    mc = ModelChain.with_pvwatts(system, site)
    mc.run_model(weather)
    annual_mwh = mc.results.ac.sum() / 1e6   # W·h -> MWh
    yields.append(annual_mwh)
    print(f'倾角 {t:2d}° : {annual_mwh:.2f} MWh')

# ---------- 4) 找最优 ----------
best_idx = int(np.argmax(yields))
best_tilt = tilts[best_idx]
best_yield = yields[best_idx]
print(f'\n==> 最优倾角 ≈ {best_tilt}° ，年发电量 {best_yield:.2f} MWh')

# ---------- 5) 画图 ----------
fig, ax = plt.subplots(figsize=(7, 3.8))
ax.plot(tilts, yields, color='#4C72B0', marker='o', ms=3, lw=1.5)
ax.axvline(best_tilt, color='#DD8452', ls='--', label=f'Optimal {best_tilt}°')
ax.scatter([best_tilt], [best_yield], color='#DD8452', zorder=5, s=60)
ax.set_xlabel('Tilt Angle (deg)')
ax.set_ylabel('Annual AC Yield (MWh)')
ax.set_title('Guangzhou 290.4 kWp: Yield vs Tilt (south-facing)')
ax.legend()
ax.grid(alpha=0.3)
plt.tight_layout()
fig.savefig(f'{OUT}/pvlib_tilt_optimize.png', dpi=130)
plt.close(fig)
print('图表已保存: pvlib_tilt_optimize.png')
