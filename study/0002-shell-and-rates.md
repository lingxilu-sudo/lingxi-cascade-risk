# 第二课：壳层几何与碰撞率

> 本课手推三个数：壳层体积 \(V=1.2925\times10^{11}\,\text{km}^3\)、碎片-卫星碰撞率 \(R_{ds}=7.130/\text{年}\)、碎片-碎片碰撞率 \(R_{dd}=16.264/\text{年}\)。推完你应能不看文献写出 Kessler–Flournoy 碰撞率公式，并说清 \(\frac12\) 因子与 \(N^2\) 的来源。

## 为什么先算几何

碰撞是一个"扫过体积"问题：一个物体在轨道上运动，它扫过的空间中如果存在别的物体，就可能相撞。因此碰撞频率取决于三样东西——目标有多少（数量密度）、相遇截面多大、单位时间扫过多长（相对速度）。这三样量都定义在一个容器里：壳体（shell）。

把 LEO 理想化为一层球壳，是轨道碎片文献的标准做法（Kessler 1981）。真实轨道环境是三维的，包含倾角与偏心率分布；单层壳体的近似牺牲了跨壳层迁移，换来的是每个量都能手算。本框架在这一近似下工作，代价记入第六课的薄弱点清单。

## 壳层体积

设地球半径 \(R_\oplus = 6371\ \text{km}\)，壳层中心高度 \(h = 800\ \text{km}\)，厚度 \(\Delta h = 200\ \text{km}\)。壳的内外半径分别为：

$$
r_{\text{in}} = R_\oplus + h - \frac{\Delta h}{2} = 6371 + 800 - 100 = 7071\ \text{km}
$$

$$
r_{\text{out}} = R_\oplus + h + \frac{\Delta h}{2} = 6371 + 800 + 100 = 7271\ \text{km}
$$

球壳体积为两球体积之差：

$$
V = \frac{4\pi}{3}\left(r_{\text{out}}^3 - r_{\text{in}}^3\right)
$$

逐步计算。先算立方：

$$
r_{\text{out}}^3 = 7271^3 \approx 3.8444\times10^{11}\ \text{km}^3
$$

$$
r_{\text{in}}^3 = 7071^3 \approx 3.5354\times10^{11}\ \text{km}^3
$$

两者之差约 \(3.090\times10^{10}\) km³，乘以 \(4\pi/3 \approx 4.18879\)：

$$
V \approx 1.2925\times10^{11}\ \text{km}^3
$$

与代码 `OrbitalShell.volume_km3` 的输出一致。这个体积是粗略直觉的 \(10^{11}\) 量级——一千亿立方公里，听起来很大；但基准场景里塞进三万六千个物体后，每立方公里只剩 \(2.8\times10^{-7}\) 个物体，密度低到必须用碰撞截面把"擦边"也算进来（下一节）。

## 轨道速度与相对速度

圆轨道速度由引力提供向心力决定：

$$
\frac{v^2}{r} = \frac{\mu_\oplus}{r^2} \quad\Rightarrow\quad v_{\text{circ}} = \sqrt{\frac{\mu_\oplus}{r}}
$$

其中 \(\mu_\oplus = 398{,}600.44\ \text{km}^3/\text{s}^2\) 是地球引力常数（地球质量与万有引力常数之积）。代入 \(r = 7171\) km：

$$
v_{\text{circ}} = \sqrt{\frac{398{,}600}{7171}} = \sqrt{55.59} \approx 7.46\ \text{km/s}
$$

注意两个物体若轨道面相同、方向相同（共轨），相对速度接近零；若轨道面接近垂直，相对速度最大可达 \(\sqrt{2}\,v_{\text{circ}} \approx 10.5\) km/s，随机倾角下的平均值也在 9–11 km/s 之间。框架取固定值：

$$
v_{\text{rel}} = 10\ \text{km/s}
$$

这个选择写在 `configs/baseline.yaml` 的 `relative_velocity_km_s` 字段里。它是保守的（偏低）：真实分布包含更高相对速度的相遇，而碰撞率与 \(v_{\text{rel}}\) 成正比。也就是说，取 10 而不是 11–14，会让算出的一切风险偏低。方向记入第六课。

## 碰撞管的推导

现在推碰撞率。考虑一个参考物体，截面 \(\sigma\)（单位 km²），以相对速度 \(v_{\text{rel}}\) 在密度均匀的壳层里运动。时间 \(T\) 内它扫过的体积是：

$$
V_{\text{swept}} = \sigma \cdot v_{\text{rel}} \cdot T
$$

壳层内若有 \(N_d\) 个碎片均匀分布，则扫过体积内的期望碎片数为：

$$
\lambda = \frac{N_d}{V} \cdot \sigma \cdot v_{\text{rel}} \cdot T
$$

这就是参考物体在 \(T\) 内与碎片发生碰撞的期望次数。碰撞事件近似服从泊松分布（Poisson distribution，描述单位时间内随机独立事件次数的分布，由法国数学家 Siméon Denis Poisson 于 1837 年提出），其含义是：在期望次数为 \(\lambda\) 的时段里，实际发生 0 次的概率为 \(e^{-\lambda}\)，至少 1 次的概率为：

$$
P(\ge 1) = 1 - e^{-\lambda} \approx \lambda \quad (\lambda \ll 1)
$$

本框架的碰撞率都远小于 1 每年（几十次除以数万个物体，单个卫星的期望碰撞次数在 \(10^{-3}\) 量级），所以近似 \(P \approx \lambda\) 处处成立，代码直接用 \(\lambda\)。

把参考物体换成整个卫星群体：每颗卫星都在扫，扫过的总体积乘以 \(N_s\)。于是碎片-卫星（debris–satellite，DS）碰撞率：

$$
R_{ds} = \frac{N_d \cdot N_s \cdot \sigma \cdot v_{\text{rel}} \cdot T_{\text{year}}}{V}
$$

其中 \(T_{\text{year}} = 31{,}557{,}600\) s。这里的 \(\sigma\) 是"两者的联合截面"的近似：卫星约 10 m²，碎片通常小于 1 m²，联合截面由大的一方主导，故取卫星截面。

对碎片-碎片的相遇，关键区别是"对"（pair）的计数。\(N_d\) 个碎片两两配对的总数是组合数：

$$
\binom{N_d}{2} = \frac{N_d(N_d-1)}{2}
$$

每一对相遇都算一次碰撞；若不除以 2，同一对会被数两遍。于是：

$$
R_{dd} = \frac{N_d(N_d-1)}{2} \cdot \frac{\sigma \cdot v_{\text{rel}} \cdot T_{\text{year}}}{V}
$$

这就是 Kessler–Flournoy 公式的两种形态。代码 `collision_model.py` 中 `collision_rate()` 与 `debris_debris_collision_rate()` 逐字对应这两式，\(\frac12\) 因子在后者。

注意：这两式在代码里共用同一个 \(\sigma=10\) m²。对 DS 这是合理的（联合截面由卫星主导），但对 DD 偏大：两块约 1 m² 的碎片，联合截面约 4 m²，而不是 10 m²。因此 DD 速率应读作上界。实测把 DD 截面取 1 m²，\(N(50)\) 从 \(1.51\times10^6\) 降到 \(7.93\times10^5\)，期望损失从 \$921.4M 降到 \$484.1M。

## 代入基线数值

先算公用因子。截面 10 m² 换算成 km²：

$$
\sigma = 10\ \text{m}^2 \times 10^{-6} = 1.0\times10^{-5}\ \text{km}^2
$$

再算每年扫过的"截面×路程"：

$$
\sigma \, v_{\text{rel}} \, T_{\text{year}} = 10^{-5} \times 10 \times 3.15576\times10^{7} = 3.15576\times10^{3}\ \text{km}^3/\text{年}
$$

除以壳层体积，得到每个有序对的年碰撞概率：

$$
q = \frac{3.15576\times10^{3}}{1.2925\times10^{11}} = 2.441\times10^{-8}\ \text{/年·对}
$$

这个 \(q\) 是本课最重要的中间量，后面所有碰撞率都由它乘组合数得到。

碎片-卫星：

$$
R_{ds} = 36{,}500 \times 8{,}000 \times 2.441\times10^{-8}
$$

分步：\(36{,}500 \times 8{,}000 = 2.92\times10^{8}\)；乘以 \(2.441\times10^{-8}\) 得 \(7.128\)，即 **7.13 次/年**。

碎片-碎片：

$$
R_{dd} = \frac{36{,}500 \times 36{,}499}{2} \times 2.441\times10^{-8}
$$

组合数 \(= 6.661\times10^{8}\)；乘以 \(q\) 得 \(16.26\)，即 **16.26 次/年**。

两个数与 `verify_baseline.py` 的输出逐位一致。物理含义：在当前碎片水平下，每年约有 7 颗卫星被碎片撞毁、16 对碎片相互撞上。卫星被撞毁的事件正是产额最大的事件，第三课会看到它如何驱动早期增长。

## 为什么是 \(N^2\)

把 \(R_{dd}\) 对 \(N_d\) 求导：

$$
\frac{dR_{dd}}{dN_d} \approx \frac{\sigma v T}{V} \, N_d = q\,N_d
$$

碰撞率对碎片数的斜率正比于碎片数本身：碎片翻倍，斜率翻倍，总碰撞率约翻四倍。这就是级联的数学根源——**正反馈**（positive feedback，系统的输出反过来增强其输入）。与之相对，自然衰减率对 \(N\) 的斜率是常数（第三课），线性项与平方项相减，必然在某个 \(N\) 处换符号。

一个容易混淆的点：\(R_{dd}=16\) 已经大于 \(R_{ds}=7\)，为什么现在轨道还没有失控？因为碰撞率大不等于产生率高——碎片-碎片碰撞的产额极小（每次约 3 块，第三课），而碎片-卫星碰撞每次约产生 245–337 块。数量的胜负要看"率 × 产额"。

## 代码对应

```python
# cascade_risk/physics/collision_model.py（摘录）
self._sigma_km2 = cross_section_m2 * 1e-6          # m² → km²
self._v_rel_km_per_year = v_rel_km_s * SECONDS_PER_YEAR

def collision_rate(self, n_debris, n_satellites):
    return (n_debris * n_satellites * self._sigma_km2
            * self._v_rel_km_per_year / self.shell.volume_km3)

def debris_debris_collision_rate(self, n_debris):
    return (0.5 * n_debris * (n_debris - 1) * self._sigma_km2
            * self._v_rel_km_per_year / self.shell.volume_km3)
```

## 动手核对

用纸笔（或计算器）完成两题，然后和脚本对照：

1. 把截面换成 \(5\ \text{m}^2\)，重算 \(R_{ds}\) 与 \(R_{dd}\)。预期结果约为 3.56 与 8.13 次/年。结论：碰撞率对截面是线性的。
2. 保持截面 10 m²，把碎片数翻倍到 73,000，重算 \(R_{dd}\)。预期约 65.0 次/年。验证"四倍"关系（严格值是 \((73000\times72999)/(36500\times36499) \approx 4.0\)）。

对应的终端验证：

```bash
python -c "
import sys; sys.path.insert(0, '.')
from cascade_risk.physics import OrbitalShell, CollisionModel
s = OrbitalShell(800, 200); cm = CollisionModel(s, 5.0, 10.0)
print(cm.collision_rate(36500, 8000), cm.debris_debris_collision_rate(73000))
"
```

## 本课小结

- 壳层体积 \(V = \frac{4\pi}{3}(r_{\text{out}}^3 - r_{\text{in}}^3) = 1.2925\times10^{11}\) km³。
- 圆轨道速度 \(v_{\text{circ}}=\sqrt{\mu/r}\approx7.46\) km/s；框架取 \(v_{\text{rel}}=10\) km/s，偏保守。
- 碰撞率由"扫过体积 × 数量密度"推出：\(R_{ds}=N_dN_sq\)，\(R_{dd}=\frac{N_d(N_d-1)}{2}q\)，其中 \(q=\sigma v T/V = 2.441\times10^{-8}\)。
- 基线速率：\(R_{ds}=7.13\)/年，\(R_{dd}=16.26\)/年。
- \(R_{dd}\propto N^2\) 是级联正反馈的数学来源。
