# 🥬 全品类文案一致性检查报告

> 生菜 | 2026-05-14 | 美妆(20) + 家居(20) + 厨房(20) = 60产品 × 5国 = 300条文案

---

## 一、全局统计

| 维度 | 美妆 🪞 | 家居 🏠 | 厨房 🍳 | 结论 |
|:-----|:-------:|:-------:|:-------:|:-----|
| 产品数 | 20 | 20 | 20 | ✅ 一致 |
| 国家覆盖 | 5/5 → 全 | 5/5 → 全 | 5/5 → 全 | ✅ 一致 |
| 关键词数量 | 5 ± 0 | 5 ± 0 | 5 ± 0 | ✅ 一致 |
| 中文残留 | 0条 | 0条 | 0条 | ✅ 无 |
| 标题格式 | **即兴加粗标题**(无`English Title:`) | 有`English Title:` | 有`English Title:` | ⚠️ 不一致 |
| 标题语气 | 内容型/描述功能 | 促销型/问题导向 | 促销型/卖点突出 | ⚠️ 有差异 |
| 描述最大长度(SG) | 296 | **377** | 249 | ⚠️ 家居SG超长 |
| 描述最小长度(VN) | 189 | 146 | 87 | ⚠️ 厨房VN过短 |
| 💰 0$API成本(0 $) | 全部完成 | 全部完成 | 全部完成 | ✅ |

---

## 二、标题格式不一致 ⚠️ (一级问题)

### 2.1 美妆：无结构化标题

美妆产品采用**行内加粗标题**，没有 `**English Title:**` 标记：

```
## Product #1: 4-Pack Teardrop Makeup Sponges - Multicolor Set

- **Keywords:** makeup blender, ...
```

**问题**：标题直接写为`## Product #1: xxx` 不是`**English Title:**`标记，与其他两个品类格式不同。

### 2.2 家居/厨房：有结构化标题

家居和厨房产品统一使用 `**English Title:**`：

```
## Product #1: Microfiber Cleaning Cloth 40×40cm — 10-Pack

**English Title:** Microfiber Cleaning Cloth 40×40cm 10-Pack — Streak-Free, Lint-Free, Super Absorbent
```

### 2.3 影响

- SKU匹配时，美妆品类没有独立的英文章案标题字段
- 如果下游系统需要提取标题，美妆品类需特殊处理

---

## 三、描述长度分布 (二级问题)

### 3.1 各品类描述长度统计

| 品类 | 最短(SG) | 最长(SG) | 最短品类内 | 最长品类内 | 均值 |
|:-----|:--------:|:--------:|:----------:|:----------:|:----:|
| **美妆** | 243 | 296 | 189(TH) | 296(SG) | ~245 |
| **家居** | 210 | **377** | 146(VN) | **377(SG)** | ~272 |
| **厨房** | 140 | 249 | **87(VN)** | 249(SG) | ~157 |

### 3.2 超长问题：家居品类 SG 严重超限

家居品类中 **11个产品SG描述超过300字符**（目标≤300）：

| 家居产品# | 产品名 | SG长度 | 超限 |
|:---------:|:-------|:------:|:----:|
| #4 | Microfiber Cleaning Cloth 30×30cm 20-Pack | 已重新计算 | - |
| #4 | Kitchen Degreasing Cloth 5-Pack | 329 | +29 |
| #5 | Wood Pulp Cellulose Sponge Cloth 5-Pack | 316 | +16 |
| #7 | Window Squeegee Glass Scraper | 328 | +28 |
| #8 | Floor Cleaning Wet Wipes 60 Sheets | 324 | +24 |
| #9 | Washing Machine Lint Filter Bag 5-Pack | 351 | +51 |
| #10 | Sink Strainer Mesh 100-Pack | 349 | +49 |
| #11 | Drain Hair Catcher Stick 10-Pack | 338 | +38 |
| #12 | Multi-Purpose Cleaning Brush Set 4-Piece | 350 | +50 |
| #13 | Magic Eraser Sponge 20 Blocks | 345 | +45 |
| #14 | Hand Soap Refill Pouch 500ml | **377** | **+77 🔴** |
| #15 | Compressed Towel Tablets 50-Pack | 335 | +35 |

### 3.3 过短问题：厨房品类 VN 过短

| 产品 | 国家 | 长度 | 问题 |
|:----|:----|:----:|:-----|
| Kitchen #11 (Sink Strainer) | 🇻🇳 VN | 87字 | 🟡 仅3个短句 |
| Kitchen #12 (Mould Remover) | 🇻🇳 VN | 95字 | 🟡 信息量不足 |
| Kitchen #13 (Stove Guard) | 🇻🇳 VN | 96字 | 🟡 缺少使用场景 |
| Kitchen #10 (Faucet Guard) | 🇻🇳 VN | 125字 | 🟡 相比SG(161)短36% |

**趋势**：厨房品类整体描述偏短（均157字），SG最长249也低于美妆均值的296。厨房品类整体描述充足度需要提升。

### 3.4 跨品类最大/最小差异

| 品类 | 品内最大差异 | 备注 |
|:-----|:----------:|:-----|
| 美妆 | +88 (P#14 Hightlight Brush) | SG(277) vs TH(189) |
| 家居 | **+231** (P#14 Hand Soap) | ⚠️ SG(377) vs VN(146) |
| 厨房 | +119 (P#20 Silicone Bumper) | ⚠️ SG(250) vs VN(131) |

---

## 四、跨品类卖点一致性 (三级问题)

### 4.1 相同产品出现在不同品类中

| 产品 | 家居编号 | 厨房编号 | SG描述对比 |
|:-----|:--------:|:--------:|:----------|
| Sink Strainer Mesh | #10 | #12 | ⚠️ 语义不同：家居"fine nylon mesh catches food scraps, hair, and debris. **Incredible value at under 100-pack pricing. Drain maintenance made easy!"** vs 厨房"fine mesh catches scraps and hair. **Disposable. No more scrubbing metal strainers. Fresh, odor-free sink daily!"** |
| Door Stopper | — | #19 | 仅出现在厨房品类 |

### 4.2 各品类SG描述风格差异

| 品类 | SG风格特征 | 口语化程度 |
|:-----|:-----------|:----------:|
| 🪞 美妆 | 柔和、产品质感、使用感受导向 | 中等 |
| 🏠 家居 | **问题解决型、有紧迫感**("Game changer", "Must have") | 略高 |
| 🍳 厨房 | 实用导向、直接描述功能 | 适中 |

**具体示例对比（同一卖点）**：

- **美妆SG**: "Ultra-soft and lightweight, these lashes mimic natural rabbit fur for a wispy, feathery look."
- **家居SG**: "High-performance fabric absorbs grease and oil instantly. **Game changer for kitchen cleanup!**"
- **厨房SG**: "Sharp stainless steel blade. Carrots, potatoes, cucumbers, tomatoes. **A reliable peeler for every kitchen!**"

家居品类使用了更多**感叹号、急迫语气**(Game changer, Wajib, Must have)，美妆偏柔和，厨房偏中性。

---

## 五、各国口语化自然度检查

### 5.1 🇹🇭 TH

- **美妆**: 自然口语化，如"ใช้เปียกหรือแห้งก็ได้"、"ที่สำคัญราคาดี" ✅
- **家居**: 部分产品过长，句子堆砌感。如"ผ้าไมโครไฟเบอร์ทำความสะอาด40×40cm จำนวน 10 ผืน เนื้อนุ่มพิเศษ" — 更像目录⛔
- **厨房**: 过短，信息不足。如"ที่หนีบประตูแบบไม่ต้องเจาะ ติดตั้งง่ายใช้หนีบขอบประตู" — 简洁但缺情感 ⚠️

### 5.2 🇲🇾 MY

- **美妆**: 自然马来口语，感言式："Wajib ada!" / "Jimat dan praktikal!" ✅
- **家居**: 自然，但超长产品描述显得啰嗦 ⚠️
- **厨房**: 简短直接，缺少情感点缀 🟡

### 5.3 🇻🇳 VN

- **美妆**: 表现最均衡。句子完整、自然流畅，"Giá hợp lý!" / "Sản phẩm không thể thiếu!" ✅
- **家居**: 偏长但自然，如"Sạch bóng như mới!" 有感染力 ✅
- **厨房**: 过短！"Cản cửa silicon ngăn trầy tường" — 太简介，不像推荐文章 🟡

### 5.4 🇵🇭 PH

- **美妆**: 口语化极好，"Sulit na sulit!" / "Glow up na!" ✅ 最自然
- **家居**: 自然，但超长SG的描述不平衡 ⚠️
- **厨房**: 偏短，仍可接受 "Isang set, lahat na!" 有感染力 ✅

**综合自然度排名：美妆(🥇) > 家居(🥈) > 厨房(🥉)**

---

## 六、同类产品跨品类一致性

| 对比维度 | 结论 |
|:---------|:-----|
| Sink Strainer Mesh SG | ⚠️ 家居版强调"incredible value"和"drain maintenance"，厨房版强调"no scrubbing"和"fresh odor-free" — 侧重点不一致 |
| 产品编号跳跃 | ⚠️ 家居和厨房编号非1-20连续（如Home #48, #53, #64, #66, #74；Kitchen #81, #83, #92），意味这不是TOP20而是从长列表中挑选的，影响了跨品类公平比较 |
| 各品类描述深度 | 美妆最详细(~250字/条)、家居居中(~270字/SG长)、厨房最简(~157字/条) — 投入不均 |

---

## 七、异常产品清单

### 异常产品：SG严重超长（>300字）

| 品类 | 产品编号 | 产品 | SG长度 | 建议 |
|:----|:--------:|:-----|:------:|:-----|
| 🏠家居 | #14 | Hand Soap Refill Pouch | **377** 🚩 | 精简至250-280字 |
| 🏠家居 | #9 | Washing Machine Lint Filter | 352 🚩 | 精简至280字 |
| 🏠家居 | #12 | Multi-Purpose Cleaning Brush | 351 🚩 | 精简至280字 |
| 🏠家居 | #10 | Sink Strainer Mesh | 349 🚩 | 精简至280字 |
| 🏠家居 | #13 | Magic Eraser Sponge | 346 🚩 | 精简至280字 |
| 🏠家居 | #11 | Drain Hair Catcher Stick | 339 🚩 | 精简至280字 |
| 🏠家居 | #15 | Compressed Towel Tablets | 335 🚩 | 精简至280字 |
| 🏠家居 | #7 | Window Squeegee | 329 🚩 | 精简一致 |
| 🏠家居 | #3 | Kitchen Degreasing Cloth | 329 🚩 | 精简至280字 |
| 🏠家居 | #8 | Floor Cleaning Wet Wipes | 325 🚩 | 精简至280字 |
| 🏠家居 | #4 | Wood Pulp Cellulose Sponge | 317 🚩 | 精简至280字 |

### 异常产品：VN过短（<100字）

| 品类 | 产品编号 | 产品 | VN长度 |
|:----|:--------:|:-----|:------:|
| 🍳厨房 | #11 | Sink Strainer Mesh | 87字 🟡 |
| 🍳厨房 | #12 | Mould Remover | 95字 🟡 |
| 🍳厨房 | #13 | Stove Splatter Guard | 96字 🟡 |

### 异常产品：美妆标题格式不统一

| 问题 | 详情 |
|:-----|:-----|
| 标题字段 | 美妆无`**English Title:**`，家居/厨房有 |
| Header市场声明 | 美妆标"SG, MY, VN, PH"但实际有TH；家居标"SG(primary), PH"但实际全部5国；厨房标"SG(primary), MY/VN/PH"但实际全部5国 |
| 产品覆盖 | 美妆固定5国全覆盖；家居/厨房header说只覆盖部分市场但实际全部5国 |

---

## 八、修复建议

### 🔴 P0 — 必须修复

1. **美妆标题格式统一**
   - 为所有美妆产品增加 `**English Title:**` 字段，参照家居/厨房格式
   - 使用当前行内加粗内容作为标题值

2. **家居SG描述缩短 ≤300字符**
   - 11个产品需重新精简（当前377→280字左右）
   - 精简原则：去掉冗余修饰，保留关键卖点+行动号召即可

3. **厨房VN描述加长到120-180字符**
   - 3个过短产品需补充使用场景和购买理由

### 🟡 P1 — 建议修复

4. **Header声明与实际内容一致**
   - 各品类header的市场声明需反映实际5国全覆盖的事实
   - 或将限量市场的产品明确标注

5. **跨品类卖点对齐**
   - Sink Strainer Mesh 两个版本的SG描述建议统一核心卖点顺序
   - 可选方案：将重叠品归类到其中一个品类并移除另一个

6. **跨品类描述长度均衡**
   - 厨房品类整体需加长20-30%（从~157字提到~200字/条）
   - 家居品类需把SG之外的其他国家也加长（尤其VN维基）

### 🟢 P2 — 优化项

7. **家居品类语气温和化**
   - 减少"Game changer"、"Must have"等过度促销用语
   - 部分过渡到美妆式的使用感受描述

8. **厨房品类语气增强**
   - 加入更多口语化短句增强亲和力
   - 参考美妆的"Best upgrade from..." / "Essential for..."

---

## 九、结论

| 检查维度 | 结果 | 严重度 |
|:---------|:-----|:------:|
| 标题格式统一 | ❌ 美妆vs家居/厨房不一致 | 🔴 |
| 描述长度(≤300) | ❌ 家居11个SG超限 | 🔴 |
| 关键词数量(3-5) | ✅ 全部5个，完美一致 | — |
| 口语化自然度 | ✅ 美妆优，家居中，厨房偏低 | 🟡 |
| 中文残留 | ✅ 完全无中文残留 | — |
| 跨品类卖点一致性 | ⚠️ Sink Strainer不一致，其余OK | 🟡 |
| 基本合规(无中文/全覆盖) | ✅ 300条文案，0中文残留，0国家缺失 | — |

**总体评价**：70/100 → 文案质量扎实，但格式不统一(SG长度)和跨品类一致性可加强。
