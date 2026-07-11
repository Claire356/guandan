<template>
  <view class="page-shell safe-bottom">
    <view class="row-between history-head"><view><text class="title">训练历史</text><text class="muted">复盘每一次关键选择</text></view><u-tag :text="`${items.length} 条`" type="success" plain /></view>
    <view v-if="items.length" class="history-list">
      <view v-for="(item,index) in items" :key="index" class="surface-card history-item">
        <view class="row-between"><view class="round-icon">{{ index + 1 }}</view><u-tag :text="item.pattern || '训练'" size="mini" type="success" plain /></view>
        <text class="history-title">{{ item.player || '你' }} · {{ item.message || '完成训练牌局' }}</text>
        <text class="muted">{{ logs[index] || '本局行为记录已保存' }}</text>
        <view class="history-meta"><text>标准四人局</text><text>{{ index + 1 }} 分钟前</text></view>
      </view>
    </view>
    <view v-else class="surface-card empty"><u-empty mode="history" text="暂无训练记录" /><u-button type="primary" color="#0b5d3b" shape="circle" text="开始第一局" @click="training" /></view>
    <u-button v-if="items.length" plain color="#0b5d3b" shape="circle" text="继续训练" @click="training" />
  </view>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { useGameStore } from '@/store/game'
const store = useGameStore()
onMounted(() => store.loadHistory())
const items = computed(() => store.history)
const logs = computed(() => store.logs)
const training = () => uni.navigateTo({ url:'/pages/training/index' })
</script>

<style scoped lang="scss">
.history-head { margin:10rpx 0 28rpx; }.history-head>view { display:flex; flex-direction:column; gap:8rpx; }.title { font-size:42rpx; font-weight:900; }.history-list { display:flex; flex-direction:column; gap:18rpx; margin-bottom:26rpx; }.history-item { display:flex; flex-direction:column; gap:14rpx; }.round-icon { width:52rpx; height:52rpx; display:flex; align-items:center; justify-content:center; border-radius:16rpx; color:#fff; background:#16784b; font-weight:800; }.history-title { font-size:30rpx; font-weight:700; }.history-meta { padding-top:14rpx; display:flex; justify-content:space-between; border-top:1rpx solid #e8eeea; color:#98a39d; font-size:22rpx; }.empty { padding:60rpx 30rpx; }
</style>
