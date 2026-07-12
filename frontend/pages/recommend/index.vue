<template>
  <view class="page-shell safe-bottom">
    <view class="surface-card recommend-card">
      <view class="ai-orb">AI</view>
      <u-tag :text="strategyName" type="success" plain />
      <text class="recommend-title">AI建议</text>
      <text class="muted">基于桌面牌型、剩余手牌和你的训练策略计算</text>
      <text class="recommend-label">推荐：</text>
      <view class="cards"><PlayingCard v-for="(card, index) in displayCards" :key="index" :card="card" disabled /></view>
      <text class="stars" :aria-label="`${starCount}星推荐`">{{ starText }}</text>
      <view class="type-row"><text>推荐牌型</text><text>{{ typeName }}</text></view>
    </view>

    <text class="section-title">原因：</text>
    <view class="surface-card reasons">
      <view v-for="(reason, index) in reasons" :key="reason"><text class="index">{{ index + 1 }}</text><text>{{ reason }}</text></view>
    </view>
    <view class="decision-actions">
      <u-button type="primary" color="#0b5d3b" shape="circle" text="采用" @click="accept" />
      <u-button plain color="#0b5d3b" shape="circle" text="取消" @click="back" />
    </view>
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
const typeName = computed(() => ({ single: '单张', pair: '对子', triple: '三张', triple_with_pair: '三带二', straight: '顺子', double_sequence: '三连对', steel_plate: '钢板', bomb: '炸弹', straight_flush: '同花顺', joker_bomb: '四王炸' }[store.recommendationType?.type] || '计算中'))
const expectedDelta = computed(() => ((store.recommendationExpectedValue || 0.5) - 0.5) * 100)
const expectedText = computed(() => `此牌 Expected Value ${expectedDelta.value >= 0 ? '+' : ''}${expectedDelta.value.toFixed(1)}`)
const reasons = computed(() => [
  ...(store.recommendationReason || '正在分析当前牌局').split('；').filter(Boolean),
  expectedText.value
])
const starCount = computed(() => Math.max(1, Math.min(5, Math.round(3 + expectedDelta.value / 10))))
const starText = computed(() => `${'★'.repeat(starCount.value)}${'☆'.repeat(5 - starCount.value)}`)
const back = () => uni.navigateBack()
const accept = () => {
  store.selectedIndices = [...store.recommendationIndices]
  uni.navigateBack()
  uni.showToast({ title: store.selectedIndices.length ? '已选中推荐牌' : '当前建议过牌', icon: 'none' })
}
</script>

<style scoped lang="scss">
.recommend-card { display: flex; flex-direction: column; align-items: center; text-align: center; }.ai-orb { width: 92rpx; height: 92rpx; margin-bottom: 18rpx; display: flex; align-items: center; justify-content: center; border-radius: 50%; color: #fff; background: linear-gradient(135deg,#0b5d3b,#2a9663); font-weight: 900; }
.recommend-title { margin: 22rpx 0 8rpx; font-size: 40rpx; font-weight: 800; }.recommend-label { align-self:flex-start; margin-top:28rpx; color:#18372a; font-weight:800; }.cards { display: flex; gap: 10rpx; margin: 20rpx 0; }.stars { margin:2rpx 0 24rpx; color:#e4b83e; font-size:38rpx; letter-spacing:5rpx; text-shadow:0 2rpx 6rpx rgba(159,112,0,.18); }.type-row { width: 100%; padding-top: 22rpx; display: flex; justify-content: space-between; border-top: 1rpx solid #e3ece6; font-weight: 700; }
.reasons { margin-bottom: 28rpx; }.reasons view { display: flex; align-items: center; padding: 18rpx 0; }.index { width: 46rpx; height: 46rpx; margin-right: 18rpx; display: flex; align-items:center; justify-content:center; border-radius:50%; color:#16784b; background:#e5f4eb; font-weight:800; }.decision-actions { display:grid; grid-template-columns:1.2fr 1fr; gap:18rpx; }
</style>
