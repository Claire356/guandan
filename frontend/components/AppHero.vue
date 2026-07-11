<template>
  <view class="hero">
    <view class="hero__badge">AI · 规则训练</view>
    <text class="hero__title">{{ title }}</text>
    <text class="hero__subtitle">{{ subtitle }}</text>
    <slot />
  </view>
</template>

<script setup>
defineProps({ title: String, subtitle: String })
</script>

<style scoped lang="scss">
.hero { padding: 46rpx 36rpx; border-radius: 30rpx; color: #fff; background: linear-gradient(145deg, #084c31, #117c50); box-shadow: 0 16rpx 40rpx rgba(8, 76, 49, .2); }
.hero__badge { display: inline-flex; padding: 8rpx 18rpx; border: 1rpx solid rgba(255,255,255,.3); border-radius: 99rpx; font-size: 22rpx; color: #e2f5e9; }
.hero__title { display: block; margin-top: 24rpx; font-size: 54rpx; line-height: 1.2; font-weight: 800; }
.hero__subtitle { display: block; margin-top: 14rpx; font-size: 27rpx; line-height: 1.7; color: rgba(255,255,255,.78); }
</style>
