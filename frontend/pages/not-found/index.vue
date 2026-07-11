<template>
  <view class="page-shell not-found safe-bottom">
    <view class="surface-card not-found__card">
      <view class="not-found__mark">404</view>
      <text class="not-found__title">这张牌不在桌上</text>
      <text class="muted">页面可能已移动，返回首页继续训练吧。</text>
      <u-button type="primary" color="#0b5d3b" shape="circle" text="返回首页" @click="home" />
    </view>
  </view>
</template>

<script setup>
const home = () => uni.reLaunch({ url: '/pages/index/index' })
</script>

<style scoped lang="scss">
.not-found { display: flex; align-items: center; justify-content: center; }
.not-found__card { width: 100%; max-width: 620rpx; padding: 70rpx 44rpx; display: flex; flex-direction: column; align-items: center; gap: 24rpx; text-align: center; }
.not-found__mark { color: #16784b; font-size: 96rpx; line-height: 1; font-weight: 900; letter-spacing: 8rpx; }
.not-found__title { font-size: 38rpx; font-weight: 800; }
</style>
