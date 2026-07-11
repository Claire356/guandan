<template>
  <view class="metric">
    <view class="row-between"><text>{{ label }}</text><text class="metric__value">{{ value }}</text></view>
    <u-line-progress :percentage="value" :showText="false" activeColor="#16784b" inactiveColor="#e4ece7" height="8" />
  </view>
</template>

<script setup>
defineProps({ label: String, value: Number })
</script>

<style scoped>
.metric { margin-bottom: 24rpx; font-size: 27rpx; }
.metric__value { color: #16784b; font-weight: 700; }
</style>
