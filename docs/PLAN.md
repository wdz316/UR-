# UR找房 · 东京MVP 项目计划书

> 目录：`D:\UR找房` ｜ 状态：demo 已落地 ｜ 纪律：每次改动 1 commit + 测试全过（见 `C:\Users\Lenovo\RULES.md`）

## 1. 背景
UR官网（ur-net.go.jp/chintai）找房费劲：都道县→エリア/沿线/地图→团地一览→逐个点进详情，空室还是 JS 异步`ロード中`加载，没法一眼比全量。本项目把东京空室聚合到**一个页面，列表+地图直接筛**。

## 2. MVP 范围（东京先行）
- 区域：仅东京都（跑通后再扩关东/全国，全国约70万户一次全爬不现实）
- 功能：① 列表筛选（家賃上限/間取り/面積下限/关键字）② 地图筛选（Leaflet 打点，与列表联动）③ 跳回官网详情/申込
- 非目标：在线签约、账号体系、实时推送（ assertions 后期再做）

## 3. 方案
```
官网团地一览 → Playwright 逐团地抓空室表 → data/ur_tokyo.json(每天1次)
                                                    ↓
demo/index.html(零构建, Leaflet CDN) ← 列表+地图联动过滤
```
- 为什么 Playwright：空室表是 JS 渲染，`requests` 拿不到；详情页形如 `/chintai/kanto/tokyo/...html`
- 礼貌爬取：间隔 2-5s/页、失败重试3次、只存公开募集字段、页脚注来源+更新时间

## 4. 数据模型（v0）
`danchi, address, ward, rent, ky MELFeeki, madori, area, floor, lat, lng, url, updated`
示例见 `data/tokyo_sample.json`（6 条手造东京样本，正式数据由爬虫替换同结构文件）。

## 5. 里程碑
- M0 demo（今天）：静态 `demo/index.html` + 样本 JSON + pytest，本地双击可筛 —— 已完成
- M1 爬虫：Playwright 抓东京 100+团地 → 生成同结构 JSON，diff 入库
- M2 定时+部署：GitHub Actions 每日更新 + Pages 托管

## 6. 验证
`python -m pytest` 全过；浏览器打开 `demo/index.html`：改家賃/間取り/关键字，列表与地图点位同步变化即算通过。

## 7. 风险
官网改版导致选择器失效 → 爬虫加选择器断言，失败即报警不覆盖旧数据；坐标缺失 → 用住址 geocode 补，补不上先只进列表不进地图。
