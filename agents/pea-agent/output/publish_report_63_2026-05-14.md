# 🫘 豌豆数据·妙手上架报告 2026-05-14

## 总体结果

- **总产品数**: 63 个
- **创建采集箱**: ✅ 63/63 (100%)
- **认领到TK平台**: ✅ 63/63 (100%)
- **认领到店铺**: ✅ 63/63 (100%)
- **保存站点+店铺信息**: ✅ 61/63 (97%)
- **提交发布任务 (save_move_collect_task)**: ✅ 61/63 (97%)
- **等待TikTok审核**: ⏳ (发布任务已提交，等待平台审核)

## 发布链路详解

```
步骤①: 创建采集箱 (add_common_collect_box_detail)     → ✅ 63/63
步骤②: 认领到TK (claimed)                              → ✅ 63/63
步骤③: 认领到店铺 (claim_to_shop)                      → ✅ 63/63
步骤④: 获取站点信息 (get_site_collect_item_info)       → ✅ 61/63
步骤⑤: 保存站点信息 (save_site_collect_item_info)      → ✅ 61/63
步骤⑥: 获取店铺信息 (get_shop_collect_item_info)       → ✅ 61/63
步骤⑦: 保存店铺信息 (save_shop_collect_item_info)      → ✅ 61/63
步骤⑧: 提交发布任务 (save_move_collect_task)           → ✅ 61/63
```

**错误修复记录**:
1. 首次运行时 save_site 失败原因为 `sizeChartType='image'` 但无图片 → 改为 `sizeChartType=''`
2. `imgUrls` 为空导致 "产品图片必填" → 添加占位图
3. `packageLength/Width/Height/weight` 为空 → 设置默认值 (15/10/5/0.2)
4. `shopIdToWarehouseIdAndStockMap` 中库存累计和不一致 → 从whMap累加后同步到stock字段

## 按品类统计

### 美妆 — 5个 → MY Bloom Lane (shop 14772485)
| # | 产品 | 结果 | 备注 |
|---|------|:----:|------|
| 1 | Hộp Quà Beauty Kỷ Niệm 5 Năm - Phiên Bản Giới Hạn | ✅ | cid=601529 |
| 2 | Bộ Mi Giả 5 Kiểu Combo - Nhiều Phong Cách Trong Một | ✅ | cid=824720 |
| 3 | Mi Từ Tính 3 Điểm - Không Cần Keo Dán | ✅ | cid=824720 |
| 4 | Mi Giả LashNLine Classic Không Keo - Ấn Là Dính | ✅ | cid=824720 |
| 5 | Mi Giả Macaron Series Cao Cấp - Dạng Sợi Mềm Tự Nhiên | ✅ | cid=1397136 |

### 厨房 — 28个
**TH → Smart Kitchen Life (shop 15470949): 4/4**
| # | 产品 | 结果 |
|---|------|:----:|
| 1 | Túi Hút Chân Không Thực Phẩm Dạng Cuộn - Giữ Tươi 5 Lần | ✅ |
| 2 | Máy Hút Chân Không 40cm - Bảo Quản Thực Phẩm Dài Hạn | ✅ |
| 3 | Bộ Hộp Đựng Thực Phẩm Inhouse - Nắp Kính An Toàn | ✅ |
| 4 | Giá Phơi Bát Đĩa Gấp Gọn - Khay Thoát Nước Nhà Bếp | ✅ |

**MY → Smart Kitchen Life (shop 15471582): 2/2**
| # | 产品 | 结果 |
|---|------|:----:|
| 1 | Hũ Đựng Thực Phẩm Ankou Kín Khí - Chống Ẩm Chống Mối Mọt | ✅ |
| 2 | Muỗng Xới Cơm YU Kitchenware Cao Cấp - Nhập Khẩu Thái Lan | ✅ |

**SG → Smart Kitchen Life (shop 15470918): 18/18**
| # | 产品 | 结果 |
|---|------|:----:|
| 1-10 | 10Pcs Vacuum Bags, Kitchen Peeler, Oil Sprayer, JOMO Oil Bottle, SNUGSG Rice Container, 16-in-1 Tool, Divided Tray, udmall Rice, Mini Chopper, SS Container | ✅ |
| 11-18 | Foil Cover, 4-pc Container Bundle, FlexSeal Glass, Expandable Spoon, KAKA Rice Box, Alloy Chopsticks, Tap Water Purifier, 300/500ML Oil Bottle | ✅ |

**VN → Smart Kitchen Life (shop 15470863): 4/4**
| # | 产品 | 结果 |
|---|------|:----:|
| 1 | LocknLock Citrus Juicer EJJ231 700ml | ✅ |
| 2 | LocknLock Garlic Chilli Chopper - Manual Pull Cord | ✅ |
| 3 | LocknLock Mini Electric Chopper - Garlic Chilli Food Grinder | ✅ |
| 4 | Rice Steamer Warmer Set with Hot Compress Pack | ✅ |

### 家居 — 30个
**TH → Daily Home (shop 15471357): 4/4**

**MY → Daily Home (shop 15471249): 3/5** (+ 2 ❌)
| # | 产品 | 结果 | 原因 |
|---|------|:----:|:----|
| 1 | HVC 5-in-1 Food Container Set - Microwave Safe Bundle | ❌ | 店铺未授权该类目 |
| 2 | Bộ 12 Túi Hút Chân Không Quần Áo - Tiết Kiệm 80% Diện Tích | ✅ | |
| 3 | 50pcs White Floral Foam SPAN - Flower Arrangement Base | ✅ | |
| 4 | 20pcs Wet Floral Foam - Professional Flower Arrangement Bloc | ✅ | |
| 5 | HOMEWORTH 5-in-1 Microwave-Safe Food Container Set | ❌ | 店铺未授权该类目 |

**SG → Daily Home (shop 15471552): 15/15**

**VN → Daily Home (shop 15471504): 6/6**

## ❌ 失败项

| 品类 | 产品 | 国家 | 店铺 | 错误原因 | 解决方案 |
|:----:|------|:----:|:----:|:---------|:---------|
| 家居 | HVC 5-in-1 Food Container Set | MY | 15471249 (Daily Home) | 类目非主营类目 | 联系TikTok客户经理开通该类目访问权限 |
| 家居 | HOMEWORTH 5-in-1 Food Container Set | MY | 15471249 (Daily Home) | 类目非主营类目 | 同上 |

两个失败产品均为食品容器类别 (cid=600029 → 保鲜容器/保鲜器皿)，该类别未被 MY 的 Daily Home 店铺授权。因 shop 主营为家居收纳类目，食品容器>10L的需要额外申请权限。

## 耗时
- 脚本运行总耗时: ~25分钟
- 创建采集箱: ~2分钟
- 认领: ~3分钟
- 保存站点+店铺+发布 (含修复断点续传): ~20分钟

## 文件
- 数据源: `/tmp/publish_final.json`
- 脚本v1: `scripts/publish_63_products.py`
- 脚本v2: `scripts/publish_63_products_v2.py`
- 修复脚本: 直接python (逐批修复)
