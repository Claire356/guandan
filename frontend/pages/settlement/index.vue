<template>
  <view class="page-shell safe-bottom">
    <view class="result-hero">
      <text class="crown">♛</text><text class="result-title">本局完成</text><text class="result-sub">{{ result.title }} · 第 {{ result.rank }} 名</text>
      <view class="score">{{ result.score }}<text>分</text></view>
    </view>
    <view class="stats">
      <view class="surface-card"><text>炸弹使用</text><text class="stat-num">{{ result.bombCount }}</text></view>
      <view class="surface-card"><text>PASS次数</text><text class="stat-num">{{ result.passCount }}</text></view>
      <view class="surface-card"><text>训练评价</text><text class="stat-num small">优秀</text></view>
    </view>
    <view class="surface-card comment"><text class="section-title compact">本局亮点</text><text class="muted">中盘成功建立牌权，并通过连续牌型快速减少手牌。行为分析和人格报告已生成。</text></view>
    <u-button type="primary" color="#0b5d3b" shape="circle" size="large" text="查看AI报告" @click="goReport" />
    <u-button class="secondary" plain color="#0b5d3b" shape="circle" text="再练一局" @click="restart" />
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { useGameStore } from '@/store/game'
const store = useGameStore()
const result = computed(() => store.result || { rank: 1, score: 86, title: '头游', bombCount: 2, passCount: 5 })
const goReport = () => uni.navigateTo({ url: '/pages/report/index' })
const restart = () => uni.redirectTo({ url: '/pages/training/index' })
</script>

<style scoped lang="scss">
.result-hero { padding: 46rpx; text-align:center; border-radius:30rpx; color:#fff; background:linear-gradient(145deg,#0b5d3b,#178456); }.crown { display:block; color:#e7ca72; font-size:70rpx; }.result-title { display:block; margin-top:8rpx; font-size:42rpx; font-weight:800; }.result-sub { display:block; margin-top:8rpx; color:rgba(255,255,255,.72); }.score { margin-top:24rpx; font-size:80rpx; font-weight:900; }.score text { margin-left:6rpx; font-size:25rpx; }
.stats { display:grid; grid-template-columns:repeat(3,1fr); gap:14rpx; margin:22rpx 0; }.stats .surface-card { padding:22rpx 10rpx; text-align:center; font-size:22rpx; color:#718079; }.stat-num { display:block; margin-top:10rpx; font-size:38rpx; color:#18372a; font-weight:800; }.stat-num.small { font-size:28rpx; color:#16784b; }.comment { margin-bottom:26rpx; line-height:1.8; }.compact { display:block; margin:0 0 14rpx; }.secondary { margin-top:16rpx; }
</style>
