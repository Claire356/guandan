<template>
  <view class="page-shell safe-bottom">
    <view class="surface-card intro">
      <u-tag text="训练配置" type="success" plain />
      <text class="intro__title">选择你的陪练风格</text>
      <text class="muted">不同风格会改变出牌推荐和牌局节奏。</text>
    </view>

    <view class="strategy-list">
      <view v-for="item in strategies" :key="item.value" class="surface-card strategy" :class="{ active: selected === item.value }" @click="selected = item.value">
        <view class="strategy__mark">{{ item.mark }}</view>
        <view class="strategy__content"><text class="strategy__title">{{ item.title }}</text><text class="muted">{{ item.desc }}</text></view>
        <u-icon :name="selected === item.value ? 'checkmark-circle-fill' : 'circle'" :color="selected === item.value ? '#16784b' : '#aab7af'" size="24" />
      </view>
    </view>

    <view class="surface-card rule-card">
      <text class="section-title compact">本次训练</text>
      <u-cell title="模式" value="四人标准局" :border="false" />
      <u-cell title="队友" value="AI-1" :border="false" />
      <u-cell title="记录" value="行为与人格评分" :border="false" />
    </view>
    <u-button :loading="store.loading" type="primary" color="#0b5d3b" shape="circle" size="large" text="进入牌桌" @click="start" />
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { useGameStore } from '@/store/game'
const store = useGameStore()
const selected = ref('balanced')
const strategies = [
  { value: 'aggressive', mark: '攻', title: '激进型', desc: '积极抢权，主动使用炸弹' },
  { value: 'balanced', mark: '衡', title: '均衡型', desc: '收益优先，适度保留资源' },
  { value: 'conservative', mark: '守', title: '保守型', desc: '帮助队友，重视残局控制' }
]
const start = async () => {
  await store.beginTraining(selected.value)
  uni.navigateTo({ url: '/pages/game/index' })
}
</script>

<style scoped lang="scss">
.intro { margin-bottom: 22rpx; }.intro__title { display: block; margin: 22rpx 0 10rpx; font-size: 38rpx; font-weight: 800; }
.strategy-list { display: flex; flex-direction: column; gap: 18rpx; margin-bottom: 24rpx; }
.strategy { display: flex; align-items: center; border: 2rpx solid transparent; }.strategy.active { border-color: #2a9663; background: #f4fbf7; }
.strategy__mark { width: 72rpx; height: 72rpx; display: flex; align-items: center; justify-content: center; border-radius: 20rpx; color: #fff; background: #16784b; font-weight: 800; }
.strategy__content { flex: 1; margin-left: 22rpx; display: flex; flex-direction: column; }.strategy__title { margin-bottom: 8rpx; font-weight: 700; }
.rule-card { margin-bottom: 26rpx; }.compact { display: block; margin: 0 0 10rpx; }
@media screen and (min-width: 768px) {
  .strategy-list { display: grid; grid-template-columns: repeat(3, 1fr); }
  .strategy { min-height: 150px; align-items: flex-start; }
}
</style>
