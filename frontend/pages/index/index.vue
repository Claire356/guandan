<template>
  <view class="page-shell dashboard safe-bottom">
    <view class="dashboard-head">
      <view>
        <text class="eyebrow">AI DASHBOARD</text>
        <text class="dashboard-title">AI掼蛋教练</text>
      </view>
      <view class="coach-avatar">AI</view>
    </view>

    <view class="today-card">
      <view class="row-between">
        <view><text class="today-label">今日训练</text><text class="stars">★★★★★</text></view>
        <view class="streak"><text>7</text><text>连续训练</text></view>
      </view>
      <text class="today-title">保持牌感，完成今天的训练</text>
      <text class="today-desc">AI将记录你的关键选择，并在牌局结束后生成专属复盘。</text>
      <u-button class="start-button" type="primary" color="#e0bc5e" shape="circle" size="large" text="开始训练" @click="goTraining" />
    </view>

    <view class="quick-links">
      <view v-for="item in quickLinks" :key="item.title" class="surface-card quick-link" @click="item.action">
        <view class="quick-icon">{{ item.icon }}</view>
        <text>{{ item.title }}</text>
        <u-icon name="arrow-right" color="#8a9991" size="16" />
      </view>
    </view>

    <view class="section-heading row-between">
      <view><text class="section-heading__title">最近20局</text><text class="muted">稳定进步中</text></view>
      <u-tag text="+8%" type="success" plain size="mini" />
    </view>

    <view class="overview-grid">
      <view class="surface-card win-card">
        <text class="metric-label">胜率</text>
        <text class="win-rate">67<text>%</text></text>
        <view class="win-ring"><view class="win-ring__inner">20局</view></view>
      </view>

      <view class="surface-card personality-card">
        <view class="row-between"><text class="metric-label">人格画像</text><text class="personality-name">团队协作型</text></view>
        <view class="score-row"><text>攻击性</text><view class="score-track"><view style="width:73%"></view></view><text>73</text></view>
        <view class="score-row"><text>团队协作</text><view class="score-track"><view style="width:81%"></view></view><text>81</text></view>
      </view>
    </view>

    <view class="surface-card growth-card" @click="goReport">
      <view class="row-between">
        <view><text class="metric-label">成长曲线</text><text class="growth-title">近期决策质量</text></view>
        <text class="growth-value">+12</text>
      </view>
      <view class="chart" aria-label="最近七次训练成长曲线">
        <view v-for="(height,index) in growth" :key="index" class="chart-bar" :style="{ height: `${height}%` }"></view>
      </view>
      <view class="chart-axis"><text>较早</text><text>最近</text></view>
    </view>

    <view class="ai-advice">
      <view class="advice-icon">AI</view>
      <view class="advice-copy"><text class="advice-label">AI建议</text><text class="advice-title">今天建议练残局</text><text class="advice-desc">重点训练剩余8张以内的牌序规划与主动权控制。</text></view>
      <u-icon name="arrow-right" color="#d9bd72" size="20" />
    </view>
  </view>
</template>

<script setup>
const goTraining = () => uni.navigateTo({ url: '/pages/training/index' })
const goHistory = () => uni.navigateTo({ url: '/pages/history/index' })
const goReport = () => uni.navigateTo({ url: '/pages/report/index' })
const growth = [38, 48, 43, 61, 68, 73, 86]
const quickLinks = [
  { icon: '▤', title: '历史报告', action: goHistory },
  { icon: '◎', title: '人格画像', action: goReport },
  { icon: '↗', title: '成长曲线', action: goReport }
]
</script>

<style scoped lang="scss">
.dashboard-head { margin: 8rpx 0 28rpx; display:flex; align-items:center; justify-content:space-between; }.dashboard-head>view:first-child { display:flex; flex-direction:column; }.eyebrow { color:#2a9663; font-size:21rpx; font-weight:800; letter-spacing:3rpx; }.dashboard-title { margin-top:8rpx; font-size:46rpx; font-weight:900; color:#17382a; }.coach-avatar { width:78rpx; height:78rpx; display:flex; align-items:center; justify-content:center; border:2rpx solid rgba(216,182,91,.5); border-radius:24rpx; color:#f4d984; background:#0b5d3b; font-weight:900; }
.today-card { padding:36rpx; border-radius:30rpx; color:#fff; background:linear-gradient(145deg,#08482f,#11784e); box-shadow:0 18rpx 44rpx rgba(8,72,47,.22); }.today-label,.stars,.today-title,.today-desc { display:block; }.today-label { font-size:24rpx; color:rgba(255,255,255,.7); }.stars { margin-top:8rpx; color:#e7c96f; font-size:28rpx; letter-spacing:5rpx; }.streak { width:98rpx; height:98rpx; display:flex; flex-direction:column; align-items:center; justify-content:center; border:1rpx solid rgba(255,255,255,.2); border-radius:50%; background:rgba(255,255,255,.08); font-size:18rpx; color:rgba(255,255,255,.7); }.streak text:first-child { color:#fff; font-size:34rpx; font-weight:900; }.today-title { margin-top:28rpx; font-size:35rpx; font-weight:800; }.today-desc { margin-top:10rpx; font-size:24rpx; line-height:1.65; color:rgba(255,255,255,.72); }.start-button { margin-top:28rpx; }
.quick-links { display:grid; grid-template-columns:repeat(3,1fr); gap:14rpx; margin:22rpx 0 32rpx; }.quick-link { min-height:142rpx; padding:20rpx 14rpx; display:flex; flex-direction:column; align-items:flex-start; justify-content:space-between; font-size:24rpx; font-weight:700; }.quick-icon { width:48rpx; height:48rpx; display:flex; align-items:center; justify-content:center; border-radius:14rpx; color:#16784b; background:#e7f3eb; font-weight:900; }
.section-heading { margin-bottom:18rpx; }.section-heading>view { display:flex; flex-direction:column; gap:5rpx; }.section-heading__title { font-size:34rpx; font-weight:900; }.overview-grid { display:grid; grid-template-columns:.85fr 1.4fr; gap:16rpx; }.metric-label { color:#73847b; font-size:23rpx; }.win-card { position:relative; min-height:230rpx; overflow:hidden; }.win-rate { display:block; margin-top:18rpx; color:#17382a; font-size:62rpx; font-weight:900; }.win-rate text { font-size:25rpx; }.win-ring { position:absolute; right:-32rpx; bottom:-38rpx; width:138rpx; height:138rpx; display:flex; align-items:center; justify-content:center; border:18rpx solid #dcece2; border-top-color:#2a9663; border-right-color:#2a9663; border-radius:50%; transform:rotate(20deg); }.win-ring__inner { transform:rotate(-20deg); color:#6f8077; font-size:21rpx; }
.personality-card { min-height:230rpx; }.personality-name { color:#16784b; font-size:22rpx; font-weight:700; }.score-row { display:grid; grid-template-columns:100rpx 1fr 42rpx; gap:12rpx; align-items:center; margin-top:30rpx; font-size:22rpx; }.score-row>text:last-child { text-align:right; font-weight:800; }.score-track { height:12rpx; overflow:hidden; border-radius:99rpx; background:#e4ece7; }.score-track view { height:100%; border-radius:99rpx; background:linear-gradient(90deg,#1c8457,#d6b75f); }
.growth-card { margin-top:18rpx; }.growth-title { display:block; margin-top:6rpx; font-weight:800; }.growth-value { color:#2a9663; font-size:34rpx; font-weight:900; }.chart { height:150rpx; margin-top:28rpx; display:flex; align-items:flex-end; gap:12rpx; border-bottom:1rpx solid #e3ebe6; }.chart-bar { flex:1; min-height:18%; border-radius:8rpx 8rpx 0 0; background:linear-gradient(180deg,#2a9663,#bcdac7); }.chart-axis { display:flex; justify-content:space-between; margin-top:8rpx; color:#9ba7a0; font-size:19rpx; }
.ai-advice { margin-top:18rpx; padding:28rpx; display:flex; align-items:center; gap:20rpx; border-radius:24rpx; color:#fff; background:#173c2c; }.advice-icon { width:66rpx; height:66rpx; display:flex; align-items:center; justify-content:center; border-radius:18rpx; color:#173c2c; background:#e0c36f; font-weight:900; }.advice-copy { flex:1; display:flex; flex-direction:column; }.advice-label { color:#d8bd72; font-size:20rpx; }.advice-title { margin-top:4rpx; font-size:29rpx; font-weight:800; }.advice-desc { margin-top:7rpx; color:rgba(255,255,255,.65); font-size:21rpx; line-height:1.55; }
@media screen and (min-width:768px) { .dashboard { max-width:1050px; }.today-card { padding:44px; }.quick-link { min-height:150px; }.overview-grid { grid-template-columns:1fr 2fr; }.win-card,.personality-card { min-height:260px; }.chart { height:190px; } }
</style>
