# EchoTik API 文档（整理中）

> 来源：天赐发接口文档中
> 用途：打通选品自动化流程

---

## 1. 接口认证

| 项目 | 内容 |
|------|------|
| Base URL | `https://open.echotik.live/api/v3` |
| 认证 | Basic Auth（Base64(username:password)） |
| Header | `Authorization: Basic <Base64>` |
| 获取凭证 | https://echotik.live/platform/api-keys |

---

## 2. 达人分类枚举（influencer_category_name）

| 分类（对我们有用的标⭐） | 
|-------------------------|
| ⭐ Beauty |
| ⭐ Shopping & Retail |
| ⭐ Life Style |
| ⭐ Health & Wellness |
| ⭐ Clothing & Accessories |
| Baby |
| Food & Beverage |
| Food & Cooking |
| Travel & Tourism |
| Home, Furniture & Appliances |
| Music & Dance |
| Education & Training |
| Sports, Fitness & Outdoors |
| Animals & Nature |
| Pets |
| Gaming |
| Media & Entertainment |
| Art & Crafts |
| Finance & Investing |
| Machinery & Equipment |
| Live Streaming Guild |
| Government Affairs |
| Real Estate |
| MCN |
| Other |
| NGO |
| Public Administration |
| Professional Services |
| IT & High-Tech |
| Software & Apps |
| Public Figure |
| Restaurants & Bars |
| Automotive & Transportation |
| Personal Blog |
| Brand |

---

## 3. GET /api/v3/echotik/influencer/list — 达人列表

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `region` | string | ✅ 是 | 地区代码，如 US/TH/MY/VN/ID/PH |
| `page_num` | string | ✅ 是 | 页码（从1开始，最大10000） |
| `page_size` | string | ✅ 是 | 每页条数（最大10） |
| `product_category_id` | string | 否 | 带货商品一级分类ID |
| `influencer_category_name` | string | 否 | 达人分类名称（见上表） |
| `influencer_sort_field_v2` | int | 否 | 排序字段<br>1=总粉丝量<br>2=近30天粉丝增长<br>3=总发布视频数<br>4=平均播放量<br>5=互动率<br>6=总带货商品数 |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `seller_id` | string | 否 | 店铺ID |
| `min_total_followers_cnt` | int | 否 | 最小粉丝量 |
| `max_total_followers_cnt` | int | 否 | 最大粉丝量 |
| `min_total_digg_cnt` | int | 否 | 最小点赞量 |
| `max_total_digg_cnt` | int | 否 | 最大点赞量 |
| `min_interaction_rate` | number | 否 | 最小互动率 |
| `max_interaction_rate` | number | 否 | 最大互动率 |
| `min_total_views_cnt` | int | 否 | 最小总播放量 |
| `max_total_views_cnt` | int | 否 | 最大总播放量 |
| `min_total_views_7d_cnt` | int | 否 | 最小近7日播放量 |
| `max_total_views_7d_cnt` | int | 否 | 最大近7日播放量 |
| `min_per_video_product_views_avg_cnt` | int | 否 | 最小平均带货视频播放量 |
| `max_per_video_product_views_avg_cnt` | int | 否 | 最大平均带货视频播放量 |
| `gender` | string | 否 | 性别（仅美区生效） |
| `influencer_language` | string | 否 | 达人语言 |
| `show_case_flag` | int | 否 | 是否开通橱窗<br>1=是 0=否 |
| `sales_flag` | int | 否 | 是否带货<br>0=不限制 >0=带货<br>1=视频带货 2=直播带货<br>3=直播+视频 4=开通橱窗 |

### 返回字段（data[]）

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `user_id` | string | 达人ID唯一标识 |
| `unique_id` | string | TikTok ID |
| `nick_name` | string | 昵称 |
| `avatar` | string | 头像URL |
| `region` | string | 地区 |
| `language` | string | 语言 |
| `gender` | string | 性别 |
| `category` | string | 分类 |
| `ec_score` | number | EchoTik评分 |
| `signature` | string | 签名 |
| `contact_email` | string | 邮箱 |
| `seller_id` | string | 关联小店ID |
| `show_case_flag` | int | 橱窗（1=是 0=否） |
| `sales_flag` | int | 带货标识 |
| `first_crawl_dt` | int | 首次抓取时间 |
| `off_mark` | int | 是否注销（0=未注销） |

**粉丝/互动数据：**
| 字段 | 说明 |
|------|------|
| `total_followers_cnt` | 总粉丝量 |
| `total_followers_1d_cnt` | 近1天粉丝增量 |
| `total_followers_7d_cnt` | 近7天粉丝增量 |
| `total_followers_30d_cnt` | 近30天粉丝增量 |
| `total_followers_90d_cnt` | 近90天粉丝增量 |
| `total_digg_cnt` | 总点赞量 |
| `total_digg_1d_cnt` | 近1天点赞增量 |
| `total_digg_7d_cnt` | 近7天点赞增量 |
| `total_digg_30d_cnt` | 近30天点赞增量 |
| `total_digg_90d_cnt` | 近90天点赞增量 |
| `total_views_cnt` | 总播放量 |
| `total_comments_cnt` | 总评论量 |
| `total_shares_cnt` | 总分享量 |
| `total_following_cnt` | 总关注量 |
| `interaction_rate` | 互动率 |
| `total_post_video_cnt` | 总发布视频数 |

**带货数据：**
| 字段 | 说明 |
|------|------|
| `total_product_cnt` | 总带货商品数 |
| `total_product_30d_cnt` | 近30天带货商品数 |
| `total_sale_cnt` | 总销量（预估） |
| `total_sale_gmv_amt` | 总GMV（预估） |
| `total_sale_gmv_30d_amt` | 近30天GMV |
| `total_live_sale_gmv_30d_amt` | 近30天直播GMV |
| `total_video_product_30d_cnt` | 近30天视频带货商品数 |
| `total_video_sale_30d_cnt` | 近30天视频带货销量 |
| `total_video_sale_gmv_30d_amt` | 近30天视频带货GMV |
| `avg_30d_price` | 近30天带货平均价格 |
| `most_category_product` | 带货最多商品分类 |
| `per_video_product_views_avg_7d_cnt` | 平均7天带货视频播放量 |

### 返回结构
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "user_id": "1000038",
      "unique_id": "hannahdowns",
      "nick_name": "Hannah Culver",
      "region": "US",
      "language": "en",
      "ec_score": 2.62,
      "total_followers_cnt": 183,
      "total_following_cnt": 571,
      "total_digg_cnt": 2,
      "total_views_cnt": 0,
      "total_post_video_cnt": 0,
      "sales_flag": 0,
      "show_case_flag": 0,
      ...
    }
  ],
  "requestId": "cf984f6f-04fa-4393-8ca3-f430d9cdec7e"
}
```

---

## curl 测试示例

```bash
# 东南亚美妆达人列表（泰国，Beauty类，粉丝>10000）
curl -X GET 'https://open.echotik.live/api/v3/echotik/influencer/list?region=TH&influencer_category_name=Beauty&min_total_followers_cnt=10000&sales_flag=1&page_num=1&page_size=10&influencer_sort_field_v2=1&sort_type=1' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 4. GET /api/v3/echotik/influencer/trend — 达人趋势（快照）

> 通过达人user_id，获取达人历史趋势快照，最多支持过去180天。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_id` | string | ✅ | 达人ID |
| `start_date` | string | ✅ | 开始日期 yyyy-MM-dd |
| `end_date` | string | ✅ | 结束日期 yyyy-MM-dd |
| `page_num` | int | ✅ | 页码（1开始，最大100000） |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段（data[]）

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `dt` | string | 日期 yyyy-MM-dd |
| `user_id` | string | 达人ID |
| `total_followers_cnt` | int | 总粉丝量 |
| `total_followers_1d_cnt` | int | 近1天粉丝增量（可为负数） |
| `total_digg_cnt` | int | 总点赞量 |
| `total_digg_1d_cnt` | int | 近1天点赞增量 |
| `total_views_cnt` | int | 总播放量 |
| `total_comments_cnt` | int | 总评论量 |
| `total_shares_cnt` | int | 总分享量 |
| `total_post_video_cnt` | int | 总发布视频数 |
| `total_live_cnt` | int | 总直播场次 |
| `total_sale_1d_cnt` | int | 近1天销量（预估） |
| `total_sale_gmv_1d_amt` | int | 近1天GMV（预估） |

### 返回示例
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "dt": "2025-08-02",
      "total_followers_cnt": 181667,
      "total_followers_1d_cnt": -11,
      "total_digg_cnt": 10922916,
      "total_views_cnt": 169385317,
      "total_comments_cnt": 301218,
      "total_shares_cnt": 26660,
      "total_post_video_cnt": 11210,
      "total_live_cnt": 2,
      "total_sale_1d_cnt": 0,
      "total_sale_gmv_1d_amt": 0,
      "user_id": "3993047"
    }
  ],
  "requestId": "bca6d3f8-..."
}
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/influencer/trend?user_id=3993047&start_date=2025-07-01&end_date=2025-08-02&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 5. GET /api/v3/echotik/influencer/detail — 批量获取达人详情

> 通过user_id或unique_id批量获取达人详情，单次最多10个，逗号分隔。
> `user_ids` 和 `unique_ids` 二选一必填。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_ids` | string | 二选一 | 多个用英文逗号，如 `100034,100037,100049` |
| `unique_ids` | string | 二选一 | TikTok唯一ID，逗号分隔 |

### 返回字段（data[]）

与 达人列表接口 返回字段完全一致，额外多一层详情字段：

| 新增字段 | 类型 | 说明 |
|----------|:----:|------|
| `influencer_video_duration_level` | string | JSON字符串：视频时长分布（15s/30s/1m/2m各多少条） |
| `influencer_video_publish_hour` | string | JSON字符串：发布小时分布（00-23各多少条） |
| `influencer_video_publish_week` | string | JSON字符串：发布周分布（1-7各多少条） |
| `most_views_video` | string | 最多播放的视频ID |
| `total_likes_cnt` | int | 总点赞数（额外字段） |

其余字段（粉丝/点赞/播放/GMV/带货数等）同达人列表，不重复列出。

### 返回示例
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "user_id": "100034034780479488",
      "unique_id": "bible._.verse",
      "nick_name": "Bible._.Verse",
      "region": "US",
      "language": "en",
      "ec_score": 4.28,
      "total_followers_cnt": 818,
      "total_digg_cnt": 17289,
      "total_views_cnt": 7428,
      "total_post_video_cnt": 97,
      "interaction_rate": 0.13,
      "influencer_video_duration_level": "{\"15s\":13,\"15s-30s\":8}",
      "influencer_video_publish_hour": "{\"08\":7,\"09\":7}",
      "influencer_video_publish_week": "{\"1\":3,\"2\":2,\"3\":4}",
      "most_views_video": "7376938080051170606",
      "signature": "Jesus Loves You"
    }
  ],
  "requestId": "5642012d-..."
}
```

### curl 示例
```bash
# 按user_id查
curl -X GET 'https://open.echotik.live/api/v3/echotik/influencer/detail?user_ids=100034034780479488,100037587565707264' \
--header 'Authorization: Basic <你的Base64>'

# 按unique_id查（TikTok ID）
curl -X GET 'https://open.echotik.live/api/v3/echotik/influencer/detail?unique_ids=bible._.verse,user2,user3' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 6. GET /api/v3/echotik/influencer/video/list — 达人视频列表

> 通过user_id或unique_id获取达人的视频列表，user_id和unique_id二选一必填。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_id` | string | 二选一 | 达人ID |
| `unique_id` | string | 二选一 | TikTok ID |
| `influencer_video_sort_field` | int | 否 | 排序：1=播放量 2=销量 3=销售额 4=发布时间 |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码（1开始，最大100000） |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段（data[]）

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `video_id` | string | 视频ID |
| `video_desc` | string | 视频标题（含话题标签） |
| `create_time` | string | 发布时间（unix时间戳） |
| `duration` | int | 视频时长（秒） |
| `region` | string | 地区 |
| `sales_flag` | int | 是否带货（1=带货 0=非带货） |
| `created_by_ai` | string | 是否AI视频 |
| `reflow_cover` | string | 封面URL |
| `ratio` | string | 分辨率（如540p） |
| `width` | string | 宽度 |
| `height` | string | 高度 |
| `data_size` | string | 文件大小 |
| `total_views_cnt` | int | 总播放量 |
| `total_views_1d_cnt` | int | 近1天播放量增量 |
| `total_views_7d_cnt` | int | 近7天播放量增量 |
| `total_views_30d_cnt` | int | 近30天播放量增量 |
| `total_digg_cnt` | int | 总点赞量 |
| `total_digg_1d_cnt` | int | 近1天点赞增量 |
| `total_digg_7d_cnt` | int | 近7天点赞增量 |
| `total_digg_30d_cnt` | int | 近30天点赞增量 |
| `total_comments_cnt` | int | 总评论量 |
| `total_shares_cnt` | int | 总分享量 |
| `total_favorites_cnt` | int | 总收藏量 |
| `total_video_sale_cnt` | int | 总视频销量（预估） |
| `total_video_sale_gmv_amt` | int | 总视频销售额（预估） |
| `user_id` | string | 达人ID |
| `unique_id` | string | TikTok ID |

### 返回示例
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "video_id": "7456066022957665553",
      "video_desc": "memang best weh ! skin nampak lebih fresh bila pakai 🤪 #faceglow #facespray",
      "create_time": "1736000679",
      "duration": 16,
      "region": "MY",
      "sales_flag": 1,
      "created_by_ai": "false",
      "total_views_cnt": 176,
      "total_digg_cnt": 8,
      "total_video_sale_cnt": 0,
      "total_video_sale_gmv_amt": 0,
      "user_id": "7122344901288068123",
      "unique_id": "mrmnaznrm_"
    }
  ],
  "requestId": "3afd1984-..."
}
```

### curl 示例
```bash
# 查达人带货视频（按播放量降序）
curl -X GET 'https://open.echotik.live/api/v3/echotik/influencer/video/list?user_id=7122344901288068123&sales_flag=1&influencer_video_sort_field=1&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 7. GET /api/v3/echotik/influencer/live/list — 达人直播列表

> 通过user_id获取达人的直播列表信息。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_id` | string | ✅ | 达人ID |
| `page_num` | int | ✅ | 页码（1开始，最大100000） |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段（data[]）

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `room_id` | string | 直播间ID |
| `title` | string | 直播标题 |
| `cover_url` | string | 封面URL |
| `create_time` | int | 开始时间（unix时间戳） |
| `finish_time` | int | 结束时间（unix时间戳） |
| `duration` | int | 直播时长（秒） |
| `nick_name` | string | 达人昵称 |
| `region` | string | 区域 |
| `total_views_cnt` | int | 总观看人次 |
| `total_digg_cnt` | int | 总点赞量 |
| `total_comments_cnt` | int | 总评论量 |
| `total_joins_cnt` | int | 总加入人数 |
| `total_product_cnt` | int | 带货商品数 |
| `total_sale_cnt` | int | 总销量（预估） |
| `total_sale_gmv_amt` | number | 总GMV（预估） |
| `total_followers_cnt` | int | 总粉丝量 |
| `user_id` | string | 达人ID |

### 返回示例
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "room_id": "7321509771910417194",
      "title": "NEW FREEBIES!!!",
      "create_time": 1704672004,
      "finish_time": 1704690013,
      "duration": 18009,
      "nick_name": "POP MART US SHOP",
      "region": "US",
      "total_views_cnt": 9335,
      "total_product_cnt": 97,
      "total_sale_cnt": 121,
      "total_sale_gmv_amt": 2627.73,
      "total_joins_cnt": 7506,
      "user_id": "7288986759428588590"
    }
  ],
  "requestId": "ec8e5830-..."
}
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/influencer/live/list?user_id=7288986759428588590&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 8. GET /api/v3/echotik/influencer/product/list — 达人带货商品列表 ⭐

> 通过user_id获取达人带过的商品信息，来源包含：直播带货 / 视频带货 / 橱窗带货。
> **注：** 不返回商品详细数据，需通过product_id在商品详情接口批量查询。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_id` | string | ✅ | 达人ID |
| `category_id` | string | 否 | 商品一级分类ID过滤 |
| `influencer_product_sort_field` | int | 否 | 排序：1=销量 2=销售额 3=均价 4=视频销量 5=视频销售额 |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码（1开始，最大100000） |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段（data[]）

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `product_id` | string | 商品ID |
| `product_name` | string | 商品名称 |
| `cover_url` | string | 商品封面（JSON数组含多张图） |
| `category_id` | string | 商品一级分类ID |
| `spu_avg_price` | number | SKU均价 |
| `total_sale_cnt` | int | **商品总销量（预估）** ⭐ |
| `total_sale_gmv_amt` | number | **商品总销售额（预估）** ⭐ |
| `total_video_cnt` | int | 关联视频数 |
| `total_video_sale_cnt` | int | 视频渠道销量 |
| `total_video_sale_gmv_amt` | int | 视频渠道销售额 |
| `total_live_cnt` | int | 关联直播场次 |
| `total_live_sale_cnt` | int | 直播渠道销量 |
| `total_live_sale_gmv_amt` | int | 直播渠道销售额 |
| `user_id` | string | 达人ID |

### 返回示例
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "product_id": "1729383941730701675",
      "product_name": "Unbrush Detangling Hair Brush by FHI Heat",
      "category_id": "601450",
      "spu_avg_price": 14.98,
      "total_sale_cnt": 943075,
      "total_sale_gmv_amt": 9604137.31,
      "total_video_cnt": 1,
      "total_video_sale_cnt": 0,
      "total_video_sale_gmv_amt": 0,
      "total_live_cnt": 0,
      "total_live_sale_cnt": 0,
      "total_live_sale_gmv_amt": 0,
      "user_id": "6813855719982466054"
    }
  ],
  "requestId": "b6a5f64d-..."
}
```

### curl 示例
```bash
# 查达人最卖货的商品（按销量降序）
curl -X GET 'https://open.echotik.live/api/v3/echotik/influencer/product/list?user_id=6813855719982466054&influencer_product_sort_field=1&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 9. GET /api/v3/echotik/influencer/ranklist — 达人榜单列表 ⭐

> 榜单分为天/周/月三个周期，周榜每周一，月榜每月一号。
> **influencer_rank_field**：1=粉丝榜 2=带货达人榜
> 返回值为当期周期内的**增量数据**。
> 返回达人一级/二级/三级带货类目，对选品极重要。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `date` | string | ✅ | yyyy-MM-dd格式（天榜当天，周榜周一，月榜1号） |
| `region` | string | ✅ | 地区代码，如 US/TH/MY/VN/ID/PH |
| `rank_type` | int | ✅ | 1=天榜 2=周榜 3=月榜 |
| `influencer_rank_field` | int | ✅ | 1=粉丝榜 2=带货达人榜 |
| `influencer_category_name` | string | 否 | 达人分类过滤（如Beauty） |
| `product_category_id` | string | 否 | 商品类目ID（1/2/3级均可） |
| `page_num` | int | ✅ | 页码（1开始） |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段（data[]）

| 字段 | 类型 | 说明 |
|------|:----:|:------|
| `user_id` | string | 达人ID |
| `unique_id` | string | TikTok handle |
| `nick_name` | string | 昵称 |
| `avatar` | string | 头像URL |
| `category` | string | 分类名称 |
| `region` | string | 地区 |
| `ec_score` | number | EchoTik评分 |

**⏱ 周期内增量数据：**
| 字段 | 说明 |
|------|------|
| `total_followers_cnt` | 周期内粉丝增量 |
| `total_followers_history_cnt` | 粉丝总数 |
| `total_digg_cnt` | 周期内点赞增量 |
| `total_digg_history_cnt` | 点赞总数 |
| `total_post_video_cnt` | 周期内发布视频数 |
| `total_post_video_history_cnt` | 发布视频总数 |
| `total_live_cnt` | 周期内直播场次 |
| `total_live_history_cnt` | 直播总场次 |
| `total_product_cnt` | 周期内带货商品数 |
| `total_product_history_cnt` | 带货商品总数 |
| `total_sale_cnt` | **周期内销量（预估）** ⭐ |
| `total_sale_gmv_amt` | **周期内销售额（预估）** ⭐ |
| `total_sale_history_cnt` | 总销量（预估） |
| `total_sale_gmv_history_amt` | 总销售额（预估） |

**🏷 选品类目信息：**
| 字段 | 说明 |
|------|------|
| `product_category_list` | 达人所有带货类目(1-2-3级类目:排名) |
| `most_category_id` | ⭐ **带货最多的一级类目ID** |
| `most_category_l2_id` | ⭐ **带货最多的二级类目ID** |
| `most_category_l3_id` | ⭐ **带货最多的三级类目ID** |

### 返回示例
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "user_id": "123456789",
      "unique_id": "beauty_influencer",
      "nick_name": "Beauty Queen",
      "ec_score": 8.5,
      "region": "TH",
      "category": "Beauty",
      "total_followers_cnt": 5000,
      "total_followers_history_cnt": 150000,
      "total_sale_cnt": 320,
      "total_sale_gmv_amt": 8500.00,
      "most_category_id": "601450",
      "most_category_l2_id": "601451",
      "most_category_l3_id": "601452",
      "product_category_list": "...",
      "sales_flag": 1
    }
  ],
  "requestId": "..."
}
```

### curl 示例
```bash
# 泰国美妆带货达人周榜
curl -X GET 'https://open.echotik.live/api/v3/echotik/influencer/ranklist?date=2026-05-04&region=TH&influencer_category_name=Beauty&rank_type=2&influencer_rank_field=2&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 10. GET /api/v3/realtime/influencer/detail — 达人详情（实时接口）⚡

> 通过unique_id**实时**获取达人详细数据。
> ⚠️ 实时接口可能触发风控，如返回code=500请重试。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `unique_id` | string | ✅ | TikTok ID（如 karladelatorre97） |

### 说明
- 实时数据（非离线T+1），适合做实时监控
- 离线接口用 /echotik/influencer/detail（前文第5节）
- 离线用user_ids/unique_ids批量查；实时用unique_id单查
- 实时接口比离线接口更可能遇到风控

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/influencer/detail?unique_id=karladelatorre97' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 11. GET /api/v3/realtime/influencer/video/list — 达人视频列表（实时接口）⚡

> 通过unique_id实时获取达人视频列表，使用offset分页。
> ⚠️ 可能触风控，code=500请重试。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `unique_id` | string | ✅ | TikTok ID |
| `offset` | string | ✅ | 分页游标（0开始，下一次用返回的max_cursor） |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/influencer/video/list?unique_id=karladelatorre97&offset=0' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 12. GET /api/v3/realtime/influencer/follower/list — 达人粉丝列表（实时接口）⚡

> 通过user_id获取该达人粉丝列表，使用offset分页。
> ⚠️ 可能触风控，code=500请重试。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_id` | string | ✅ | 达人ID |
| `offset` | string | ✅ | 分页游标（0开始，用返回的min_time作为下一次offset） |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/influencer/follower/list?user_id=6804496986206749701&offset=0' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 13. GET /api/v3/realtime/influencer/following/list — 达人关注列表（实时接口）⚡

> 通过user_id获取该达人关注列表，可使用offset分页。
> ⚠️ 可能触风控，code=500请重试。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_id` | string | ✅ | 达人ID |
| `offset` | string | 否 | 分页游标（用返回的min_time作为下一次offset） |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/influencer/following/list?user_id=6804496986206749701&offset=0' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 14. GET /api/v3/realtime/influencer/region — 达人地区获取（实时接口）

> 通过unique_id实时获取达人所属地区。
> ⚠️ 可能触风控，code=500请重试。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `unique_id` | string | ✅ | TikTok ID |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/influencer/region?unique_id=aadaehoon' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 15. GET /api/v3/realtime/influencer/generate/qr-code — 达人主页二维码生成

> 通过user_id生成达人主页二维码。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_id` | string | ✅ | 达人ID |

### 返回字段

| 字段 | 说明 |
|------|------|
| `qrcode_url` | 二维码图片URL（多个分辨率可选） |

### 返回示例
```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "qrcode_url": {
      "uri": "tikcode-tx/7603966499316826125",
      "url_list": [
        "https://...720.webp",
        "https://...720.jpeg"
      ]
    }
  }
}
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/influencer/generate/qr-code?user_id=6865486669187171334' \
--header 'Authorization: Basic <你的Base64>'
```

---
---

# 二、商品模块

## 16. GET /api/v3/echotik/category/l1 — 商品一级分类列表

> 获取TikTok商品一级分类数据。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `language` | string | ✅ | 语言：`th-TH` `en-US` `id-ID` `zh-CN` `ms-MY` `vi-VN` |

### 返回字段

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `category_id` | string | 分类ID |
| `category_level` | string | 级别（1/2/3） |
| `category_name` | string | 分类名称（对应语言） |
| `language` | string | 语言 |
| `parent_id` | string | 父级ID（一级为"0"） |

### 返回示例
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "category_id": "2344592",
      "category_level": "1",
      "category_name": "Bookings & Vouchers",
      "language": "en-US",
      "parent_id": "0"
    }
  ],
  "requestId": "4893e64f-..."
}
```

### curl 示例
```bash
# 获取泰文版分类
curl -X GET 'https://open.echotik.live/api/v3/echotik/category/l1?language=th-TH' \
--header 'Authorization: Basic <你的Base64>'

# 获取英文版分类
curl -X GET 'https://open.echotik.live/api/v3/echotik/category/l1?language=en-US' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 17. GET /api/v3/echotik/category/l2 — 商品二级分类列表

> 获取商品二级分类数据。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `language` | string | ✅ | 语言：th-TH/en-US/id-ID/zh-CN/ms-MY/vi-VN |
| `parent_id` | string | 否 | 父节点ID（一级分类ID），不传则返回全部二级分类 |

### 返回字段

同 L1：category_id / category_level / category_name / language / parent_id

### curl 示例
```bash
# 获取某个一级分类下的全部二级分类
curl -X GET 'https://open.echotik.live/api/v3/echotik/category/l2?language=en-US&parent_id=602118' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 18. GET /api/v3/echotik/category/l3 — 商品三级分类列表

> 获取商品三级分类数据（最细粒度）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `language` | string | ✅ | 语言 |
| `parent_id` | string | 否 | 父节点ID（二级分类ID） |

### 返回字段

同 L1/L2：category_id / category_level / category_name / language / parent_id

### curl 示例
```bash
# 获取某二级分类下的全部三级分类
curl -X GET 'https://open.echotik.live/api/v3/echotik/category/l3?language=en-US&parent_id=1001992' \
--header 'Authorization: Basic <你的Base64>'
```

---
---

## 19. GET /api/v3/echotik/product/list — 商品列表 ⭐⭐（选品核心）

> 提供EchoTik离线（T+1）商品库数据，适用于大批量获取商品数据。**这是选品自动化最核心的接口。**

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `region` | string | ✅ | 地区代码，如 US/TH/MY/VN/ID/PH |
| `page_num` | int | ✅ | 页码（1开始，最大100000） |
| `page_size` | int | ✅ | 每页条数（最大10） |

**类目筛选：**
| 参数 | 说明 |
|------|------|
| `category_id` | 一级分类ID |
| `category_l2_id` | 二级分类ID |
| `category_l3_id` | 三级分类ID |

**销量/价格/佣金/达人过滤：**
| 参数 | 说明 |
|------|------|
| `min/max_total_sale_cnt` | 总销量范围 |
| `min/max_total_sale_30d_cnt` | 近30天销量 ⭐（看近期热度） |
| `min/max_spu_avg_price` | 均价范围（如 $2-$15 美妆工具价格带） |
| `min/max_product_commission_rate` | 佣金率范围 |
| `min/max_total_ifl_cnt` | 带货达人数范围 |
| `min/max_total_video_cnt` | 带货视频数范围 |
| `min/max_total_views_cnt` | 带货视频播放量范围 |
| `min/max_product_rating` | 商品评分范围 |
| `min/max_review_count` | 评论数范围 |
| `min/max_total_sale_gmv_amt` | 总GMV范围 |
| `min/max_total_sale_gmv_30d_amt` | 近30天GMV范围 |

**店铺/标签过滤：**
| 参数 | 取值 | 说明 |
|------|:----:|------|
| `is_s_shop` | 0/1 | 是否全托管店铺 |
| `free_shipping` | 0/1 | 是否包邮 |
| `is_hot` | 0/1 | 是否爆款商品 |
| `sales_trend_flag` | 0/1/2 | 近7天销售趋势（平稳/上升/下降） |
| `off_mark` | 0 | off_mark=0 过滤已下架 |
| `from_flag` | 1/2 | 1=本土店 2=跨境店 |
| `shop_type` | 0/1 | 是否品牌店 |
| `first_crawl_dt` | yyyyMMdd | 首次抓取时间范围 |

**排序：**
| 参数 | 取值 |
|:-----|:-----|
| `product_sort_field` | 1=总销量 2=总GMV 3=均价<br>4=近7天销量 5=近30天销量<br>6=近7天GMV 7=近30天GMV |
| `sort_type` | 0=升序 1=降序 |

### 返回字段（data[]）— 关键字段标注 ⭐

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `product_id` | string | ⭐ 商品ID |
| `product_name` | string | ⭐ 商品名称 |
| `cover_url` | string | 封面URL |
| `desc_detail` | string | 商品描述 |
| `category_id` | string | 一级分类ID |
| `category_l2_id` | string | ⭐ 二级分类ID |
| `category_l3_id` | string | ⭐ 三级分类ID（精准定位美妆工具） |
| `region` | string | 区域 |
| `seller_id` | string | ⭐ 小店ID |
| `min_price` | number | 最低SKU价格 |
| `max_price` | number | 最高SKU价格 |
| `spu_avg_price` | number | ⭐ SKU均价 |
| `product_commission_rate` | int | ⭐ 佣金率 |
| `product_rating` | int | 商品评分 |
| `review_count` | int | 评论数 |
| `discount` | string | 折扣 |
| `free_shipping` | int | 包邮（1=是） |
| `is_s_shop` | int | 全托管（1=是） |
| `off_mark` | int | 下架标识（<2未下架） |
| `sale_props` | string | 商品属性 |
| `skus` | string | 规格 |
| `sales_trend_flag` | int | ⭐ 7天趋势（0=平稳 1=上升 2=下降） |
| `sales_flag` | int | 带货方式 |
| `total_ifl_cnt` | int | ⭐ 总带货达人数 |
| `total_video_cnt` | int | 关联视频数 |
| `total_live_cnt` | int | 关联直播数 |
| `total_sale_cnt` | int | ⭐ 总销量 |
| `total_sale_gmv_amt` | number | ⭐ 总GMV |
| `total_sale_7d_cnt` | int | 近7天销量 |
| `total_sale_30d_cnt` | int | ⭐ 近30天销量 |
| `total_sale_gmv_7d_amt` | number | 近7天GMV |
| `total_sale_gmv_30d_amt` | number | 近30天GMV |
| `total_ifl_live_7d_cnt` | int | 近7天直播达人增量 |
| `total_ifl_video_7d_cnt` | int | 近7天视频达人增量 |
| `total_video_sale_7d_cnt` | int | 近7天视频销量 |
| `total_live_sale_7d_cnt` | int | 近7天直播销量 |
| `total_views_7d_cnt` | int | 近7天播放量 |
| 更多... | int | 1d/15d/30d/60d/90d 各维度数据 |

### 返回示例
```json
{
  "code": 0,
  "message": "success",
  "data": [
    {
      "product_id": "1729383941730701675",
      "product_name": "Unbrush Detangling Hair Brush by FHI Heat",
      "category_id": "601450",
      "category_l2_id": "601451",
      "category_l3_id": "601452",
      "region": "US",
      "seller_id": "6813855719982466054",
      "spu_avg_price": 14.98,
      "min_price": 14.98,
      "max_price": 14.98,
      "product_commission_rate": 10,
      "product_rating": 5,
      "review_count": 128,
      "free_shipping": 1,
      "total_sale_cnt": 943075,
      "total_sale_gmv_amt": 9604137.31,
      "total_sale_30d_cnt": 5000,
      "total_ifl_cnt": 342,
      "total_video_cnt": 1,
      "total_live_cnt": 0,
      "sales_trend_flag": 1,
      "cover_url": "[{\"url\":\"...\",\"index\":0}]"
    }
  ],
  "requestId": "..."
}
```

### curl 示例
```bash
# 泰国美妆工具爆品（$2-$15均价，近30天销量>1000）
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/list?region=TH&category_id=601450&min_spu_avg_price=2&max_spu_avg_price=15&min_total_sale_30d_cnt=1000&is_hot=1&product_sort_field=5&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 20. GET /api/v3/echotik/product/trend — 商品趋势（快照）

> 通过product_id获取商品历史趋势快照，最多过去180天。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `product_id` | string | ✅ | 商品ID |
| `start_date` | string | ✅ | yyyy-MM-dd |
| `end_date` | string | ✅ | yyyy-MM-dd |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `dt` | string | 日期 |
| `product_id` | string | 商品ID |
| `spu_avg_price` | number | 当日均价 |
| `total_sale_cnt` | int | 总销量 |
| `total_sale_1d_cnt` | int | 当日销量增量 |
| `total_sale_gmv_amt` | int | 总GMV |
| `total_sale_gmv_1d_amt` | int | 当日GMV增量 |
| `total_ifl_cnt` | int | 总带货达人数 |
| `total_video_cnt` | int | 总关联视频数 |
| `total_live_cnt` | int | 总直播场次 |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/trend?product_id=1729649010208641832&start_date=2025-07-01&end_date=2025-09-08&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 21. GET /api/v3/echotik/product/comment — 商品评论列表

> 通过product_id获取EchoTik已采集的评论列表。
> 注：仅能采集EchoTik已收录的评论数据。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `product_id` | string | ✅ | 商品ID |
| `page_num` | int | ✅ | 页码（1开始，最大100000） |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `review_id` | string | 评论ID |
| `display_text` | string | ⭐ 评论内容 |
| `rating` | int | 评分 |
| `review_timestamp` | int | 评论时间戳 |
| `product_id` | string | 商品ID |
| `sku_id` | string | SKU ID |
| `sku_specification` | string | SKU 规格 |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/comment?product_id=1729383941730701675&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 22. GET /api/v3/echotik/product/detail — 批量获取商品详情 ⭐

> 通过product_id批量获取商品详情，**单次最多10个**，逗号分隔。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `product_ids` | string | ✅ | 商品ID，多个用英文逗号分隔（最多10个） |

### 返回字段

与 `product/list` 返回字段几乎一致（含全部时间序列数据：1d/7d/15d/30d/60d/90d各维度的销量/GMV/视频/直播/达人增量）。

额外包含 `specification` 字段。

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/detail?product_ids=1729383941730701675,1729649010208641832' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 23. GET /api/v3/echotik/product/influencer/list — 商品关联带货达人列表 ⭐

> 通过product_id获取该商品关联的带货达人列表。
> 注：不返回达人明细，如需更多详情可在达人详情接口获取。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `product_id` | string | ✅ | 商品ID |
| `product_influencer_sort_field` | int | 否 | 排序：1=粉丝量 2=点赞量 3=该品销量 4=该品GMV 5=视频数 6=播放量 7=直播观看 |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `user_id` | string | 达人ID |
| `nick_name` | string | 昵称 |
| `avatar` | string | 头像URL |
| `category` | string | 达人分类（如Beauty） |
| `region` | string | 地区 |
| `total_followers_cnt` | int | 总粉丝数 |
| `total_digg_cnt` | int | 总点赞量 |
| `total_views_cnt` | int | 总播放量 |
| `total_post_video_cnt` | int | 总发布视频数 |
| `total_live_cnt` | int | 总直播场次 |
| `total_live_views_cnt` | int | 总直播观看人次 |
| `total_following_cnt` | int | 总关注数 |
| **`per_product_ifl_sale_cnt`** | int | ⭐ **该达人对此品的带货销量** |
| **`per_product_ifl_gmv_amt`** | int | ⭐ **该达人对此品的带货销售额** |
| `product_id` | string | 商品ID |

### curl 示例
```bash
# 查这个品谁在卖、谁卖得最好（按该品销量排序）
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/influencer/list?product_id=1729492547846767618&product_influencer_sort_field=3&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 24. GET /api/v3/echotik/product/video/list — 商品关联视频列表 ⭐

> 通过product_id获取该商品关联的带货视频列表。含视频播放地址 `play_addr`。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `product_id` | string | ✅ | 商品ID |
| `min_create_time` | int | 否 | 视频发布时间下限（unix时间戳） |
| `max_create_time` | int | 否 | 视频发布时间上限 |
| `product_video_sort_field` | int | 否 | 排序：1=播放量 2=点赞 3=分享 4=视频销量 5=视频GMV 6=发布时间 |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 类型 | 说明 |
|------|:----:|------|
| `video_id` | string | 视频ID |
| `video_desc` | string | ⭐ 视频标题/文案 |
| `hash_tag` | string | ⭐ 视频标签（可用于复制爆款话题） |
| `play_addr` | string | ⭐ **视频播放地址**（可能过期，过期用实时接口重取） |
| `reflow_cover` | string | 视频封面URL |
| `duration` | int | 视频时长（秒） |
| `data_size` | string | 视频大小（字节） |
| `region` | string | 地区 |
| `create_time` | string | 发布时间 |
| `user_id` | string | 达人ID |
| `total_views_cnt` | int | 播放量 |
| `total_digg_cnt` | int | 点赞数 |
| `total_comments_cnt` | int | 评论数 |
| `total_shares_cnt` | int | 分享数 |
| `total_favorites_cnt` | int | 收藏数 |
| `total_video_sale_cnt` | int | ⭐ **该视频销量** |
| `total_video_sale_gmv_amt` | int | ⭐ **该视频销售额** |

### curl 示例
```bash
# 看这个品哪个视频转化最好（按视频销量排序）
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/video/list?product_id=1729382310407603945&product_video_sort_field=4&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 25. GET /api/v3/echotik/product/live/list — 商品关联直播列表

> 通过product_id获取该商品关联的带货直播列表。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `product_id` | string | ✅ | 商品ID |
| `min_create_time` | int | 否 | 直播开始时间下限 |
| `max_create_time` | int | 否 | 直播开始时间上限 |
| `product_live_sort_field` | int | 否 | 排序：1=峰值观看 2=商品数 3=销量 4=GMV 5=总观看 |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `room_id` | 直播间ID |
| `cover_url` | 封面URL |
| `create_time` | 直播创建时间 |
| `max_views_cnt` | 峰值观看人次 |
| `total_views_cnt` | 总观看人次 |
| `total_product_cnt` | 该场直播带货商品数 |
| `total_sale_cnt` | 该场直播销量 |
| `total_sale_gmv_amt` | 该场直播GMV |
| `spu_avg_price` | 该品在该场的均价 |
| `region` | 地区 |
| `user_id` | 达人ID |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/live/list?product_id=1729382310407603945&product_live_sort_field=3&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 26. GET /api/v3/echotik/product/ranklist — 商品榜单列表 ⭐⭐

> 天/周/月商品榜单。价格**product_rank_field=1=热销榜**，**2=热推榜**（带货达人数最多）。
> 返回值为周期内的**增量数据**。周榜每周一，月榜每月一号。
> 可按三级类目精确筛选。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `date` | string | ✅ | yyyy-MM-dd（天榜当天，周榜周一，月榜1号） |
| `region` | string | ✅ | 地区代码 |
| `rank_type` | int | ✅ | 1=天榜 2=周榜 3=月榜 |
| `product_rank_field` | int | ✅ | **1=热销榜**（按销量）**2=热推榜**（按带货达人数） |
| `category_id` | string | 否 | 一级类目ID |
| `category_l2_id` | string | 否 | 二级类目ID |
| `category_l3_id` | string | 否 | 三级类目ID |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `product_id` | 商品ID |
| `product_name` | ⭐ 商品名称 |
| `region` | 地区 |
| `category_id/l2/l3` | 三级类目 |
| `min_price` | 最低价 |
| `max_price` | 最高价 |
| `spu_avg_price` | ⭐ 均价 |
| `product_commission_rate` | ⭐ 佣金率 |
| `total_sale_cnt` | **周期内销量增量（热销榜核心）** |
| `total_sale_gmv_amt` | 周期内销售额增量 |
| `total_ifl_cnt` | ⭐ **带货达人数（热推榜核心）** |
| `total_video_cnt` | 关联视频数 |
| `total_live_cnt` | 关联直播数 |

### curl 示例
```bash
# 泰国美妆工具热销月榜
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/ranklist?date=2026-05-01&region=TH&category_id=601450&rank_type=3&product_rank_field=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'

# 泰国美妆工具热推月榜（看哪些品最多达人带货）
curl -X GET 'https://open.echotik.live/api/v3/echotik/product/ranklist?date=2026-05-01&region=TH&category_id=601450&rank_type=3&product_rank_field=2&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 27. GET /api/v3/realtime/extract_product_id — 商品分享链接提取ID（实时接口）

> 通过商品分享链接获取商品ID和地区。
> ⚠️ 实时接口，可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `share_url` | string | ✅ | TikTok商品分享链接 |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/extract_product_id?share_url=https://www.tiktok.com/t/ZPH7PbVhQDwt7-vS8eu/' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 28. GET /api/v3/realtime/product/comment — 商品评论列表（实时接口）⚡

> 实时商品评论接口。不支持高QPS，可能风控（code=500重试）。
> 与离线版`/product/comment`的区别：实时+需要region参数+offset游标分页。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `product_id` | string | ✅ | 商品ID |
| `region` | string | ✅ | 地区代码（US/GB/DE/FR/IT/ID/MY/MX/PH/SG/ES/TH/VN/BR/JP/IE） |
| `offset` | string | ✅ | 从1开始，has_more=true时用返回的next_cursor |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/product/comment?product_id=1729679758111249333&region=TH&offset=1' \
--header 'Authorization: Basic <你的Base64>'
```

---

# 三、店铺模块

## 29. GET /api/v3/echotik/seller/list — 店铺列表 ⭐

> 离线（T+1）店铺数据，大批量获取店铺。可以区分**本土店**和**跨境店**！

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `region` | string | ✅ | 地区代码 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

**类目筛选：** `category_id` / `category_l2_id` / `category_l3_id`
**店铺类型：** `from_flag` — 1=本土店 **2=跨境店**
**带货方式：** `sales_flag` — 1=视频 2=直播
**销售趋势：** `sales_trend_flag` — 0=平稳 1=上升 2=下降
**排序：** `seller_sort_field` — 1=总销量 2=总GMV 3=均价

### 返回字段

| 字段 | 说明 |
|------|------|
| `seller_id` | ⭐ 小店ID |
| `seller_name` | ⭐ 店铺名称 |
| `seller_link` | 店铺链接 |
| `region` | 地区 |
| `from_flag` | **1=本土 2=跨境** ⭐ |
| `rating` | 评分 |
| `cover_url` | 店铺封面 |
| `spu_avg_price` | 店均SKU均价 |
| `product_category_list` | 商品分类列表 |
| `most_product_category_list` | TOP1商品分类 |
| `total_product_cnt` | 历史商品数 |
| `total_crawl_product_cnt` | 在店商品数 |
| `total_ifl_cnt` | 总带货达人数 |
| `total_video_cnt` | 总视频数 |
| `total_live_cnt` | 总直播数 |
| `total_sale_cnt` | 总销量 |
| `total_sale_gmv_amt` | 总销售额 |
| `total_sale_1d/7d/30d/90d_cnt` | 各周期增量销量 |
| `total_sale_gmv_1d/7d/30d/90d_amt` | 各周期增量GMV |
| `sales_trend_flag` | 销售趋势 |
| `sales_flag` | 带货方式 |
| `first_crawl_dt` | 首次抓取日期 |
| `user_id` | 达人UID |

### curl 示例
```bash
# 泰国跨境美妆店（按销量降序）
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/list?region=TH&category_id=601450&from_flag=2&seller_sort_field=1&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 30. GET /api/v3/echotik/seller/trend — 店铺趋势（快照）

> 通过seller_id获取店铺历史趋势快照，最多180天。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `seller_id` | string | ✅ | 店铺ID |
| `start_date` | string | ✅ | yyyy-MM-dd |
| `end_date` | string | ✅ | yyyy-MM-dd |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `dt` | 日期 |
| `seller_id` | 店铺ID |
| `total_product_cnt` | 总商品数（含已下架） |
| `total_crawl_product_cnt` | 在店商品数 |
| `total_sale_cnt` | 总销量 |
| `total_sale_1d_cnt` | 当日销量 |
| `total_sale_gmv_amt` | 总销售额 |
| `total_sale_gmv_1d_amt` | 当日销售额 |
| `total_video_cnt` | 总视频数 |
| `total_video_ifl_cnt` | 视频带货达人数 |
| `total_live_cnt` | 总直播数 |
| `total_live_ifl_cnt` | 直播达人数 |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/trend?seller_id=7494089513770779735&start_date=2025-06-01&end_date=2025-09-01&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 31. GET /api/v3/echotik/seller/detail — 店铺详情

> 根据seller_id获取店铺详细数据。
> 返回字段与`seller/list`一致。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `seller_id` | string | ✅ | 店铺ID |

### 返回字段

与 `seller/list` 返回字段一致，包含：from_flag（本土/跨境）、rating、spu_avg_price、total_sale_cnt、1d/7d/30d/90d 各周期销量/GMV增量、总带货达人数、视频数、直播数等。

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/detail?seller_id=7494089513770779735' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 32. GET /api/v3/echotik/seller/product/list — 店铺商品列表 ⭐

> 通过seller_id获取该店铺的所有商品列表（带完整商品数据）。
> 注：非实时，可能和实际店铺商品数有差距。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `seller_id` | string | ✅ | 店铺ID |
| `seller_product_sort_field` | int | 否 | 排序：1=总销量 2=总GMV 3=均价 4=7天销量 5=7天GMV |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | string | ✅ | 每页条数（最大10） |

### 返回字段

与 `product/list` 返回字段一致（含完整时间序列数据）。

### curl 示例
```bash
# 看跨境美妆店卖得最好的品
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/product/list?seller_id=7496107241529510668&seller_product_sort_field=1&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 33. GET /api/v3/echotik/seller/influencer/list — 店铺关联带货达人列表

> 通过seller_id获取该店铺关联的带货达人列表（谁在帮这家店带货）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `seller_id` | string | ✅ | 店铺ID |
| `seller_influencer_sort_field` | int | 否 | 排序：1=粉丝量 2=销量 3=GMV |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `user_id` | 达人UID |
| `unique_id` | TikTok ID |
| `nick_name` | 昵称 |
| `avatar` | 头像URL |
| `region` | 地区 |
| `seller_id` | 小店ID |
| `total_followers_cnt` | 粉丝数 |
| `total_digg_cnt` | 点赞量 |
| `total_following_cnt` | 关注数 |
| `total_sale_cnt` | 达人总销量 |
| `total_sale_gmv_amt` | 达人总销售额 |

### curl 示例
```bash
# 看这家店哪些达人在带货（按销量排序）
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/influencer/list?seller_id=7494818275540568755&seller_influencer_sort_field=2&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 34. GET /api/v3/echotik/seller/video/list — 店铺关联视频列表

> 通过seller_id获取该店铺关联的带货视频列表。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `seller_id` | string | ✅ | 店铺ID |
| `seller_video_sort_field` | int | 否 | 排序：1=播放量 2=视频销量 3=视频GMV |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `video_id` | 视频ID |
| `video_desc` | ⭐ 视频标题/文案 |
| `reflow_cover` | 封面URL |
| `create_time` | 发布时间 |
| `nick_name` | 达人昵称 |
| `user_id` | 达人ID |
| `avatar` | 达人头像 |
| `region` | 地区 |
| `seller_id` | 店铺ID |
| `total_views_cnt` | 播放量 |
| `total_digg_cnt` | 点赞 |
| `total_comments_cnt` | 评论 |
| `total_shares_cnt` | 分享 |
| `total_video_sale_cnt` | ⭐ 视频销量 |
| `total_video_sale_gmv_amt` | ⭐ 视频GMV |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/video/list?seller_id=7494662098975951181&seller_video_sort_field=2&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 35. GET /api/v3/echotik/seller/live/list — 店铺关联直播列表

> 通过seller_id获取该店铺关联的带货直播列表。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `seller_id` | string | ✅ | 店铺ID |
| `seller_live_sort_field` | int | 否 | 排序：1=播放量 2=销量 3=GMV |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `room_id` | 直播间ID |
| `title` | 直播标题 |
| `cover_url` | 封面URL |
| `create_time` | 开始时间 |
| `finish_time` | 结束时间 |
| `duration` | 时长（秒） |
| `nick_name` | 达人昵称 |
| `user_id` | 用户ID |
| `max_views_cnt` | 峰值人数 |
| `total_views_cnt` | 累计观看 |
| `total_joins_cnt` | 观看人数 |
| `total_sale_cnt` | 直播销量 |
| `total_sale_gmv_amt` | 直播GMV |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/live/list?seller_id=7494818275540568755&seller_live_sort_field=2&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 36. GET /api/v3/echotik/seller/ranklist — 店铺榜单列表 ⭐

> 天/周/月店铺榜单。1=热销榜（销量）2=热推榜（带货达人数）。
> 按三级类目筛选，**支持from_flag过滤跨境店**。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `date` | string | ✅ | yyyy-MM-dd（周榜周一，月榜1号） |
| `region` | string | ✅ | 地区代码 |
| `rank_type` | int | ✅ | 1=天 2=周 3=月 |
| `seller_rank_field` | int | ✅ | **1=热销榜**（销量）**2=热推榜**（达人数） |
| `category_id/l2/l3` | string | 否 | 三级类目筛选 |
| **`from_flag`** | int | 否 | **1=本土店 2=跨境店** |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `seller_id` | 小店ID |
| `seller_name` | 店铺名称 |
| `from_flag` | ⭐ 1=本土 2=跨境 |
| `region` | 地区 |
| `rating` | 评分 |
| `most_product_category_list` | ⭐ 店铺最多带货品类 |
| `total_sale_cnt` | 周期内销量 |
| `total_sale_gmv_amt` | 周期内销售额 |
| `total_ifl_cnt` | 带货达人数 |
| `total_video_cnt` | 总视频数 |
| `total_live_cnt` | 直播场次 |
| `total_product_cnt` | 商品数 |

### curl 示例
```bash
# 泰国跨境美妆店月榜热销
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/ranklist?date=2026-05-01&region=TH&category_id=601450&from_flag=2&rank_type=3&seller_rank_field=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'

# 泰国跨境美妆店月榜热推（看哪些店达人合作最多）
curl -X GET 'https://open.echotik.live/api/v3/echotik/seller/ranklist?date=2026-05-01&region=TH&category_id=601450&from_flag=2&rank_type=3&seller_rank_field=2&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 35. GET /api/v3/realtime/seller/product/list — 店铺商品列表（实时接口）⚡

> 实时店铺商品列表。不支持高QPS，可能风控（code=500重试）。
> 与离线版区别：实时+region参数+offset游标分页。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `seller_id` | string | ✅ | 店铺ID |
| `region` | string | ✅ | 地区代码（US/GB/DE/FR/IT/ID/MY/MX/PH/SG/ES/TH/VN/BR/JP/IE） |
| `offset` | string | 否 | 分页游标，首次可不传空，has_more=true时用返回的next_scroll_param |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/seller/product/list?seller_id=7495045046260173699&region=TH' \
--header 'Authorization: Basic <你的Base64>'
```

---

# 四、视频模块

## 36. GET /api/v3/echotik/video/list — 视频列表 ⭐

> 离线（T+1）视频数据，独立视频搜索，非限定某达人/某商品的视频。
> 因成本考虑，不会覆盖所有视频，如需更多用实时接口。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `region` | string | ✅ | 地区代码 |
| `sales_flag` | int | 否 | 0=非带货 1=带货 |
| `created_by_ai` | string | 否 | true/false 是否AI视频 |
| `is_ad` | int | 否 | ⭐ **1=投流视频 0=非投流** |
| `product_category_id` | string | 否 | 带货商品类目ID |
| `product_id` | string | 否 | 带货商品ID |
| `min_create_time` | int | 否 | 发布时间范围 |
| `max_create_time` | int | 否 | 发布时间范围 |
| `min_duration` | int | 否 | 时长筛选（秒） |
| `max_duration` | int | 否 | 时长筛选 |
| `min_total_views_cnt` | int | 否 | 播放量下限 |
| `max_total_views_cnt` | int | 否 | 播放量上限 |
| `video_sort_field` | int | 否 | 排序：1=点赞量 2=发布时间 3=播放量 |
| `sort_type` | int | 否 | 0=升序 1=降序 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `video_id` | 视频ID |
| `video_desc` | ⭐ 视频描述 |
| `video_products` | 关联商品列表 |
| `duration` | 时长（秒） |
| `data_size` | 文件大小 |
| `is_ad` | ⭐ 是否投流 |
| `created_by_ai` | 是否AI视频 |
| `reflow_cover` | 封面URL |
| `unique_id` | 达人TikTok ID |
| `user_id` | 达人ID |
| `avatar` | 达人头像 |
| `region` | 地区 |
| `sales_flag` | 是否带货 |
| `total_views_cnt` / `1d` / `7d` / `30d` | 播放量（总/1天/7天/30天增量） |
| `total_digg_cnt` / `1d` / `7d` / `30d` | 点赞量 |
| `total_comments_cnt` | 评论数 |
| `total_shares_cnt` | 分享数 |
| `total_favorites_cnt` | 收藏数 |
| `total_video_sale_cnt` | 视频销量 |
| `total_video_sale_gmv_amt` | 视频销售额 |
| `product_category_list` | 带货类目列表 |
| `width` / `height` / `ratio` | 视频尺寸 |

### curl 示例
```bash
# 泰国美妆带货视频（播放量降序）
curl -X GET 'https://open.echotik.live/api/v3/echotik/video/list?region=TH&sales_flag=1&product_category_id=601450&video_sort_field=3&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'

# 泰国投流视频
curl -X GET 'https://open.echotik.live/api/v3/echotik/video/list?region=TH&is_ad=1&video_sort_field=3&sort_type=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 37. GET /api/v3/echotik/video/trend — 视频趋势（快照）

> 通过video_id获取视频历史趋势快照，最多180天。
> 如需更完整互动趋势，可尝试实时接口（14天互动快照）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_id` | string | ✅ | 视频ID |
| `start_date` | string | ✅ | yyyy-MM-dd |
| `end_date` | string | ✅ | yyyy-MM-dd |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `dt` | 日期 |
| `video_id` | 视频ID |
| `total_views_cnt` | 播放量 |
| `total_digg_cnt` | 点赞 |
| `total_comments_cnt` | 评论 |
| `total_shares_cnt` | 分享 |
| `total_favorites_cnt` | 收藏 |
| `total_video_sale_cnt` | 销量 |
| `total_video_sale_gmv_amt` | 销售额 |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/video/trend?video_id=7560175324038728973&start_date=2026-01-01&end_date=2026-05-09&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 38. GET /api/v3/echotik/video/detail — 批量获取视频详情

> 通过video_id批量获取视频详情，最多10个，逗号分隔。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_ids` | string | ✅ | 逗号分隔，最多10个 |

### 返回字段

与 `video/list` 返回字段一致（含AI标记、投流、带货、时间序列数据）。

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/video/detail?video_ids=7560175324038728973,7590123280372190477' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 39. GET /api/v3/echotik/video/product/list — 视频带货商品列表 ⭐

> 通过视频ID获取其关联的商品列表。返回**play_addr（可下载视频）**和**hash_tag**。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_ids` | string | ✅ | 视频ID，多个用逗号分隔 |
| `page_num` | int | ✅ | 页码 |
| `page_size` | int | ✅ | 每页条数（最大10） |

### 返回字段

| 字段 | 说明 |
|------|------|
| `video_id` | 视频ID |
| `product_id` | ⭐ 关联商品ID |
| `play_addr` | ⭐⭐ **视频播放地址（可能过期）** |
| `hash_tag` | ⭐ 视频标签如 `#beauty #tiktokmademebuyit` |
| `video_desc` | 视频标题 |
| `reflow_cover` | 封面URL |
| `create_time` | 发布时间 |
| `duration` | 时长 |
| `user_id` | 达人ID |
| `region` | 地区 |
| `total_views_cnt` | 播放量 |
| `total_digg_cnt` | 点赞 |
| `total_comments_cnt` | 评论 |
| `total_shares_cnt` | 分享 |
| `total_favorites_cnt` | 收藏 |
| `total_video_sale_cnt` | 视频销量 |
| `total_video_sale_gmv_amt` | 视频销售额 |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/video/product/list?video_ids=7521783049722285367&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 40. GET /api/v3/echotik/video/ranklist — 视频榜单列表 ⭐

> 天/周/月视频榜单。1=热门榜（播放量）2=带货榜（销量）。
> 可按商品类目+AI视频过滤，含达人信息。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `date` | string | ✅ | yyyy-MM-dd |
| `region` | string | ✅ | 地区代码 |
| `rank_type` | int | ✅ | 1=天 2=周 3=月 |
| `video_rank_field` | int | ✅ | **1=热门榜**（播放量）**2=带货榜**（销量） |
| `product_category_id` | string | 否 | 商品一级类目ID |
| `created_by_ai` | string | 否 | true/false 筛AI视频 |

### 返回字段

| 字段 | 说明 |
|------|------|
| `video_id` | 视频ID |
| `video_desc` | ⭐ 视频描述 |
| `video_products` | 带货商品信息 |
| `nick_name` | 达人昵称 |
| `unique_id` | 达人TikTok ID |
| `user_id` | 达人ID |
| `avatar` | 达人头像 |
| `category` | 达人分类 |
| `region` | 地区 |
| `sales_flag` | 1=视频带货 2=直播带货 |
| `create_time` | 发布时间 |
| `duration` | 时长 |
| `total_views_cnt` | **周期内播放量增量** |
| `total_digg_cnt` | 点赞 |
| `total_comments_cnt` | 评论 |
| `total_shares_cnt` | 分享 |
| `total_favorites_cnt` | 收藏 |
| `total_video_sale_cnt` | ⭐ **周期内销量增量（带货榜）** |
| `total_video_sale_gmv_amt` | 周期内销售额 |
| `product_category_list` | 带货类目信息 |
| `created_by_ai` | 是否AI视频 |

### curl 示例
```bash
# 泰国美妆视频热榜
curl -X GET 'https://open.echotik.live/api/v3/echotik/video/ranklist?date=2026-05-09&region=TH&product_category_id=601450&rank_type=1&video_rank_field=1&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'

# 泰国美妆视频带货榜
curl -X GET 'https://open.echotik.live/api/v3/echotik/video/ranklist?date=2026-05-09&region=TH&product_category_id=601450&rank_type=1&video_rank_field=2&page_num=1&page_size=10' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 41. GET /api/v3/realtime/video/detail — 视频详情（实时接口）⚡

> 实时获取视频详情。可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_id` | string | ✅ | 视频ID |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/video/detail?video_id=7560175324038728973' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 42. GET /api/v3/realtime/video/captions — 视频文案提取（实时接口）⭐

> 通过视频ID提取视频文案/字幕，可能返回多语言脚本。
> 实时接口，可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_id` | string | ✅ | 视频ID |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/video/captions?video_id=7563511121240395022' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 43. GET /api/v3/realtime/hashtag/video/list — Hashtag关联视频列表（实时接口）⭐

> 通过hashtag_id获取该标签下的视频列表。适合追热门话题视频。
> 实时接口，可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `hashtag_id` | string | ✅ | Hashtag ID（从hash_tag字段取） |
| `region` | string | ✅ | 地区代码 |
| `offset` | string | 否 | 游标分页，has_more=1时使用cursor值 |
| `count` | string | 否 | 每页数量（默认20？） |

### 选品场景
```python
# 从热榜视频取hashtag → 搜同标签视频找更多品
video/ranklist → 视频hash_tag → hashtag/video/list → 更多同类视频 → 关联商品
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/hashtag/video/list?hashtag_id=37644733&region=TH&offset=0&count=20' \
--header 'Authorization: Basic <你的Base64>'
```

---

# 五、Hashtag & 评论

## 44. GET /api/v3/realtime/video/comments — 视频评论列表（实时接口）

> 通过video_id获取视频评论。按销量判断用户对爆品的真实反馈。
> 实时接口，可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_id` | string | ✅ | 视频ID |
| `offset` | string | 否 | 游标has_more=1时用cursor |
| `count` | string | 否 | 每页条数（默认20） |

### 用途
```python
# 选品辅助：看爆品视频下的用户评论
video_ranklist → 取top视频 → video/comments → 分析真实反馈（质量/价格/物流抱怨）
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/video/comments?video_id=7560802497552567582&offset=0&count=20' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 45. GET /api/v3/realtime/video/comments/replies — 视频评论回复列表（实时接口）

> 通过video_id + comment_id获取评论回复列表。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_id` | string | ✅ | 视频ID |
| `comment_id` | string | ✅ | 评论ID |
| `offset` | string | 否 | has_more=1时用cursor |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/video/comments/replies?video_id=7560802497552567582&comment_id=7571269780301513502&offset=0' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 46. GET /api/v3/realtime/video/download-url — 获取视频下载地址 ⭐⭐

> ⭐⭐ **核心接口！** 通过TikTok视频链接获取无下载地址（**含无水印版**）。
> 支持Web和App端分享链接。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `url` | string | ✅ | TikTok视频链接（支持 `https://vt.tiktok.com/ZShA8F5de/` 或 `https://www.tiktok.com/@user/video/xxxx`） |

### 返回字段

| 字段 | 说明 |
|:----:|:-----:|
| `video_id` | 视频ID |
| `cover_url` | 视频封面 |
| `dynamic_cover_url` | 动态封面 |
| `play_url` | 播放地址 |
| `download_url` | 下载地址 |
| **`no_watermark_download_url`** | ⭐⭐ **无水印下载地址** |
| --- | --- |
| `data.video_id` | 视频ID |

### 核心用途（内容分析）
```python
# 取爆款视频原文 → 再生成
video/list → 热门视频 → download-url → 下载无水印
                                       → cover_url + dynamic_cover → 素材分析
                                       → captions提取 → 借鉴文案
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/video/download-url?url=https://vt.tiktok.com/ZShA8F5de/' \
--header 'Authorization: Basic <你的Base64>'
```

---

# 六、直播模块

## 47. GET /api/v3/realtime/live/detail — 直播详情（实时接口）

> 通过room_id + user_id获取直播详情。**仅直播中有效**，关播后无法获取。
> 实时接口，可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `room_id` | string | ✅ | 直播间ID |
| `user_id` | string | ✅ | 达人UID |

### 选品场景
```python
# 看热门直播间在卖什么 → 截取正在爆卖的品
influencer/live/list → 取room_id → 找热销直播间
seller/live/list → 取在播房间 → 产看实时直播产品
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/live/detail?room_id=7571439020442405646&user_id=7291543591306347562' \
--header 'Authorization: Basic <你的Base64>'
```

---

# 七、搜索模块

## 48. GET /api/v3/echotik/search/items — 通用搜索接口 ⭐⭐⭐

> ⭐⭐⭐ **选品最核心接口！** 支持达人/商品/小店/视频/直播全类型搜索。
> 最多返回30条（简要数据），如需更多指标调对应的detail/list接口。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `sk` | string | ✅ | 搜索词 |
| `type` | int | ✅ | **1=达人 2=商品 3=店铺 4=视频 5=直播** |
| `region` | string | 否 | 地区过滤（不填则不限制） |
| `size` | int | ✅ | 最多30条 |
| `searchType` | int | 否 | 0=模糊 1=精准（默认模糊） |

### 返回字段（因type不同而异）

**type=1（达人）示例返回：**
| 字段 | 说明 |
|------|------|
| `unique_id` | TikTok ID |
| `nick_name` | 昵称 |
| `avatar` | 头像URL |
| `region` | 地区 |
| `category` | 达人类别 |
| `influencer_level` | 达人等级 |
| `total_followers_cnt` | 粉丝数 |
| `total_views_cnt` | 播放量 |
| `total_digg_cnt` | 点赞 |
| `total_sale_cnt` | 销量 |
| `total_sale_gmv_amt` | 销售额 |
| `total_product_cnt` | 带货商品数 |
| `total_post_video_cnt` | 发布视频数 |
| `total_live_cnt` | 直播场次 |
| `total_live_views_cnt` | 直播观看 |

### 选品核心链路
```python
# 第一步：关键词搜商品
search/items(sk="美容工具/化妆刷/眉笔", region=TH, type=2, size=30)
→ 得到热门商品简况

# 第二步：商品详情（补充完整指标）
product/detail(产品IDs) → 完整销量/GMV/佣金
product/trend → 180天趋势

# 第三步：找卖家
seller/detail → 店铺完整信息
seller/product/list → 同店更多品

# 第四步：找达人
influencer/product/list → 谁在卖同款
product/influencer/list → 交叉验证
```

### curl 示例
```bash
# 泰国搜美容工具
curl -X GET 'https://open.echotik.live/api/v3/echotik/search/items?sk=พู่กันแต่งหน้า&region=TH&type=2&size=30&searchType=0' \
--header 'Authorization: Basic <你的Base64>'

# 搜泰国美容达人
curl -X GET 'https://open.echotik.live/api/v3/echotik/search/items?sk=ความงาม&region=TH&type=1&size=30' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 49. POST /api/v3/echotik/product/image_search — 以图搜款 ⭐⭐⭐

> ⭐⭐⭐ **王炸接口！** 通过图片base64搜EchoTik商品库找同款。
> 选填product_name + region辅助过滤。最大30条。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `image_base64` | string | ✅ | 图片base64（格式：`data:image/jpeg;base64,xxxx`） |
| `product_name` | string | 否 | 商品名称辅助匹配 |
| `region` | string | 否 | 地区限制 |
| `size` | int | ✅ | 最大30条 |

### 核心选品场景
```python
# 场景1：1688找到品 → 搜TikTok同款验证市场
1688商品图片 → image_search → 看TikTok是否有人卖 → 销量/达人验证

# 场景2：竞品截图 → 找同款供应商
TikTok热门商品截图 → image_search → 找到EchoTik商品ID → 看谁在卖/价格/销量

# 场景3：素材库反向验证
我们已经上传的产品 → 图片搜一下 → 看有没有同类竞品在卖 → 价格/销量对比
```

### curl 示例
```bash
curl -X POST 'https://open.echotik.live/api/v3/echotik/product/image_search' \
--header 'Authorization: Basic <你的Base64>' \
--header 'Content-Type: application/json' \
--data-raw '{
  "image_base64": "data:image/jpeg;base64,/9j/4AAQ...",
  "product_name": "eyebrow razor",
  "region": "TH",
  "size": 10
}'
```

---

## 50. GET /api/v3/realtime/hashtag/search — Hashtag搜索（实时接口）

> 通过关键词搜索相关地区的Hashtag标签。实时接口，可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `keyword` | string | ✅ | 搜索关键词 |
| `region` | string | ✅ | 地区代码 |
| `offset` | string | 否 | has_more=1时用cursor |
| `count` | string | 否 | 每页条数（默认20） |

### 选品场景
```python
# 搜索各国美妆相关热门Hashtag
keyword="beauty"/"skincare"/"makeup" → 搜到各hashtag_id → 取video/list看热门
# 对比不同国家的美妆标签趋势
TH: keyword="ความงาม" / MY: keyword="kecantikan" / VN: keyword="làm đẹp"
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/hashtag/search?keyword=fpy&region=US&offset=0&count=20' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 51. GET /api/v3/realtime/influencer/search — 达人搜索（实时接口）

> 通过关键词实时搜索达人（offset游标分页）。
> 比 `search/items(type=1)` 更实时，支持滚动分页。
> 实时接口，可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `keyword` | string | ✅ | 搜索关键词 |
| `region` | string | ✅ | 地区代码 |
| `offset` | string | 否 | has_more=1时用cursor |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/influencer/search?keyword=beauty&region=TH&offset=0' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 52. GET /api/v3/realtime/music/search — 音乐搜索（实时接口）

> 通过关键词实时搜索TikTok视频音乐，可按标题/创作者过滤，按使用量/时长排序。
> 实时接口，可能风控（code=500重试）。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `keyword` | string | ✅ | 搜索关键词 |
| `region` | string | ✅ | 地区代码 |
| `filter_by` | string | 否 | 0=不过滤 1=音乐标题 2=创作者名称 |
| `sort_type` | string | 否 | 0=相关性 1=最多使用 2=最近 3=最短 4=最长 |
| `offset` | string | 否 | has_more=1时用cursor |

### 选品/BGM场景
```python
# 各国热歌搜索 → 选为BGM
keyword="beautiful"/"makeup"/"relax" → 搜各国热门BGM → 用于视频配乐
# 看竞品用啥BGM
下载竞品视频 → 音乐搜索验证 → 找到同款BGM做自己的视频
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/music/search?keyword=เพลงเพราะ&region=TH&filter_by=0&sort_type=1&offset=0' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 53. GET /api/v3/realtime/video/search — 视频搜索（实时接口）

> 通过关键词实时搜索视频列表（offset游标分页）。
> 发布时间过滤 + 排序（相关性/点赞量）。比 `search/items(type=4)` 更实时。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `keyword` | string | ✅ | 搜索关键词 |
| `region` | string | ✅ | 地区代码 |
| `publish_time` | string | 否 | 0=全部 1=昨日 7=7天 30=30天 90=3个月 180=6个月 |
| `sort_type` | string | 否 | 0=相关性 1=最多点赞 |
| `offset` | string | 否 | has_more=1时用cursor |

### curl 示例
```bash
# 泰国搜美容工具·最多点赞·最近7天
curl -X GET 'https://open.echotik.live/api/v3/realtime/video/search?keyword=พู่กันแต่งหน้า&region=TH&publish_time=7&sort_type=1&offset=0' \
--header 'Authorization: Basic <你的Base64>'
```

---

# 八、社交媒体分析

## 54. GET /api/v3/realtime/video/comment_keywords_insight — 评论关键词分析 ⭐

> 通过video_id获取头部评论关键词+明细数据。TK原生返回内容。

### 选品场景
```python
# 看爆品视频下的关键词云 → 快速了解用户反馈
# 正面关键词 → 确认卖点
# 负面关键词 → 发现痛点（退货/质量/尺寸）
```

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_id` | string | ✅ | 视频ID |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/video/comment_keywords_insight?video_id=7561644792577363221' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 55. GET /api/v3/realtime/video/trend_insight — 视频近14日互动趋势（实时接口）⭐

> 通过video_id获取最近14天的收藏/评论/点赞/播放数据。比离线版 `video/trend`（T+1/180天）更实时。
> TK原生返回内容。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `video_id` | string | ✅ | 视频ID |

### 与 #37 离线趋势对比
| 特性 | #37 video/trend | #55 trend_insight |
|:----|:---------------:|:-----------------:|
| 数据源 | T+1 | 实时 |
| 时间跨度 | 180天 | 14天 |
| 适用场景 | 长周期趋势分析 | 最新互动爆发检测 |

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/video/trend_insight?video_id=7561644792577363221' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 56. GET /api/v3/realtime/influencer/milestones_insight — 创作者里程碑（实时接口）

> 通过达人user_id获取创作里程碑数据（粉丝增长里程碑、销售里程碑等）。
> TK原生返回内容。

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `user_id` | string | ✅ | 达人UID |

### 选品场景
```python
# 判断达人合作价值
influencer/ranklist → 取达人user_id → milestones_insight
→ 看是否近期成长迅速(新号暴增)还是成熟稳定(老号稳增)
→ 新号暴增=合作红利期 老号稳增=稳定ROI
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/influencer/milestones_insight?user_id=6754281736047723521' \
--header 'Authorization: Basic <你的Base64>'
```

---

# 九、热门趋势模块（New）

## 57. GET /api/v3/realtime/trending/popular/hashtag/list — 热门话题Hashtag列表 ⭐⭐⭐

> ⭐⭐⭐ **新！趋势发现王炸接口！** 按行业/时间/国家/热点筛选实时热门话题。
> 返回：排名、投稿数、归属行业、趋势方向、热门创作者、播放量等。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `page` | string | 否 | 页码，默认1 |
| `limit` | string | 否 | 单页条数1~20，默认20 |
| `period` | string | 否 | **7**=近7天 **30**=近30天 **120**=近120天 |
| `region` | string | 否 | 地区代码，默认`all_regions` |
| `industry_id` | string | 否 | 一级行业ID（需从行业分类映射获取） |
| `new_to_top_100` | string | 否 | **true=仅首次进前100的热点 ⭐** false=全部 |

### 选品核心场景
```python
# 场景1：各国美妆热门话题追踪
period=7, region=TH, industry_id=美妆
→ 看到泰国最火的美妆Hashtag
→ 每个#beautytip都有排名/投稿量/播放量
→ 做视频时带上这些热门Hashtag

# 场景2：追新趋势（选品风向标）
new_to_top_100=true, period=7, region=VN
→ 看到越南刚🔥的新话题
→ 新话题意味着新需求/新品机会
→ 结合产品搜对应商品

# 场景3：多国趋势对比
region=TH/MY/VN/ID/PH 分别查 → 发现各国差异
→ 泰美丽容✓ 马美白✓ 越清新✓ 印尼护肤✓ 菲性价比✓
→ 不同国家侧重点选不同品
```

### curl 示例
```bash
# 泰国近7天热门话题
curl -X GET 'https://open.echotik.live/api/v3/realtime/trending/popular/hashtag/list?region=TH&period=7&limit=20' \
--header 'Authorization: Basic <你的Base64>'

# 美妆行业首次入前100的新话题
curl -X GET 'https://open.echotik.live/api/v3/realtime/trending/popular/hashtag/list?region=TH&period=7&new_to_top_100=true&limit=20' \
--header 'Authorization: Basic <你的Base64>'
```

---

### 热门趋势模块接口清单

## 58. GET /api/v3/realtime/trending/popular/hashtag/detail — 热门话题详情 ⭐⭐

> 按时间周期+国家+话题名称查深度详情。
> 返回：投稿数、兴趣趋势、热门视频、年龄段、相关兴趣、区域热度等。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `hashtag_name` | string | 否 | 话题名称（从list取） |
| `period` | string | 否 | **7/30/120/365/1095天** |
| `region` | string | 否 | 地区代码，默认`all_regions` |

### 返回字段

| 字段 | 说明 |
|:----:|:-----:|
| 投稿数 | 周期内投稿量 |
| 兴趣变化趋势 | ⭐ 上升/下降曲线 |
| 相关热门视频 | ⭐ 关联到的爆款视频 |
| 年龄段分布 | ⭐ 年龄/性别结构 |
| 相关兴趣 | 关联的其他话题 |
| 区域热度 | ⭐⭐ **不同国家/地区热度对比** |

### 选品场景
```python
# 判断话题是否适合我们的品
hashtag/detail(hashtag_name="#เครื่องสำอาง", region=TH, period=30)
→ 看到年龄段：18-24占比多少 → 是否目标用户
→ 区域热度：主要在曼谷还是全国 → 选品覆盖
→ 相关热门视频 → 看视频在卖啥品 → 借鉴
→ 兴趣趋势上升/下降 → 判断是否还有红利

# 对比多个话题选方向
t1 = "#beautytool" t2 = "#makeup" t3 = "#skincare"
→ 看哪个年龄段最匹配 → 选品方向定了
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/trending/popular/hashtag/detail?hashtag_name=beauty&region=TH&period=30' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 59. GET /api/v3/realtime/trending/popular/music/list — 热门音乐列表 ⭐⭐⭐

> ⭐⭐⭐ **BGM选曲神器！** 按关键词/时间/地区筛热门音乐。
> 支持**商用音乐筛选**+首次进前100新歌发现。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `search_keyword` | string | 否 | 搜索关键词，FALSE=不执行搜索 |
| `page` | string | 否 | 页码 |
| `limit` | string | 否 | 1~20条 |
| `period` | string | 否 | 7/30/120天 |
| `region` | string | 否 | 地区代码 |
| `new_to_top_100` | string | 否 | true=首次入前100新歌 |
| **`commercial_music`** | string | 否 | ⭐ **true=仅可商用音乐** |

### 返回字段
> 排名、近期趋势、音乐信息等

### BGM选曲场景
```python
# 核心场景：找各国可商用热门BGM
commercial_music=true, period=30, region=TH
→ 泰国可商用热歌 → 下载 → 用作我们视频BGM

# 新歌发现
new_to_top_100=true, period=7, region=VN
→ 越南新爆🔥的BGM → 抢先使用 = 流量红利

# BGM搜索
search_keyword="makeup"/"beautiful"/"relax", commercial_music=true
→ 搜到美妆相关可商用BGM → 选最合适的
```

### curl 示例
```bash
# 泰国可商用热门音乐
curl -X GET 'https://open.echotik.live/api/v3/realtime/trending/popular/music/list?region=TH&period=30&limit=20&commercial_music=true' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 60. GET /api/v3/realtime/trending/popular/music/detail — 热门音乐详情 ⭐⭐

> 根据clip_id查音乐深度详情：受众画像、趋势曲线、商用标记等。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `clip_id` | string | 否 | 音乐clip_id（从music/list取） |
| `period` | string | 否 | 7/30/120天 |
| `region` | string | 否 | 地区代码 |

### 返回字段

| 字段 | 说明 |
|:----:|:-----:|
| `sound.title` | 音乐名称 |
| `sound.author` | 创作者 |
| `sound.cover` | 封面图 |
| `sound.duration` | 时长（秒） |
| `sound.link` | TikTok音乐链接 |
| `sound.music_url` | ⭐ 音乐下载地址（可能为空） |
| **`sound.if_cml`** | ⭐ **true=可商用** |
| `sound.audience_ages` | ⭐⭐ **年龄段分布** |
| `sound.audience_countries` | ⭐⭐ **受众国家分布+热度分数** |
| `sound.audience_interests` | ⭐⭐ **受众兴趣画像** |
| `sound.trend` | ⭐ 时间序列人气曲线 |
| `sound.rank` / `rank_diff` | 当前排名+变化 |
| `sound.longevity` | 持久度（爆红/长尾） |
| `sound.related_items` | 相关音乐推荐 |

### BGM选曲场景
```python
# 选BGM标准
music/detail(clip_id=xxx)
→ check if_cml=true（可商用）
→ 看audience_ages 是否18-34（目标用户）
→ 看audience_countries 是否TH/MY/VN（我们的市场）
→ 看trend曲线 是否仍在上升
→ 看duration 8-15s（适合我们短视频）
→ 下载music_url → 剪辑BGM

# 竞品BGM分析
video/download-url → 看视频音轨 → 搜相似音乐
music/list(search_keyword="相似风格") → music/detail → 对比数据
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/trending/popular/music/detail?clip_id=6703723351497508865&region=TH&period=30' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 61. GET /api/v3/realtime/trending/popular/video/list — 热门视频列表 ⭐⭐⭐

> ⭐⭐⭐ **趋势发现！** 按国家/时间/互动排序筛选热门TikTok视频。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `region` | string | 否 | 地区代码 |
| `period` | string | 否 | 7=近7天 30=近30天 |
| `order_by` | string | 否 | `vv`=热点(播放) `like`=点赞 `comment`=评论 `repost`=转发 |
| `page` | string | 否 | 页码 |
| `limit` | string | 否 | 1~20条 |

### 返回字段

| 字段 | 说明 |
|:----:|:-----:|
| `videos[].id` | 视频ID |
| `videos[].title` | ⭐ 视频标题/描述 |
| `videos[].cover` | 封面图 |
| `videos[].duration` | 时长(秒) |
| `videos[].region` | 国家名称 |
| `videos[].country_code` | 国家代码 |
| `videos[].item_url` | ⭐ 视频链接 |
| `pagination.has_more` | 是否还有更多 |
| `pagination.total_count` | 总数 |

### 选品场景
```python
# 每日各国热门视频扫榜
for region in [TH, MY, VN, ID, PH]:
  热门视频 = trending/video/list(region, period=7, order_by=vv, limit=20)
  for v in 热门视频:
    video_id = v.id
    # 看这个视频在卖什么品
    video/product/list(video_ids=video_id) → 关联商品
    # 看视频文案
    realtime/video/captions(video_id=video_id) → 提取脚本
    # 看达人
    记住user_name → influencer/detail → 评估是否合作
```

### curl 示例
```bash
# 泰国近7天热门视频（按播放量）
curl -X GET 'https://open.echotik.live/api/v3/realtime/trending/popular/video/list?region=TH&period=7&order_by=vv&limit=20' \
--header 'Authorization: Basic <你的Base64>'
```

---

# 十、数据洞察模块（New）

## 62. GET /api/v3/realtime/insights/keyword — 热门关键词洞察 ⭐⭐⭐

> ⭐⭐⭐ **选品+文案双用！** 按行业/地区/投放目标/关键词类型筛选热门关键词。
> 返回：排名/热度/变化/CTR/CVR/CPA/展示量/6s播放率/互动数。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `search_keyword` | string | 否 | 搜索关键词，FALSE=不搜索 |
| `region` | string | 否 | 地区，`nothing`=不限 |
| `industry` | string | 否 | 行业ID（从行业分类映射取） |
| `period` | string | 否 | 7/30/120天 |
| `objective` | string | 否 | **投放目标：1=访问量 2=应用安装 3=转化量 4=视频播放 5=覆盖 8=潜在客户 14=商品销量** |
| `keyword_type` | string | 否 | **关键词类型：1=卖点 2=痛点 3=目标用户 4=行动号召 5=其他 6=产品** |
| `page` / `limit` | string | 否 | 分页 |

### 返回字段

| 字段 | 说明 |
|:----:|:-----:|
| 排名 | 🔥 关键词排名 |
| 热度 | 热度分数 |
| 热度变化 | 上升/下降幅度 |
| CTR | ⭐ 点击率 |
| CVR | ⭐⭐ **转化率（选品关键指标！）** |
| CPA | 单次转化成本 |
| 展示量 | 曝光量 |
| 6秒视频播放率 | ⭐ 视频前6秒留存 |
| 互动数 | 点赞/评论/分享 |

### 选品+文案核心场景
```python
# 场景1：选品验证（按投放目标）
keyword_type=6(产品), objective=14(商品销量), region=TH, period=30
→ 泰国哪些产品关键词有高CVR → 说明适合带货 → 选品方向

# 场景2：卖点挖掘（写文案用）
keyword_type=1(卖点), industry=美妆ID, region=TH, period=7
→ 哪些卖点词热 → 加到视频文案/标题/hashtag
→ 如：#持久不脱妆 #自然妆感 #防水

# 场景3：痛点营销（戳中用户）
keyword_type=2(痛点), industry=美妆ID, region=MY
→ 马来西亚用户最关心的痛点
→ 视频开头直接戳痛点 → 产品做解决方案

# 场景4：行动号召测试（CTA优化）
keyword_type=4(行动号召), region=PH, period=30
→ 菲律宾哪些CTA词点击率高
→ "try now" × "shop now" × "learn more" 选最优

# 场景5：目标用户定位（投放人群）
keyword_type=3(目标用户), region=VN
→ 越南用户搜什么关键词找产品
→ 标题/描述精准命中
```

### curl 示例
```bash
# 泰国美妆卖点词（近7天）
curl -X GET 'https://open.echotik.live/api/v3/realtime/insights/keyword?keyword_type=1&region=TH&period=7&limit=20' \
--header 'Authorization: Basic <你的Base64>'

# 泰国商品销量转化词
curl -X GET 'https://open.echotik.live/api/v3/realtime/insights/keyword?keyword_type=6&objective=14&region=TH&period=30&limit=20' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 63. GET /api/v3/realtime/insights/top/product/category/list — 热门商品类目洞察 ⭐⭐⭐

> ⭐⭐⭐ **选品核心！** 按关键词/类目/国家/时间筛爆品类目。
> 返回：热度/变化/CTR/CVR/CPA/互动/6s完播率。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `search_keyword` | string | 否 | 搜索关键词，FALSE=不搜索 |
| `region` | string | 否 | 地区，`all_regions`=全部 |
| `ecom_category_id` | string | 否 | ⭐ **三级类目ID过滤** |
| `time_scope` | string | 否 | 1=近1天 7=近7天 30=近30天 或`YYYY-MM`月数据（最多4个月前） |
| `page` / `limit` | string | 否 | 分页1~20 |

### 返回字段
> 类目热搜热度、热度变化、CTR(点击率)、CVR(转化率)、CPA(转化成本)、互动数、6秒完播率

### 选品核心场景
```python
# 场景1：各国热卖品类对比
for region in [TH, MY, VN, ID, PH]:
  data = insights/category(time_scope=30, region=region)
  → 看各国什么品类热 + CVR高
  → 泰国：彩妆热CVR高 → 彩妆优先
  → 越南：护肤热CVR高 → 护肤优先
  → 差异化选品策略

# 场景2：类目深度验证
ecom_category_id = 美妆工具三级ID
→ 看这个类目在泰国CTR/CVR/完播率多少
→ CVR>3%? 可做 → CVR<1%? 谨慎投入

# 场景3：结合关键词
search_keyword="化妆刷", time_scope=30, region=TH
→ 化妆刷类目在泰国的CTR/CVR
→ 验证单品选择
```

### curl 示例
```bash
# 泰国近30天热卖品类
curl -X GET 'https://open.echotik.live/api/v3/realtime/insights/top/product/category/list?time_scope=30&region=TH&limit=20' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 64. GET /api/v3/realtime/insights/top/product/category/detail — 商品类目洞察详情 ⭐⭐

> 三级类目深度洞察：受众画像、类目层级、相关话题、热门视频。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `id` | string | ✅ | **三级类目ID** |
| `time_scope` | string | 否 | 1/7/30天 或 YYYY-MM |
| `region` | string | 否 | 地区，默认`all_regions` |

### 返回字段

| 字段 | 说明 |
|:----:|:-----:|
| `info.audience_ages` | ⭐⭐ **年龄段分布**（18/25/35/45/55各占比） |
| `info.audience_interests` | 受众兴趣画像 |
| `info.first_ecom_category` | ⭐ **一级类目**（如：Beauty & Personal Care） |
| `info.second_ecom_category` | **二级类目**（如：Makeup & Perfume） |
| `info.third_ecom_category` | ⭐ **三级类目**（如：Perfume） |
| `info.hashtags` | ⭐ **相关热门HashTag** |
| `info.posts` | ⭐⭐ **该类目下的热门视频ID列表**（带商品） |

### 类目层级示例（美妆）
```
L1: Beauty & Personal Care (601450)
  └─ L2: Makeup & Perfume (848648)
       └─ L3: Perfume (601583) ← 三级ID传入detail
```

### 选品场景
```python
# 三步验证法
step1: category/list → 看哪些品类CVR高
step2: category/detail(id=三级ID) → 看受众年龄/话题/热卖视频
step3: check 受众25-34占比高 → OK → 选品
       check related hashtags → 写文案时加上
       check 热门视频 → 下载分析/看卖点
```

### curl 示例
```bash
# 看"Perfume"类目在泰国的详情
curl -X GET 'https://open.echotik.live/api/v3/realtime/insights/top/product/category/detail?id=601583&region=TH&time_scope=30' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 65. GET /api/v3/realtime/insights/top/ads/list — 热门广告洞察 ⭐⭐⭐

> ⭐⭐⭐ **竞品分析核武！** 按行业/国家/投放目标/广告语言/格式筛选热门广告。
> 排序：推荐/曝光/CTR/2s完播率/6s完播率/CVR/点赞

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `search_keyword` | string | 否 | 搜索关键词 |
| `region` | string | 否 | 地区 |
| `industry` | string | 否 | 行业ID |
| `period` | string | 否 | 7/30/120天 |
| `objective` | string | 否 | 投放目标：1=访问量 2=安装 3=转化 **14=商品销量** |
| `ad_language` | string | 否 | 广告语言：`th`泰 `vi`越 `id`印尼 `ms`马来 `en`英 |
| `ad_format` | string | 否 | 1=**Spark Ads** 2=Non-Spark Ads |
| `order_by` | string | 否 | `for_you`推荐 `impression`曝光 `ctr`点击率 `play_6s_rate`6s完播 **`cvr`转化率** `like`点赞 |
| `like` | string | 否 | 点赞分位：1=Top1-20% 2=21-40% 3=41-60% |
| `page` / `limit` | string | 否 | 分页 |

### 返回字段
> 品牌、花费、CTR、互动量、关联视频数据等

### 竞品分析场景
```python
# 场景1：泰国美妆赛道谁在投广告
industry=美妆ID, region=TH, period=30, objective=14(商品销量)
→ 看哪些品牌在投 → 预估花费 → 看广告CTR/CVR
→ 好广告(高CTR高CVR) → 下载分析素材 → 借鉴
→ 不好广告 → 避开

# 场景2：Spark Ads vs Non-Spark分析
ad_format=1(Spark Ads), order_by=cvr, ad_language=th
→ 泰国Spark Ads高转化广告 → 借鉴达人素材风格

# 场景3：泰语广告素材参考
ad_language=th, order_by=play_6s_rate
→ 哪些前6秒留存率高 → 学习开头话术/画面
```

### curl 示例
```bash
# 泰国美妆广告（按转化率排序）
curl -X GET 'https://open.echotik.live/api/v3/realtime/insights/top/ads/list?region=TH&objective=14&order_by=cvr&period=30&limit=20' \
--header 'Authorization: Basic <你的Base64>'

# 泰语Spark Ads（按6s完播率排序）
curl -X GET 'https://open.echotik.live/api/v3/realtime/insights/top/ads/list?ad_language=th&ad_format=1&order_by=play_6s_rate&period=30&limit=20' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 66. GET /api/v3/realtime/insights/top/ads/detail — 广告洞察详情 ⭐⭐⭐

> ⭐⭐⭐ **竞品拆解！** 广告素材完整数据：文案、视频、落地页、投放数据。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `material_id` | string | ✅ | 广告素材ID（from ads/list） |

### 返回字段

| 字段 | 说明 |
|:----:|:-----:|
| `ad_title` | ⭐⭐ **广告文案/话术** |
| `brand_name` | 品牌名 |
| `id` (material_id) | 广告ID |
| `cost` | 广告花费 |
| `ctr` | ⭐ **点击率** |
| `like` / `comment` / `share` | 互动数 |
| `objective_key` / `objectives` | 投放目标（如视频播放） |
| `country_code` | 投放国家 |
| `industry_key` | 行业 |
| `landing_page` | ⭐⭐ **落地页链接** |
| `source` / `source_key` | 广告来源 |
| `keyword_list` | 关键词列表 |
| `video_info.video_url` | ⭐⭐ **广告视频720p地址** |
| `video_info.cover` | 视频封面 |
| `video_info.duration` | 时长 |
| `video_info.vid` | 视频ID |
| `video_info.voice_over` | 是否配音 |

### 竞品拆解流程
```python
# 完整竞品分析
ads/list(region=TH, industry=美妆, order_by=cvr, period=30)
→ 取高CVR广告的material_id

for each ad:
  ads/detail(material_id=xxx)
  → ad_title: 记录文案/话术结构
  → video_url: 下载720p广告视频
  → landing_page: 看产品页面/定价/促销
  → ctr: 看点击率
  → cost: 估算预算
  → voice_over: 有没有配音

# 输出：竞品素材库
# - 文案模板库（开头/卖点/CTA结构）
# - 视频素材库（画面风格/节奏）
# - 定价策略（折扣/包邮/赠品）
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/realtime/insights/top/ads/detail?material_id=7599659133885874193' \
--header 'Authorization: Basic <你的Base64>'
```

---

## 67. GET /api/v3/echotik/batch/cover/download — 封面图片批量下载

> 将EchoTik的封面图转换为可访问临时地址（24h有效）。
> **不消耗接口调用次数！**
> 仅支持 `echosell-images.tos-ap-southeast-1.volces.com` 域名。
> 如未下载则1-3天异步完成。

### 请求参数

| 参数 | 类型 | 必填 | 说明 |
|------|:----:|:----:|------|
| `cover_urls` | string | ✅ | 最多10个封面URL，逗号分隔 |

### 返回

```json
{
  "code": 0,
  "message": "success",
  "data": {
    "来源URL1": "临时可访问URL1",
    "来源URL2": "临时可访问URL2"
  }
}
```

### curl 示例
```bash
curl -X GET 'https://open.echotik.live/api/v3/echotik/batch/cover/download?cover_urls=https://echosell-images.tos-ap-southeast-1.volces.com/user-avatar/xxx.webp,https://echosell-images.tos-ap-southeast-1.volces.com/video-cover/xxx.jpg' \
--header 'Authorization: Basic <你的Base64>'
```
