<template>
  <view class="card" :class="[{ selected, disabled }, colorClass]" @click="$emit('select')">
    <text class="card__label">{{ displayLabel }}</text>
    <text class="card__suit">{{ suit }}</text>
  </view>
</template>

<script setup>
import { computed } from 'vue'
const props = defineProps({ card: { type: [String, Object], required: true }, selected: Boolean, disabled: Boolean })
defineEmits(['select'])
const label = computed(() => typeof props.card === 'string' ? props.card : props.card.label || `${props.card.suit || ''}${props.card.rank || ''}`)
const suit = computed(() => label.value.slice(0, 1))
const displayLabel = computed(() => label.value.slice(1) || label.value)
const colorClass = computed(() => ['♥', '♦'].includes(suit.value) ? 'red' : 'black')
</script>

<style scoped lang="scss">
.card { position: relative; width: 82rpx; height: 118rpx; flex: 0 0 82rpx; padding: 10rpx; border: 2rpx solid #dce5df; border-radius: 12rpx; background: #fff; box-shadow: 0 5rpx 12rpx rgba(0,0,0,.15); transition: transform .12s ease; }
.card.selected { transform: translateY(-18rpx); border-color: #d8b65b; box-shadow: 0 8rpx 20rpx rgba(216,182,91,.4); }
.card.red { color: #cc3d3d; } .card.black { color: #1d2923; }
.card__label { display: block; font-size: 30rpx; font-weight: 800; line-height: 1; }
.card__suit { display: block; margin-top: 8rpx; font-size: 28rpx; }
</style>
