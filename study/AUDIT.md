# 审计报告：Bug 与不严谨清单（2026-10-20）

> 审计对象：`cascade_risk/` 代码、`main.py`、三份手稿（`paper/framework_paper.md`、`gen_paper_pdf.py`、`gen_paper_docx.py`）、`docs/index.html`、README、`SGAC_proposal.md`、`op_ed_draft.md`、`study/` 课件。
> 方法：静态阅读 → 量纲/代数手算 → 数值探针（`audit_probe.py`、`audit_n0.py`、`audit_convergence.py`）→ 跨文档一致性核对（代码 / md / PDF / DOCX / HTML / 课件）。
> 原则：只记录**已复现**的问题；每条给出证据命令与修正后数值。

---

## 0. 复现命令

```bash
python main.py                     # 主链路，约 30 s，生成 output/*.png
python study/audit_probe.py        # A–N 节，EVT/聚合/配置/时点/单调性等探针
python study/audit_n0.py           # N0 敏感性（300 路径）
python study/audit_convergence.py  # 路径数与 dt 收敛（300/1000/2000）
python study/verify_baseline.py    # 基线数字快照
python -m pytest tests/ -q         # 43 passed
```

基线（1,000 路径，seed 42，dt=0.1）：EL $921.4M、VaR95 $1,365.1M、CVaR95 $1,565.4M、
VaR99 $1,720.8M、保费 $2,057.5M、每保单 $4,115,098、倍数 16.46×。

---

## 1. P0：确认的代码错误（已修）

### P0-1 EVT VaR 漏掉超阈比例 ζ

- **现象**：`_evt_var()` 直接把 `1-p` 当作 GPD 尾概率，忽略了只有 `ζ=N_u/n` 比例的样本进入尾部。
- **后果**：尾概率被高估 `1/ζ=10` 倍，EVT VaR95 虚高到 $1,802.5M，并由此编出"经验分位低估 32%"的结论。
- **证据**：`audit_probe.py` B 节，u=$1,240.1M、β=$196.9M、ζ=0.10、ξ=−0.0321。
- **修正**：`tail_prob=(1-p)/ζ`，`VaR_p=u+β/ξ[( (1-p)/ζ )^(−ξ)−1]`；`_evt_cvar` 同样透传 ζ。

| 量 | 旧（漏 ζ） | 修正 | 经验分位 | 偏差 |
|---|---|---|---|---|
| EVT VaR95 | $1,802.5M | **$1,375.1M** | $1,365.1M | +0.7% |
| EVT VaR99 | $2,083.1M | **$1,677.2M** | $1,720.8M | −2.5% |
| EVT CVaR95 | — | **$1,561.7M** | $1,565.4M | −0.2% |

- **影响面**：EVT 不进保费，因此 16.5× 不变；但论文/网页/课件的尾部叙事全部改写。

### P0-2 `aggregate_losses` 的贴现与 dt 双重错误

- **现象 a**：贴现因子用步索引 `t` 而不是日历时间 `t·dt`，501 步被当成 501 年贴现。
- **现象 b**：修好 a 后，把 501 个"年化损失率"直接相加，等于把 0.1 年当成 1 年，结果放大 10 倍。
- **证据**：`audit_probe.py` F 节。旧值 $687.4M → 仅修贴现 $25,175.1M → 乘 `dt` 后 **$2,517.5M**（3.7×）。
- **修正**：`1/(1+r)^(t·dt)`，并对求和乘 `dt_years`；函数签名增加 `dt_years`，`main.py` 传入。
- **影响面**：该字段不参与头条保费，仅影响若有后续 NPV 分析。

### P0-3 论文组合损失公式与概率论冲突

- **现象**：`E[L]=p_hit·V_sat·n·(1+(n−1)ρ)/n`，把方差比当成了均值因子。
- **后果**：`n=500, ρ=0.3` 时因子 0.3014，EL 被压到 $277.7M，与代码 $921.4M 矛盾。
- **证据**：`audit_probe.py` C 节。
- **修正**：EL 写成 `n·p_hit·V_sat`（与 ρ 无关）；相关性只进入
  `Var(L)=n·σ_L²[1+(n−1)ρ]`；明确 copula 模块不进口径。

### P0-4 保费图漏乘保单数、风险加载口径不一致

- **现象**：时间序列图把**每星**损失传给期望**组合**损失的函数，曲线低 500 倍；加载项也未按四项公式逐步计算。
- **修正**：`visualization.py` 先乘 `n_policies`；`compute_time_varying_premium()` 在每一步用
  `EL + 1.5(CVaR95−EL) + 0.04(VaR99−EL) + 0.15EL`，与头条一致。

### P0-5 `carrying_capacity` 硬编码衰减率

- **现象**：`K = b·N/(λ+aN)` 中的 λ 写死 0.005，配置改衰减率时 K 不变。
- **证据**：`audit_probe.py` I 节：K(0.005)=204,783；K(0.05)=**2,047,828**（10×，方向正确）。
- **修正**：增加 `decay_rate_per_year` 参数并校验为正；`main.py` 传入配置值。

### P0-6 敏感性龙卷风图运行时崩溃且信息量为零

- **现象 a**：`tornado` 使用 `ax` 但从未创建 `fig, ax` → `NameError`。
- **现象 b**：修好后多数参数的 OAT 区间跨过奇点，柱状图被 1e6 截断，读者无法解读。
- **修正**：改为"到奇点时间 t\*"的龙卷风图（低/高值两段 + 50 年线 + 基线 61.1 年），区间 27–136 年。

### P0-7 配置未知键被静默丢弃

- **现象**：YAML 拼错键名（如 `shell_thicknes_km`）不报错，直接使用默认值。
- **修正**：`Config.from_yaml` 对 physics/economics 的未知键抛 `ValueError`；探针 G 节确认被拒。

---

## 2. P1：口径与严谨性问题（已修）

| # | 问题 | 证据 | 修正 |
|---|---|---|---|
| P1-1 | "calibrated to three events" 不成立 | `calibrate_k_debris()` 给出 μ=4.152/σ=1.008/中位 63.5，配置是 5.5/0.8/244.7，且该函数未回填 | 全文改为 "event-anchored prior / order-of-magnitude check" |
| P1-2 | "no free parameters" 不成立 | N₀、产额、0.5% 基准、V_sat、N_pol 都是选择 | 改为 "no separately tuned cascade-rate parameter" 并列出选择项 |
| P1-3 | 基准说成 launch failure | 0.5% 是 in-orbit 假设，非观测保费 | 全文改 in-orbit，并注明是 assumption；删除伪造引用 `[5]` |
| P1-4 | EL 定义含糊 | 样本是 `max_t L(t)`，不是年均 | 统一写 "mean worst-year loss"；说明最差年即第 50 年 |
| P1-5 | **16.5× 的时间口径** | t=0 的 EL $22.3M（0.18×），t=25 $111.0M（0.89×），t=50 $921.4M（7.37×）；1,000 路径 100% 最差年在最后一步 | 明确 "第 50 年公平保费 vs 静态基准"，不是"今天低估 16.5×" |
| P1-6 | N₀ 把全球目录塞进单壳层 | 300 路径：8k→$114.1M(2.21×)、10k→149.4(2.76×)、12k→185.0(3.37×)、20k→347.1(6.13×)、36.5k→925.0(15.51×) | 写入 limitations 并给敏感性表 |
| P1-7 | 有限时间奇点未披露 | t\*=61.1；N(55)=89.3N₀、N(60)=581.5N₀；OAT 27–136 年 | 摘要、结果、limitations 全部披露 |
| P1-8 | 二项索赔噪声未建模 | EL $921.4M→$1,242.5M(+35%)，VaR95 $1,365.1M→$1,752.5M(+28%)，sd $283.1M | 说明头条是期望索赔口径的下界 |
| P1-9 | "systemic insolvency" 与 $1.2B 市场不自洽 | 缺口 $1,933M > 全市场 $1,200M | 改为"500 星集中组合的 solvency 信号"，不声称全行业破产 |
| P1-10 | "41× 与 Liou & Johnson 一致"无依据 | 其情景/产额/时限不同 | 改为定性一致，不给定量对齐 |
| P1-11 | "last 18 years" | 2007–2021 = 14 年 | 改为 14 年 |
| P1-12 | 每保单 $4,116,000 | 代码输出 $4,115,098 | 全部统一为 $4,115,098 |
| P1-13 | EVT 叙事自相矛盾 | ξ=−0.032 是有界尾，却写 "bounded but heavy tail" | 改为 bounded tail；删除"尾部被低估 32%" |
| P1-14 | 命中概率线性化 | `min(λ,1)` vs `1−e^(−λ)`：t=0 差 0.045%，t=50 差 1.820% | 写入 limitations |
| P1-15 | 三份手稿各自维护会漂移 | DOCX 摘要仍写 "launch failure"、"systemic insolvency"、"not fitted parameters"；md 4.2 仍写 "systemic insolvency risk" | md / PDF / DOCX 三份同步；md 为规范源 |

---

## 3. P2：卫生问题（已处理或已标注）

| # | 问题 | 处理 |
|---|---|---|
| P2-1 | `loss_model.compute_hit_probability` 的 `n_debris_0` 参数未使用 | 保留以兼容签名，已在 docstring 标注可选 |
| P2-2 | `compute_time_varying_premium` 的 `historical_premium` 未使用 | 保留 API 兼容，docstring 已说明 |
| P2-3 | 网页 demo 用均匀 ±10% 衰减噪声，Python 用 N(1,0.1) | 改为 `max(0.1, 1+0.1·randn())` |
| P2-4 | `framework_paper.docx` / `_fixed` / `_formatted` / `_final` 为历史中间产物 | 仅 `framework_paper_new.docx` 已重生成；其余为旧版，建议投稿前删除 |
| P2-5 | README 写 "first model"、包 docstring 写 "first framework" | 改为 "integrated model / framework" |
| P2-6 | `paper/framework_paper.md` 2.3 节标题仍为 "Calibration" | 改为 "Consistency Check Against Observed Events" |
| P2-7 | `docs/index.html` 的 dt 偏差数字无法复现（+0.1%/+1.2%/+1.4%） | 换成实测：EL 896.5/925.0/913.0（dt=0.2/0.1/0.05） |
| P2-8 | `PortfolioRiskModel` 单步 0.56 s，501 步约 4.7 min | 不进入主链路；已标注为独立模块 |

---

## 4. 复核后确认"没有问题"的部分

这些项目被反复检查过，**不需要改**：

1. **碰撞率与量纲**：`q=σvT/V=2.4416×10⁻⁸ yr⁻¹`；`R_ds=N_dN_sq=7.130`；`R_dd=N_d(N_d−1)q/2=16.264`，与代码、论文、课件三处一致。
2. **单位换算**：σ 由 m² 转 1e−6 km²，V 用 km³，v 用 km/s，T=31,557,600 s。
3. **保费四项算术**：921.36+966.01+31.98+138.20=2,057.55；风险加载 =1.5×(1,565.37−921.36)=966.01；资本 =0.04×(1,720.77−921.36)=31.98；费用 =0.15×921.36=138.20。
4. **GPD 的 CVaR 代数**：`ES_p=(VaR_p+β−ξu)/(1−ξ)` 与代码 `var/(1−ξ)+(β−ξu)/(1−ξ)` 等价。
5. **等相关系数方差**：`Var(L)=nσ_L²[1+(n−1)ρ]`，与 `portfolio_risk.py` 的抽样结果一致（EL 与 ρ 无关）。
6. **路径收敛**：EL 925.0/921.4/921.6（300/1000/2000）；VaR95 1,354.9/1,365.1/1,364.9。
7. **dt 收敛**：EL 896.5/925.0/913.0（0.2/0.1/0.05），VaR95 差 <0.2%。
8. **配置解析**：合法 YAML 往返一致，未知键报错；`Config` 的默认值与 `baseline.yaml` 一致。
9. **测试**：`pytest` 43 passed（含碰撞率、壳层几何、保费分解、copula、EVT ζ、聚合贴现/dt、Sobol 解析、ASCII repr、分散化比率、配置校验、饱和保护）。

---

## 5. 仍未解决 / 无法由本审计保证的事项

1. **预测有效性**：没有任何样本外检验能证明 50 年轨迹是"预测"而非"情景推演"。
2. **产额先验**：log-normal 参数是事件锚定的先验，未按碰撞能量/质量逐次拟合；NASA 公式只是量级锚。
3. **单种子**：全部头条数字来自 seed=42 的单次 1,000 路径集合；未做多 seed 扫描，99% 分位与 ξ 的抽样误差未给出置信区间。
4. **物理简化**：单壳层、随机相位、忽略倾角/偏心率相关、无 ADR、卫星数固定、无跨高度迁移。
5. **保费不是"应收保费"**：它是第 50 年的公平年保费；真实市场按年续保、会随密度调整，因此 16.5× 是"不调价的代价"，不是"当前应收"。
6. **0.5% 基准**：是假设，不是对市场实际费率的调查；0.3%/1.0% 对应 27.5×/8.2×。

---

## 6. 第二轮追加审计（同日）

第一轮之后再做了静态阅读 + 数值探针，新增 2 个代码错误、3 个口径问题、4 个卫生问题。

### 6.1 新增代码错误（已修，附回归测试）

| # | 问题 | 证据 | 修正 |
|---|---|---|---|
| P0-8 | `sobol_analysis()` 的 Saltelli 配对写反 | `f=x1+2x2` 精确 S=(0.2, 0.8)，旧实现给出 (0.77, 0.19)；对 `f=x1+x3`，完全不入模的 x2 得到 S≈0.996 | 一阶用 `mean(f_A*(f_AB-f_B))/V`，总效应用 Jansen `mean((f_B-f_AB)^2)/(2V)`；新增 `tests/test_sensitivity.py` 三个解析测试 |
| P0-9 | `main.py` 在 Windows 默认 GBK 控制台崩溃 | `OrbitalShell.__repr__` 含 `km³` → `UnicodeEncodeError`，在 `[1/6]` 处退出（本轮实测复现） | repr 改为 ASCII `km^3`；新增 `test_repr_is_ascii` |

### 6.2 新增口径问题（已修）

| # | 问题 | 证据 | 修正 |
|---|---|---|---|
| P1-16 | "碎片单调增长"不成立 | 300 路径 seed 42：10.24% 的步碎片下降，100% 路径至少下降一次，平均每条路径 51 次；但 100% 路径的最大值仍在最后一步 | 论文、0004、0005、0006 改为"期望增长但路径非单调；最大值仍在末步"；探针新增 N 节 |
| P1-17 | 基准覆盖范围与模型不匹配 | 基准 0.5% 是**全部在轨故障**，模型只计**碎片碰撞**；year-0 的 0.18× 不是同口径比较 | 论文 3.3、README、网页、PDF/DOCX 手稿、0005/0006 各加一句：debris-only 基准更小，16.5× 在覆盖上保守 |
| P1-18 | `K` 被当作"承载容量/阈值" | `K=V/(σvτ)=λ/q=204,783`，未计产额与卫星解体项；基线 `b=0.0658>λ=0.005`，完整平均场没有正平衡点，`N*=λ/a=120,313` 只是 DD 子系统诊断量 | `main.py` 打印改为 "Kessler criterion … diagnostic only"；0001/0003/0006 明确"不能当作是否越过临界点的判据"；`carrying_capacity` docstring 同步（P2-14） |
| P1-19 | 组合风险模块的分散化比率恒为 1 | `sum_individual_var_95` 用**单年**伯努利 VaR：$p=3.66\%$ 时名义 95% 分位数为 0，故 sum=0、ratio=1.0（已验证输出 portfolio VaR95 $3,800M、sum individual $0M、ratio 1.0） | 改为**保单期**任意一年被击中概率 $p_{any}=1-\prod_t(1-p_t)$，`individual_var=V_sat`（$p_{any}>5\%$），否则 NaN；新增 `test_diversification_ratio_is_defined` |
| P1-20 | DD 项把 1–10 cm 碎片计入 >10 cm 编目数，且与 DS 共用卫星截面 | 每次 DD 事件约 3 块碎片被加进 \(N\)，但代码注释自述这是"small (~1-10cm)"；论文限制第 2 条同时声称"只统计 >10 cm"。实测：DD 产额置零 → \(N(50)=757{,}844\)、EL \$462.6M；DD 截面取 1 m² → \(N(50)=793{,}117\)、EL \$484.1M（基线 1,509,425 / \$921.4M） | 不改基线（会改变全部头条），在 `debris_growth.py` 模块 docstring、论文 4.4 第 2 条、README、网页、0003、0006、PDF/DOCX 手稿中披露为**该维度的上界**并给出两个实测数字；tornado 增加 DD yield 一行（t* 53–69，仍在 27–136 内） |
| P1-21 | 配置校验只查 section 内部，拼错的 section 名被静默忽略 | `Config.from_yaml` 用 `data.get("physics", {})`；若 YAML 写成 `physic:`，取到空字典，所有物理参数回落到默认值且无任何警告——与 P0-4 同一类失效 | 增加顶层 section 白名单校验；新增 `tests/test_config.py`（section 拼错、键拼错、基线可加载） |

### 6.3 新增卫生问题（已修）

| # | 问题 | 处理 |
|---|---|---|
| P2-9 | 保费图的"90% confidence band"是零宽度 | `prem_time` 是逐点分位数复合，不是路径样本；p5/median/p95 三条曲线完全相同。删除 band 与图例；"Historical Pricing"改为"Static 0.5% benchmark (assumption)" |
| P2-10 | DD 产额 1.1/0.5 硬编码在三处 | 提升为 `constants.DD_FRAGMENT_MU/SIGMA`，`debris_growth.py`（两处）与 `visualization.py` 共用 |
| P2-11 | `collision_model.py` 模块 docstring 仍称碎片 "drawn from the NASA Standard Breakup Model" | 改为 event-anchored log-normal，NASA 仅作量级锚 |
| P2-12 | P0-1/P0-2/P0-5 没有回归测试 | 新增 EVT ζ、聚合贴现/dt、K 随衰减率变化、Sobol 解析、repr ASCII 五类测试；另加分散化比率、配置校验、饱和保护测试；`pytest` 43 passed |
| P2-13 | 组合模块把"路径不确定性"压成一条平均命中率 | `simulate_portfolio_losses` 只接收每步**跨路径均值** `mean_hit_prob`，再在其上抽样；因此已命中路径数在步与步之间不是由同一批路径演化而来，分散化比率只是近似 | docstring 明写该局限；不改变头条数字（该模块不进入定价链） |
| P2-14 | `carrying_capacity()` docstring 仍称"cascade becomes self-sustaining" | 与 P1-18 的 CLI/讲义口径矛盾，代码里还留着旧叙事 | docstring 改为"characteristic scale, not a tipping point"，并注明 \(b>\lambda\) 时无正平衡点 |
| P2-15 | `LossModel` 的 `n_debris_0` 参数完全未使用 | `compute_hit_probability` 只用密度 \(n\sigma vT/V\)，不按参考数缩放；docstring 却写 "Reference debris population for scaling" | docstring 标注"kept for API compatibility; not used" |
| P2-16 | `simulate_trajectory` 返回的 `annual_collisions` 实为累计值，且从未被下游使用 | `n_collisions_total` 单调累加；`SimulationResult.all_n_collisions` 无消费者 | docstring 与 dataclass 注释标注 cumulative（不改字段名，避免 API 变动） |
| P2-17 | `calibrate_k_debris()` 校准的是"每 kg 总碎片数"，与抽样用的"每次碰撞编目碎片数"不同量纲 | 返回中位约 64，而操作值是 245；论文已说明未回填，代码 docstring 未说明 | 模块/类/方法 docstring 均加警告：仅为一致性诊断，不写入 `k_debris_mu/sigma` |

### 6.4 本轮复核结论

- 头条数字不变：EL $921.36M、VaR95 $1,365.13M、CVaR95 $1,565.37M、VaR99 $1,720.77M、EVT $1,375.08M/$1,677.17M、保费 $2,057.55M、每保单 $4,115,098、16.5×。
- `python main.py` 在默认 Windows 控制台可完整跑完并重生成 5 张图。
- DD 项的敏感度已实测并可复现（`python study/audit_probe.py` O 节）：产额置零 → EL \$462.6M；DD 截面 1 m² → \$484.1M（基线 \$921.4M）。头条因此在 DD 维度上读作上界。
- 仍未解决：单种子、无样本外检验、产额先验、单壳层。这些是研究设计问题，不是代码缺陷。

---

## 7. 修改文件索引

| 文件 | 改动 |
|---|---|
| `cascade_risk/actuarial/risk_metrics.py` | EVT 加 ζ；CVaR 透传 |
| `cascade_risk/actuarial/loss_model.py` | 贴现用 `t·dt`；求和乘 `dt` |
| `cascade_risk/actuarial/premium_calculator.py` | 时间序列四项公式 |
| `cascade_risk/actuarial/portfolio_risk.py` | 分散化比率改为保单期 $p_{any}$；单年退化时返回 NaN；docstring 澄清 latent ρ / 对角抖动 / 比率含义 |
| `cascade_risk/physics/orbital_shell.py` | K 接受衰减率参数；`__repr__` 改 ASCII（Windows 控制台）；K docstring 改为诊断量 |
| `cascade_risk/analysis/sensitivity.py` | Sobol 一阶/总效应估计量配对修正 |
| `cascade_risk/analysis/visualization.py` | 龙卷风图重建（含 DD yield 行）；保费图乘 n_policies；删零宽度 band；K 读常数 |
| `cascade_risk/physics/collision_model.py` | 模块 docstring 改为 event-anchored log-normal；新增 `saturation_population = 1/q` |
| `cascade_risk/physics/debris_growth.py` | DD 产额改用共享常数；模块 docstring 写明 DD 产额/截面的上界性质；新增饱和保护（避免 51.7 GiB 分配） |
| `cascade_risk/calibration/historical_events.py` | 明确 `calibrate_k_debris` 只是每 kg 诊断，不回填抽样参数 |
| `cascade_risk/utils/constants.py` | 新增 `DD_FRAGMENT_MU/SIGMA` |
| `cascade_risk/config.py` | 未知键与未知 section 报错；缺少默认 baseline 时告警并回落到逐字段相同的默认值 |
| `tests/` | 新增 EVT ζ、聚合贴现/dt、K 衰减、Sobol 解析、ASCII repr、分散化比率、配置校验、饱和保护、shell_volume required、simulate_path 饱和保护；43 passed |
| `main.py` | 传 decay/dt；打印口径说明；K 标注为诊断量 |
| `paper/framework_paper.md` | 摘要、1.3、2.1–2.3、3.2–3.4、4.1–4.5 全面改写 |
| `gen_paper_pdf.py` | 同上（另一份口语版手稿） |
| `gen_paper_docx.py` | 同上（第三份手稿，含伪造引用清理） |
| `docs/index.html` | 物理/校准/经济/风险/发现/局限六节改写；demo 噪声对齐 |
| `README.md` | 关键结果表 + 条件说明 + 事件锚 |
| `SGAC_proposal.md` / `op_ed_draft.md` | 同步 16.5× 的时间口径与锚定措辞 |
| `study/0002`、`0003`、`0004`、`0005`、`0006`、`README.md` | DD 截面/产额上界、EVT 推导、时间对齐、修正清单状态；0004 补中位数；0005 改为截面强非线性（实测 0.63×） |
| `output/explainer.html` | 恢复被删文件；EVT 1,803 → 1,375M；16.5× 改为第 50 年 vs 静态基准；补 DD 上界/奇点/时点限制；JS demo 加饱和保护 |
| `pytest.ini` | 新增：只收集 `tests/`，排除 `skills/` 的 900+ 个无关测试 |
| `setup.py` | `py_modules=["main"]`，修复 console script 的 ModuleNotFoundError |
| `study/audit_probe.py` | 新增 M 节（时间对齐）、N 节（路径单调性）、O 节（DD 敏感性）、G 节新增强 section 名检查；A–L 节改为修复后校验 |

---

## 8. 第三轮追加审计（同日）

第三轮针对数值边界与公开材料复核，新增 1 个崩溃级缺陷、2 个口径错误与 6 个卫生问题；测试 36 → 40。

### 8.1 新增缺陷与口径问题（已修）

| # | 问题 | 证据 | 修正 |
|---|---|---|---|
| P1-22 | \(\sigma=20\) m²（龙卷风图自身的上界）在 50 年视界内申请 **51.7 GiB** 内存并崩溃 | \(R_{dd}\propto N^2\)；\(N\) 越过饱和尺度后单步 Poisson 事件数达 69 亿，`rng.lognormal(size=n_dd)` 直接 MemoryError（本轮实测） | 新增 `CollisionModel.saturation_population = 1/q`（基线 \(4.10\times10^7\)）；`simulate_trajectory` 在 \(N\) 达到该尺度时抛 `RuntimeError`，提示缩短视界或减小截面；新增 2 个回归测试（σ=20 立即报错、饱和尺度 \(=1/q\)） |
| P1-23 | 0005 断言倍数对 σ、\(v_{rel}\) "近线性"，并给出"σ 减半 → 倍数约 8.2"的核对预期 | 实测 σ=5：EL \$48.6M、倍数 **0.63**（不是 8.1–8.3）。σ 同时进入碰撞率：\(t^*\) 从 61 年推到约 130 年，\(N(50)\) 仅约 \(4.4\times N_0\) | 0005 表格改为"强非线性"；实验段与小结按实测重写，并给出"得到 8 说明只改了损失侧"的诊断 |
| P1-24 | 公开 explainer 仍是修复前口径 | `output/explainer.html`：EVT VaR95 \$1,803M、"16.5× higher than current market rates"、"unfunded liability"、copula 被写成进入保费、"NASA calibrated"；该文件同时在工作区被删除（公开链接指向它） | 恢复文件并改为 ζ 修正后的 \$1,375M、第 50 年 vs 静态基准、copula 不入定价链、NASA 仅作量级锚；补 DD 上界、奇点、基准/时点三条限制；JS demo 加饱和保护 |

### 8.2 新增卫生问题（已修）

| # | 问题 | 处理 |
|---|---|---|
| P2-18 | `pytest` 从仓库根会收集 `skills/` 下 900+ 个无关测试并失败，破坏"36 passed"的可复现性 | 新增 `pytest.ini`：`testpaths=tests`、`norecursedirs=skills …`；`pytest -q` = 40 passed |
| P2-19 | 损失分布图 x 轴写作 "Maximum Annual Expected Loss"，但样本是已实现损失而非期望 | 改为 "Maximum Annual Loss" / "Worst-Year Loss Across Debris Paths" |
| P2-20 | 组合模块 docstring 把 latent ρ 说成命中事件相关；`_nearest_positive_definite` 自称 Higham 2002；`diversification_ratio` 名不副实 | 分别注明 latent 相关、实际是对角抖动、比率是"占最大可能损失的比例"；字段名保留以免破坏已发布 API |
| P2-21 | pip 安装后 `Config.from_yaml()` 找不到 `configs/`，console script 直接崩 | 缺少默认 `baseline.yaml` 时发出 `RuntimeWarning` 并回落到与文件逐字段相同的 dataclass 默认值（有测试钉住）；显式文件名仍报错；新增 2 个测试 |
| P2-22 | `main.py --output a/b/c` 因缺 `parents` 失败；安装后默认会写进 site-packages/output | `mkdir(parents=True)`；默认输出改为 `Path.cwd()/output` |
| P2-23 | 0004 把 EL 说成"半数以上年份不超过 921M 附近"（把均值当成了中位数） | 表中补中位数 \$872.6M；正文改为"EL 是均值，比中位数高 5.6%，偏度 1.11" |

### 8.3 第四轮追加审计（同日）

#### 8.3.1 新增缺陷与口径问题（已修）

| # | 问题 | 证据 | 修正 |
|---|---|---|---|
| P1-25 | 论文摘要/结论/§3.3、PDF/DOCX 生成器、README、op-ed、SGAC 提案、study 讲义均写"implements/decomposes according to the Solvency II Directive"，暗示合规 | 论文摘要 L12 "implements the Solvency II premium decomposition"；结论 L256 "according to the Solvency II regulatory framework"；§3.3 标题 "Solvency II Decomposition"；中文讲义 0005 L7 "要求保险公司按…思路给风险定价"（错：指令规定资本要求，不规定保费公式） | 全部改为 "Solvency-II-style"；论文结论加括号注明"6% cost-of-capital calculation of Directive 2009/138/EC is not reproduced"；0005 改写为"指令规定资本要求，不是保费公式；本框架只借用四项分解的写法，系数是定价假设"；configs/baseline.yaml 注释同步 |

#### 8.3.2 新增卫生问题（已修）

| # | 问题 | 证据 | 修正 |
|---|---|---|---|
| P2-24 | `compute_hit_probability` 与 `compute_loss_distribution` 的 `shell_volume_km3` 默认 1.0 km³ 是 10¹¹ 倍的陷阱 | 默认值 1.0 km³ 使命中率被裁剪到 1.0，损失变成 \$25B（上限）；所有调用方都显式传了 shell.volume_km3，但外部用户若省略则静默错 10¹¹ 倍 | 改为 `Optional[float] = None`，未传时抛 `ValueError("shell_volume_km3 is required")`；新增 2 个回归测试 |
| P2-25 | `simulate_path` 与 `simulate_trajectory` 重复实现，前者缺少饱和保护 | `simulate_path` 在 σ=20 时仍会申请 51.7 GiB 内存并崩溃，而 `simulate_trajectory` 已加饱和保护 | 在 `simulate_path` 的循环中加同样的 8 行饱和保护；新增 1 个回归测试 `test_simulate_path_also_raises_at_saturation` |
| P2-26 | `CalibrationEngine.validate_model` 把模拟的 per-collision 产额（~245）与历史的 total_fragments_estimated（100,000）直接比较，报出 99.8% "relative error" | 两个量纲不同：前者是 trackable >10 cm 的 per-collision 抽样，后者包含亚厘米碎片的 catalogue 总量 | 在 docstring 加 caveat 说明量纲不匹配，提示用户需先缩放到同一基准再比较 |
| P2-27 | `study/verify_baseline.py` 用位置参数调用 `compute_loss_distribution`，在 P2-24 改 required 后崩溃 | `TypeError: takes from 2 to 6 positional arguments but 7 were given` | 改为关键字参数调用 |

### 8.4 本轮复核结论

- 头条不变：EL \$921.36M、VaR95 \$1,365.13M、CVaR95 \$1,565.37M、VaR99 \$1,720.77M、EVT \$1,375.08M/\$1,677.17M、保费 \$2,057.55M、每保单 \$4,115,098、16.5×（`python study/verify_baseline.py` 逐项复现）。
- `pytest -q` = 43 passed（+3：shell_volume required × 2、simulate_path 饱和保护 × 1）；`python main.py` 正常重生成 5 张图。
- 新认识：Solvency II 命名问题横跨论文/生成器/README/op-ed/SGAC/中文讲义共 15+ 处，全部改为 "Solvency-II-style" 并在关键位置注明"6% cost-of-capital calculation of Directive 2009/138/EC is not reproduced"。
- 新认识：`shell_volume_km3` 的默认值 1.0 km³ 是 10¹¹ 倍的陷阱，改为 required 并加 ValueError 保护。
- PDF/DOCX 已重生成并同步到 `Lu_2026_*.pdf` 和 `docs/paper.pdf`。

---

## 9. 一句话结论

代码里最实质的三个错误是 **EVT 漏 ζ**、**聚合损失贴现/dt**、**组合 EL 公式**；第二轮又查出 **Sobol 估计量配对写反** 和 **Windows 控制台崩溃**；第三轮查出 **σ=20 时 51.7 GiB 的崩溃式分配**（现由饱和保护拦截）与 **0005 把倍数说成"正比于截面"**（实测 σ 减半使倍数从 16.5 掉到 0.63）。文档里最实质的问题是 **把第 50 年的公平保费说成了"今天的低估幅度"**，其次是 **"碎片单调增长"** 与 **基准/模型覆盖范围不一致**。以上均已修且不改头条（EL $921.36M、每保单 $4,115,098、16.5×）。头条 16.5× 在"单壳层 + 期望索赔 + 第 50 年 + all-peril 基准"四个条件下成立，离开任一条件都必须重新报数；在 DD 产额/截面维度上它是上界，在索赔计数噪声维度上它是下界。
