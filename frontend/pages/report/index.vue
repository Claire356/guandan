<template>
  <view class="page-shell safe-bottom">
    <view class="personality-card">
      <text class="eyebrow">本局人格画像</text><text class="personality">{{ report.personality }}</text>
      <text class="personality-desc">理性规划牌序，在收益与风险之间保持稳定判断。</text>
    </view>

    <text class="section-title">五维行为评分</text>
    <view class="surface-card metrics">
      <MetricBar v-for="item in metrics" :key="item.key" :label="item.label" :value="report.metrics[item.key]" />
    </view>

    <text class="section-title">AI复盘</text>
    <view class="surface-card analysis">
      <view><u-icon name="checkmark-circle-fill" color="#2a9663" size="22" /><view><text>总结</text><text class="muted">{{ report.summary }}</text></view></view>
      <view><u-icon name="warning-fill" color="#d6a640" size="22" /><view><text>需要留意</text><text class="muted">{{ report.mistake }}</text></view></view>
      <view><u-icon name="info-circle-fill" color="#16784b" size="22" /><view><text>下一局建议</text><text class="muted">{{ report.suggestion }}</text></view></view>
    </view>
    <u-button type="primary" color="#0b5d3b" shape="circle" text="查看历史记录" @click="history" />
    <u-button class="secondary" plain color="#0b5d3b" shape="circle" text="返回首页" @click="home" />
  </view>
</template>

<script setup>
import { computed } from 'vue'
import { useGameStore } from '@/store/game'
import MetricBar from '@/components/MetricBar.vue'
const store = useGameStore()
const fallback = { personality:'均衡稳健型', summary:'整体牌序清晰，关键轮次保持了较好的资源控制。', mistake:'中盘有一次过早拆对。', suggestion:'保留中高对子，观察队友牌权。', metrics:{ attack:68, cooperation:76, risk:55, hesitation:38, emotion:82 } }
const report = computed(() => store.report || fallback)
const metrics = [{key:'attack',label:'攻击性'},{key:'risk',label:'风险偏好'},{key:'cooperation',label:'团队协作'},{key:'hesitation',label:'决策犹豫'},{key:'emotion',label:'情绪稳定'}]
const history = () => uni.navigateTo({ url:'/pages/history/index' })
const home = () => uni.reLaunch({ url:'/pages/index/index' })
</script>

<style scoped lang="scss">
.personality-card { padding:42rpx 34rpx; border-radius:28rpx; color:#fff; background:linear-gradient(135deg,#0b5d3b,#239261); }.eyebrow { display:block; font-size:23rpx; color:rgba(255,255,255,.7); }.personality { display:block; margin:14rpx 0; font-size:44rpx; font-weight:900; }.personality-desc { font-size:25rpx; line-height:1.7; color:rgba(255,255,255,.78); }
.metrics { padding-bottom:8rpx; }.analysis { margin-bottom:26rpx; }.analysis>view { display:flex; gap:18rpx; padding:20rpx 0; border-bottom:1rpx solid #edf1ee; }.analysis>view:last-child { border:0; }.analysis view view { flex:1; display:flex; flex-direction:column; gap:8rpx; line-height:1.6; }.secondary { margin-top:16rpx; }
</style>
