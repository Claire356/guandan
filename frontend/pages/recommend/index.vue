<template>
  <view class="page-shell safe-bottom">
    <view class="surface-card recommend-card">
      <view class="ai-orb">AI</view>
      <u-tag :text="strategyName" type="success" plain />
      <text class="recommend-title">本轮建议</text>
      <text class="muted">基于桌面牌型、剩余手牌和你的训练策略计算</text>
      <view class="cards"><PlayingCard v-for="(card, index) in displayCards" :key="index" :card="card" disabled /></view>
      <view class="type-row"><text>推荐牌型</text><text>{{ typeName }}</text></view>
      <view class="type-row"><text>期望收益</text><text>{{ expectedValue }}</text></view>
    </view>

    <text class="section-title">为什么这样出</text>
    <view class="surface-card reasons">
      <view v-for="(reason, index) in reasons" :key="reason"><text class="index">{{ index + 1 }}</text><text>{{ reason }}</text></view>
    </view>
    <u-button type="primary" color="#0b5d3b" shape="circle" text="采用建议" @click="accept" />
    <u-button class="secondary" plain color="#0b5d3b" shape="circle" text="返回牌桌" @click="back" />
  </view>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useGameStore } from '@/store/game'
import PlayingCard from '@/components/PlayingCard.vue'
const store = useGameStore()
onMounted(() => store.recommend())
const strategyName = computed(() => ({ aggressive: '激进策略', balanced: '均衡策略', conservative: '保守策略' }[store.strategy]))
const displayCards = computed(() => store.recommendation.length ? store.recommendation : ['♠8'])
const typeName = computed(() => ({ single: '单张', pair: '对子', bomb: '炸弹', straight: '顺子' }[store.recommendationType?.type] || '计算中'))
const reasons = computed(() => (store.recommendationReason || '正在分析当前牌局').split('；').filter(Boolean))
const expectedValue = computed(() => `${Math.round((store.recommendationExpectedValue || 0) * 100)}%`)
const back = () => uni.navigateBack()
const accept = () => {
  store.selectedIndices = [...store.recommendationIndices]
  uni.navigateBack()
  uni.showToast({ title: store.selectedIndices.length ? '已选中推荐牌' : '当前建议过牌', icon: 'none' })
}
</script>

<style scoped lang="scss">
.recommend-card { display: flex; flex-direction: column; align-items: center; text-align: center; }.ai-orb { width: 92rpx; height: 92rpx; margin-bottom: 18rpx; display: flex; align-items: center; justify-content: center; border-radius: 50%; color: #fff; background: linear-gradient(135deg,#0b5d3b,#2a9663); font-weight: 900; }
.recommend-title { margin: 22rpx 0 8rpx; font-size: 40rpx; font-weight: 800; }.cards { display: flex; gap: 10rpx; margin: 34rpx 0; }.type-row { width: 100%; padding-top: 22rpx; display: flex; justify-content: space-between; border-top: 1rpx solid #e3ece6; font-weight: 700; }
.reasons { margin-bottom: 28rpx; }.reasons view { display: flex; align-items: center; padding: 18rpx 0; }.index { width: 46rpx; height: 46rpx; margin-right: 18rpx; display: flex; align-items:center; justify-content:center; border-radius:50%; color:#16784b; background:#e5f4eb; font-weight:800; }.secondary { margin-top: 16rpx; }
</style>
